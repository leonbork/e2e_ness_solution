#!/bin/bash
# run_tests.sh
# As per PDF guidelines, this script produces a unique allure results folder per run.

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RESULTS_DIR="reports/allure-results-${TIMESTAMP}"

echo "Executing tests in parallel matrix..."
echo "Results will be saved to: ${RESULTS_DIR}"

PYTHONPATH=. pytest tests/test_ebay_purchase.py -n 2 --browser chromium --alluredir="${RESULTS_DIR}"

echo ""
echo "Test execution completed. You can view the report by running:"
echo "allure serve ${RESULTS_DIR}"
