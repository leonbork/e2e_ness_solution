import pytest
import allure
from playwright.sync_api import sync_playwright
from playwright_stealth.stealth import Stealth

@pytest.fixture
def page(context):
    """
    Override default Pytest-Playwright page fixture to universally inject stealth scripts.
    This scrubs the navigator.webdriver signatures hiding the automated browser from eBay CAPTCHA.
    """
    page = context.new_page()
    stealth_bot = Stealth()
    stealth_bot.apply_stealth_sync(page)
    yield page
    page.close()

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args, request):
    browser_name = request.config.getoption("--browser")
    
    # Assign native-looking User Agents to prevent Bot fingerprinting mismatch
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    if browser_name == "firefox":
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
    elif browser_name == "webkit":
        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15"

    return {
        **browser_context_args,
        "viewport": {
            "width": 1920,
            "height": 1080,
        },
        "user_agent": user_agent,
        "bypass_csp": True,
        "java_script_enabled": True
    }

@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args, request):
    browser_name = request.config.getoption("--browser")
    if browser_name == "chromium":
        return {
            **browser_type_launch_args,
            "args": ["--disable-blink-features=AutomationControlled"]
        }
    elif browser_name == "firefox":
        return {
            **browser_type_launch_args,
            "firefox_user_prefs": {
                "dom.webdriver.enabled": False,
                "useAutomationExtension": False
            }
        }
    return browser_type_launch_args

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook to capture screenshot on test failure.
    """
    outcome = yield
    report = outcome.get_result()
    
    if report.when == "call" and report.failed:
        try:
            # We need to access the page fixture from the test item
            page = item.funcargs.get("page")
            if page:
                screenshot_bytes = page.screenshot(full_page=True)
                allure.attach(
                    screenshot_bytes, 
                    name=f"Failure_{item.name}", 
                    attachment_type=allure.attachment_type.PNG
                )
        except Exception as e:
            print(f"Fail to capture screenshot: {e}")
