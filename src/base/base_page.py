import time
from typing import Callable, TypeVar

from playwright.sync_api import Page
from src.base.smart_locator import SmartLocator
from src.utils.logger import get_logger
from config.config import BASE_URL
import allure

logger = get_logger(__name__)

T = TypeVar("T")


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
            loc.click(force=True)

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

    def retry_action(
        self,
        action: Callable[[], T],
        retries: int = 3,
        backoff_seconds: float = 2.0,
        action_name: str = "action",
    ) -> T:
        """
        Executes a callable with exponential backoff retry.
        Implements the Retry + Backoff + Graceful Recovery pattern required by the exercise.

        :param action:          Zero-argument callable to attempt.
        :param retries:         Maximum number of retry attempts after the first failure.
        :param backoff_seconds: Base wait time between retries (doubles each attempt).
        :param action_name:     Human-readable label used in logs and Allure steps.
        :returns:               The return value of the successful action call.
        :raises:                The last exception if all attempts are exhausted.
        """
        last_exc: Exception | None = None
        delay = backoff_seconds

        for attempt in range(1, retries + 2):  # attempts: 1 … retries+1
            try:
                logger.info(f"[Retry] '{action_name}' — attempt {attempt}/{retries + 1}")
                result = action()
                if attempt > 1:
                    logger.info(f"[Retry] '{action_name}' succeeded on attempt {attempt}.")
                return result
            except Exception as exc:
                last_exc = exc
                if attempt <= retries:
                    logger.warning(
                        f"[Retry] '{action_name}' failed (attempt {attempt}): {exc}. "
                        f"Retrying in {delay:.1f}s…"
                    )
                    self.capture_screenshot(f"Retry_{action_name}_attempt_{attempt}")
                    time.sleep(delay)
                    delay *= 2  # exponential backoff
                else:
                    logger.error(
                        f"[Retry] '{action_name}' exhausted all {retries + 1} attempts. Last error: {exc}"
                    )
                    self.capture_screenshot(f"Retry_{action_name}_final_failure")

        raise last_exc

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
