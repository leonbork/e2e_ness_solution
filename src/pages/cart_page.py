import re
from playwright.sync_api import Page, expect
from src.base.base_page import BasePage
from src.base.smart_locator import SmartLocator
from src.utils.logger import get_logger
import allure

logger = get_logger(__name__)

class CartPage(BasePage):
    # Class-level Locators
    CART_TOTAL_PRICE_SELECTORS = [
        "[data-test-id='SUBTOTAL'] span.text-display-span",
        "[data-test-id='SUBTOTAL'] span",
        "[data-test-id='SUBTOTAL']",
        ".cart-summary-line-item .val span",
        ".cart-summary-item__value span",
        "div.total-row span",
        ".summary-total",
        "text='Subtotal' >> xpath=.."
    ]
    EMPTY_CART_SELECTOR = ".empty-cart, .cart-empty, .font-title-3"

    def __init__(self, page: Page):
        super().__init__(page)
        self.cart_total_price = SmartLocator("Cart Total Price", self.CART_TOTAL_PRICE_SELECTORS)
        
    def assert_cart_total_not_exceeds(self, budget_per_item: float, items_count: int) -> None:
        max_budget = budget_per_item * items_count
        logger.info(f"Validating cart max budget: {budget_per_item} * {items_count} = {max_budget}")
        
        with allure.step("Navigate to Cart and validate totals"):
            self._ensure_on_cart_page()
            self.capture_screenshot("Cart_Page_Before_Validation")
            
            if "Security Measure" in self.page.title():
                import pytest
                logger.warning("eBay Datadome CAPTCHA triggered on Cart. Skipping evaluation gracefully.")
                pytest.skip("Test blocked by eBay CAPTCHA on Cart Page (non-Chromium engine limitation).")
                
            self._validate_not_empty()
            
            total_text = self.get_text(self.cart_total_price, timeout_per_selector=5000)
                
            logger.info(f"Extracted cart total string: {total_text}")
            
            actual_total = self._parse_cart_total(total_text)
            self._assert_budget(actual_total, max_budget)

    def _ensure_on_cart_page(self) -> None:
        if "cart.ebay.com" not in self.page.url:
            self.page.locator("a[href*='cart.ebay.com'], .gh-cart-icon, a[aria-label*='cart' i]").first.click(force=True)
        self.page.wait_for_load_state("networkidle", timeout=5000)

    def _validate_not_empty(self) -> None:
        is_empty_text = "empty" in self.page.title().lower()
        is_empty_selector = self.page.locator(self.EMPTY_CART_SELECTOR).first.is_visible()
        
        if is_empty_text or is_empty_selector:
            logger.error("Cart is empty!")
            raise AssertionError("Cart is empty, could not validate total.")

    def _parse_cart_total(self, total_text: str) -> float:
        price_match = re.search(r'[\d,]+(\.\d+)?', total_text)
        
        if not price_match:
            raise ValueError(f"Could not parse a numeric price from '{total_text}'")
            
        parsed_price_str = price_match.group(0).replace(",", "")
        actual_total = float(parsed_price_str)
        logger.info(f"Parsed real total as Float: {actual_total}")
        return actual_total

    def _assert_budget(self, actual: float, limit: float) -> None:
        assert actual <= limit, f"Cart total {actual} EXCEEDS max budget {limit}"
        logger.info(f"Validation successful: {actual} <= {limit}")
