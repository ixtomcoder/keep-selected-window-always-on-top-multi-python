# keep-selected-window-always-on-top-multi-python

Cross-platform CLI utilities to keep selected windows always on top or clear the flag. Lists visible top-level windows, supports multi-select (indices, ranges, *), optional focus control, safe clear-all with confirm, auto-cleanup unless --persist. Windows (SetWindowPos) and Linux/X11 (wmctrl); macOS lists only. Python 3.10+; psutil optional. Ready.

Repository: https://github.com/ixtomcoder/keep-selected-window-always-on-top-multi-python

This repository contains the main CLI scripts (English versions are the primary tools):

- `always_on_top.py` — Multi-select utility to set selected windows to "Always on Top" (Windows / X11).
- `clear_topmost.py` — Windows-only utility to remove the "Always on Top" flag from windows (interactive or filtered by title / all).


---

## Short description (for GitHub "Description" field)
Cross-platform CLI utilities to list visible top-level windows and set them "Always on Top" on Windows and X11 (Linux). Multi-select, optional focus, safe clear-all, auto-cleanup.

(Kurzbeschreibung auf Deutsch)
CLI-Tools zum Setzen/Entfernen von „Always on Top“ für ausgewählte Fenster (Windows & X11). Multi-Select, optionaler Fokus, sichere Massen-Operationen, Auto-Cleanup.

---

## Summary of recent changes

- English scripts are now the primary files (`always_on_top.py`, `clear_topmost.py`).
- Project requires Python **3.10+** (modern type syntax used).
- Quick UX improvements:
  - `--focus` flag (both scripts): optional — brings a window to foreground when requested (default: do not steal focus).
  - `--yes` flag (for `clear_topmost.py -A`) to skip confirmation.
  - Process name lookups are cached for better performance when many windows are listed.
- LICENSE file (MIT) added and the repository information updated.

---

## Features

- List visible top-level windows with process / PID information (when `psutil` is available).
- Multi-select windows by index, ranges, or `*` (all).
- Set "Always on Top" on Windows using Win32 APIs.
- Set "Always on Top" on X11 using `wmctrl`.
- Clear "Always on Top" on Windows interactively, by title substring, or for all topmost windows.
- Auto-cleanup: scripts remove the topmost flag on exit by default (unless `--persist` is used).

---

## Platform Notes / Limitations (IMPORTANT)

- Windows
  - Full set/unset support using Win32 APIs.
  - Some windows may be protected by elevation: if the target window runs elevated (Administrator), changing its topmost state from a non-elevated process will fail. Run the script as Administrator to operate on elevated windows.
- Linux / X11 (CRITICAL)
  - Scripts rely on `wmctrl` to modify window properties and require an X11/Xorg session.
  - Wayland: most Wayland sessions prevent these kinds of window property changes. If your desktop uses Wayland, the scripts may not work reliably or at all. Check `XDG_SESSION_TYPE` (should be `x11` for reliable behavior).
- macOS
  - The tool can list windows but cannot enforce "Always on Top" for foreign application windows in a reliable cross-app way (system restrictions).

---

## Requirements

- Python 3.10+
- Optional but recommended:
  - psutil — to show nicer process names and PIDs (`pip install psutil`)
- Linux specific:
  - wmctrl — used to list and set topmost on X11.
    - Debian/Ubuntu: `sudo apt install wmctrl`
    - Fedora: `sudo dnf install wmctrl`
- Windows:
  - No external dependencies required for the Win32 implementation, but `psutil` is recommended for nicer output.

---

## Installation

Clone the repository:

git clone https://github.com/ixtomcoder/keep-selected-window-always-on-top-multi-python.git
cd keep-selected-window-always-on-top-multi-python

Install optional Python dependencies:

pip install --user psutil

Linux example (Debian/Ubuntu):

sudo apt update
sudo apt install wmctrl python3-pip
pip3 install --user psutil

Windows example (PowerShell):

python -m pip install --user psutil

---

## Usage

All commands below assume you are in the project root or the directory where the scripts are located.

Important: The repository uses the English scripts `always_on_top.py` and `clear_topmost.py` as the primary tools. The German originals remain in the repo with `_de` suffix but are not required for normal use.

CLI flags introduced:
- `-f`, `--focus` — Bring the window to the foreground when changing topmost state (may steal focus). Default behavior is to avoid stealing focus.
- `-p`, `--persist` — (always_on_top.py) Do NOT automatically remove topmost state on exit.
- `-A`, `--all` — (clear_topmost.py) Clear ALL topmost windows (confirmation required unless `--yes` is provided).
- `--yes` — Skip confirmation prompts (use with care).

### always_on_top.py (cross-platform: Windows & X11)

Lists visible windows and allows you to select multiple windows to set as topmost.

Basic usage:

python always_on_top.py

- Choose windows by index. Selection formats:
  - Single numbers separated by space or comma: `1 3 5`
  - Ranges: `2-5`
  - Combined: `1 3-4 7`
  - All: `*`, `a`, or `all`

Flags:

- `-p / --persist` — Do NOT automatically remove the topmost state on exit.
- `-f / --focus` — Bring the selected window(s) to foreground when setting topmost (may steal focus).

Examples:

- Set two windows topmost (no focus steal):
  - python always_on_top.py
  - Input selection: `2 5`
- Set all visible windows topmost:
  - python always_on_top.py
  - Input selection: `*`
- Keep windows topmost after exit:
  - python always_on_top.py --persist
- Set topmost and bring windows to foreground:
  - python always_on_top.py --focus

Notes:

- On Windows, if changing a window fails with an error mentioning access/Code 5, the target app likely runs elevated. Re-run the script with Administrator privileges.
- On Linux, ensure you're running an X11 session and that `wmctrl` is installed. For Wayland sessions this script may not work.

### clear_topmost.py (Windows only)

Removes topmost status from windows. Interactive or filtered.

Basic usage:

python clear_topmost.py

- Shows a numbered list of visible windows; topmost windows are marked.
- Choose a number to clear topmost for that window.

Flags:

- `-t / --title "TEXT"` — Finds windows whose title contains the substring (case-insensitive). If multiple matches occur you can choose interactively from the matches. The first match will be cleared if unique.
- `-A / --all` — Clears ALL topmost windows. Use with caution; confirmation is required unless `--yes` is supplied.
- `--yes` — Skip the confirmation prompt for destructive actions like `-A`.
- `-f / --focus` — Bring target window to foreground before clearing (may steal focus).

Examples:

- Interactive:
  - python clear_topmost.py
  - Choose number `3` to clear.
- Clear by title:
  - python clear_topmost.py -t "chrome"
- Clear all topmost (confirmation required):
  - python clear_topmost.py -A
- Clear all topmost without confirmation (use with extreme care):
  - python clear_topmost.py -A --yes
- Clear by title and focus the window first:
  - python clear_topmost.py -t "Notepad" --focus

Notes:

- If clearing fails with an access error, run the script as Administrator to affect elevated windows.

---

## Troubleshooting & Common Errors

- "wmctrl not found" (Linux)
  - Install wmctrl via your package manager (e.g., `sudo apt install wmctrl`).
  - Confirm you are running an X11 session (not Wayland). Check `XDG_SESSION_TYPE` (should be `x11` for reliable behavior).
- "SetWindowPos failed ... Code 5" (Windows)
  - Means access denied; target window probably runs elevated. Run this script with Administrator privileges.
- No windows listed / titles missing
  - Some windows are not considered top-level or are hidden; ensure the application windows are visible on the current desktop.
- psutil missing or fails to import
  - Process names will be omitted; install psutil for nicer output: `pip install psutil`

---

## Security & Safety

- Scripts use system-level window APIs and can affect other applications. Only run them if you understand the effects.
- Use `--persist` only when you intentionally want windows to remain topmost after the script exits.
- Avoid using `clear_topmost.py -A` on critical systems or when unsure which windows are topmost.
- Use `--yes` only when scripting or when you intentionally want to skip confirmations.

---

## Contributing

- Bug reports and feature requests: open an Issue on GitHub.
- Pull requests: preferred style is small focused PRs with a short description.
- Tests: none included; manual testing recommended for various desktop environments.

---

## License

This project is licensed under the MIT License — see [LICENSE](./LICENSE) for details.

Copyright (c) 2025 https://github.com/ixtomcoder

---

## Next improvements (ideas / optional)

- Refactor duplicated utilities into `window_utils.py`.
- Add `--json` / `--csv` output for scripting / automation.
- Replace prints with `logging` and add verbosity flags.
- Add `--ids` non-interactive selection, or regex filters for title/process.
- Add packaging (pyproject.toml) and CI checks (linting, type checks).
