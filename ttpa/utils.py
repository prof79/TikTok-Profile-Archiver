"""Utility functions for TikTok Profile Archiver."""

import re
import sys
from pathlib import Path
from re import Pattern
from typing import Final, Optional
from urllib.parse import urlparse

USER_AGENT: Final[str] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36'

URL_STRING_PATTERN: Final[str] = r'^(?:\S+ URL:)?\s*https://www.tiktok.com/@[^/]+/(?:video|photo)/(\d+)'
URL_PATTERN: Final[Pattern[str]] = re.compile(URL_STRING_PATTERN, re.IGNORECASE)


def clean_user_name(user_name: str) -> str:
    """Sanitizes a TikTok user name by removing URL components and normalizing.

    :param user_name: The raw user name or URL to clean.
    :type user_name: str

    :return: The cleaned user name in lowercase.
    :rtype: str
    """
    return (
        user_name
        .strip()
        .replace('https://www.tiktok.com/', '')
        .replace('/', '')
        .lstrip('@')
        .lower()
    )


def parse_user_names(combined_user_names: str, *, separator: str = ',') -> list[str]:
    """Parses a comma-separated string of user names and removes duplicates.

    :param combined_user_names: Comma-separated user names or URLs.
    :type combined_user_names: str

    :param separator: The separator between user names. Defaults to ','.
    :type separator: str

    :return: A list of unique, cleaned user names.
    :rtype: list[str]
    """
    user_names = [clean_user_name(name) for name in combined_user_names.split(separator) if name]
    # Preserve order while removing duplicates
    return list(dict.fromkeys(user_names))


def get_profile_url(user_name: str) -> str:
    """Constructs the TikTok profile URL for a given user name.

    :param user_name: The TikTok user name.
    :type user_name: str

    :return: The full profile URL.
    :rtype: str
    """
    return f"https://www.tiktok.com/@{user_name}"


def get_file_name_from_url(url: str) -> str:
    """Extracts the file name from a URL by taking the last path segment.

    :param url: The URL to parse.
    :type url: str

    :return: The extracted file name from the URL path.
    :rtype: str
    """
    parsed_url = urlparse(url)
    return str(parsed_url.path).split('/')[-1]


def get_tiktok_id_from_url(url: str) -> Optional[str]:
    """Extracts the TikTok post ID from a TikTok video or photo URL.

    :param url: The TikTok URL to extract the ID from.
    :type url: str

    :return: The TikTok post ID, or None if the URL is not a valid TikTok post URL.
    :rtype: Optional[str]
    """
    match = re.match(URL_PATTERN, url)
    return match.group(1) if match else None


def save_url_to_file(base_path: Path, url: str, *, file_name: Optional[str] = None) -> Path:
    """Downloads a URL and saves the content to a file in the given directory.

    :param base_path: The directory to save the file in.
    :type base_path: Path

    :param url: The URL to download.
    :type url: str

    :param file_name: Optional file name. If None, derived from the URL.
    :type file_name: Optional[str]

    :return: The path to the saved file.
    :rtype: Path
    """
    import mimetypes
    import requests

    if file_name is None:
        file_name = get_file_name_from_url(url)

    target_path = base_path / file_name

    # If no extension, try to determine from content type
    if not target_path.suffix:
        with requests.get(url, stream=True) as response:
            if response.ok:
                content_type = response.headers.get('Content-Type', '')
                extension = mimetypes.guess_extension(content_type)
                if extension:
                    target_path = target_path.with_suffix(extension)

    # Download the file
    response = requests.get(url)
    response.raise_for_status()

    target_path.write_bytes(response.content)
    return target_path


def clear_screen() -> None:
    """Clears the terminal screen in a platform-agnostic way."""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

