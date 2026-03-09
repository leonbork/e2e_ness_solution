import random
import time
from playwright.sync_api import Page
from src.base.base_page import BasePage
from src.base.smart_locator import SmartLocator
from src.utils.logger import get_logger
import allure

logger = get_logger(__name__)

class ItemPage(BasePage):
    # Class-level Locators
    ADD_TO_CART_BTN_SELECTORS = [
        "a[id='isCartBtn_btn']",
        "span:has-text('Add to cart')",
        "[data-testid='x-atc-action']"
    ]
    DROPDOWN_SELECTOR = "select[class*='x-msku__select-box'], select.listbox__native, select.msku-sel"
    OPTION_SELECTOR = "option"

    def __init__(self, page: Page):
        super().__init__(page)
        self.add_to_cart_btn = SmartLocator("Add To Cart Button", self.ADD_TO_CART_BTN_SELECTORS)
        
    def add_items_to_cart(self, urls: list[str]) -> None:
        """
        Iterates over a list of URLs and delegates cart addition to dynamic helpers.
        """
        # Completely flattened architecture. Dynamic iteration.
        list(map(self._process_single_item, enumerate(urls)))

    def _process_single_item(self, enumerated_item: tuple) -> None:
        index, url = enumerated_item
        logger.info(f"Adding item {index + 1} to cart: {url}")
        
        with allure.step(f"Add item to cart: {url}"):
            self._navigate_and_wait(url)
            self._handle_variant_dropdowns()
            self._click_add_to_cart_and_wait(index)

    def _navigate_and_wait(self, url: str) -> None:
        self.page.goto(url)
        self.page.wait_for_load_state("domcontentloaded")

    def _handle_variant_dropdowns(self) -> None:
        try:
            dropdowns = self.page.locator(self.DROPDOWN_SELECTOR).all()
            # Dynamic method filtering visible models without nested loops/ifs
            visible_dropdowns = list(filter(lambda d: d.is_visible(), dropdowns))
            list(map(self._select_random_variant, visible_dropdowns))
        except Exception as e:
            logger.warning(f"Failed to handle variant selection: {e}")

    def _select_random_variant(self, dropdown) -> None:
        options = dropdown.locator(self.OPTION_SELECTOR).all()
        # Extract valid values functionally
        values = list(map(lambda opt: opt.get_attribute("value"), options))
        valid_values = list(filter(lambda v: bool(v) and v != "-1", values))
        
        self._execute_drop_selection(dropdown, valid_values)

    def _execute_drop_selection(self, dropdown, valid_values: list[str]) -> None:
        if not valid_values:
            return
            
        random_value = random.choice(valid_values)
        dropdown.select_option(random_value)
        logger.info(f"Selected variant: {random_value}")
        time.sleep(0.5)

    def _click_add_to_cart_and_wait(self, index: int) -> None:
        try:
            self.click(self.add_to_cart_btn, timeout_per_selector=5000)
            logger.info("Clicked Add to Cart successfully.")
            self.capture_screenshot(f"Added_Item_{index}")
            self.page.wait_for_load_state("networkidle", timeout=5000)
        except Exception as e:
            logger.error(f"Failed to add item to cart: {e}")
            self.capture_screenshot(f"Failed_To_Add_Item_{index}")
