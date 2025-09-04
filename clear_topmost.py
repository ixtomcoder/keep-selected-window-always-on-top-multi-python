#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
clear_topmost.py (Windows)
- Removes the "Always on Top" (topmost) status from windows.
- Interactive or via --title filter; optional --all to clear all topmost windows.
- Confirmation added for --all; use --yes to skip confirmation.
- Optional --focus to bring a target window to foreground before clearing.

Examples:
    python clear_topmost.py              # show list, choose number -> remove topmost
    python clear_topmost.py -t "Chrome"  # clear topmost for first window with title substring "Chrome"
    python clear_topmost.py -A           # clear ALL topmost windows (confirmation required)
    python clear_topmost.py -A --yes     # clear ALL topmost windows without interactive confirmation
    python clear_topmost.py -t "Note" -f # focus the window before clearing (may change active window)
"""

import argparse
import ctypes
import platform
from ctypes import wintypes
from dataclasses import dataclass
from functools import lru_cache

# Optional: nicer process names in the list
try:
    import psutil  # type: ignore[reportMissingImports]
except Exception:
    psutil = None  # type: ignore[assignment]

SYSTEM = platform.system()
if SYSTEM != "Windows":
    raise SystemExit("This script is for Windows only.")

# Win32 constants & Signatures
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

GWL_EXSTYLE = -20
WS_EX_TOPMOST = 0x00000008

user32.EnumWindows.argtypes = [ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM), wintypes.LPARAM]
user32.EnumWindows.restype = wintypes.BOOL
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsWindowVisible.restype = wintypes.BOOL
user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
user32.GetWindowTextLengthW.restype = ctypes.c_int
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextW.restype = ctypes.c_int
user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetClassNameW.restype = ctypes.c_int
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
user32.GetWindowLongW.restype = ctypes.c_long
user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
user32.SetWindowPos.restype = wintypes.BOOL
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.SetForegroundWindow.restype = wintypes.BOOL

HWND_NOTOPMOST = wintypes.HWND(-2)
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040

@dataclass
class WindowInfo:
    hwnd: int
    title: str
    pid: int
    app: str | None
    cls: str | None

def _format_last_win_error(prefix: str = "Error") -> str:
    err = kernel32.GetLastError()
    if not err:
        return f"{prefix}: Unknown error (GetLastError=0)."
    FORMAT_MESSAGE_FROM_SYSTEM = 0x00001000
    FORMAT_MESSAGE_IGNORE_INSERTS = 0x00000200
    buf = ctypes.create_unicode_buffer(1024)
    n = kernel32.FormatMessageW(
        FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS,
        None, err, 0, buf, len(buf), None
    )
    msg = buf.value.strip() if n else "Unknown Win32 error message."
    return f"{prefix}: {msg} (Code {err})"

# -------------------------
# Utilities
# -------------------------
@lru_cache(maxsize=512)
def get_proc_name(pid: int | None) -> str | None:
    if not pid or not psutil:
        return None
    try:
        return psutil.Process(int(pid)).name()
    except Exception:
        return None

def list_windows() -> list[WindowInfo]:
    windows: list[WindowInfo] = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, lparam):
        try:
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value.strip()
            if not title:
                return True
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            cls_buf = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls_buf, 256)
            app = None
            if psutil:
                try:
                    app = get_proc_name(int(pid.value))
                except Exception:
                    app = None
            windows.append(WindowInfo(int(hwnd), title, int(pid.value), app, cls_buf.value))
        except Exception:
            pass
        return True

    user32.EnumWindows(cb, 0)
    windows.sort(key=lambda w: ((w.app or "").lower(), w.title.lower()))
    return windows

def is_topmost(hwnd: int) -> bool:
    ex = user32.GetWindowLongW(wintypes.HWND(hwnd), GWL_EXSTYLE)
    return bool(ex & WS_EX_TOPMOST)

def clear_topmost(hwnd: int, focus: bool = False) -> None:
    """
    Remove topmost. If focus=True, attempt to bring window to foreground first.
    """
    if focus:
        try:
            user32.SetForegroundWindow(wintypes.HWND(hwnd))
        except Exception:
            pass

    ok = user32.SetWindowPos(
        wintypes.HWND(hwnd), HWND_NOTOPMOST,
        0, 0, 0, 0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW
    )
    if not ok:
        msg = _format_last_win_error("SetWindowPos (NOTOPMOST) failed")
        if "Code 5" in msg or "access" in msg.lower():
            msg += ("\nHint: The target window is likely running with elevated privileges (Administrator). "
                    "Run this script as Administrator or start the target app without elevation.")
        raise RuntimeError(msg)

def choose_window(windows: list[WindowInfo]) -> WindowInfo | None:
    print("\nFound windows:")
    for i, w in enumerate(windows, 1):
        meta = []
        if w.app: meta.append(w.app)
        if w.pid: meta.append(f"PID {w.pid}")
        if w.cls: meta.append(w.cls)
        m = " • ".join(meta)
        mark = " [TOPMOST]" if is_topmost(w.hwnd) else ""
        print(f"[{i:>3}] {w.title}{mark}" + (f"  ({m})" if m else ""))
    while True:
        sel = input("\nChoose number (or Enter to cancel): ").strip()
        if not sel:
            return None
        if sel.isdigit() and 1 <= int(sel) <= len(windows):
            return windows[int(sel) - 1]
        print("Invalid input.")

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("-t", "--title", help="Title substring (case-insensitive); first match will be cleared.")
    ap.add_argument("-A", "--all", action="store_true", help="Clear ALL topmost windows (use with caution).")
    ap.add_argument("--yes", action="store_true", help="Skip confirmation prompts (use with care).")
    ap.add_argument("-f", "--focus", action="store_true", help="Bring window to foreground before clearing (may steal focus).")
    return ap.parse_args()

def main():
    args = parse_args()

    wins = list_windows()

    if args.all:
        if not args.yes:
            confirm = input("Are you sure you want to clear ALL topmost windows? This may affect important windows. (y/N): ").strip().lower()
            if confirm != "y":
                print("Aborted.")
                return
        count = 0
        for w in wins:
            if is_topmost(w.hwnd):
                try:
                    clear_topmost(w.hwnd, focus=args.focus)
                    print(f'Cleared: \"{w.title}\" (PID {w.pid}, {w.app or "?"})')
                    count += 1
                except Exception as e:
                    print(f'Error for \"{w.title}\": {e}')
        print(f"Done. Cleared {count} windows.")
        return

    target: WindowInfo | None = None
    if args.title:
        needle = args.title.lower()
        matches = [w for w in wins if needle in w.title.lower()]
        if not matches:
            print(f'No window found with title fragment \"{args.title}\".')
            return
        if len(matches) > 1:
            print(f'Multiple matches for \"{args.title}\":')
            target = choose_window(matches)
        else:
            target = matches[0]
    else:
        target = choose_window(wins)

    if not target:
        print("Cancelled.")
        return

    if not is_topmost(target.hwnd):
        print(f'"{target.title}" is not topmost – nothing to do.')
        return

    try:
        clear_topmost(target.hwnd, focus=args.focus)
        print(f'Topmost removed for: \"{target.title}\" (PID {target.pid}, {target.app or "?"})')
    except Exception as e:
        print(str(e))

if __name__ == "__main__":
    main()
