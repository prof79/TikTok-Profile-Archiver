"""TikTok Profile Archiver Constants"""

__all__: list[str] = [
    'APP_NAME',
    'KILL_BROWSER_TIMEOUT',
    'BROWSER_INIT_TIMEOUT',
    'VIDEO_PAGE_LOAD_TIMEOUT',
    'COMMENTS_LOAD_TIMEOUT',
    'MAIN_PAGE_LOAD_TIMEOUT',
    'SMALL_CONTENT_LOAD_TIMEOUT',
    'SCROLLING_LOAD_TIMEOUT',
]

from typing import Final

APP_NAME: Final[str] = "TikTok Profile Archiver"

# Timeouts
KILL_BROWSER_TIMEOUT: Final[int] = 5
BROWSER_INIT_TIMEOUT: Final[int] = 4
VIDEO_PAGE_LOAD_TIMEOUT: Final[int] = 3
COMMENTS_LOAD_TIMEOUT: Final[int] = 2
MAIN_PAGE_LOAD_TIMEOUT: Final[int] = 5
SMALL_CONTENT_LOAD_TIMEOUT: Final[int] = 2
SCROLLING_LOAD_TIMEOUT: Final[int] = 5
