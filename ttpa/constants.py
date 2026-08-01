"""TikTok Profile Archiver Constants"""

__all__: list[str] = [
    'APP_NAME',
    'LOG_FILE',
    'USER_AGENT',
    'URL_STRING_PATTERN',
    'URL_PATTERN',
    'WINDOW_SIZE',
    'KILL_BROWSER_TIMEOUT',
    'BROWSER_INIT_TIMEOUT',
    'VIDEO_PAGE_LOAD_TIMEOUT',
    'COMMENTS_LOAD_TIMEOUT',
    'MAIN_PAGE_LOAD_TIMEOUT',
    'SMALL_CONTENT_LOAD_TIMEOUT',
    'SCROLLING_LOAD_TIMEOUT',
    'BODY_DRIVER_WAIT_TIMEOUT',
    'LOGIN_CONTAINER_DRIVER_WAIT_TIMEOUT',
    'COOKIE_BANNER_DRIVER_WAIT_TIMEOUT',
    'CAPTCHA_DRIVER_WAIT_TIMEOUT',
    'POST_ITEM_DRIVER_WAIT_TIMEOUT',
    'DRIVER_SCRIPT_TIMEOUT',
    'VIDEO_DIR_NAME',
    'VIDEO_INFOS_DIR_NAME',
    'PHOTO_DIR_NAME',
    'PHOTO_INFOS_DIR_NAME',
    'AVATAR_FILE_NAME',
    'BIO_FILE_NAME',
    'STATS_FILE_NAME',
]


import re

from re import Pattern
from typing import Final


# Constants

APP_NAME: Final[str] = "TikTok Profile Archiver"

LOG_FILE: Final[str] = "TikTok-Profile-Archiver.log"

USER_AGENT: Final[str] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36'

URL_STRING_PATTERN: Final[str] = r'^(?:\S+ URL:)?\s*https://www.tiktok.com/@[^/]+/(?:video|photo)/(\d+)'
URL_PATTERN: Final[Pattern[str]] = re.compile(URL_STRING_PATTERN, re.IGNORECASE)

# WebDriver Customizations
WINDOW_SIZE: Final[tuple[int, int]] = (1600, 800)

# Sleep Timeouts
KILL_BROWSER_TIMEOUT: Final[int] = 5
BROWSER_INIT_TIMEOUT: Final[int] = 4
VIDEO_PAGE_LOAD_TIMEOUT: Final[int] = 3
COMMENTS_LOAD_TIMEOUT: Final[int] = 2
MAIN_PAGE_LOAD_TIMEOUT: Final[int] = 4
SMALL_CONTENT_LOAD_TIMEOUT: Final[int] = 2
SCROLLING_LOAD_TIMEOUT: Final[int] = 5

# WebDriverWait Timeouts
BODY_DRIVER_WAIT_TIMEOUT: Final[int] = 10
LOGIN_CONTAINER_DRIVER_WAIT_TIMEOUT: Final[int] = 2
COOKIE_BANNER_DRIVER_WAIT_TIMEOUT: Final[int] = 20
CAPTCHA_DRIVER_WAIT_TIMEOUT: Final[int] = 20
POST_ITEM_DRIVER_WAIT_TIMEOUT: Final[int] = 10

# WebDriver Timeouts
DRIVER_SCRIPT_TIMEOUT: Final[int] = 120

# Path Constants
METADATA_DIR_NAME: Final[str] = "infos"
VIDEO_DIR_NAME: Final[str] = "videos"
PHOTO_DIR_NAME: Final[str] = "photos"
AVATAR_FILE_NAME: Final[str] = "avatar.png"
BIO_FILE_NAME: Final[str] = "bio.txt"
STATS_FILE_NAME: Final[str] = "stats.txt"
