"""Profile information scraping for TikTok Profile Archiver."""


import requests

from pathlib import Path
from rich import print
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from ttpa.browser.base import BrowserBase
from ttpa.constants import USER_AGENT
from ttpa.paths import (
    get_avatar_file_path,
    get_bio_file_path,
    get_stats_file_path,
)
from ttpa.utils import _get_href_safe, _get_text_safe


def scrape_profile_info(
    driver: BrowserBase,
    user_dir: Path,
) -> bool:
    """Scrapes profile information (bio, stats, avatar) from a TikTok profile.

    :param driver: The Selenium browser instance.
    :type driver: BrowserBase

    :param user_dir: The backup directory for the user.
    :type user_dir: Path

    :return: True if the profile information was scraped successfully, False otherwise.
    :rtype: bool
    """
    print("[green]Scraping profile information ...[/green]")

    try:
        # Get bio using JavaScript to get the full text content
        bio = driver.execute_script("""
            return document.querySelector('h2[data-e2e="user-bio"]').textContent
            || document.querySelector('h2[data-e2e="user-subtitle"]').textContent
        """)
        if not bio:
            bio = "No bio found."

        # Get stats
        following = _get_text_safe(driver, By.CSS_SELECTOR, "strong[data-e2e='following-count']")
        followers = _get_text_safe(driver, By.CSS_SELECTOR, "strong[data-e2e='followers-count']")
        likes = _get_text_safe(driver, By.CSS_SELECTOR, "strong[data-e2e='likes-count']")

        # Get website
        website = _get_href_safe(driver, By.CSS_SELECTOR, "a[data-e2e='user-link']")

        # Save bio
        bio_path = get_bio_file_path(user_dir)
        bio_path.parent.mkdir(parents=True, exist_ok=True)
        bio_path.write_text(f"{following}\nFollowing\n{followers}\nFollowers\n{likes}\nLikes\n{bio}\n{website}", encoding='utf-8')

        # Save stats
        stats_path = get_stats_file_path(user_dir)
        stats_path.parent.mkdir(parents=True, exist_ok=True)
        stats_path.write_text(f"Following: {following}\nFollowers: {followers}\nLikes: {likes}", encoding='utf-8')

        # Download avatar
        _download_avatar(driver, user_dir)

        print("[green]Profile information saved successfully!\n[/green]")
        return True

    except Exception as e:
        print(f"[red]Error scraping profile information: {str(e)}\n[/red]")
        return False


def _download_avatar(driver: BrowserBase, user_dir: Path) -> None:
    """Downloads the user's avatar image.

    :param driver: The Selenium browser instance.
    :type driver: BrowserBase

    :param user_dir: The backup directory for the user.
    :type user_dir: Path
    """
    try:
        # Get avatar URL specifically from within ShareLayoutHeader
        avatar_url = driver.execute_script("""
            const header = document.querySelector('[class*="ShareLayoutHeader"]');
            if (header) {
                const avatar = header.querySelector('img[class*="ImgAvatar"]');
                return avatar ? avatar.src : null;
            }
            return null;
        """)

        if avatar_url:
            print(f'[cyan]Found avatar URL: {avatar_url}[/cyan]')
            avatar_path = get_avatar_file_path(user_dir)
            avatar_path.parent.mkdir(parents=True, exist_ok=True)

            # Download with headers
            headers = {
                'User-Agent': USER_AGENT,
                'Referer': 'https://www.tiktok.com/',
            }

            if requests is None:
                print("[yellow]Warning: requests library not available. Avatar not downloaded.[/yellow]")
                return

            response = requests.get(avatar_url, headers=headers)

            if response.status_code == 200:
                avatar_path.write_bytes(response.content)
                print("[green]Avatar download successful.[/green]")
            else:
                print(f"[red]Failed to download avatar: HTTP {response.status_code}[/red]")
        else:
            print("[yellow]Correct avatar URL could not be found.[/yellow]")

    except Exception as e:
        print(f"[yellow]Warning: Could not download avatar: {str(e)}[/yellow]")
