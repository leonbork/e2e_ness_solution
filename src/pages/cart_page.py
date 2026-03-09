import re
from playwright.sync_api import Page, expect
from src.base.base_page import BasePage
from src.base.smart_locator import SmartLocator
from src.utils.logger import get_logger
import allure

logger = get_logger(__name__)

class CartPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        
        self.cart_total_price = SmartLocator("Cart Total Price", [
            "[data-test-id='SUBTOTAL'] span.text-display-span",
            ".cart-summary-line-item .val span",
            "div.total-row span"
        ])
        
    def assert_cart_total_not_exceeds(self, budget_per_item: float, items_count: int) -> None:
        """
        Calculates the maximum allowed budget and asserts the actual cart total is lower.
        """
        max_budget = budget_per_item * items_count
        logger.info(f"Validating cart max budget: {budget_per_item} * {items_count} = {max_budget}")
        
        with allure.step("Navigate to Cart and validate totals"):
            # Navigate to the explicitly known cart URL in case we aren't there yet
            self.navigate("/cart")
            self.page.wait_for_load_state("domcontentloaded")
            
            # The test spec requires taking a screenshot immediately of the cart
            self.capture_screenshot("Cart_Page_Before_Validation")
            
            # Check for empty cart
            if "empty" in self.page.title().lower() or self.page.locator(".empty-cart").is_visible():
                logger.error("Cart is empty!")
                raise AssertionError("Cart is empty, could not validate total.")
            
            total_text = self.get_text(self.cart_total_price)
            logger.info(f"Extracted cart total string: {total_text}")
            
            # Extract numbers like "$340.50" or "US $340.50" or "₪340.5" -> "340.50"
            price_match = re.search(r'[\d,]+(\.\d+)?', total_text)
            if not price_match:
                raise ValueError(f"Could not parse a numeric price from '{total_text}'")
                
            parsed_price_str = price_match.group(0).replace(",", "")
            actual_total = float(parsed_price_str)
            logger.info(f"Parsed real total as Float: {actual_total}")
            
            assert actual_total <= max_budget, f"Cart total {actual_total} EXCEEDS max budget {max_budget}"
            logger.info(f"Validation successful: {actual_total} <= {max_budget}")
