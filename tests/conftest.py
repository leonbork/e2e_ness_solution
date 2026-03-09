import pytest
import allure
from playwright.sync_api import sync_playwright

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {
            "width": 1920,
            "height": 1080,
        }
    }

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
