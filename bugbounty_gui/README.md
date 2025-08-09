# Recon to Master — Bug Bounty GUI (Upgraded)

This upgraded PySide6 GUI wraps your reconnaissance checklist into an interactive dashboard.

Features:
- Dark theme, resizable split layout
- Search, favorites toggle, run-in-terminal option
- PTY-based runner for interactive tools
- Log saving for each run in ./logs

Requirements:
- Python 3.10+
- PySide6

Install:
```
python -m pip install --upgrade pip
pip install pyside6
```

Run:
```
python main.py
```

Notes:
- Commands in `commands.py` include placeholders like {target}, {cidr}, {asn} and API keys placeholders such as [api-key]. Replace before running.
- External terminal execution tries common Linux terminal emulators. If none are found, will run inside the GUI.
- PTY mode allows interactive programs. Some programs may still not behave perfectly inside the GUI due to terminal emulation limits.
- Always have explicit authorization before testing any target.
