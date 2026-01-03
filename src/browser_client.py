#!/usr/bin/env python3
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from config import HEADERS

# =====================
# BROWSER CLIENT
# =====================

_driver = None

def get_driver():
    """Get or create a Chrome driver instance"""
    global _driver
    if _driver is None:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument(f'user-agent={HEADERS["User-Agent"]}')
        _driver = webdriver.Chrome(options=options)
    return _driver

def close_driver():
    """Close the driver if it exists"""
    global _driver
    if _driver is not None:
        _driver.quit()
        _driver = None

def fetch_with_browser(url: str, wait_for_selector: str = None, timeout: int = 10) -> str:
    """
    Fetch a URL using Selenium WebDriver to handle JavaScript-rendered content
    
    Args:
        url: The URL to fetch
        wait_for_selector: Optional CSS selector to wait for before returning content
        timeout: Maximum time to wait for the selector (default: 10 seconds)
    
    Returns:
        The page source HTML after JavaScript execution
    """
    driver = get_driver()
    driver.get(url)
    
    # Wait for the specified element if provided
    if wait_for_selector:
        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_selector))
            )
        except TimeoutException:
            # Element didn't appear, but continue with the page source we have
            pass
    else:
        # Give JavaScript time to execute even without a specific selector
        time.sleep(2)
    
    return driver.page_source
