"""TikTok Profile Archiver"""


import argparse
import mimetypes
import os
import re
import sys
import time
import subprocess

import requests

from datetime import datetime
from logging import info, warning, error
from getpass import getpass
from pathlib import Path
from re import Pattern
from typing import Any, Final, Optional, Tuple
from urllib.parse import urlparse

from rich import print
from rich.progress import Progress, BarColumn, SpinnerColumn, TextColumn

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC

from ttpa.browser import create_browser
from ttpa.browser.base import BrowserBase
from ttpa.constants import *
from ttpa.handlers.captcha import detect_captcha
from ttpa.handlers.login_interests import handle_login_interests_dialog
from ttpa.handlers.tiktok_page import handle_tiktok_page_load
from ttpa.logging import setup_logging


#region Constants

USER_AGENT: Final[str] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36'

URL_STRING_PATTERN: Final[str] = r'^(?:\S+ URL:)?\s*https://www.tiktok.com/@[^/]+/(?:video|photo)/(\d+)'
URL_PATTERN: Final[Pattern[str]] = re.compile(URL_STRING_PATTERN, re.IGNORECASE)

#endregion


#region Helper Functions

def clean_user_name(user_name: str) -> str:
    return user_name \
        .strip() \
        .replace('https://www.tiktok.com/', '') \
        .replace('/', '') \
        .lstrip('@')


def parse_user_names(combined_user_names: str, *, separator: str=',') -> list[str]:

    user_names = [clean_user_name(user_name) for user_name in combined_user_names.split(separator) if user_name]

    unique_users = list(dict.fromkeys(user_names))

    return unique_users


def get_profile_url(user_name: str) -> str:
    return f"https://www.tiktok.com/@{user_name}"


def get_file_name_from_url(url: str) -> str:
    """Fetches the last part of an URL without query
    to be used as a file name.

    param url: The URL to parse.
    type url: str

    return: The parsed file name.
    rtype: str
    """
    parsed_url = urlparse(url)

    file_name = str(parsed_url.path).split('/')[-1]

    return file_name


def get_tiktok_id_from_url(url: str) -> Optional[str]:
    """Fetches the medium/posting ID form a TikTok URL.

    param url: The URL to parse.
    type url: str

    return: The parsed ID.
    rtype: str
    """

    parsed_url = re.match(URL_PATTERN, url)

    if parsed_url is not None:
        return parsed_url.group(1)

    return None


def save_url_to_file(base_path: str, url: str, *, file_name: Optional[str]=None) -> None:

    if file_name is None:
        file_name = get_file_name_from_url(url)

    with requests.get(url) as response:

        if response.ok:

            if Path(file_name).suffix in [None, '']:
                extension = mimetypes.guess_extension(response.headers.get('Content-Type', ''))

                if extension:
                    file_name += extension

            file_path = os.path.join(base_path, file_name)

            with open(file_path, 'wb') as file:
                file.write(response.content)

#endregion

#region Argument Handling

def get_arguments() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        prog=__file__,
        description='TikTok Profile Archiver',
    )

    parser.add_argument(
        '-u', '--users',
        default=None,
        metavar='USERS',
        dest='users',
        help='TikTok user names separated by comma',
    )

    parser.add_argument(
        '-b', '--browser-name',
        default=None,
        metavar='BROWSER',
        dest='browser_name',
        choices=['chrome', 'edge', 'firefox'],
        help='Browser to use (chrome, edge, firefox)',
    )

    parser.add_argument(
        '--headless',
        default=False,
        action='store_true',
        dest='headless',
        help='Run browser in headless mode (no GUI)',
    )
    
    return parser.parse_args()

#endregion

#region Dependencies

def install_dependencies():
    """Installs required dependencies."""

    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "rich"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])

    except Exception as e:
        print(f"Error installing dependencies: {str(e)}\n")

#endregion

#region User Interaction

def display_welcome_message():
    print("""
╔════════════════════════════════════════════════════════════════╗
║                     TikTok Backup Tool                         ║
╚════════════════════════════════════════════════════════════════╝

This tool will create a backup of a TikTok profile including:
- Profile information (avatar, bio, stats)
- Videos (including pinned)
- Playlists
- Comments
- HTML snapshot of the profile

Note: Running this tool multiple times will:
- Create a new timestamped folder for each backup
- Overwrite files if using the same destination
- Update all content to the latest version

This allows for:
- Tracking changes over time
- Maintaining multiple backup versions
- Automated scheduled backups
""")


def get_user_choices():

    print("\nEnter TikTok profile user name(s) separated by commas: https://www.tiktok.com/@", end="")
    
    user_names_input = input().strip()
    
    print()

    return parse_user_names(user_names_input)

    print("""
Select backup options (enter numbers separated by commas):
1. Reposts
2. Favorites
3. Liked videos
4. All of the above
5. None of the above (just profile backup)

Enter your choices (e.g., 1,2,3,4 or 5): """, end="")
    
    choices = input().strip()

    #return user_names, choices

#endregion

#region Browser Setup

def initialize_browser(browser_name: Optional[str]=None, headless: bool=False) -> BrowserBase:
    
    try:

        browser = create_browser(browser_name, headless=headless)

        time.sleep(BROWSER_INIT_TIMEOUT)

        browser.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        return browser

    except Exception as e:
        print(f"Error: {str(e)}")
        display_browser_name = browser_name.capitalize() if browser_name else 'the specified browser'
        sys.exit(f"Could not initialize browser. Please make sure {display_browser_name} is installed.\n\n")

#endregion

#region Directory Handling

def handle_empty_directory(directory, message="No content was found to scrape for this section."):
    """Create an explanation file in empty directories"""
    if os.path.exists(directory) and not os.listdir(directory):
        with open(os.path.join(directory, "Nothing to Scrape.txt"), 'w', encoding='utf-8') as f:
            f.write(message)


def create_backup_structure(user_name: str) -> str:
    """Creates the backup directory structure and handles empty folders.
    
    :param user_name: TikTok user name. Will be sanitized.
    :type user_name: str

    :return: The backup directory base path for the given user.
    :rtype: str
    """
    # Sorry, this is stupid, not sort-friendly plus include time
    # Format the date as before
    # date_str = datetime.now().strftime("%B %d")
    # day = int(datetime.now().strftime("%d"))
    # if 10 <= day % 100 <= 20:
    #     suffix = 'th'
    # else:
    #     suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    # date_str = f"{date_str}{suffix}-{datetime.now().strftime('%Y')}"

    date_str = datetime.now().strftime('%Y-%m-%d_%H%M')

    # People often use _ at the end so this is a bad separator
    #user_dir = f"@{user_name}_{date_str}"
    user_dir = f"@{user_name} {date_str}"

    script_dir = os.path.dirname(os.path.abspath(__file__))
    user_path = os.path.join(script_dir, user_dir)
    
    # Updated directory structure without comments folder
    directories: dict[str, dict[str, Any]] = {
        "01_profile": {
            "path": os.path.join(user_path, "01_profile"),
            "subdirs": ["01_avatar", "02_bio", "03_stats"],
            "message": "No profile information was found to scrape."
        },
        "02_pinned_videos": {
            "path": os.path.join(user_path, "02_pinned_videos"),
            "message": "No pinned videos were found on this profile."
        },
        "03_playlists": {
            "path": os.path.join(user_path, "03_playlists"),
            "message": "No playlists were found on this profile."
        },
        "04_videos": {
            "path": os.path.join(user_path, "04_videos"),
            "message": "No videos were found on this profile."
        },
        "05_reposts": {  # Renumbered from 06
            "path": os.path.join(user_path, "05_reposts"),
            "message": "No reposts were found on this profile."
        },
        "06_favorites": {  # Renumbered from 07
            "path": os.path.join(user_path, "06_favorites"),
            "message": "No favorites were found on this profile."
        },
        "07_liked": {  # Renumbered from 08
            "path": os.path.join(user_path, "07_liked"),
            "message": "No liked videos were found on this profile."
        },
        "08_html_snapshot": {  # Renumbered from 09
            "path": os.path.join(user_path, "08_html_snapshot"),
            "message": "No HTML snapshot was created for this profile."
        }
    }
    
    # Create directories
    for dir_info in directories.values():

        os.makedirs(dir_info["path"], exist_ok=True)
        
        if "subdirs" in dir_info:
            for subdir in dir_info["subdirs"]:
                os.makedirs(os.path.join(dir_info["path"], subdir), exist_ok=True)
        
        handle_empty_directory(dir_info["path"], dir_info["message"])
    
    return user_path

#endregion

#region Video Download & Saving

def download_video(url, path) -> bool:
    """Downloads a video file from an URL using yt-dlp.
    """
    try:
        import yt_dlp

        ydl_opts: yt_dlp._Params = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'outtmpl': path,
            'http_headers': {
                # https://github.com/yt-dlp/yt-dlp/issues/15418
                'User-Agent': 'Unknown',
            },
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            return True
            
    except Exception as e:
        #raise Exception(f"Failed to download video: {str(e)}")
        print(e)
        return False


def get_video_without_watermark(video_url: str) -> Optional[str]:
    """Downloads a video without watermark using yt-dlp.
    """
    try:
        import yt_dlp
        
        ydl_opts: yt_dlp._Params = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'http_headers': {
                # https://github.com/yt-dlp/yt-dlp/issues/15418
                'User-Agent': 'Unknown',
            },
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(video_url, download=False)
            if 'url' in result:
                return result['url']

    except Exception as e:
        print(f"Error getting video without watermark: {str(e)}")

    return None


def save_media(driver: BrowserBase, user_name: str, user_dir: str, media_elements: list[WebElement], media_dir: str='04_videos') -> BrowserBase:

    media_urls: list[str] = []

    for index, medium in enumerate(media_elements, 1):

        try:
            print(f"Collecting video URL {index}/{len(media_elements)} ...")

            # Get medium link
            medium_link = medium.find_element(By.CSS_SELECTOR, "a").get_attribute("href")

            if medium_link is None:
                print(f'Error: Link URL for medium {index} not found.')

            else:
                print(medium_link, '\n')
                media_urls.append(medium_link)

        except Exception as e:
            print(f"Error processing medium {index}: {str(e)}")
            continue

    print()

    for index, medium_link in enumerate(media_urls, 1):

        try:
            print(f"Processing medium {index}/{len(media_urls)} {medium_link} ...\n")
            
            # Re-create Selenium/Chrome session after 1000 videos to prevent stale sessions
            if index % 1000 == 0:
                new_driver = initialize_browser_for_user(
                    None,
                    user_name=user_name,
                    browser_name=driver.name,
                    headless=driver.headless,
                )

                if new_driver is None:
                    raise RuntimeError(f'@{user_name}: Browser could not be re-initialized on medium {index}.')
                
                driver = new_driver

            if '/photo/' in medium_link.lower():
                save_photos(driver, user_dir, media_dir, index, medium_link)
                continue

            # Create directory for media and metadata

            video_dir = f"{str(index).zfill(4)}_video"

            tiktok_id = get_tiktok_id_from_url(medium_link)

            if tiktok_id is not None:
                video_dir = f'{tiktok_id}_video'

            full_video_dir = os.path.join(user_dir, media_dir, video_dir)

            video_path = os.path.join(full_video_dir, "video.mp4")

            os.makedirs(full_video_dir, exist_ok=True)

            download_success = download_video(medium_link, video_path)

            if download_success:
                print(f"Video {index} downloaded successfully.")

            else:
                print(f"Error downloading video {index}.")
            
            # Determine final directory name based on download success
            final_video_dir = f"{full_video_dir}_PRIVATE" if not download_success else full_video_dir
            
            # If the folder exists with a different name, rename it
            if os.path.exists(full_video_dir) and not download_success:
                os.rename(full_video_dir, final_video_dir)

            elif not os.path.exists(final_video_dir):
                os.makedirs(final_video_dir, exist_ok=True)
            
            # Now open video in new tab to get metadata
            original_window = driver.current_window_handle

            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])
            driver.get(medium_link)

            # Wait for video page to load
            time.sleep(VIDEO_PAGE_LOAD_TIMEOUT)

            # Handle login dialog
            handle_login_interests_dialog(driver)

            print('Fetching video metadata ...')

            try:
                # Get optional music info
                music = '-'

                try:
                    music = driver.find_element(By.CSS_SELECTOR, "div[class*='--DivMusicContainer']").text

                except:
                    pass

                # Check if video is private
                is_private = False
                privacy = "Public Video"

                try:
                    driver.find_element(By.CSS_SELECTOR, "span[data-e2e='private-video']")
                    is_private = True

                except:
                    pass

                if is_private:
                    privacy = "Private Video"

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

                except:
                    pass
                
                # Get metadata
                try:
                    container = driver.find_element(By.CSS_SELECTOR, "span[class*='--SpanOtherInfos']")

                except:
                    container = driver.find_element(By.CSS_SELECTOR, "div[class*='--DivCreatorInfoContainer']")    

                components = [part.strip() for part in container.text.split('·') if part.strip()]

                meta_user_name = components[0]
                date = components[1]

                try:
                    description_element = driver.find_element(By.CSS_SELECTOR, "div[class*='--DivDescriptionContentContainer']")
                    description = description_element.text.strip()
                
                except:
                    description = ''

                # Save metadata
                with open(os.path.join(final_video_dir, "info.txt"), 'w', encoding='utf-8') as f:
                    f.write(f"@{meta_user_name}\n")
                    f.write("·\n")
                    f.write(f"Date - {date}\n")
                    f.write("·\n")
                    f.write(f"{privacy}\n")
                    f.write("·\n")
                    f.write("URL: \n")
                    f.write(f"{medium_link}\n")
                    f.write("·\n")
                    f.write("Video Caption Description:\n")
                    f.write(f"{description}\n")
                    f.write("·\n")
                    f.write(f"Music: {music}\n")
                    f.write("·\n")
                    f.write(f"{comment_count} Comment(s)\n\n")
                    f.write(f"Comments:\n\n")
                    if comment_text:
                        f.write(f"{comment_text}\n")
                    else:
                        f.write("(no comments available)\n")
                
            except Exception as e:
                print(f"Error getting video metadata: {str(e)}")
                # Save at least the URL if metadata fails
                with open(os.path.join(final_video_dir, "info.txt"), 'w', encoding='utf-8') as f:
                    f.write(f"Video URL: {medium_link}\n")

            finally:
                # Close video tab and return to main window
                driver.close()
                driver.switch_to.window(original_window)

                print('Done.\n')

        except Exception as e:
            print(f"Error processing video {index}: {str(e)}")
            continue

    return driver

#endregion

#region Slideshow Handling

def save_photos(driver: BrowserBase, user_dir: str, media_dir: str, index: int, medium_link: str) -> None:

    print('Medium is a photo/slideshow.\n')

    # Create directory for media and metadata

    photos_dir = f"{str(index).zfill(4)}_photos"

    tiktok_id = get_tiktok_id_from_url(medium_link)

    if tiktok_id is not None:
        photos_dir = f'{tiktok_id}_photos'

    photos_path = os.path.join(user_dir, media_dir, photos_dir)

    os.makedirs(photos_path, exist_ok=True)
    
    # Now open slideshow in new tab to get photos
    original_window = driver.current_window_handle

    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(medium_link)

    # Wait for video page to load
    time.sleep(VIDEO_PAGE_LOAD_TIMEOUT)

    # Handle login dialog
    handle_login_interests_dialog(driver)

    print(f'Fetching photos from {medium_link} ...\n')
 
    try:
        photos = driver.find_elements(By.CSS_SELECTOR, 'img[class*="--ImgPhotoSlide"]')

        for photo in photos:
            image_source = photo.get_attribute('src')

            if image_source is not None:
                print(f'Saving photo {image_source} ...')
                save_url_to_file(photos_path, image_source)

        try:
            audio = driver.find_element(By.TAG_NAME, 'audio')
            audio_source = audio.get_attribute('src')

            if audio_source is not None:
                print(f'Saving audio {audio_source} ...')
                save_url_to_file(photos_path, audio_source, file_name=tiktok_id)
        
        except:
            pass

    except Exception as e:
        print(f"Error getting slideshow photos: {str(e)}")

    finally:
        # Save the URL as metadata
        with open(os.path.join(photos_path, "info.txt"), 'w', encoding='utf-8') as f:
            f.write(f"Slideshow URL: {medium_link}\n")

        # Close video tab and return to main window
        driver.close()
        driver.switch_to.window(original_window)

        print()
        print('Done.\n')

#endregion

#region Scraping

def initialize_browser_for_user(browser: Optional[BrowserBase], /, user_name: str, browser_name: Optional[str]=None, headless: bool=False) -> Optional[BrowserBase]:

    profile_url = get_profile_url(user_name)

    if browser is None:
        browser = initialize_browser(browser_name, headless=headless)

    if not handle_tiktok_page_load(browser, profile_url):
        print(f"Failed to load TikTok page for @{user_name}, skipping to next account ...")
        return None

    # Handle CAPTCHA
    captcha_present = detect_captcha(browser)

    if captcha_present:
        print('PLEASE SOLVE THE CAPTCHA, THEN PRESS ENTER')
        getpass(prompt='')
        print()

    # Handle login dialog
    handle_login_interests_dialog(browser)

    # Handle cookie banner
    #handle_cookie_banner(driver)

    return browser


def scrape_profile_info(driver: BrowserBase, user_dir: str):
    print("Scraping profile information ...")

    try:
        # Get profile information using updated selectors
        try:
            # Get bio using JavaScript to get the full text content
            bio = driver.execute_script("""
                return document.querySelector('h2[data-e2e="user-bio"]').textContent
                || document.querySelector('h2[data-e2e="user-subtitle"]').textContent
            """)
            if not bio:
                bio = "No bio found."

        except:
            bio = "No bio found."
            
        try:
            following = driver.find_element(By.CSS_SELECTOR, "strong[data-e2e='following-count']").text

        except:
            following = "0"
            
        try:
            followers = driver.find_element(By.CSS_SELECTOR, "strong[data-e2e='followers-count']").text

        except:
            followers = "0"
            
        try:
            likes = driver.find_element(By.CSS_SELECTOR, "strong[data-e2e='likes-count']").text

        except:
            likes = "0"
            
        try:
            website = driver.find_element(By.CSS_SELECTOR, "a[data-e2e='user-link']").get_attribute('href')

        except:
            website = "None"
        
        # Save bio and stats as plain text
        bio_path = os.path.join(user_dir, "01_profile", "02_bio", "bio.txt")

        with open(bio_path, 'w', encoding='utf-8') as f:
            f.write(f"{following}\nFollowing\n{followers}\nFollowers\n{likes}\nLikes\n{bio}\n{website}")
        
        # Save stats separately
        stats_path = os.path.join(user_dir, "01_profile", "03_stats", "stats.txt")

        with open(stats_path, 'w', encoding='utf-8') as f:
            f.write(f"Following: {following}\nFollowers: {followers}\nLikes: {likes}")
        
        # Download avatar with direct method
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
                print(f"Found avatar URL: {avatar_url}")
                avatar_path = os.path.join(user_dir, "01_profile", "01_avatar", "avatar.jpeg")
                
                # Download with headers
                headers = {
                    'User-Agent': USER_AGENT,
                    'Referer': 'https://www.tiktok.com/'
                }
                
                response = requests.get(avatar_url, headers=headers)
                
                if response.status_code == 200:
                    with open(avatar_path, 'wb') as f:
                        f.write(response.content)
                    print("Avatar download successful.")

                else:
                    print(f"Failed to download avatar: HTTP {response.status_code}")

            else:
                print("Correct avatar URL could not be found.")
                
        except Exception as e:
            print(f"Warning: Could not download avatar: {str(e)}")
        
        print("Profile information saved successfully!\n")

        return True
        
    except Exception as e:
        print(f"Error scraping profile information: {str(e)}\n")
        return False


def scrape_pinned_videos(driver: BrowserBase, user_name: str, user_dir: str) -> Tuple[bool, BrowserBase]:
    print("Scraping pinned media ...\n")

    try:
        # Wait for video grid to load
        driver.wait_for(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-e2e='user-post-item']")),
            timeout=POST_ITEM_DRIVER_WAIT_TIMEOUT
        )
        
        # Get first 3 videos (pinned)
        media_elements = driver.find_elements(By.CSS_SELECTOR, "[data-e2e='user-post-item']")[:3]

        print(f"Found {len(media_elements)} pinned items.")

        driver = save_media(driver, user_name, user_dir, media_elements, media_dir='02_pinned_videos')

        print("Pinned items scraped successfully!")

        return (True, driver)
        
    except Exception as e:
        print(f"Error scraping pinned items: {str(e)}\n")
        return (False, driver)


def scrape_videos(driver: BrowserBase, user_name: str, user_dir: str) -> Tuple[bool, BrowserBase]:
    print("Scraping media ...\n")
    
    try:
        # Wait for initial video grid to load
        driver.wait_for(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-e2e='user-post-item']")),
            timeout=POST_ITEM_DRIVER_WAIT_TIMEOUT
        )
        
        # Scroll to load all videos first
        print("Loading all media ...\n")

        last_height = driver.execute_script("return document.documentElement.scrollHeight")

        driver.set_script_timeout(DRIVER_SCRIPT_TIMEOUT)

        with Progress(SpinnerColumn(), TextColumn('{task.description}'), BarColumn()) as progress:

            scroll_task = progress.add_task('Scrolling for media', total=None)

            while True:

                #print(f'Last height: {last_height}')
                # Scroll down to bottom
                driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")

                # Wait for new videos to load
                time.sleep(SCROLLING_LOAD_TIMEOUT)

                # Calculate new scroll height and compare with last scroll height
                new_height = driver.execute_script("return document.documentElement.scrollHeight")

                #print(f'New height: {new_height}')

                if new_height == last_height:
                    break

                last_height = new_height

            progress.remove_task(scroll_task)

        print('Scrolling successful.\n')

        # Now get all video elements after everything is loaded
        media_elements = driver.find_elements(By.CSS_SELECTOR, "[data-e2e='user-post-item']")
        total_media = len(media_elements)

        print(f"Found {total_media} items total.\n")

        driver = save_media(driver, user_name, user_dir, media_elements)

        print("Media scraped successfully!\n")

        return (True, driver)
        
    except Exception as e:
        print(f"Error scraping media: {str(e)}\n")
        return (False, driver)

#endregion


#region MAIN

def main():
    # Invoke command-line parser
    args = get_arguments()

    # Set up logging to file
    setup_logging()

    info(f"Program started with arguments: {args}")

    # Clear the screen first
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Install required dependencies first
    print("Checking and installing dependencies ...")
    install_dependencies()
    
    # Clear screen again after dependency installation
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Now display welcome message
    display_welcome_message()
    
    # Get input from user or command-line

    user_names: list[str] = []

    if args.users is None:
        #user_names, choices = get_user_choices()
        user_names = get_user_choices()

    else:
        user_names = parse_user_names(args.users)

        print(f'Users specified: @{',@'.join(user_names)}')
        print()

    driver = initialize_browser(browser_name=args.browser_name, headless=args.headless)

    try:
        # Process each user name
        for index, user_name in enumerate(user_names, 1):
            # Initialize browser per user to prevent long-run crashes and memory issues
            # ... can't do right now due to CAPTCHA
            #print("\nInitializing browser ...")
            #
            #driver = setup_chrome_profile()

            msg = f"Processing account {index}/{len(user_names)}: @{user_name}\n"
            print(msg)
            info(msg)
            
            # Create backup directory structure
            user_dir = create_backup_structure(user_name)
            
            # Navigate to profile with handling for automation detection
            driver = initialize_browser_for_user(
                driver,
                user_name=user_name,
                browser_name=args.browser_name,
                headless=args.headless,
            )

            if driver is None:
                msg = f"Failed to load TikTok page for @{user_name}, skipping to next account ...\n"
                print(msg)
                warning(msg)
                continue

            # Scrape profile information
            if not scrape_profile_info(driver, user_dir):
                msg = f"Warning: Failed to scrape profile information for @{user_name}.\n"
                print(msg)
                warning(msg)
            
            # Scrape pinned videos
            pinned_ok, driver = scrape_pinned_videos(driver, user_name, user_dir)

            if not pinned_ok:
                msg = f"Warning: Failed to scrape pinned videos for @{user_name}.\n"
                print(msg)
                warning(msg)
            
            videos_ok, driver = scrape_videos(driver, user_name, user_dir)

            # Scrape videos
            if not videos_ok:
                msg = f"Error: Failed to scrape videos for @{user_name}.\n"
                print(msg)
                error(msg)
            
            msg = f"Backup completed for @{user_name}.\n"
            print(msg)
            info(msg)

            # Can't do right now due to CAPTCHA
            #driver.quit()
        
        msg = "All accounts processed successfully!"
        print(msg)
        info(msg)

    except KeyboardInterrupt:
        msg = 'Program aborted.'
        print(msg)
        warning(msg)

    except Exception as e:
        msg = f"An error occurred: {str(e)}"
        print(msg)
        error(msg)

    finally:
        if driver:
            driver.quit()
        
        info("Program finished.")

#endregion

#region ENTRYPOINT

if __name__ == "__main__":
    print()
    main()
    print()
    print()

#endregion
