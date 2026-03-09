@echo off
setlocal

:: Get formatted timestamp (e.g., 20231024_153022)
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set TIMESTAMP=%datetime:~0,4%%datetime:~4,2%%datetime:~6,2%_%datetime:~8,2%%datetime:~10,2%%datetime:~12,2%

set RESULTS_DIR=reports\allure-results-%TIMESTAMP%

echo Executing tests in parallel matrix...
echo Results will be saved to: %RESULTS_DIR%

set PYTHONPATH=.
pytest tests/test_ebay_purchase.py -n 3 --browser chromium --alluredir="%RESULTS_DIR%"

echo.
echo Test execution completed. You can view the report by running:
echo allure serve %RESULTS_DIR%
