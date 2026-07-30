# Project Architecture

This is a Python text-based application for scraping TikTok content using Selenium and YT-DLP. For enriched colorful output Rich is used.

The structure is as follows:

- The main application is `TikTok-Profile-Archiver.py`
- Local modules are in `/ttpa`, code has still to be re-factored out from the main file
- Additional standalone tools are in `/tools`
- Legacy documentation in `/web` that needs to be reviewed
- `/build`, `/dist` and `/assets` reserved for use by PyInstaller
- `build.py` as an attempt to automate PyInstaller
- `gui.py` was an attempt of the previous author to create a Tk-based GUI for the application
- `/ttpa/browser` contains facades for major browser to abstract Selenium usage
- `TikTok Backup - Structure.txt` contains a sample directory structure for downloads

## Coding Standards

- Use Python 3.12 for all new files
- Use typing everywhere (function arguments, return values, variables, ...)
- Keep/modify function docstrings and add them for new functions
- Use `Path` from `pathlib` instead of `os` functions where possible and be idiomatic (eg. using `/`-operator)
- Make sure Rich is used for colorful output (eg. `from rich import print`)
- Use the `BrowserBase` facade instead of accessing Selenium directly
- Follow the existing naming conventions
- Write tests for all new features
