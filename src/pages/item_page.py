import os
import random
import time

import pytest
from playwright.sync_api import Page
from src.base.base_page import BasePage
from src.base.smart_locator import SmartLocator
from src.utils.logger import get_logger
import allure

logger = get_logger(__name__)

_DEBUG_DIR = "debug"


class ItemPage(BasePage):
    # Class-level Locators
    ADD_TO_CART_BTN_SELECTORS = [
        "a[id='isCartBtn_btn']",
        "span:has-text('Add to cart')",
        "[data-testid='x-atc-action']"
    ]
    DROPDOWN_SELECTOR = "select[class*='x-msku__select-box'], select.listbox__native, select.msku-sel"
    OPTION_SELECTOR = "option, [role='option']"

    def __init__(self, page: Page):
        super().__init__(page)
        self.add_to_cart_btn = SmartLocator("Add To Cart Button", self.ADD_TO_CART_BTN_SELECTORS)
        os.makedirs(_DEBUG_DIR, exist_ok=True)

    def add_items_to_cart(self, urls: list[str]) -> None:
        """
        Iterates over a list of URLs and delegates cart addition to dynamic helpers.
        Each item is processed independently — a failure on one item is logged and skipped
        so remaining items are still attempted.
        """
        for index, url in enumerate(urls):
            try:
                self._process_single_item((index, url))
            except Exception as e:
                logger.error(f"Item {index + 1} failed and will be skipped: {e}")

    def _process_single_item(self, enumerated_item: tuple) -> None:
        index, url = enumerated_item
        logger.info(f"Adding item {index + 1} to cart: {url}")

        with allure.step(f"Add item to cart: {url}"):
            self._navigate_and_wait(url)
            self._handle_variant_dropdowns()
            self._dump_html(f"item_{index}_before")
            self._click_add_to_cart_and_wait(index)
            self._return_to_search()

    def _navigate_and_wait(self, url: str) -> None:
        self.page.goto(url)
        self.page.wait_for_load_state("domcontentloaded")

        if "Security Measure" in self.page.title():
            logger.warning("eBay Datadome CAPTCHA triggered on Item Page. Skipping evaluation gracefully.")
            pytest.skip("Test blocked by eBay CAPTCHA on Item Page (Datadome bot interception).")

    def _handle_variant_dropdowns(self) -> None:
        try:
            dropdowns = self.page.locator(self.DROPDOWN_SELECTOR).all()
            visible_dropdowns = [d for d in dropdowns if d.is_visible()]
            for dropdown in visible_dropdowns:
                self._select_random_variant(dropdown)
        except Exception as e:
            logger.warning(f"Failed to handle variant selection: {e}")

    def _select_random_variant(self, dropdown) -> None:
        options = dropdown.locator(self.OPTION_SELECTOR).all()
        values = [opt.get_attribute("value") for opt in options]
        valid_values = [v for v in values if v and v != "-1"]

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
            # Wait for the cart AJAX request to settle before navigating away.
            # Falls back to a short fixed wait if networkidle is not reached in time.
            try:
                self.page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                self.page.wait_for_timeout(2000)
            self.capture_screenshot(f"Added_Item_{index}")
            self._dump_html(f"item_{index}_after")
        except Exception as e:
            logger.error(f"Failed to add item to cart: {e}")
            self.capture_screenshot(f"Failed_To_Add_Item_{index}")
            self._dump_html(f"item_dump_exception_{index}")
            raise

    def _return_to_search(self) -> None:
        """Navigate back to the search results page after adding an item to cart."""
        with allure.step("Return to search screen"):
            try:
                self.page.go_back()
                self.page.wait_for_load_state("domcontentloaded")
                logger.info("Returned to search screen successfully.")
            except Exception as e:
                logger.warning(f"Could not navigate back to search screen: {e}")

    def _dump_html(self, name: str) -> None:
        path = os.path.join(_DEBUG_DIR, f"chromium_{name}.html")
        try:
            with open(path, "w") as f:
                f.write(self.page.content())
        except Exception as e:
            logger.warning(f"Failed to write HTML dump '{path}': {e}")
