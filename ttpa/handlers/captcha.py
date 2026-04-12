"""Handler for TikTok captcha verification page"""


from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from ttpa.browser.base import BrowserBase
from ttpa.constants import CAPTCHA_DRIVER_WAIT_TIMEOUT


def detect_captcha(browser: BrowserBase) -> bool:
    try:
        browser.wait_for(
            EC.presence_of_element_located((By.CLASS_NAME, 'captcha-verify-container')),
            timeout=CAPTCHA_DRIVER_WAIT_TIMEOUT,
        )

        return True

    except:

        return False
