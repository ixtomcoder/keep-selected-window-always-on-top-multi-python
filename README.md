# keep-selected-window-always-on-top-multi-python

[![OS](https://img.shields.io/badge/OS-Windows%20%7C%20macOS%20%7C%20Linux%20(X11)-informational?style=flat-square)](#platform-notes)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square)](#requirements)
[![License](https://img.shields.io/badge/License-MIT-success?style=flat-square)](./LICENSE)


Cross-platform CLI utilities to keep selected windows always on top or clear the flag. Lists visible top-level windows, supports multi-select (indices, ranges, *), optional focus control, safe clear-all with confirm, auto-cleanup unless --persist. Windows (SetWindowPos) and Linux/X11 (wmctrl); macOS lists only. Python 3.10+; psutil optional.

Repository: https://github.com/ixtomcoder/keep-selected-window-always-on-top-multi-python

---

## Quickstart (copy/paste)

Windows (PowerShell):
```powershell
# optional: install psutil for nicer process names
python -m pip install --user psutil

# set "always on top" for selected windows (multi-select via indices/ranges/*)
python .\always_on_top.py

# keep topmost after exit
python .\always_on_top.py --persist

# set and bring windows to foreground (may steal focus)
python .\always_on_top.py --focus

# clear topmost (interactive list)
python .\clear_topmost.py

# clear by title substring
python .\clear_topmost.py -t "chrome"

# clear ALL topmost (asks for confirmation)
python .\clear_topmost.py -A

# clear ALL topmost without confirmation (use with care)
python .\clear_topmost.py -A --yes
```

Linux (Bash, X11 required — Wayland typically not supported):
```bash
# install dependencies (Debian/Ubuntu)
sudo apt update && sudo apt install -y wmctrl python3-pip
pip3 install --user psutil  # optional

# set "always on top" for selected windows (X11 only)
python3 always_on_top.py

# keep topmost after exit
python3 always_on_top.py --persist

# set and bring windows to foreground (focus)
python3 always_on_top.py --focus
```

macOS (listing only, no cross-app always-on-top available):
```bash
python3 always_on_top.py
```

---

## Common commands

```bash
# Windows: set topmost for selected windows (no focus steal)
python .\always_on_top.py

# Windows: set topmost and focus the windows
python .\always_on_top.py --focus

# Windows: keep topmost after script exits
python .\always_on_top.py --persist

# Windows: clear a single topmost window via interactive list
python .\clear_topmost.py

# Windows: clear by title substring (case-insensitive)
python .\clear_topmost.py -t "notepad"

# Windows: clear all topmost (with confirmation)
python .\clear_topmost.py -A

# Windows: clear all topmost (no confirmation; use with care)
python .\clear_topmost.py -A --yes

# Linux/X11: set topmost (requires wmctrl and X11 session)
python3 always_on_top.py
```

---

## Features

- List visible top-level windows with process/PID info (when `psutil` is installed).
- Multi-select windows by index, ranges, or `*` (all).
- Set "Always on Top"
  - Windows via Win32 APIs
  - Linux/X11 via `wmctrl`
- Clear "Always on Top" on Windows (interactive, by title, or all with confirmation).
- Auto-cleanup on exit (unless `--persist` is used).
- Optional focus control: `--focus` (may steal focus).

---

## Requirements

- Python 3.10+
- Optional (recommended): `psutil` for nicer process names and PIDs
- Linux/X11 only: `wmctrl`
  - Debian/Ubuntu: `sudo apt install wmctrl`
  - Fedora: `sudo dnf install wmctrl`

---

## Installation

Clone the repository:
```bash
git clone https://github.com/ixtomcoder/keep-selected-window-always-on-top-multi-python.git
cd keep-selected-window-always-on-top-multi-python
```

Install optional Python dependency:
```bash
# Windows
python -m pip install --user psutil

# Linux
pip3 install --user psutil
```

Linux packages:
```bash
sudo apt update && sudo apt install -y wmctrl python3-pip
```

---

## Usage

Important: This repository uses the English scripts `always_on_top.py` and `clear_topmost.py` as the primary tools. The German originals remain with `_de` suffix for reference.

always_on_top.py (Windows & X11):
```bash
# list and multi-select (indices, ranges, *)
python always_on_top.py              # Windows (PowerShell: python .\always_on_top.py)
python always_on_top.py --persist    # keep topmost after exit
python always_on_top.py --focus      # bring selected window(s) to foreground
```

clear_topmost.py (Windows only):
```bash
python clear_topmost.py              # interactive (marks [TOPMOST] in the list)
python clear_topmost.py -t "chrome"  # clear by title substring (first match; multiple -> choose)
python clear_topmost.py -A           # clear ALL topmost (asks for confirmation)
python clear_topmost.py -A --yes     # clear ALL topmost (no confirmation; use with care)
python clear_topmost.py -t "Note" -f # focus window before clearing
```

---

## Platform notes

- Windows
  - Full set/unset support via Win32 APIs.
  - Elevated windows: If a target window runs elevated (Administrator), changing its topmost state from a non-elevated script may fail (error/Code 5). Run this script as Administrator.
- Linux / X11
  - Requires an X11 session; Wayland generally does not support this use-case.
  - `wmctrl` must be installed.
- macOS
  - Listing only; no reliable cross-app always-on-top.

---

## Troubleshooting

```text
"wmctrl not found" (Linux)
-> Install wmctrl (e.g., sudo apt install wmctrl) and ensure X11 session (XDG_SESSION_TYPE=x11).

"SetWindowPos failed ... Code 5" (Windows)
-> Access denied; target window likely runs elevated. Run script as Administrator.

No windows listed / titles missing
-> Ensure windows are visible & top-level; some special windows are hidden or not top-level.

psutil missing
-> Install it for nicer output: pip install --user psutil (Windows) / pip3 install --user psutil (Linux).
```

---

## Files

- `always_on_top.py` (primary, English)
- `clear_topmost.py` (primary, English, Windows only)
- `always_on_top_de.py` (original German, reference)
- `clear_topmost_de.py` (original German, reference)

---

## Contributing

- Issues and PRs are welcome. Keep PRs focused and small for easier review.

---

## License

MIT — see [LICENSE](./LICENSE)

Copyright (c) 2025 https://github.com/ixtomcoder
