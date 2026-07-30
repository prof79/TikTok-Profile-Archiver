"""TikTok Profile Archiver - Main Application

Archives TikTok user profiles including:
- Profile information (avatar, bio, stats)
- Videos (named by TikTok post ID)
- Photos/slideshows (with original filenames)
- Metadata for each post

New folder structure per backup:
@username YYYY-MM-DD_HHMM/
├── avatar.png
├── bio.txt
├── stats.txt
├── videos/<tiktok_id>.mp4
│   └── infos/<tiktok_id>.txt
└── photos/<original_filename>
    └── infos/<tiktok_id>.txt
"""

import argparse
import subprocess
import sys

from pathlib import Path
from typing import Optional

from rich import print
from rich.panel import Panel

from ttpa.browser.base import BrowserBase
from ttpa.logging import setup_logging
from ttpa.paths import create_backup_structure
from ttpa.scraper.browser import (
    clear_screen,
    initialize_browser,
    initialize_browser_for_user,
)
from ttpa.scraper.media import scrape_videos
from ttpa.scraper.profile import scrape_profile_info
from ttpa.utils import parse_user_names


# ─────────────────────────────────────────────
# Argument Handling
# ─────────────────────────────────────────────

def get_arguments() -> argparse.Namespace:
    """Parses command-line arguments for the application.

    :return: Parsed arguments namespace.
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(
        prog=__file__,
        description="TikTok Profile Archiver - Archive TikTok user profiles locally.",
    )

    parser.add_argument(
        "-u", "--users",
        default=None,
        metavar="USERS",
        dest="users",
        help="TikTok user names separated by comma",
    )

    parser.add_argument(
        "-b", "--browser-name",
        default=None,
        metavar="BROWSER",
        dest="browser_name",
        choices=["chrome", "edge", "firefox"],
        help="Browser to use (chrome, edge, firefox)",
    )

    parser.add_argument(
        "--headless",
        default=False,
        action="store_true",
        dest="headless",
        help="Run browser in headless mode (no GUI)",
    )

    return parser.parse_args()


# ─────────────────────────────────────────────
# Dependencies
# ─────────────────────────────────────────────

def install_dependencies() -> None:
    """Installs required Python dependencies via pip."""
    packages = ["requests", "rich", "selenium", "yt-dlp"]
    for package in packages:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--quiet", package],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            print(f"[yellow]Warning: Could not install {package}: {e}[/yellow]")


# ─────────────────────────────────────────────
# User Interaction
# ─────────────────────────────────────────────

def display_welcome_message() -> None:
    """Displays the application welcome message."""
    print()
    print(Panel(
        "[bold]TikTok Profile Archiver[/bold]\n\n"
        "Archives a TikTok profile including:\n"
        "  • Profile information (avatar, bio, stats)\n"
        "  • Videos (named by TikTok post ID)\n"
        "  • Photos/slideshows (with original filenames)\n"
        "  • Metadata for each post\n\n"
        "New folder structure:\n"
        "  @username YYYY-MM-DD_HHMM/\n"
        "  ├── avatar.png\n"
        "  ├── bio.txt\n"
        "  ├── stats.txt\n"
        "  ├── videos/<tiktok_id>.mp4\n"
        "  │   └── infos/<tiktok_id>.txt\n"
        "  └── photos/<original_filename>\n"
        "      └── infos/<tiktok_id>.txt",
        title="[bold cyan]TikTok Profile Archiver[/bold cyan]",
        border_style="cyan",
    ))
    print()


def get_user_names_interactive() -> list[str]:
    """Prompts the user to enter TikTok user names interactively.

    :return: List of user names entered by the user.
    :rtype: list[str]
    """
    print("[cyan]Enter TikTok profile user name(s) separated by commas:[/cyan] [bold]https://www.tiktok.com/@[/bold]", end="")
    user_names_input = input().strip()
    print()
    return parse_user_names(user_names_input)


# ─────────────────────────────────────────────
# Main Application Logic
# ─────────────────────────────────────────────

def process_user(
    user_name: str,
    user_index: int,
    total_users: int,
    driver: BrowserBase,
    browser_name: Optional[str],
    headless: bool,
) -> BrowserBase:
    """Processes a single TikTok user profile.

    :param user_name: The TikTok user name to process.
    :type user_name: str

    :param user_index: The 1-based index of this user among all users.
    :type user_index: int

    :param total_users: Total number of users to process.
    :type total_users: int

    :param driver: The current browser instance.
    :type driver: BrowserBase

    :param browser_name: The name of the browser to use.
    :type browser_name: Optional[str]

    :param headless: Whether to run the browser in headless mode.
    :type headless: bool

    :return: The (possibly updated) browser instance.
    :rtype: BrowserBase
    """
    msg = f"[cyan]Processing account {user_index}/{total_users}: @{user_name}[/cyan]"
    print(msg)

    # Create backup directory structure
    user_dir = create_backup_structure(user_name)

    # Navigate to profile with handling for automation detection
    browser = initialize_browser_for_user(
        driver,
        user_name=user_name,
        browser_name=browser_name,
        headless=headless,
    )

    if browser is None:
        msg = f"[red]Failed to load TikTok page for @{user_name}, skipping to next account ...[/red]"
        print(msg)
        return driver

    # Scrape profile information
    if not scrape_profile_info(browser, user_dir):
        msg = f"[yellow]Warning: Failed to scrape profile information for @{user_name}.[/yellow]"
        print(msg)

    # Scrape videos/media
    videos_ok, browser = scrape_videos(browser, user_name, user_dir)

    if not videos_ok:
        msg = f"[red]Error: Failed to scrape videos for @{user_name}.[/red]"
        print(msg)

    msg = f"[green]Backup completed for @{user_name}.[/green]"
    print(msg)

    return browser


def main() -> None:
    """Main entry point for the TikTok Profile Archiver."""
    # Parse command-line arguments
    args = get_arguments()

    # Set up logging to file
    setup_logging()

    # Clear the screen
    clear_screen()

    # Install required dependencies
    print("[cyan]Checking and installing dependencies ...[/cyan]")
    install_dependencies()

    # Clear screen again after dependency installation
    clear_screen()

    # Display welcome message
    display_welcome_message()

    # Get user names
    user_names: list[str] = []

    if args.users is None:
        user_names = get_user_names_interactive()
    else:
        user_names = parse_user_names(args.users)
        print(f"[cyan]Users specified: @{', @'.join(user_names)}[/cyan]")
        print()

    if not user_names:
        print("[yellow]No user names provided. Exiting.[/yellow]")
        return

    # Initialize browser
    try:
        driver = initialize_browser(browser_name=args.browser_name, headless=args.headless)
    except RuntimeError as e:
        print(f"[red]Error: {e}[/red]")
        sys.exit(1)

    try:
        # Process each user name
        for index, user_name in enumerate(user_names, 1):
            driver = process_user(
                user_name,
                index,
                len(user_names),
                driver,
                args.browser_name,
                args.headless,
            )

    except KeyboardInterrupt:
        print("\n[yellow]Program aborted by user.[/yellow]")

    except Exception as e:
        print(f"\n[red]An error occurred: {str(e)}[/red]")

    finally:
        if driver:
            driver.quit()
        print("\n[green]Program finished.[/green]")


# ─────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print()
    main()
    print()
