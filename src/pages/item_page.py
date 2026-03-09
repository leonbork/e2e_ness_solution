import random
import time
from playwright.sync_api import Page
from src.base.base_page import BasePage
from src.base.smart_locator import SmartLocator
from src.utils.logger import get_logger
import allure

logger = get_logger(__name__)

class ItemPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        
        # Locators
        self.add_to_cart_btn = SmartLocator("Add To Cart Button", [
            "a[id='isCartBtn_btn']",
            "span:has-text('Add to cart')",
            "[data-testid='x-atc-action']"
        ])
        
    def add_items_to_cart(self, urls: list[str]) -> None:
        """
        Iterates over a list of URLs, handling dynamic variants and adding them to the cart.
        """
        for index, url in enumerate(urls):
            logger.info(f"Adding item {index + 1}/{len(urls)} to cart: {url}")
            with allure.step(f"Add item to cart: {url}"):
                self.page.goto(url)
                self.page.wait_for_load_state("domcontentloaded")
                
                # Check for variant dropdowns (e.g. Color, Size)
                try:
                    dropdowns = self.page.locator("select[class*='x-msku__select-box']").all()
                    for dropdown in dropdowns:
                        if dropdown.is_visible():
                            # Extract all valid options except the default 'Select' or '-1'
                            options = dropdown.locator("option").all()
                            valid_values = []
                            for opt in options:
                                value = opt.get_attribute("value")
                                # Exclude placeholders
                                if value and value != "-1":
                                    valid_values.append(value)
                            
                            if valid_values:
                                random_value = random.choice(valid_values)
                                dropdown.select_option(random_value)
                                logger.info(f"Selected variant: {random_value}")
                                time.sleep(0.5) # Slight delay to let DOM re-render combinations
                except Exception as e:
                    logger.warning(f"Failed to handle variant selection: {e}")
                
                 # Click Add to Cart
                try:
                    self.click(self.add_to_cart_btn, timeout_per_selector=5000)
                    logger.info("Clicked Add to Cart successfully.")
                    
                    # Take screenshot as proof
                    self.capture_screenshot(f"Added_Item_{index}")
                    
                    # Wait for cart page or success popup to ensure it actually added
                    # eBay usually redirects to cart or shows a side panel. Let's just wait for idle.
                    self.page.wait_for_load_state("networkidle", timeout=5000)
                except Exception as e:
                    logger.error(f"Failed to add item to cart: {e}")
                    self.capture_screenshot(f"Failed_To_Add_Item_{index}")
