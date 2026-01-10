import mimetypes
import os
import sys
import time
import requests
import subprocess

from datetime import datetime
from getpass import getpass
from pathlib import Path
from typing import Any, Final, Optional, Tuple
from urllib.parse import urlparse

from rich import print

from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


#region Constants

USER_AGENT: Final[str] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36'

#endregion


#region Helper Functions

def clean_user_name(user_name: str) -> str:
    return user_name \
        .strip() \
        .replace('https://www.tiktok.com/', '') \
        .replace('/', '') \
        .lstrip('@')


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


def save_url_to_file(base_path: str, url: str) -> None:

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

    print("\nEnter TikTok profile Usernames (separated by commas): https://www.tiktok.com/@", end="")
    
    usernames_input = input().strip()

    usernames = [clean_user_name(username) for username in usernames_input.split(',')]
    
    return usernames

    print("""
Select backup options (enter numbers separated by commas):
1. Reposts
2. Favorites
3. Liked videos
4. All of the above
5. None of the above (just profile backup)

Enter your choices (e.g., 1,2,3,4 or 5): """, end="")
    
    choices = input().strip()

    #return usernames, choices

#endregion

#region Chrome Setup

def setup_chrome_profile() -> WebDriver:
    
    print("Initializing browser ...\n")

    chrome_options = webdriver.ChromeOptions()
    
    # Get the correct path for Windows
    user_data_dir = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data')
    
    # Add necessary options to prevent crashes and detection
    chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
    chrome_options.add_argument('--profile-directory=Default')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--remote-debugging-port=9222')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Close any existing Chrome instances
    os.system("taskkill /f /im chrome.exe")
    time.sleep(4)
    
    # try:
    #     driver = webdriver.Chrome(options=chrome_options)
    #     # Mask selenium's presence
    #     driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    #     return driver
    # except Exception as e:
    #    print(f"Error initializing Chrome with profile: {str(e)}")

    # From experience, "with profile" does not seem to work anymore
    print("\nTrying alternative method without user profile ...\n")
    
    try:
        chrome_options = webdriver.ChromeOptions()

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        driver = webdriver.Chrome(options=chrome_options)
        
        time.sleep(2)

        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver

    except Exception as e:
        print(f"Error with alternative method: {str(e)}")
        sys.exit("Could not initialize Chrome. Please make sure Chrome is installed.\n\n")

#endregion

#region Directory Handling

def handle_empty_directory(directory, message="No content was found to scrape for this section."):
    """Create an explanation file in empty directories"""
    if os.path.exists(directory) and not os.listdir(directory):
        with open(os.path.join(directory, "Nothing to Scrape.txt"), 'w', encoding='utf-8') as f:
            f.write(message)


def create_backup_structure(username: str) -> str:
    """Creates the backup directory structure and handles empty folders.
    
    :param username: TikTok user name. Will be sanitized.
    :type username: str

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
    #base_dir = f"@{username}_{date_str}"
    base_dir = f"@{username} {date_str}"

    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.join(script_dir, base_dir)
    
    # Updated directory structure without comments folder
    directories: dict[str, dict[str, Any]] = {
        "01_profile": {
            "path": os.path.join(base_dir, "01_profile"),
            "subdirs": ["01_avatar", "02_bio", "03_stats"],
            "message": "No profile information was found to scrape."
        },
        "02_pinned_videos": {
            "path": os.path.join(base_dir, "02_pinned_videos"),
            "message": "No pinned videos were found on this profile."
        },
        "03_playlists": {
            "path": os.path.join(base_dir, "03_playlists"),
            "message": "No playlists were found on this profile."
        },
        "04_videos": {
            "path": os.path.join(base_dir, "04_videos"),
            "message": "No videos were found on this profile."
        },
        "05_reposts": {  # Renumbered from 06
            "path": os.path.join(base_dir, "05_reposts"),
            "message": "No reposts were found on this profile."
        },
        "06_favorites": {  # Renumbered from 07
            "path": os.path.join(base_dir, "06_favorites"),
            "message": "No favorites were found on this profile."
        },
        "07_liked": {  # Renumbered from 08
            "path": os.path.join(base_dir, "07_liked"),
            "message": "No liked videos were found on this profile."
        },
        "08_html_snapshot": {  # Renumbered from 09
            "path": os.path.join(base_dir, "08_html_snapshot"),
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
    
    return base_dir

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


def save_media(driver: WebDriver, user_name: str, base_dir: str, media_elements: list[WebElement], folder_name: str='04_videos') -> WebDriver:

    media_urls: list[str] = []

    for idx, medium in enumerate(media_elements, 1):

        try:
            print(f"Collecting video URL {idx}/{len(media_elements)} ...")

            # Get medium link
            medium_link = medium.find_element(By.CSS_SELECTOR, "a").get_attribute("href")

            if medium_link is None:
                print(f'Error: Link URL for medium {idx} not found.')

            else:
                print(medium_link, '\n')
                media_urls.append(medium_link)

        except Exception as e:
            print(f"Error processing medium {idx}: {str(e)}")
            continue

    print()

    for idx, medium_link in enumerate(media_urls, 1):

        try:
            print(f"Processing medium {idx}/{len(media_urls)} {medium_link} ...\n")
            
            # Re-create Selenium/Chrome session after 1000 videos to prevent stale sessions
            if idx % 1000 == 0:
                new_driver = initialize_browser_for_user(None, user_name)

                if new_driver is None:
                    raise RuntimeError(f'@{user_name}: Browser could not be re-initialized on medium {idx}.')
                
                driver = new_driver

            if '/photo/' in medium_link.lower():
                save_photos(driver, base_dir, folder_name, idx, medium_link)
                continue

            # Create initial folder name (without private suffix)
            base_video_path = os.path.join(base_dir, folder_name, f"video_{idx}")

            video_path = os.path.join(base_video_path, "video.mp4")

            os.makedirs(base_video_path, exist_ok=True)

            download_success = download_video(medium_link, video_path)

            if download_success:
                print(f"Video {idx} downloaded successfully.")

            else:
                print(f"Error downloading video {idx}.")
            
            # Determine final folder name based on download success
            final_folder_name = f"video_{idx}_PRIVATE-VIDEO" if not download_success else f"video_{idx}"

            final_path = os.path.join(base_dir, folder_name, final_folder_name)
            
            # If the folder exists with a different name, rename it
            if os.path.exists(base_video_path) and not download_success:
                os.rename(base_video_path, final_path)

            elif not os.path.exists(final_path):
                os.makedirs(final_path, exist_ok=True)
            
            # Now open video in new tab to get metadata
            original_window = driver.current_window_handle

            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])
            driver.get(medium_link)

            # Wait for video page to load
            time.sleep(3)

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
                    time.sleep(2)
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

                username = components[0]
                date = components[1]

                try:
                    description_element = driver.find_element(By.CSS_SELECTOR, "div[class*='--DivDescriptionContentContainer']")
                    description = description_element.text.strip()
                
                except:
                    description = ''

                # Save metadata
                with open(os.path.join(final_path, "info.txt"), 'w', encoding='utf-8') as f:
                    f.write(f"@{username}\n")
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
                with open(os.path.join(final_path, "info.txt"), 'w', encoding='utf-8') as f:
                    f.write(f"Video URL: {medium_link}\n")

            finally:
                # Close video tab and return to main window
                driver.close()
                driver.switch_to.window(original_window)

                print('Done.\n')

        except Exception as e:
            print(f"Error processing video {idx}: {str(e)}")
            continue

    return driver

#endregion

#region Slideshow Handling

def save_photos(driver: WebDriver, base_dir: str, folder_name: str, idx: int, medium_link: str) -> None:

    print('Medium is a photo/slideshow.\n')

    # Create initial folder name (without private suffix)
    base_path = os.path.join(base_dir, folder_name, f"photos_{idx}")
    os.makedirs(base_path, exist_ok=True)
    
    # Now open slideshow in new tab to get photos
    original_window = driver.current_window_handle

    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(medium_link)

    # Wait for video page to load
    time.sleep(3)

    # Handle login dialog
    handle_login_interests_dialog(driver)

    print(f'Fetching photos from {medium_link} ...\n')
 
    try:
        photos = driver.find_elements(By.CSS_SELECTOR, 'img[class*="--ImgPhotoSlide"]')

        for photo in photos:
            image_source = photo.get_attribute('src')

            if image_source is not None:
                print(f'Saving photo {image_source} ...')
                save_url_to_file(base_path, image_source)

        try:
            audio = driver.find_element(By.TAG_NAME, 'audio')
            audio_source = audio.get_attribute('src')

            if audio_source is not None:
                print(f'Saving audio {audio_source} ...')
                save_url_to_file(base_path, audio_source)
        
        except:
            pass

    except Exception as e:
        print(f"Error getting slideshow photos: {str(e)}")

    finally:
        # Save the URL as metadata
        with open(os.path.join(base_path, "info.txt"), 'w', encoding='utf-8') as f:
            f.write(f"Slideshow URL: {medium_link}\n")

        # Close video tab and return to main window
        driver.close()
        driver.switch_to.window(original_window)

        print()
        print('Done.\n')

#endregion

#region Page Handlers

def handle_tiktok_page_load(driver, url):
    try:
        # Initial page load
        driver.get(url)

        # Wait for initial load
        time.sleep(3)  

        # Refresh the page to bypass automation detection
        # -> doesn't really help
        #driver.refresh()
        #time.sleep(3)  # Wait after refresh
        
        # Wait for body element to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Additional wait for content to load
        time.sleep(2)
        
        return True

    except Exception as e:
        print(f"Error loading page: {str(e)}")
        return False


def handle_cookie_banner(driver: WebDriver) -> None:

    print('Trying to detect and dismiss cookie banner ...')

    try:
        cookie_banner = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, 'tiktok-cookie-banner'))
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


def handle_login_interests_dialog(driver: WebDriver) -> None:

    print('Trying to detect and dismiss login dialog ...')

    try:
        login_dialog = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.ID, 'loginContainer'))
        )

        print('Login dialog found.')

        # Additional wait for content to load
        time.sleep(2)

        login_buttons = login_dialog.find_elements(By.XPATH, '//button[text()="Skip"]')

        if len(login_buttons) == 0:
            print('Login buttons not found.')

        else:
            print('Login buttons found, skipping ...')
            login_buttons[0].click()

    except Exception as ex:
        print('Login banner or buttons not found.')

    print()


def detect_captcha(driver: WebDriver) -> bool:

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'captcha-verify-container'))
        )

        return True

    except:

        return False

#endregion

#region Scraping

def initialize_browser_for_user(driver: Optional[WebDriver], username: str) -> Optional[WebDriver]:

    profile_url = get_profile_url(username)

    if driver is None:
        driver = setup_chrome_profile()

    if not handle_tiktok_page_load(driver, profile_url):
        print(f"Failed to load TikTok page for @{username}, skipping to next account ...")
        return None

    # Handle CAPTCHA
    captcha_present = detect_captcha(driver)

    if captcha_present:
        print('PLEASE SOLVE THE CAPTCHA, THEN PRESS ENTER')
        getpass(prompt='')
        print()

    # Handle login dialog
    handle_login_interests_dialog(driver)

    # Handle cookie banner
    #handle_cookie_banner(driver)

    return driver


def scrape_profile_info(driver: WebDriver, base_dir: str):
    print("Scraping profile information ...")

    try:
        # Wait longer for the page to fully load
        time.sleep(5)
        
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
        bio_path = os.path.join(base_dir, "01_profile", "02_bio", "bio.txt")

        with open(bio_path, 'w', encoding='utf-8') as f:
            f.write(f"{following}\nFollowing\n{followers}\nFollowers\n{likes}\nLikes\n{bio}\n{website}")
        
        # Save stats separately
        stats_path = os.path.join(base_dir, "01_profile", "03_stats", "stats.txt")
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
                avatar_path = os.path.join(base_dir, "01_profile", "01_avatar", "avatar.jpeg")
                
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


def scrape_pinned_videos(driver: WebDriver, user_name: str, base_dir: str) -> Tuple[bool, WebDriver]:
    print("Scraping pinned videos ...\n")

    try:
        # Wait for video grid to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-e2e='user-post-item']"))
        )
        
        # Get first 3 videos (pinned)
        video_elements = driver.find_elements(By.CSS_SELECTOR, "[data-e2e='user-post-item']")[:3]

        print(f"Found {len(video_elements)} pinned videos.")

        driver = save_media(driver, user_name, base_dir, video_elements, folder_name='02_pinned_videos')

        print("Pinned videos scraped successfully!")

        return (True, driver)
        
    except Exception as e:
        print(f"Error scraping pinned videos: {str(e)}\n")
        return (False, driver)


def scrape_videos(driver: WebDriver, user_name: str, base_dir: str) -> Tuple[bool, WebDriver]:
    print("Scraping videos ...\n")
    
    try:
        # Wait for initial video grid to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-e2e='user-post-item']"))
        )
        
        # Scroll to load all videos first
        print("Loading all videos ...\n")

        last_height = driver.execute_script("return document.documentElement.scrollHeight")

        while True:

            #print(f'Last height: {last_height}')
            # Scroll down to bottom
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(2.4)  # Wait for new videos to load

            print('Scrolling ...')

            # Calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script("return document.documentElement.scrollHeight")

            #print(f'New height: {new_height}')

            if new_height == last_height:
                break

            last_height = new_height
        
        print('Scrolling successful.\n')

        # Now get all video elements after everything is loaded
        video_elements = driver.find_elements(By.CSS_SELECTOR, "[data-e2e='user-post-item']")
        total_videos = len(video_elements)

        print(f"Found {total_videos} videos total.\n")

        driver = save_media(driver, user_name, base_dir, video_elements)

        print("Videos scraped successfully!\n")

        return (True, driver)
        
    except Exception as e:
        print(f"Error scraping videos: {str(e)}\n")
        return (False, driver)

#endregion


#region MAIN

def main():
    # Clear the screen first
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Install required dependencies first
    print("Checking and installing dependencies ...")
    install_dependencies()
    
    # Clear screen again after dependency installation
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Now display welcome message
    display_welcome_message()
    
    # Get user input
    #usernames, choices = get_user_choices()
    usernames = get_user_choices()

    driver = setup_chrome_profile()

    try:
        # Process each username
        for i, username in enumerate(usernames, 1):
            # Initialize browser per user to prevent long-run crashes and memory issues
            # ... can't do right now due to CAPTCHA
            #print("\nInitializing browser ...")
            #
            #driver = setup_chrome_profile()

            print(f"Processing account {i}/{len(usernames)}: @{username}\n")
            
            # Create backup directory structure
            base_dir = create_backup_structure(username)
            
            # Navigate to profile with handling for automation detection
            driver = initialize_browser_for_user(driver, username=username)

            if driver is None:
                print(f"Failed to load TikTok page for @{username}, skipping to next account ...\n")
                continue

            # Scrape profile information
            if not scrape_profile_info(driver, base_dir):
                print(f"Warning: Failed to scrape profile information for @{username}.\n")
            
            # Scrape pinned videos
            pinned_ok, driver = scrape_pinned_videos(driver, username, base_dir)

            if not pinned_ok:
                print(f"Warning: Failed to scrape pinned videos for @{username}.\n")
            
            videos_ok, driver = scrape_videos(driver, username, base_dir)

            # Scrape videos
            if not videos_ok:
                print(f"Warning: Failed to scrape videos for @{username}.\n")
            
            print(f"Backup completed for @{username}.\n")

            # Can't do right now due to CAPTCHA
            #driver.quit()
        
        print("All accounts processed successfully!")

    except KeyboardInterrupt:
        print('Program aborted.')

    except Exception as e:
        print(f"An error occurred: {str(e)}")

    finally:
        if driver:
            driver.quit()

#endregion

#region ENTRYPOINT

if __name__ == "__main__":
    print()
    main()
    print()
    print()

#endregion
