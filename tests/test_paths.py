from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ttpa.paths import (
    create_backup_structure,
    get_avatar_path,
    get_bio_path,
    get_photo_infos_dir,
    get_photo_metadata_path,
    get_photos_dir,
    get_stats_path,
    get_video_infos_dir,
    get_video_metadata_path,
    get_video_path,
    get_videos_dir,
)

