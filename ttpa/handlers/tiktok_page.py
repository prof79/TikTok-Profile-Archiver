"""Handle TikTok page loading and waiting for necessary elements to be present."""


import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from ttpa.browser.base import BrowserBase
from ttpa.constants import MAIN_PAGE_LOAD_TIMEOUT, BODY_DRIVER_WAIT_TIMEOUT


def handle_tiktok_page_load(browser: BrowserBase, url: str) -> bool:
    try:
        # Initial page load
        browser.get(url)

        # Wait for initial load
        time.sleep(MAIN_PAGE_LOAD_TIMEOUT)  

        # Wait for body element to be present
        browser.wait_for(
            EC.presence_of_element_located((By.TAG_NAME, "body")),
            BODY_DRIVER_WAIT_TIMEOUT
        )
        
        return True

    except Exception as e:
        print(f"Error loading page: {str(e)}")
        return False
