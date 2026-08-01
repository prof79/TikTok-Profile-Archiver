from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ttpa.paths import (
    create_backup_structure,
    get_avatar_file_path,
    get_bio_file_path,
    get_photo_metadata_dir,
    get_photo_metadata_file_path,
    get_photos_dir,
    get_stats_file_path,
    get_video_metadata_dir,
    get_video_metadata_file_path,
    get_video_file_path,
    get_videos_dir,
)
