"""Media (video and photo) scraping for TikTok Profile Archiver."""

import time
from pathlib import Path
from typing import Tuple

from rich import print
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC

from ttpa.browser.base import BrowserBase
from ttpa.constants import (
    COMMENTS_LOAD_TIMEOUT,
    POST_ITEM_DRIVER_WAIT_TIMEOUT,
    SCROLLING_LOAD_TIMEOUT,
    VIDEO_PAGE_LOAD_TIMEOUT,
)
from ttpa.handlers.login_interests import handle_login_interests_dialog
from ttpa.paths import (
    get_photo_metadata_path,
    get_photos_dir,
    get_photos_infos_dir,
    get_video_metadata_path,
    get_video_path,
    get_videos_dir,
)
from ttpa.scraper.downloader import download_video
from ttpa.utils import get_tiktok_id_from_url, save_url_to_file


def save_media(
    driver: BrowserBase,
    user_name: str,
    user_dir: Path,
    media_elements: list[WebElement],
) -> BrowserBase:
    """Saves media (videos or photos) from the given elements.

    :param driver: The Selenium browser instance.
    :type driver: BrowserBase

    :param user_name: The TikTok user name.
    :type user_name: str

    :param user_dir: The backup directory for the user.
    :type user_dir: Path

    :param media_elements: List of Selenium WebElements representing media items.
    :type media_elements: list[WebElement]

    :return: The (possibly re-initialized) browser instance.
    :rtype: BrowserBase
    """
    media_urls: list[str] = []
    msg = f'Found {len(media_elements)} posts for @{user_name}.'
    print(f"[green]{msg}[/green]\n")

    # First pass: collect all URLs
    for index, medium in enumerate(media_elements, 1):
        try:
            print(f"[cyan]Collecting post URL {index}/{len(media_elements)} ...[/cyan]")
            medium_link = medium.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
            if medium_link is None:
                print(f"[red]Error: Link URL for medium {index} not found.[/red]")
            else:
                print(f"{medium_link}\n")
                media_urls.append(medium_link)
        except Exception as e:
            print(f"[red]Error processing medium {index}: {str(e)}[/red]")
            continue

    print()

    # Second pass: process each media item
    for index, medium_link in enumerate(media_urls, 1):
        try:
            print(f"[cyan]Processing medium {index}/{len(media_urls)} {medium_link} ...[/cyan]\n")

            # Re-create browser session every 1000 items to prevent stale sessions
            if index % 1000 == 0:
                new_driver = _initialize_browser_for_user(
                    user_name=user_name,
                    browser_name=driver.name,
                    headless=driver.headless,
                )
                if new_driver is None:
                    raise RuntimeError(f'@{user_name}: Browser could not be re-initialized on medium {index}.')
                driver = new_driver

            if '/photo/' in medium_link.lower():
                _save_photos(driver, user_dir, index, medium_link)
                continue

            # Process video
            tiktok_id = get_tiktok_id_from_url(medium_link)
            if tiktok_id is None:
                print(f"[red]Could not extract TikTok ID from URL: {medium_link}[/red]")
                continue

            video_path = get_video_path(user_dir, tiktok_id)

            # Ensure videos directory exists
            get_videos_dir(user_dir).mkdir(parents=True, exist_ok=True)

            # Download the video
            download_success = download_video(medium_link, video_path)

            if download_success:
                print(f"[green]Video {index} downloaded successfully.[/green]")
            else:
                print(f"[red]Error downloading video {index}.[/red]")
                # Mark as private/unavailable
                _save_failed_video_metadata(user_dir, tiktok_id, medium_link)
                continue

            # Fetch metadata by opening the video page
            _fetch_and_save_video_metadata(driver, user_dir, tiktok_id, medium_link)

        except Exception as e:
            print(f"[red]Error processing medium {index}: {str(e)}[/red]")
            continue

    return driver


def scrape_videos(
    driver: BrowserBase,
    user_name: str,
    user_dir: Path,
) -> Tuple[bool, BrowserBase]:
    """Scrapes all videos from a TikTok profile.

    :param driver: The Selenium browser instance.
    :type driver: BrowserBase

    :param user_name: The TikTok user name.
    :type user_name: str

    :param user_dir: The backup directory for the user.
    :type user_dir: Path

    :return: A tuple of (success status, browser instance).
    :rtype: Tuple[bool, BrowserBase]
    """
    print("[green]Scraping media ...[/green]\n")

    try:
        # Wait for initial video grid to load
        driver.wait_for(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-e2e='user-post-item']")),
            timeout=POST_ITEM_DRIVER_WAIT_TIMEOUT,
        )

        # Scroll to load all videos
        print("[cyan]Loading all media ...[/cyan]\n")

        last_height = driver.execute_script("return document.documentElement.scrollHeight")
        driver.set_script_timeout(120)

        with Progress(SpinnerColumn(), TextColumn('{task.description}'), BarColumn()) as progress:
            scroll_task = progress.add_task('Scrolling for media', total=None)

            while True:
                driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
                time.sleep(SCROLLING_LOAD_TIMEOUT)
                new_height = driver.execute_script("return document.documentElement.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            progress.remove_task(scroll_task)

        print('[green]Scrolling successful.\n[/green]')

        # Get all media elements
        media_elements = driver.find_elements(By.CSS_SELECTOR, "[data-e2e='user-post-item']")
        total_media = len(media_elements)
        print(f"[cyan]Found {total_media} items total.\n[/cyan]")

        driver = save_media(driver, user_name, user_dir, media_elements)

        print("[green]Media scraped successfully!\n[/green]")
        return (True, driver)

    except Exception as e:
        print(f"[red]Error scraping media: {str(e)}\n[/red]")
        return (False, driver)


def _save_photos(
    driver: BrowserBase,
    user_dir: Path,
    index: int,
    medium_link: str,
) -> None:
    """Saves photos from a slideshow post.

    :param driver: The Selenium browser instance.
    :type driver: BrowserBase

    :param user_dir: The backup directory for the user.
    :type user_dir: Path

    :param index: The index of the media item (for logging).
    :type index: int

    :param medium_link: The URL of the slideshow post.
    :type medium_link: str
    """
    print('[cyan]Medium is a photo/slideshow.\n[/cyan]')

    tiktok_id = get_tiktok_id_from_url(medium_link)
    if tiktok_id is None:
        print(f"[red]Could not extract TikTok ID from URL: {medium_link}[/red]")
        return

    photos_path = get_photos_dir(user_dir)

    # Open slideshow in new tab
    original_window = driver.current_window_handle
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(medium_link)
    time.sleep(VIDEO_PAGE_LOAD_TIMEOUT)
    handle_login_interests_dialog(driver)

    print(f'[cyan]Fetching photos from {medium_link} ...\n[/cyan]')

    try:
        photos = driver.find_elements(By.CSS_SELECTOR, 'img[class*="--ImgPhotoSlide"]')

        for photo in photos:
            image_source = photo.get_attribute('src')
            if image_source is not None:
                print(f'[cyan]Saving photo {image_source} ...[/cyan]')
                save_url_to_file(photos_path, image_source)

        # Try to save audio if present
        try:
            audio = driver.find_element(By.TAG_NAME, 'audio')
            audio_source = audio.get_attribute('src')
            if audio_source is not None:
                print(f'[cyan]Saving audio {audio_source} ...[/cyan]')
                save_url_to_file(photos_path, audio_source, file_name=tiktok_id)
        except Exception:
            pass

    except Exception as e:
        print(f"[red]Error getting slideshow photos: {str(e)}[/red]")

    finally:
        # Save metadata
        metadata_path = get_photo_metadata_path(user_dir, tiktok_id)
        photos_path.mkdir(parents=True, exist_ok=True)
        get_photos_infos_dir(user_dir).mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(f"Slideshow URL: {medium_link}\n", encoding='utf-8')

        # Close tab and return to main window
        driver.close()
        driver.switch_to.window(original_window)
        print('[green]Done.\n[/green]')


def _fetch_and_save_video_metadata(
    driver: BrowserBase,
    user_dir: Path,
    tiktok_id: str,
    medium_link: str,
) -> None:
    """Fetches and saves metadata for a video post.

    :param driver: The Selenium browser instance.
    :type driver: BrowserBase

    :param user_dir: The backup directory for the user.
    :type user_dir: Path

    :param tiktok_id: The TikTok post ID.
    :type tiktok_id: str

    :param medium_link: The URL of the video post.
    :type medium_link: str
    """
    original_window = driver.current_window_handle
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(medium_link)
    time.sleep(VIDEO_PAGE_LOAD_TIMEOUT)
    handle_login_interests_dialog(driver)

    print('[cyan]Fetching video metadata ...[/cyan]')

    try:
        # Get optional music info
        music = '-'
        try:
            music = driver.find_element(By.CSS_SELECTOR, "div[class*='--DivMusicContainer']").text
        except Exception:
            pass

        # Check if video is private
        is_private = False
        privacy = "Public Video"
        try:
            driver.find_element(By.CSS_SELECTOR, "span[data-e2e='private-video']")
            is_private = True
            privacy = "Private Video"
        except Exception:
            pass

        # Get comments
        comment_count = 0
        comment_text = ''
        try:
            driver.find_element(By.ID, 'comments').click()
            time.sleep(COMMENTS_LOAD_TIMEOUT)
            comment_count_text = driver.find_element(By.CSS_SELECTOR, "div[class*='--DivCommentCountContainer']").text
            comment_count = int(comment_count_text.split(' ')[0])
            if comment_count > 0:
                comment_text = driver.find_element(By.CSS_SELECTOR, "div[class*='--DivCommentListContainer']").text.strip()
        except Exception:
            pass

        # Get metadata
        try:
            container = driver.find_element(By.CSS_SELECTOR, "span[class*='--SpanOtherInfos']")
        except Exception:
            container = driver.find_element(By.CSS_SELECTOR, "div[class*='--DivCreatorInfoContainer']")

        components = [part.strip() for part in container.text.split('·') if part.strip()]
        meta_user_name = components[0] if len(components) > 0 else 'Unknown'
        date = components[1] if len(components) > 1 else 'Unknown'

        try:
            description_element = driver.find_element(By.CSS_SELECTOR, "div[class*='--DivDescriptionContentContainer']")
            description = description_element.text.strip()
        except Exception:
            description = ''

        # Save metadata
        metadata_path = get_video_metadata_path(user_dir, tiktok_id)
        get_video_infos_dir(user_dir).mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(
            f"@{meta_user_name}\n"
            f"·\n"
            f"Date - {date}\n"
            f"·\n"
            f"{privacy}\n"
            f"·\n"
            f"URL: \n"
            f"{medium_link}\n"
            f"·\n"
            f"Video Caption Description:\n"
            f"{description}\n"
            f"·\n"
            f"Music: {music}\n"
            f"·\n"
            f"{comment_count} Comment(s)\n\n"
            f"Comments:\n\n"
            f"{'(no comments available)' if not comment_text else comment_text}\n",
            encoding='utf-8',
        )

    except Exception as e:
        print(f"[red]Error getting video metadata: {str(e)}[/red]")
        # Save at least the URL if metadata fails
        metadata_path = get_video_metadata_path(user_dir, tiktok_id)
        get_video_infos_dir(user_dir).mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(f"Video URL: {medium_link}\n", encoding='utf-8')

    finally:
        driver.close()
        driver.switch_to.window(original_window)
        print('[green]Done.\n[/green]')


def _save_failed_video_metadata(
    user_dir: Path,
    tiktok_id: str,
    medium_link: str,
) -> None:
    """Saves metadata for a video that failed to download.

    :param user_dir: The backup directory for the user.
    :type user_dir: Path

    :param tiktok_id: The TikTok post ID.
    :type tiktok_id: str

    :param medium_link: The URL of the video post.
    :type medium_link: str
    """
    metadata_path = get_video_metadata_path(user_dir, tiktok_id)
    get_video_infos_dir(user_dir).mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        f"Video URL: {medium_link}\n"
        f"Status: Failed to download\n",
        encoding='utf-8',
    )


def _initialize_browser_for_user(
    user_name: str,
    browser_name: str,
    headless: bool,
) -> BrowserBase:
    """Initializes a browser for a specific user.

    :param user_name: The TikTok user name.
    :type user_name: str

    :param browser_name: The name of the browser to use.
    :type browser_name: str

    :param headless: Whether to run the browser in headless mode.
    :type headless: bool

    :return: The initialized browser instance.
    :rtype: BrowserBase
    """
    from ttpa.browser import create_browser
    from ttpa.handlers.tiktok_page import handle_tiktok_page_load
    from ttpa.utils import get_profile_url

    profile_url = get_profile_url(user_name)
    browser = create_browser(browser_name, headless=headless)
    handle_tiktok_page_load(browser, profile_url)
    return browser
