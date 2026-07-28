# ttpa-rename.py
# Media directory name fixer for TikTok-Profile-Archiver
# 2026-01-10T15:31:00+01

#region Imports

import argparse
import itertools
import os
import re
import shutil
import time
#import traceback

from pathlib import Path
from re import Pattern
from rich import print, traceback
from typing import Final, Optional, Union

#endregion

#region Variables

URL_STRING_PATTERN: Final[str] = r'^(?:\S+ URL:)?\s*https://www.tiktok.com/@[^/]+/(?:video|photo)/(\d+)'
URL_PATTERN: Final[Pattern[str]] = re.compile(URL_STRING_PATTERN, re.IGNORECASE)

#endregion

#region Functions

def get_id_from_info_file(path: Path) -> Optional[str]:
    """Fetches media ID from info.txt."""

    if not path.exists() or not path.is_file():
        return None

    text = path.read_text(encoding='utf8')

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for line in lines:
        if match := re.match(URL_PATTERN, line):
            return match.group(1)

    return None


def get_profile_name(profile_path: Union[Path, str]) -> str:

    directory_name = None

    if isinstance(profile_path, str):
        directory_name = profile_path
    
    elif isinstance(profile_path, Path):
        directory_name = profile_path.name
    
    else:
        raise RuntimeError(f'Invalid argument type: {repr(profile_path)}')

    name_pattern = r'^(@[a-zA-Z0-9_.]+)\s'

    if name_match := re.match(name_pattern, directory_name):
        name = name_match.group(1)
        return name
    
    else:
        raise RuntimeError(f'Path contains no valid TikTok user name: "{directory_name}"')


def dir_path(string) -> str:
    """Validates that a string represents an existing OS directory."""

    if os.path.isdir(string):
        return string

    else:
        raise NotADirectoryError(string)


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='TikTok-Profile-Archiver media collector/renamer'
    )

    parser.add_argument(
        dest='path',
        metavar='PATH',
        help='Path to a profile saved by TikTok-Profile-Archiver.',
        type=dir_path,
    )

    parser.add_argument(
        '--force',
        help='Overwrite existing media from source.',
        action='store_true',
    )

    parser.add_argument(
        '--what-if',
        help='Dry run - do not create directories/copy files,'
            ' just write what would be done.',
        action='store_true',
    )

    return parser.parse_args()

#endregion

#region MAIN

def main() -> None:

    args = get_args()

    profile_path = Path(args.path)

    media_base_path = profile_path / '04_videos'

    profile_name = get_profile_name(profile_path)

    print(f'Processing media directories for [purple]{profile_name}[/] ...')
    print()

    if media_base_path.exists():

        folder_count = 0
        video_count = 0
        slideshow_count = 0
        processed_count = 0

        folder_patterns = ['video_*', 'photos_*']

        for path in itertools.chain.from_iterable(media_base_path.glob(pattern, case_sensitive=False) for pattern in folder_patterns):

            if path.is_dir():

                info_file = path / 'info.txt'

                folder_count += 1

                is_photo_folder = 'photos' in path.name

                private_suffix = '_PRIVATE'

                is_private = private_suffix.lower() in path.name.lower()

                suffix = private_suffix if is_private else ''

                if tiktok_id := get_id_from_info_file(info_file):

                    processed_count += 1

                    if not is_photo_folder:

                        # Rename video folder
                        new_video_dir = f'{tiktok_id}_video{suffix}'

                        new_video_path = path.parent / new_video_dir

                        if args.what_if:
                            print(f'[yellow]Would rename "{str(path)}" to "{str(new_video_path)}".')

                        else:
                            print(f'Renaming "{str(path)}" to "{str(new_video_path)}" ...')
                            path.rename(new_video_path)

                        video_count += 1
                    
                    else:

                        # Rename photos folder
                        new_photos_dir = f'{tiktok_id}_photos{suffix}'

                        new_photos_path = path.parent / new_photos_dir

                        if args.what_if:
                            print(f'[yellow]Would rename "{str(path)}" to "{str(new_photos_path)}".')

                        else:
                            print(f'Renaming "{str(path)}" to "{str(new_photos_path)}" ...')
                            path.rename(new_photos_path)

                        slideshow_count += 1

                else:
                    print(f'[red]Error: Could not locate TikTok ID for "{str(path)}".')
                    print()
                    time.sleep(1.25)

        print(f'Statistics: {folder_count} folders / {video_count} videos / {slideshow_count} slideshows / {processed_count} processed')

#endregion

#region ENTRYPOINT

if __name__ == '__main__':
    print()
    print('TikTok Archive Directory Renamer')
    print()

    try:
        main()

    except KeyboardInterrupt:
        pass

    except NotADirectoryError as no_dir:
        print(f'[red]Error: "{no_dir}" is not an existing directory.')

    except Exception as ex:
        print(f'[red]Error: {ex}')
        print()
        print(traceback.Traceback())

    print()
    print()

#endregion
