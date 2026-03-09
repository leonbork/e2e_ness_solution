from playwright.sync_api import Page
from src.base.base_page import BasePage
import allure
from src.utils.logger import get_logger

logger = get_logger(__name__)

class LoginPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

    def login_as_guest(self):
        """
        Stub for authentication as required by the exercise ('הזדהות').
        Since eBay requires complex CAPTCHAs for real logins in headless,
        we act as a Guest session.
        """
        with allure.step("Authenticate as Guest"):
            logger.info("Authenticating as Guest User (Stub)")
            self.navigate()
            # If there was a real login flow, it would go here.
            # self.click(self.SIGN_IN_BTN)
            self.page.wait_for_load_state("domcontentloaded")
