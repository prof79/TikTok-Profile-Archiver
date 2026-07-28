# ttpa-bundle.py
# Media collection/name bundler for TikTok-Profile-Archiver
# 2026-01-11T20:17:00+01

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
    """Fetches TikTok media ID from info.txt."""

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

    photos_target_path = Path(profile_name) / '99_all_photos'
    videos_target_path = Path(profile_name) / '99_all_videos'

    force = args.force

    print(f'Processing media directories for [purple]{profile_name}[/] ...')
    print()

    if not videos_target_path.exists():
        if args.what_if:
            print(f'[yellow]Would create dir: "{videos_target_path}"')
        else:
            videos_target_path.mkdir(parents=True)

    if not photos_target_path.exists():
        if args.what_if:
            print(f'[yellow]Would create dir: "{photos_target_path}"')
        else:
            photos_target_path.mkdir(parents=True)

    if media_base_path.exists():

        folder_count = 0
        video_count = 0
        videos_copied = 0
        slideshow_count = 0
        photo_count = 0
        photos_copied = 0
        processed_count = 0

        folder_patterns = ['video_*', 'photos_*', '*_video', '*_photos']
        jpeg_patterns = ['*.jpg', '*.jpeg']

        for path in itertools.chain.from_iterable(media_base_path.glob(pattern, case_sensitive=False) for pattern in folder_patterns):

            if path.is_dir():

                info_file = path / 'info.txt'
                video_file = path / 'video.mp4'

                folder_count += 1

                is_photo_folder = 'photos' in path.name

                if video_file.exists() or is_photo_folder:

                    if id := get_id_from_info_file(info_file):

                        processed_count += 1

                        if not is_photo_folder:

                            renamed_video_file = videos_target_path / f'{id}.mp4'

                            copied = copy_media(path, id, video_file, renamed_video_file, args.what_if, force)

                            if copied:
                                videos_copied += 1

                            video_count += 1
                        
                        else:

                            slideshow_count += 1

                            for photo in itertools.chain.from_iterable(path.glob(pattern, case_sensitive=False) for pattern in jpeg_patterns):

                                if photo.is_file():

                                    renamed_photo_file = photos_target_path / photo.name

                                    copied = copy_media(path, id, photo, renamed_photo_file, args.what_if, force)

                                    if copied:
                                        photos_copied += 1

                                    photo_count += 1

                    else:
                        print(f'[red]Error: Could not locate TikTok ID for "{str(path)}".')
                        print()
                        time.sleep(1.25)

        print(f'Statistics: {folder_count} folders / {processed_count} processed / {video_count} videos ({videos_copied} copied) / {slideshow_count} slideshows / {photo_count} photos ({photos_copied} copied)')


def copy_media(path: Path, id: str, source_file: Path, renamed_file: Path, what_if: bool=False, force: bool=False) -> bool:

    print(f'[magenta]Path: "{str(path)}"')
    print(f'ID {id} found.')

    if renamed_file.exists() and not force:
        print(f'[green]"{str(renamed_file)}" already exists.\n')

    elif what_if:
        print(f'[yellow]Would copy to: "{str(renamed_file)}"\n')

    else:
        print(f'Copying to file "{str(renamed_file)}" ...\n')
        shutil.copy2(source_file, renamed_file)
        return True

    return False

#endregion

#region ENTRYPOINT

if __name__ == '__main__':
    print()
    print('TikTok Archived Media Bundler')
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
