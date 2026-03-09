from playwright.sync_api import Page
from src.base.smart_locator import SmartLocator
from src.utils.logger import get_logger
from config.config import BASE_URL
import allure

logger = get_logger(__name__)

class BasePage:
    """
    Base abstraction layer for all Page Objects.
    Encapsulates Playwright interactions and integrates with SmartLocator.
    """

    def __init__(self, page: Page):
        self.page = page

    def navigate(self, path: str = ""):
        url = f"{BASE_URL}{path}"
        logger.info(f"Navigating to {url}")
        self.page.goto(url)

    def click(self, smart_locator: SmartLocator, timeout_per_selector: float = 8000):
        """
        Resolves the smart locator and clicks the element.
        """
        logger.info(f"Clicking on '{smart_locator.name}'")
        with allure.step(f"Click on {smart_locator.name}"):
            loc = smart_locator.resolve(self.page, timeout_per_selector)
            loc.click()

    def fill(self, smart_locator: SmartLocator, text: str, timeout_per_selector: float = 3000):
        """
        Resolves the smart locator and fills the element with text.
        """
        logger.info(f"Filling '{smart_locator.name}' with text: {text}")
        with allure.step(f"Fill {smart_locator.name} with '{text}'"):
            loc = smart_locator.resolve(self.page, timeout_per_selector)
            loc.fill(text)

    def get_text(self, smart_locator: SmartLocator, timeout_per_selector: float = 3000) -> str:
        """
        Resolves the smart locator and returns its inner text.
        """
        logger.info(f"Getting text from '{smart_locator.name}'")
        with allure.step(f"Get text from {smart_locator.name}"):
            loc = smart_locator.resolve(self.page, timeout_per_selector)
            return loc.inner_text()
            
    def capture_screenshot(self, name: str):
        """
        Takes a screenshot and attaches it to Allure.
        """
        try:
            screenshot_bytes = self.page.screenshot(full_page=True)
            allure.attach(
                screenshot_bytes, 
                name=name, 
                attachment_type=allure.attachment_type.PNG
            )
            logger.info(f"Captured screenshot: {name}")
        except Exception as e:
            logger.error(f"Failed to capture screenshot {name}: {e}")
