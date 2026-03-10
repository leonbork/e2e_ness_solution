import re
from playwright.sync_api import Page
from src.base.base_page import BasePage
from src.base.smart_locator import SmartLocator
from src.utils.logger import get_logger
import allure

logger = get_logger(__name__)

class SearchPage(BasePage):
    # Class-level Locators
    SEARCH_INPUT_SELECTORS = [
        "input[aria-label='Search for anything']",
        "input[name='_nkw']",
        "#gh-ac"
    ]
    SEARCH_BUTTON_SELECTORS = [
        "button[type='submit']",
        "button[id='gh-search-btn']",
        "input[value='Search']",
        "#gh-btn"
    ]
    RESULTS_SELECTOR = ".srp-results, .srp-river"
    ITEM_CARD_SELECTOR = "ul.srp-results li.s-item, .srp-results .s-item, .srp-results .s-card"
    PRICE_SELECTOR = ".s-item__price, .s-card__price"
    LINK_SELECTOR = ".s-item__link, .s-card__link"
    NEXT_BTN_SELECTOR = "a.pagination__next, a[aria-label='Next page']"
    MAX_PRICE_INPUT_SELECTORS = [
        "input[aria-label='Maximum Value in $']",
        "input[name='_udhi']",
        ".x-refine__price input:last-of-type",
    ]
    PRICE_FILTER_GO_SELECTORS = [
        "button[aria-label='Submit price range']",
        ".x-refine__price button",
        "button.fake-btn:has-text('Go')",
    ]

    def __init__(self, page: Page):
        super().__init__(page)
        self.search_input = SmartLocator("Search Input Field", self.SEARCH_INPUT_SELECTORS)
        self.search_button = SmartLocator("Search Submit Button", self.SEARCH_BUTTON_SELECTORS)

    def search_items_by_name_under_price(
        self, 
        query: str, 
        max_price: float, 
        limit: int = 5,
        max_pages_to_check: int = 5
    ) -> list[str]:
        """
        Searches for a query, applies a max price filter, and returns up to `limit` URLs of items matching criteria.
        Handles Pagination dynamically without nested structures.
        """
        urls = []
        with allure.step(f"Search for '{query}' and collect up to {limit} items under {max_price}"):
            self.fill(self.search_input, query)
            self.click(self.search_button)
            self.page.wait_for_selector(self.RESULTS_SELECTOR, timeout=10000)
            
            self._apply_buy_it_now_filter()
            self._apply_max_price_filter(max_price)

            # Map over pages up to max pages. The helper handles early exit internally.
            page_sequence = range(1, max_pages_to_check + 1)
            # using a stateful lambda to allow breaking the mapping if quota met
            self._traverse_pages(page_sequence, urls, max_price, limit, max_pages_to_check)

        logger.info(f"Capping at {len(urls)} URLs collected overall.")
        return urls

    def _apply_max_price_filter(self, max_price: float) -> None:
        with allure.step(f"Apply max price filter: ${max_price}"):
            try:
                # Try each known max-price input selector
                price_input = None
                for selector in self.MAX_PRICE_INPUT_SELECTORS:
                    loc = self.page.locator(selector).first
                    if loc.is_visible(timeout=2000):
                        price_input = loc
                        logger.info(f"Found max price input using: {selector}")
                        break

                if not price_input:
                    logger.warning("Max price filter input not found on page — skipping UI filter, will filter manually.")
                    return

                price_input.click()
                price_input.fill(str(int(max_price)))

                # Click the "Go" submit button for the price range
                for selector in self.PRICE_FILTER_GO_SELECTORS:
                    btn = self.page.locator(selector).first
                    if btn.is_visible(timeout=1500):
                        btn.click(force=True)
                        logger.info(f"Submitted price filter using: {selector}")
                        break

                self.page.wait_for_load_state("networkidle", timeout=5000)
                logger.info(f"Max price filter applied: <= ${max_price}")
            except Exception as e:
                logger.warning(f"Could not apply max price filter: {e}. Will fall back to manual price parsing.")

    def _apply_buy_it_now_filter(self) -> None:
        with allure.step("Apply 'Buy It Now' filter to exclude Auctions"):
            try:
                loc = self.page.locator("ul.srp-sortable-bttn li:has-text('Buy It Now'), a:has-text('Buy It Now')").first
                if loc.is_visible(timeout=2000):
                    loc.click(timeout=3000, force=True)
                    self.page.wait_for_load_state("networkidle", timeout=3000)
            except Exception as e:
                logger.warning(f"Could not apply Buy It Now filter: {e}")

    def _traverse_pages(self, page_sequence: range, urls: list[str], max_price: float, limit: int, max_pages: int) -> None:
        def process_page(page_num):
            if len(urls) >= limit:
                return False
                
            logger.info(f"Scanning search results page {page_num}...")
            self._gather_urls_from_page(urls, max_price, limit)
            
            if len(urls) >= limit or page_num == max_pages:
                return False
                
            self._handle_pagination(len(urls))
            return True
            
        # Iterate until a page reports False (quota met or max page reached)
        for page_num in page_sequence:
            if not process_page(page_num):
                break

    def _gather_urls_from_page(self, urls: list[str], max_price: float, limit: int) -> None:
        items = self.page.locator(self.ITEM_CARD_SELECTOR).all()
        for item in items:
            self._process_single_card(item, urls, max_price, limit)

    def _process_single_card(self, item, urls: list[str], max_price: float, limit: int) -> None:
        if len(urls) >= limit:
            return
            
        try:
            self._extract_product_data(item, urls, max_price)
        except Exception as e:
            logger.warning(f"Error parsing item price or URL: {e}")

    def _extract_product_data(self, item, urls: list[str], max_price: float) -> None:
        # Exclude auction items which do not have a Buy It Now button natively
        # Sponsored Auctions often hide their native CSS tags entirely
        bids_locator = item.locator(".s-item__bids, .s-item__bidCount")
        if bids_locator.count() > 0:
            return
            
        try:
            card_text = item.inner_text(timeout=2000).lower()
            if "bid" in card_text or "offert" in card_text:
                return
        except Exception:
            pass
            
        price_element = item.locator(self.PRICE_SELECTOR).first
        is_visible = price_element.is_visible(timeout=500)
        
        self._evaluate_price(is_visible, price_element, item, urls, max_price)

    def _evaluate_price(self, is_visible: bool, price_element, item, urls: list[str], max_price: float) -> None:
        if not is_visible:
            return
            
        price_text = price_element.inner_text()
        price_match = re.search(r'[\d,]+(\.\d+)?', price_text)
        
        self._validate_and_append(price_match, item, urls, max_price)

    def _validate_and_append(self, price_match, item, urls: list[str], max_price: float) -> None:
        if not price_match:
            return
            
        parsed_price_str = price_match.group(0).replace(",", "")
        item_price = float(parsed_price_str)
        
        self._finalize_url_extraction(item_price, max_price, item, urls)

    def _finalize_url_extraction(self, item_price: float, max_price: float, item, urls: list[str]) -> None:
        if item_price > max_price:
            return
            
        link_element = item.locator(self.LINK_SELECTOR).first
        href = link_element.get_attribute("href")
        
        self._commit_url(href, item_price, max_price, urls)

    def _commit_url(self, href, item_price: float, max_price: float, urls: list[str]) -> None:
        if href and href not in urls:
            urls.append(href)
            logger.info(f"Found item under {max_price}: {item_price} at {href}")

    def _handle_pagination(self, current_url_count: int) -> None:
        next_btn = self.page.locator(self.NEXT_BTN_SELECTOR).first
        
        # Check if the button exists and is interactive before asking for attributes to avoid timeouts
        if not next_btn.is_visible(timeout=3000):
            logger.info("Pagination reached the end or 'Next' button not visible.")
            return

        is_disabled = next_btn.get_attribute("aria-disabled") == "true"
        self._execute_click_next(next_btn, is_disabled, current_url_count)

    def _execute_click_next(self, next_btn, is_disabled: bool, current_url_count: int) -> None:
        if is_disabled:
            logger.info("Pagination reached the end or 'Next' button disabled.")
            return
            
        logger.info(f"Collected {current_url_count} items. Clicking next page...")
        with allure.step("Click next page symbol"):
            next_btn.click(force=True)
            self.page.wait_for_selector(self.RESULTS_SELECTOR, timeout=10000)
