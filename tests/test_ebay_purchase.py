import pytest
import allure
from src.pages.search_page import SearchPage
from src.pages.item_page import ItemPage
from src.pages.cart_page import CartPage
from config.config import TEST_DATA
from playwright.sync_api import expect

@allure.feature("eBay E2E Purchase Flow")
@allure.story("Search items, filter by price, add to cart, and validate totals")
def test_ebay_purchase_flow(page):
    """
    Main E2E test mapping to the Senior Automation Developer capabilities.
    Steps:
    1. Search for items and get up to N links under a certain price.
    2. Add all these items to the cart.
    3. Assert the cart total doesn't exceed the budget limit.
    """
    # Initialize Page Objects
    search_page = SearchPage(page)
    item_page = ItemPage(page)
    cart_page = CartPage(page)
    
    # Read test variables from config
    query = TEST_DATA.get("search_query", "shoes")
    max_price = TEST_DATA.get("max_price", 220)
    limit = TEST_DATA.get("limit", 5)
    budget_per_item = TEST_DATA.get("budget_per_item", 220)
    
    with allure.step("Navigate to eBay Home"):
        search_page.navigate()
        
    with allure.step(f"Search items by name under ${max_price}"):
        # Returns up to X item URLs
        urls = search_page.search_items_by_name_under_price(query, max_price, limit)
        allure.attach(str(urls), name="Fetched_URLs", attachment_type=allure.attachment_type.TEXT)
        
        # It's okay if it found 0 (instructed by requirements)
        if not urls:
            pytest.skip(f"No items found for '{query}' under {max_price}. Skipping further steps.")
            
    with allure.step("Add returned items to cart"):
        item_page.add_items_to_cart(urls)
        
    with allure.step("Assert total cart value"):
        # The number of items to validate is the number of URLs successfully processed.
        # Note: If an individual item addition failed (like out of stock), the overall cart
        # might be cheaper. The exact requirement: "Verify sum <= budgetPerItem * urls.length"
        cart_page.assert_cart_total_not_exceeds(budget_per_item, len(urls))
