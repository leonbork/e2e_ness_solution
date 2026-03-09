import json
import os

def load_test_data() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), 'test_data.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Hardcoded or Env based variables
BASE_URL = os.getenv("BASE_URL", "https://www.ebay.com")
DEFAULT_TIMEOUT_MS = int(os.getenv("DEFAULT_TIMEOUT_MS", 10000))

TEST_DATA = load_test_data()
