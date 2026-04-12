"""Selenium Generic WebDriver Wrapper"""


__all__: list[str] = [
    'create_browser',
]


from typing import Optional

from .base import BrowserBase
from .chrome import ChromeBrowser
from .edge import EdgeBrowser
from .firefox import FirefoxBrowser


def create_browser(browser_name: Optional[str] = None, /, headless: bool = False) -> BrowserBase:

    name = browser_name if browser_name else 'chrome'

    if name in ("chrome", "chromium"):
        return ChromeBrowser(headless=headless)

    if name in ("edge", "msedge"):
        return EdgeBrowser(headless=headless)

    if name in ("firefox", "ff"):
        return FirefoxBrowser(headless=headless)

    raise ValueError(f"Unsupported browser: {name}")
