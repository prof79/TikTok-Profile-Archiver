"""Path management for TikTok Profile Archiver backup structure."""

from datetime import datetime
from pathlib import Path
from typing import Final

from ttpa.constants import (
    AVATAR_FILE_NAME,
    BIO_FILE_NAME,
    PHOTO_DIR_NAME,
    PHOTO_INFOS_DIR_NAME,
    STATS_FILE_NAME,
    VIDEO_DIR_NAME,
    VIDEO_INFOS_DIR_NAME,
)


def create_backup_structure(user_name: str) -> Path:
    """Creates the backup directory structure for a TikTok user.

    The structure is:
    @username YYYY-MM-DD_HHMM/
    â”œâ”€â”€ avatar.png
    â”œâ”€â”€ bio.txt
    â”œâ”€â”€ stats.txt
    â”œâ”€â”€ videos/
    â”‚   â””â”€â”€ infos/
    â””â”€â”€ photos/
        â””â”€â”€ infos/

    :param user_name: TikTok user name. Will be sanitized.
    :type user_name: str

    :return: The backup directory base path for the given user.
    :rtype: Path
    """
    date_str = datetime.now().strftime('%Y-%m-%d_%H%M')
    user_dir = f"@{user_name} {date_str}"

    base_path = Path.cwd() / user_dir

    # Create all directories
    (base_path / VIDEO_DIR_NAME / VIDEO_INFOS_DIR_NAME).mkdir(parents=True, exist_ok=True)
    (base_path / PHOTO_DIR_NAME / PHOTO_INFOS_DIR_NAME).mkdir(parents=True, exist_ok=True)

    return base_path


def get_avatar_path(user_dir: Path) -> Path:
    """Returns the path for the user's avatar.

    :param user_dir: The backup directory for the user.
    :type user_dir: Path

    :return: Path to the avatar file.
    :rtype: Path
    """
    return user_dir / AVATAR_FILE_NAME


def get_bio_path(user_dir: Path) -> Path:
    """Returns the path for the user's bio file.

    :param user_dir: The backup directory for the user.
    :type user_dir: Path

    :return: Path to the bio file.
    :rtype: Path
    """
    return user_dir / BIO_FILE_NAME


def get_stats_path(user_dir: Path) -> Path:
    """Returns the path for the user's stats file.

    :param user_dir: The backup directory for the user.
    :type user_dir: Path

    :return: Path to the stats file.
    :rtype: Path
    """
    return user_dir / STATS_FILE_NAME


def get_videos_dir(user_dir: Path) -> Path:
    """Returns the path to the videos directory.

    :param user_dir: The backup directory for the user.
    :type user_dir: Path

    :return: Path to the videos directory.
    :rtype: Path
    """
    return user_dir / VIDEO_DIR_NAME


def get_video_infos_dir(user_dir: Path) -> Path:
    """Returns the path to the video infos directory.

    :param user_dir: The backup directory for the user.
    :type user_dir: Path

    :return: Path to the video infos directory.
    :rtype: Path
    """
    return user_dir / VIDEO_DIR_NAME / VIDEO_INFOS_DIR_NAME


def get_video_metadata_path(user_dir: Path, tiktok_id: str) -> Path:
    """Returns the path for a video's metadata file.

    :param user_dir: The backup directory for the user.
    :type user_dir: Path

    :param tiktok_id: The TikTok post ID.
    :type tiktok_id: str

    :return: Path to the video metadata file.
    :rtype: Path
    """
    return get_video_infos_dir(user_dir) / f"{tiktok_id}.txt"


def get_video_path(user_dir: Path, tiktok_id: str) -> Path:
    """Returns the path for a video file.

    :param user_dir: The backup directory for the user.
    :type user_dir: Path

    :param tiktok_id: The TikTok post ID.
    :type tiktok_id: str

    :return: Path to the video file.
    :rtype: Path
    """
    return get_videos_dir(user_dir) / f"{tiktok_id}.mp4"


def get_photos_dir(user_dir: Path) -> Path:
    """Returns the path to the photos directory.

    :param user_dir: The backup directory for the user.
    :type user_dir: Path

    :return: Path to the photos directory.
    :rtype: Path
    """
    return user_dir / PHOTO_DIR_NAME


def get_photo_infos_dir(user_dir: Path) -> Path:
    """Returns the path to the photo infos directory.

    :param user_dir: The backup directory for the user.
    :type user_dir: Path

    :return: Path to the photo infos directory.
    :rtype: Path
    """
    return user_dir / PHOTO_DIR_NAME / PHOTO_INFOS_DIR_NAME


def get_photo_metadata_path(user_dir: Path, tiktok_id: str) -> Path:
    """Returns the path for a photo/slideshow's metadata file.

    :param user_dir: The backup directory for the user.
    :type user_dir: Path

    :param tiktok_id: The TikTok post ID.
    :type tiktok_id: str

    :return: Path to the photo metadata file.
    :rtype: Path
    """
    return get_photo_infos_dir(user_dir) / f"{tiktok_id}.txt"
