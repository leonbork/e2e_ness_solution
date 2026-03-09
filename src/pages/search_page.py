import re
from playwright.sync_api import Page
from src.base.base_page import BasePage
from src.base.smart_locator import SmartLocator
from src.utils.logger import get_logger
import allure

logger = get_logger(__name__)

class SearchPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        
        # Locators
        self.search_input = SmartLocator("Search Input Field", [
            "input[aria-label='Search for anything']",
            "input[name='_nkw']",
            "#gh-ac"
        ])
        
        self.search_button = SmartLocator("Search Submit Button", [
            "input[value='Search']",
            "button[id='gh-btn']",
            "#gh-btn"
        ])

        # We don't strictly use SmartLocator for all dynamic list items since we iterate over them natively in Playwright.

    def search_items_by_name_under_price(self, query: str, max_price: float, limit: int = 5) -> list[str]:
        """
        Searches for a query, applies a max price filter, and returns up to `limit` URLs of items matching criteria.
        Handles Pagination if < 5 items on the first page.
        """
        urls = []
        
        with allure.step(f"Search for '{query}' and collect up to {limit} items under {max_price}"):
            # 1. Search for items
            self.fill(self.search_input, query)
            self.click(self.search_button)
            
            # 2. Wait for results to load
            self.page.wait_for_selector(".srp-results", timeout=10000)
            
            # It's better to iterate pages up to a reasonable amount
            max_pages_to_check = 5
            
            for page_num in range(1, max_pages_to_check + 1):
                logger.info(f"Scanning search results page {page_num}...")
                
                # Fetch all item cards on the current page
                items = self.page.locator("ul.srp-results li.s-item").all()
                for item in items:
                    try:
                        # Extract price text
                        price_element = item.locator(".s-item__price")
                        # Sometimes rows might not be products (e.g. ads or empty stubs without price)
                        if not price_element.is_visible(timeout=500):
                            continue
                        
                        price_text = price_element.inner_text()
                        
                        # Handle cases like "ILs 150.00 to ILs 200.00" - take the minimum or just parse first float
                        price_match = re.search(r'[\d,]+(\.\d+)?', price_text)
                        if price_match:
                            parsed_price_str = price_match.group(0).replace(",", "")
                            item_price = float(parsed_price_str)
                            
                            if item_price <= max_price:
                                link_element = item.locator(".s-item__link")
                                href = link_element.get_attribute("href")
                                if href and href not in urls:
                                    urls.append(href)
                                    logger.info(f"Found item under {max_price}: {item_price} at {href}")
                                    
                                if len(urls) >= limit:
                                    logger.info(f"Successfully collected {limit} URLs.")
                                    return urls
                    except Exception as e:
                        logger.warning(f"Error parsing item price or URL: {e}")
                        continue
                
                # If we haven't reached the limit, try to go to the next page
                if len(urls) < limit:
                    next_btn = self.page.locator("a.pagination__next")
                    if next_btn.is_visible() and not next_btn.get_attribute("aria-disabled") == "true":
                        logger.info(f"Collected {len(urls)} items. Clicking next page...")
                        with allure.step("Click next page symbol"):
                            next_btn.click()
                            self.page.wait_for_selector(".srp-results", timeout=10000)
                    else:
                        logger.info("Pagination reached the end or 'Next' button disabled.")
                        break

        logger.info(f"Capping at {len(urls)} URLs collected overall.")
        return urls
