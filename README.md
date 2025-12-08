# TikTok Profile Backup Tool

A TikTok profile backup tool that creates complete local archives of TikTok profiles including videos, metadata, and profile information.

Please note that some content in this Read Me is still incorrect as it reflects the expectations of the original developer for the final tool not what the actual codebase can do (like command-line arguments).

## Features

- **Profile Backup**
  - Avatar images (high resolution)
  - Bio text with formatting
  - Statistics (followers, following, likes)
  - Profile links and website info
  - Custom fields and verification status

- **Video Content**
  - Regular videos (highest quality)
  - Pinned videos with priority handling
  - Video metadata (date, likes, shares)
  - Comments & replies (including timestamps)
  - Sound information and music details
  - Hashtags and mentions
  - Video thumbnails

- **Organization**
  - Timestamped backups for version control
  - Clear folder structure
  - Detailed metadata files (JSON format)
  - HTML snapshots for offline viewing
  - Automatic file naming
  - Duplicate detection

## Requirements

- Python 3.8 or higher
- Google Chrome browser (latest version recommended)
- Internet connection (broadband recommended)
- Windows/macOS/Linux
- Storage space (varies by profile size)
- RAM: 4GB minimum, 8GB recommended

## Quick Start

1. Ensure Python 3.8+ and Chrome are installed
2. Download tt-backup.py
3. Run: `python tt-backup.py`
4. Enter usernames when prompted
5. Select backup options
6. Wait for completion

### Advanced Usage
bash
Backup specific sections only
python tt-backup.py --videos-only @username
Backup multiple accounts
python tt-backup.py --accounts @user1,@user2,@user3
Set custom output directory
python tt-backup.py --output /path/to/backup/folder
Enable debug logging
python tt-backup.py --debug

## Output Structure

@username YearMonthDay_HoursMinutes/
├── 01_profile/
│ ├── 01_avatar/
│ ├── 02_bio/
│ └── 03_stats/
├── 02_pinned_videos/
├── 03_playlists/
├── 04_videos/
├── 05_reposts/
├── 06_favorites/
├── 07_liked/
└── 08_html_snapshot/

### File Formats

- Videos: MP4 (highest quality available)
- Images: JPG/PNG (original quality)
- Metadata: JSON
- Text: UTF-8 encoded
- Snapshots: HTML/CSS/JS

## Known Issues

- Chrome profile loading may crash occasionally
  - Workaround: Retry with --new-profile flag
- Some private videos need manual verification
  - Solution: Use logged-in Chrome profile
- Rate limiting on mass downloads
  - Mitigation: Built-in throttling system

## Usage Tips

- Use existing Chrome profile for logged-in state
- Back up most important content first
- Run during off-peak hours for better performance
- Check output folders for successful downloads
- Keep Chrome browser updated
- Regular backups recommended
- Monitor available disk space
- Use stable internet connection

## Troubleshooting

Common issues and solutions:

1. **Chrome Won't Start**
   - Update Chrome to latest version
   - Clear Chrome user data
   - Try --new-profile flag

2. **Download Failures**
   - Check internet connection
   - Verify TikTok account accessibility
   - Try with different Chrome profile
   - Use --retry flag

3. **Missing Content**
   - Verify account privacy settings
   - Check storage permissions
   - Run with --verify flag

## Resources

- [Privacy Policy](web/privacy.html)
- [Full Documentation](web/readme.html)
- [Original Roadmap](roadmap.map) (with no intent of completion)

## License

MIT License - See LICENSE file for details

## Acknowledgments

- The original developers (@itsKayWat) and their supporters
