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
        },
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "bypass_csp": True,
        "java_script_enabled": True
    }

@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args, request):
    # Conditionally inject Chromium-specific Blink flags
    browser_name = request.config.getoption("--browser")
    if browser_name == "chromium":
        return {
            **browser_type_launch_args,
            "args": ["--disable-blink-features=AutomationControlled"]
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
