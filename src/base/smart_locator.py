from typing import List, Optional
from playwright.sync_api import Page, Locator
from src.utils.logger import get_logger
import allure

logger = get_logger(__name__)

class SmartLocator:
    """
    Utility class to handle multiple locators for a single element.
    Provides resilience by falling back to alternative locators if the primary fails.
    """

    def __init__(self, name: str, selectors: List[str]):
        """
        :param name: Human-readable name of the element (for logging)
        :param selectors: List of Playwright selectors (e.g. ['#id', '//*[@id="id"]'])
        """
        self.name = name
        self.selectors = selectors

    def _try_locate(self, page: Page, selector: str, timeout: float) -> Optional[Locator]:
        try:
            loc = page.locator(selector).first
            # wait for it to be visible or attached within the short timeout
            loc.wait_for(state='visible', timeout=timeout)
            return loc
        except Exception:
            return None

    def resolve(self, page: Page, timeout_per_selector: float = 8000) -> Locator:
        """
        Attempts to find the element using the provided selectors in order.
        Raises an exception if all selectors fail, taking a screenshot via Allure.
        """
        logger.info(f"Attempting to resolve SmartLocator for '{self.name}'")
        
        for index, selector in enumerate(self.selectors):
            logger.info(f"[{self.name}] Try {index + 1}/{len(self.selectors)} Using selector: {selector}")
            loc = self._try_locate(page, selector, timeout_per_selector)
            if loc is not None:
                logger.info(f"[{self.name}] Success! Resolved using: {selector}")
                return loc
            else:
                logger.warning(f"[{self.name}] Failed to resolve using: {selector}")

        # If we reach here, all locators failed
        error_msg = f"Failed to locate '{self.name}' after trying {len(self.selectors)} selectors."
        logger.error(error_msg)
        
        # Take screenshot on final failure and attach to allure
        screenshot_bytes = page.screenshot(full_page=True)
        allure.attach(
            screenshot_bytes, 
            name=f"{self.name}_failure_screenshot", 
            attachment_type=allure.attachment_type.PNG
        )
        
        raise Exception(error_msg)
