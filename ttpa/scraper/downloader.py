"""Download utilities for TikTok Profile Archiver."""

from pathlib import Path
from typing import Optional

from rich import print


def download_video(url: str, output_path: Path) -> bool:
    """Downloads a video file from a URL using yt-dlp.

    :param url: The URL to download the video from.
    :type url: str

    :param output_path: The path where the video file should be saved.
    :type output_path: Path

    :return: True if the download was successful, False otherwise.
    :rtype: bool
    """
    try:
        import yt_dlp

        ydl_opts: yt_dlp.YDLOptions = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'outtmpl': str(output_path),
            'http_headers': {
                'User-Agent': 'Unknown',
            },
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            return True

    except Exception as e:
        print(f"[red]Error downloading video: {str(e)}[/red]")
        return False


def get_video_without_watermark(video_url: str) -> Optional[str]:
    """Gets the direct video URL without watermark using yt-dlp.

    :param video_url: The TikTok video URL.
    :type video_url: str

    :return: The direct video URL if successful, None otherwise.
    :rtype: Optional[str]
    """
    try:
        import yt_dlp

        ydl_opts: yt_dlp.YDLOptions = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'http_headers': {
                'User-Agent': 'Unknown',
            },
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(video_url, download=False)
            if 'url' in result:
                return result['url']

    except Exception as e:
        print(f"[red]Error getting video without watermark: {str(e)}[/red]")

    return None
