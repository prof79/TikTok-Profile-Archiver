"""Handler for TikTok cookie banner"""


from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from ttpa.browser.base import BrowserBase
from ttpa.constants import COOKIE_BANNER_DRIVER_WAIT_TIMEOUT


def handle_cookie_banner(browser: BrowserBase) -> None:

    print('Trying to detect and dismiss cookie banner ...')

    try:
        cookie_banner = browser.wait_for(
            EC.presence_of_element_located((By.TAG_NAME, 'tiktok-cookie-banner')),
            timeout=COOKIE_BANNER_DRIVER_WAIT_TIMEOUT
        )

        print('Cookie banner found.')

        #shadow_root = driver.execute_script('return arguments[0].shadowRoot', cookie_banner)
        shadow_root = cookie_banner.shadow_root

        cookie_buttons = shadow_root.find_elements(By.TAG_NAME, 'button')

        if len(cookie_buttons) == 0:
            print('Cookie buttons not found.')

        else:
            print('Cookie buttons found, clicking ...')
            cookie_buttons[0].click()

    except Exception as ex:
        print('Cookie banner or buttons not found.')
        print(ex)

    print()
