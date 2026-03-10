# eBay E2E Automation Framework

A clean, scalable, object-oriented End-to-End automation framework for eBay, built with Python + Playwright + Pytest.

---

## Project Structure

```
e2e_ness_solution/
├── src/
│   ├── base/
│   │   ├── base_page.py          # Base class: click/fill/get_text/retry_action + Allure
│   │   └── smart_locator.py      # Multi-selector fallback locator with logging & screenshot
│   ├── pages/
│   │   ├── login_page.py         # Authentication stub (guest session)
│   │   ├── search_page.py        # Search, price filter UI, pagination, URL extraction
│   │   ├── item_page.py          # Item page: variants, add-to-cart, return to search
│   │   └── cart_page.py          # Cart navigation and budget assertion
│   └── utils/
│       └── logger.py             # Logger factory
├── tests/
│   ├── conftest.py               # Stealth, browser args, timeout, failure screenshot hook
│   └── test_ebay_purchase.py     # Main parametrized E2E test
├── config/
│   ├── config.py                 # ENV-based config loader (BASE_URL, DEFAULT_TIMEOUT_MS)
│   └── test_data.json            # Data-Driven test scenarios
├── .github/
│   └── workflows/
│       ├── playwright_e2e.yml    # Main CI: 4-browser matrix (push/PR)
│       └── playwright.yml        # Manual-only: Allure history report
├── images/
│   └── code_review_guidelines.txt  # AI code review analysis (exercise Section 4)
├── run_tests.sh                  # Mac/Linux: timestamped parallel run
├── run_tests.bat                 # Windows: timestamped parallel run
├── requirements.txt
└── pytest.ini
```

---

## Architecture

### Page Object Model (POM)
All DOM interaction is encapsulated in Page Objects (`SearchPage`, `ItemPage`, `CartPage`, `LoginPage`). Tests interact only with high-level methods — never with raw selectors.

### Smart Locators (`src/base/smart_locator.py`)
Each element defines **multiple fallback selectors**. At runtime, `SmartLocator.resolve()` tries each in order, logging every attempt. On total failure it attaches a full-page screenshot to Allure and raises a descriptive exception. Tests remain clean — they never reference selector strings directly.

### Retry + Backoff + Graceful Recovery
Three-layer resilience strategy:
- **Action-level**: `BasePage.retry_action(fn, retries=3, backoff_seconds=2.0)` — exponential backoff with per-attempt screenshots.
- **Test-level**: `pytest-rerunfailures` (`--reruns 2 --reruns-delay 3` in `pytest.ini`) reruns any failing test up to 2 times with a 3-second delay.
- **Graceful skips**: CAPTCHA detection and empty search results use `pytest.skip()` to abort without failing the suite.

### Data-Driven Testing (DDT)
`@pytest.mark.parametrize` is bound to `config/test_data.json`. Adding a new JSON object spawns a new independent test scenario with zero code changes.

### Session Isolation
Each test worker gets its own isolated `BrowserContext` (cookies, storage, history never shared). Fully compatible with `pytest-xdist` parallel workers.

### ENV-Based Configuration

| Variable | Default | Description |
|---|---|---|
| `BASE_URL` | `https://www.ebay.com` | Target site URL |
| `DEFAULT_TIMEOUT_MS` | `10000` | Global Playwright timeout, applied via `page.set_default_timeout()` |

---

## Core Functions

| Function | Location | Description |
|---|---|---|
| `login_as_guest()` | `LoginPage` | Authentication stub — navigates to eBay as guest |
| `search_items_by_name_under_price(query, max_price, limit)` | `SearchPage` | Searches, applies native max-price UI filter + Buy It Now filter, collects up to `limit` item URLs across pages |
| `add_items_to_cart(urls)` | `ItemPage` | Navigates each URL, selects random variants, clicks Add to Cart, returns to search screen, logs screenshot |
| `assert_cart_total_not_exceeds(budget_per_item, items_count)` | `CartPage` | Opens cart, reads subtotal, asserts total ≤ budget_per_item × items_count |

---

## Prerequisites

- Python 3.11+
- Allure CLI: `brew install allure` (Mac) or `npm install -g allure-commandline`

---

## How To Run

### 1. Clone & set up

```bash
git clone <repo-url> && cd e2e_ness_solution
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium firefox webkit
```

### 2. Run tests

**Mac / Linux** — timestamped Allure results folder per run:
```bash
./run_tests.sh
```

**Windows:**
```bat
run_tests.bat
```

**Or directly via Pytest:**
```bash
PYTHONPATH=. pytest tests/test_ebay_purchase.py -n 2 -v --alluredir=reports/allure-results
```

### 3. View the Allure report

```bash
allure serve reports/allure-results-YYYYMMDD_HHMMSS
```

---

## Cross-Browser & Multi-Version Testing

```bash
# Playwright-bundled Chromium (default)
pytest tests/test_ebay_purchase.py --browser chromium

# Firefox
pytest tests/test_ebay_purchase.py --browser firefox

# WebKit (Safari engine)
pytest tests/test_ebay_purchase.py --browser webkit

# System Google Chrome (different version from bundled Chromium)
pytest tests/test_ebay_purchase.py --browser chromium --browser-channel chrome

# Microsoft Edge
pytest tests/test_ebay_purchase.py --browser chromium --browser-channel msedge

# Full matrix locally
pytest tests/test_ebay_purchase.py --browser chromium --browser firefox --browser webkit
```

---

## CI/CD Pipeline (GitHub Actions)

**Main workflow**: `.github/workflows/playwright_e2e.yml` — triggers on every `push` and `pull_request` to `main`.

| Job | Engine | Notes |
|---|---|---|
| `chromium` | Playwright-bundled Chromium | Default engine |
| `firefox` | Playwright-bundled Firefox | |
| `webkit` | Playwright-bundled WebKit | Safari engine |
| `chrome` | System Google Chrome | Different Chromium version — covers multi-version requirement |

Each job:
- Installs only its own browser (`playwright install <browser> --with-deps`)
- Runs `pytest -n 2` with `--reruns 2` on transient failures
- Uploads a separate `allure-results-<browser>` artifact

**Manual workflow**: `.github/workflows/playwright.yml` — triggered via `workflow_dispatch`. Runs Chromium only and generates a persistent Allure report with history.

---

## Stability Notes

- **Stealth**: `playwright-stealth` scrubs `navigator.webdriver` fingerprints. Chromium also passes `--disable-blink-features=AutomationControlled`.
- **Price filter**: `SearchPage` fills eBay's native max-price input (`_udhi`) server-side first. Falls back to client-side per-card price parsing if the filter UI is absent (A/B variant).
- **Auction exclusion**: "Buy It Now" filter + raw DOM text scan removes sponsored auction items that bypass eBay's normal CSS class tagging.
- **Cart routing**: Direct `goto("https://cart.ebay.com")` bypasses eBay's unstable cart overlay/slider UI.

---

## AI-Generated Code Review (Exercise Section 4)

Static analysis of the provided AI-generated test code identifying architectural flaws and proposed fixes:

**[View Code Review Guidelines](images/code_review_guidelines.txt)**

Issues identified: no test framework (`pytest`/assertions), no POM, hardcoded credentials, browser never closed, missing context manager for `sync_playwright`, no assertion on API status, `import requests` inside a function, and test orchestration via `if __name__ == "__main__"` instead of a test runner.

---

## Assumptions & Limitations

1. **Authentication**: eBay's headless bot detection requires a guest flow. `LoginPage.login_as_guest()` fulfills the interface requirement; actual login would require CAPTCHA solving beyond the scope of this exercise.
2. **Item Availability**: Sold-out or restricted variants display as `value="-1"` dropdowns — the variant picker skips these automatically.
3. **Currency**: eBay localises prices by IP geolocation. The regex `[\d,]+(\.\d+)?` extracts the numeric component regardless of currency symbol, assuming a single currency per run.
4. **Chrome Version Matrix**: Playwright bundles its own Chromium and does not support arbitrary version pinning. The exercise requirement is met by running both bundled Chromium and system Chrome (`--browser-channel chrome`) in CI, which typically differ by several major versions.
5. **Cart Session**: Items are added within a single persistent browser session. Parallel multi-session cart operations would require shared authenticated state, which is out of scope for a guest flow.
