"""Path management for TikTok Profile Archiver backup structure."""


from datetime import datetime
from pathlib import Path


from ttpa.constants import (
    AVATAR_FILE_NAME,
    BIO_FILE_NAME,
    METADATA_DIR_NAME,
    PHOTO_DIR_NAME,
    STATS_FILE_NAME,
    VIDEO_DIR_NAME,
)


def create_backup_structure(user_name: str) -> Path:
    """Creates the backup directory structure for a TikTok user.

    The structure is:

    @username YYYY-MM-DD_HHMM/
    ├── avatar.png
    ├── bio.txt
    ├── stats.txt
    ├── videos/<tiktok_id>.mp4
    │   └── infos/<tiktok_id>.txt
    └── photos/<original_filename>.jpeg
        └── infos/<tiktok_id>.txt
        
    :param user_name: TikTok user name. Will be sanitized.
    :type user_name: str

    :return: The backup directory base path for the given user.
    :rtype: Path
    """
    date_str = datetime.now().strftime('%Y-%m-%d_%H%M')
    user_dir = f"@{user_name} {date_str}"

    user_path = Path.cwd() / user_dir

    # Create all necessary directories by indirection
    get_photo_metadata_dir(user_path).mkdir(parents=True, exist_ok=True)
    get_video_metadata_dir(user_path).mkdir(parents=True, exist_ok=True)

    return user_path


def get_avatar_file_path(user_dir: Path) -> Path:
    """Returns the path for the user's avatar.

    :param user_dir: The download directory for the user backup.
    :type user_dir: Path

    :return: Path to the avatar file.
    :rtype: Path
    """
    return user_dir / AVATAR_FILE_NAME


def get_bio_file_path(user_dir: Path) -> Path:
    """Returns the path for the user's bio file.

    :param user_dir: The download directory for the user backup.
    :type user_dir: Path

    :return: Path to the bio file.
    :rtype: Path
    """
    return user_dir / BIO_FILE_NAME


def get_stats_file_path(user_dir: Path) -> Path:
    """Returns the path for the user's stats file.

    :param user_dir: The download directory for the user backup.
    :type user_dir: Path

    :return: Path to the stats file.
    :rtype: Path
    """
    return user_dir / STATS_FILE_NAME


def get_photos_dir(user_dir: Path) -> Path:
    """Returns the path to the photos directory.

    :param user_dir: The download directory for the user backup.
    :type user_dir: Path

    :return: Path to the photos directory.
    :rtype: Path
    """
    return user_dir / PHOTO_DIR_NAME


def get_photo_metadata_dir(user_dir: Path) -> Path:
    """Returns the path to the photo metadata directory.

    :param user_dir: The download directory for the user backup.
    :type user_dir: Path

    :return: Path to the photo metadata directory.
    :rtype: Path
    """
    return get_photos_dir(user_dir) / METADATA_DIR_NAME


def get_photo_metadata_file_path(user_dir: Path, tiktok_id: str) -> Path:
    """Returns the path for a photo/slideshow's metadata file.

    :param user_dir: The download directory for the user backup.
    :type user_dir: Path

    :param tiktok_id: The TikTok post ID.
    :type tiktok_id: str

    :return: Path to the photo metadata file.
    :rtype: Path
    """
    return get_photo_metadata_dir(user_dir) / f"{tiktok_id}.txt"


def get_videos_dir(user_dir: Path) -> Path:
    """Returns the path to the videos directory.

    :param user_dir: The download directory for the user backup.
    :type user_dir: Path

    :return: Path to the videos directory.
    :rtype: Path
    """
    return user_dir / VIDEO_DIR_NAME


def get_video_file_path(user_dir: Path, tiktok_id: str) -> Path:
    """Returns the path for a video file.

    :param user_dir: The download directory for the user backup.
    :type user_dir: Path

    :param tiktok_id: The TikTok post ID.
    :type tiktok_id: str

    :return: Path to the video file.
    :rtype: Path
    """
    return get_videos_dir(user_dir) / f"{tiktok_id}.mp4"


def get_video_metadata_dir(user_dir: Path) -> Path:
    """Returns the path to the video metadata directory.

    :param user_dir: The download directory for the user backup.
    :type user_dir: Path

    :return: Path to the video metadata directory.
    :rtype: Path
    """
    return get_videos_dir(user_dir) / METADATA_DIR_NAME


def get_video_metadata_file_path(user_dir: Path, tiktok_id: str) -> Path:
    """Returns the path for a video's metadata file.

    :param user_dir: The download directory for the user backup.
    :type user_dir: Path

    :param tiktok_id: The TikTok post ID.
    :type tiktok_id: str

    :return: Path to the video metadata file.
    :rtype: Path
    """
    return get_video_metadata_dir(user_dir) / f"{tiktok_id}.txt"
