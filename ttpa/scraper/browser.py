"""Browser initialization and management for TikTok Profile Archiver."""

from typing import Optional

from rich import print
from selenium.webdriver.support import expected_conditions as EC

from ttpa.browser import create_browser
from ttpa.browser.base import BrowserBase
from ttpa.constants import (
    BROWSER_INIT_TIMEOUT,
    BODY_DRIVER_WAIT_TIMEOUT,
    MAIN_PAGE_LOAD_TIMEOUT,
)
from ttpa.handlers.captcha import detect_captcha
from ttpa.handlers.login_interests import handle_login_interests_dialog
from ttpa.utils import get_profile_url
import time


def initialize_browser(
    browser_name: Optional[str] = None,
    headless: bool = False,
) -> BrowserBase:
    """Initializes a browser instance.

    :param browser_name: The name of the browser to use (chrome, edge, firefox).
    :type browser_name: Optional[str]

    :param headless: Whether to run the browser in headless mode.
    :type headless: bool

    :return: The initialized browser instance.
    :rtype: BrowserBase
    """
    try:
        browser = create_browser(browser_name, headless=headless)
        time.sleep(BROWSER_INIT_TIMEOUT)
        return browser

    except Exception as e:
        print(f"Error: {str(e)}")
        display_browser_name = browser_name.capitalize() if browser_name else 'the specified browser'
        raise RuntimeError(
            f"Could not initialize browser. Please make sure {display_browser_name} is installed."
        )


def initialize_browser_for_user(
    browser: Optional[BrowserBase],
    user_name: str,
    browser_name: Optional[str] = None,
    headless: bool = False,
) -> Optional[BrowserBase]:
    """Initializes or reuses a browser for a specific TikTok user profile.

    Handles page loading, CAPTCHA detection, and login dialogs.

    :param browser: An existing browser instance to reuse, or None to create a new one.
    :type browser: Optional[BrowserBase]

    :param user_name: The TikTok user name.
    :type user_name: str

    :param browser_name: The name of the browser to use (if creating a new one).
    :type browser_name: Optional[str]

    :param headless: Whether to run the browser in headless mode.
    :type headless: bool

    :return: The browser instance, or None if the page could not be loaded.
    :rtype: Optional[BrowserBase]
    """
    profile_url = get_profile_url(user_name)

    if browser is None:
        browser = initialize_browser(browser_name, headless=headless)

    try:
        # Initial page load
        browser.get(profile_url)
        time.sleep(MAIN_PAGE_LOAD_TIMEOUT)
        browser.refresh()
        time.sleep(MAIN_PAGE_LOAD_TIMEOUT)

        # Wait for body element to be present
        browser.wait_for(
            EC.presence_of_element_located((By.TAG_NAME, "body")),
            BODY_DRIVER_WAIT_TIMEOUT,
        )

        # Handle CAPTCHA
        captcha_present = detect_captcha(browser)
        if captcha_present:
            print("[yellow]PLEASE SOLVE THE CAPTCHA, THEN PRESS ENTER[/yellow]")
            from getpass import getpass
            getpass(prompt='')
            print()

        # Handle login dialog
        handle_login_interests_dialog(browser)

        return browser

    except Exception as e:
        print(f"[red]Error loading page for @{user_name}: {str(e)}[/red]")
        return None


def clear_screen() -> None:
    """Clears the terminal screen in a platform-agnostic way."""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')
