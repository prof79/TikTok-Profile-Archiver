"""Handler for TikTok login/interests dialog"""


import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from ttpa.browser.base import BrowserBase
from ttpa.constants import LOGIN_CONTAINER_DRIVER_WAIT_TIMEOUT, SMALL_CONTENT_LOAD_TIMEOUT


def handle_login_interests_dialog(browser: BrowserBase) -> None:

    print('Trying to detect and dismiss login dialog ...')

    try:
        login_dialog = browser.wait_for(
            EC.presence_of_element_located((By.ID, 'loginContainer')),
            timeout=LOGIN_CONTAINER_DRIVER_WAIT_TIMEOUT
        )

        print('Login dialog found.')

        # Additional wait for content to load
        time.sleep(SMALL_CONTENT_LOAD_TIMEOUT)

        login_buttons = login_dialog.find_elements(By.XPATH, '//button[contains(text(), "Skip")]')

        if len(login_buttons) == 0:
            print('Login buttons not found.')

        else:
            print('Login buttons found, skipping dialog ...')
            login_buttons[0].click()

    except Exception as ex:
        print('Login dialog not found.')

    print()
