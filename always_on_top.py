#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
always_on_top.py (Multi-Select)
- Lists all visible top-level windows.
- Multi-select windows, e.g. "1 3 5-7" or "*" for all.
- Sets the selected windows to "Always on Top" (Windows/X11).
- Automatically removes "Always on Top" on exit (including CTRL+C), unless run with --persist.
- macOS: listing only; true always-on-top for foreign app windows is not available.

Notes:
- Default behavior does NOT steal focus. Use --focus if you want the window focused.
- Requires Python 3.10+ (uses modern type syntax).
Usage:
    python always_on_top.py [--persist] [--focus]
"""

import os
import sys
import time
import platform
import shutil
import argparse
from dataclasses import dataclass
from functools import lru_cache

# Optional: nicer process names; skipped if not available.
try:
    import psutil  # type: ignore[reportMissingImports]
except Exception:
    psutil = None  # type: ignore[assignment]

SYSTEM = platform.system()

@dataclass
class WindowInfo:
    wid: str          # Windows: HWND as string; X11: hex id; macOS: CGWindowNumber
    title: str
    pid: int | None
    app: str | None   # process/owner name
    extra: str | None # e.g. class name (Windows)

def _truncate(s: str, n: int = 90) -> str:
    s = s or ""
    return s if len(s) <= n else s[:n - 1] + "…"

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

# -------------------------
# Windows-specific
# -------------------------
def list_windows_windows() -> list[WindowInfo]:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32

    EnumWindows = user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    IsWindowVisible = user32.IsWindowVisible
    GetWindowTextW = user32.GetWindowTextW
    GetWindowTextLengthW = user32.GetWindowTextLengthW
    GetClassNameW = user32.GetClassNameW
    GetWindowThreadProcessId = user32.GetWindowThreadProcessId

    windows: list[WindowInfo] = []

    def callback(hwnd, lParam):
        try:
            if IsWindowVisible(hwnd):
                length = GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    GetWindowTextW(hwnd, buf, length + 1)
                    title = buf.value.strip()
                    if title:
                        pid = wintypes.DWORD()
                        GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                        cls = ctypes.create_unicode_buffer(256)
                        GetClassNameW(hwnd, cls, 256)
                        app = get_proc_name(int(pid.value))
                        windows.append(WindowInfo(str(int(hwnd)), title, int(pid.value), app, cls.value))
        except Exception:
            pass
        return True

    EnumWindows(EnumWindowsProc(callback), 0)
    windows.sort(key=lambda w: ((w.app or "").lower(), w.title.lower()))
    return windows

def _format_last_win_error(prefix: str = "Error") -> str:
    import ctypes
    kernel32 = ctypes.windll.kernel32
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

def set_always_on_top_windows(hwnd_int: int, enable: bool = True, focus: bool = False):
    """
    Set or clear topmost on Windows.
    If focus is True, SetForegroundWindow will be called; otherwise the window will not steal focus.
    """
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
    user32.SetWindowPos.restype = wintypes.BOOL
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.ShowWindow.restype = wintypes.BOOL

    HWND_TOPMOST = wintypes.HWND(-1)
    HWND_NOTOPMOST = wintypes.HWND(-2)
    SWP_NOSIZE = 0x0001
    SWP_NOMOVE = 0x0002
    SWP_SHOWWINDOW = 0x0040
    SW_SHOWNOACTIVATE = 4

    flags = SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
    target = HWND_TOPMOST if enable else HWND_NOTOPMOST

    hwnd = wintypes.HWND(hwnd_int)
    # Show non-activating to avoid stealing focus unless requested
    user32.ShowWindow(hwnd, SW_SHOWNOACTIVATE)

    ok = user32.SetWindowPos(hwnd, target, 0, 0, 0, 0, flags)
    if not ok:
        msg = _format_last_win_error("SetWindowPos failed")
        if "Code 5" in msg or "access" in msg.lower():
            msg += ("\nHint: The target window is likely running with elevated privileges (Administrator). "
                    "Run this script with the same elevated privileges OR start the target app without elevation.")
        raise RuntimeError(msg)
    if focus:
        try:
            user32.SetForegroundWindow(hwnd)
        except Exception:
            pass

# -------------------------
# Linux / X11
# -------------------------
def list_windows_linux_x11() -> list[WindowInfo]:
    if not shutil.which("wmctrl"):
        raise RuntimeError("wmctrl not found. Install it, e.g.: sudo apt install wmctrl")
    import subprocess
    proc = subprocess.run(["wmctrl", "-l", "-p"], capture_output=True, text=True, check=True)
    windows: list[WindowInfo] = []
    for line in proc.stdout.splitlines():
        parts = line.split(None, 4)
        if len(parts) < 5:
            continue
        wid_hex, desktop, pid_str, host, title = parts
        pid = int(pid_str) if pid_str.isdigit() else None
        app = get_proc_name(pid)
        windows.append(WindowInfo(wid_hex, title.strip() or "<no title>", pid, app, None))
    windows.sort(key=lambda w: ((w.app or "").lower(), w.title.lower()))
    return windows

def set_always_on_top_linux_x11(wid_hex: str, enable: bool = True, sticky: bool = False, focus: bool = False):
    import subprocess
    action = "add" if enable else "remove"
    subprocess.run(["wmctrl", "-i", "-r", wid_hex, "-b", f"{action},above"], check=True)
    if sticky:
        subprocess.run(["wmctrl", "-i", "-r", wid_hex, "-b", f"{action},sticky"], check=True)
    if focus:
        subprocess.run(["wmctrl", "-i", "-a", wid_hex], check=True)

# -------------------------
# macOS (listing only)
# -------------------------
def list_windows_macos() -> list[WindowInfo]:
    from Quartz import (  # type: ignore[reportMissingImports]
        CGWindowListCopyWindowInfo,
        kCGWindowListOptionOnScreenOnly,
        kCGNullWindowID,
    )
    info = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
    windows: list[WindowInfo] = []
    for w in info:
        owner = w.get("kCGWindowOwnerName", "")
        name = w.get("kCGWindowName", "")
        number = w.get("kCGWindowNumber", None)
        pid = w.get("kCGWindowOwnerPID", None)
        title = f"{owner} — {name}" if name else owner
        if title and number:
            windows.append(WindowInfo(str(int(number)), title.strip(), int(pid) if pid else None, owner, None))
    windows = [w for w in windows if w.title and w.pid]
    windows.sort(key=lambda w: ((w.app or "").lower(), w.title.lower()))
    return windows

# -------------------------
# Multi-Select UI
# -------------------------
def parse_multi_selection(sel: str, n: int) -> list[int]:
    """
    Selection format:
      - multiple numbers separated by spaces/commas: "1 3,4"
      - ranges: "5-8"
      - star: "*" or "a" -> all
    Returns 1-based indices in ascending unique order.
    """
    sel = sel.strip().lower()
    if not sel:
        return []
    if sel in ("*", "a", "all", "alle"):
        return list(range(1, n + 1))

    out: list[int] = []
    def add_idx(i: int):
        if 1 <= i <= n and i not in out:
            out.append(i)

    for tok in sel.replace(",", " ").split():
        if "-" in tok:
            try:
                start_s, end_s = tok.split("-", 1)
                start, end = int(start_s), int(end_s)
                if start > end:
                    start, end = end, start
                for i in range(start, end + 1):
                    add_idx(i)
            except ValueError:
                continue
        else:
            if tok.isdigit():
                add_idx(int(tok))
    out.sort()
    return out

def choose_windows_multi(windows: list[WindowInfo]) -> list[WindowInfo]:
    if not windows:
        print("No windows found.")
        return []
    print("\nFound windows:")
    for i, w in enumerate(windows, 1):
        meta = []
        if w.app: meta.append(w.app)
        if w.pid: meta.append(f"PID {w.pid}")
        if w.extra: meta.append(w.extra)
        m = " • ".join(meta)
        print(f"[{i:>3}] { _truncate(w.title) }" + (f"  ({m})" if m else ""))
    print("\nMultiple numbers possible, e.g.: 1 3 5-7   or   *  for all.")
    while True:
        sel = input("Select numbers (Enter = cancel): ").strip()
        if not sel:
            return []
        idxs = parse_multi_selection(sel, len(windows))
        if idxs:
            return [windows[i - 1] for i in idxs]
        print("Invalid input.")

# -------------------------
# CLI / main
# -------------------------
def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("-p", "--persist", action="store_true",
                   help="Do NOT automatically remove topmost status on exit.")
    p.add_argument("-f", "--focus", action="store_true",
                   help="Bring window to foreground when setting topmost (may steal focus).")
    return p.parse_args()

def main():
    args = parse_args()
    print(f"Platform: {SYSTEM}")
    if SYSTEM == "Windows":
        windows = list_windows_windows()
        chosen = choose_windows_multi(windows)
        if not chosen:
            print("Cancelled.")
            return

        hwnds_ok: list[int] = []
        try:
            for win in chosen:
                hwnd = int(win.wid)
                try:
                    set_always_on_top_windows(hwnd, True, focus=args.focus)
                    hwnds_ok.append(hwnd)
                    print(f'↑ Topmost set: \"{_truncate(win.title)}\"  ({win.app or "?"}, PID {win.pid})')
                except RuntimeError as e:
                    print(f'⚠️  Could not set for \"{_truncate(win.title)}\": {e}')

            if hwnds_ok:
                print("\nENTER: exit (Auto-Cleanup),  'u'+ENTER: remove topmost for all selected and exit.")
                cmd = input("> ").strip().lower()
                if cmd == "u":
                    for hwnd in hwnds_ok:
                        try:
                            set_always_on_top_windows(hwnd, False, focus=args.focus)
                        except Exception:
                            pass
                    hwnds_ok.clear()
                    print("Topmost removed for all selected windows.")
        finally:
            if hwnds_ok and not args.persist:
                # Auto-Cleanup
                for hwnd in hwnds_ok:
                    try:
                        set_always_on_top_windows(hwnd, False, focus=args.focus)
                    except Exception:
                        pass
                print("Topmost (Auto-Cleanup) removed for all selected windows.")
    elif SYSTEM == "Linux":
        session = os.environ.get("XDG_SESSION_TYPE", "").lower()
        if session == "wayland":
            print("Note: Wayland restricts window management. This script requires X11 (Xorg).")
            print("If your desktop session uses Wayland, 'wmctrl' usually does not work reliably.")
            return
        windows = list_windows_linux_x11()
        chosen = choose_windows_multi(windows)
        if not chosen:
            print("Cancelled.")
            return

        ids_ok: list[str] = []
        try:
            for win in chosen:
                try:
                    set_always_on_top_linux_x11(win.wid, True, sticky=False, focus=args.focus)
                    ids_ok.append(win.wid)
                    print(f'↑ Topmost set: \"{_truncate(win.title)}\"  ({win.app or "?"}, PID {win.pid})')
                except Exception as e:
                    print(f'⚠️  Could not set for \"{_truncate(win.title)}\": {e}')

            if ids_ok:
                print("\nENTER: exit (Auto-Cleanup),  'u'+ENTER: remove topmost for all selected and exit.")
                cmd = input("> ").strip().lower()
                if cmd == "u":
                    for wid in ids_ok:
                        try:
                            set_always_on_top_linux_x11(wid, False, sticky=False, focus=args.focus)
                        except Exception:
                            pass
                    ids_ok.clear()
                    print("Topmost removed for all selected windows.")
        finally:
            if ids_ok and not args.persist:
                for wid in ids_ok:
                    try:
                        set_always_on_top_linux_x11(wid, False, sticky=False, focus=args.focus)
                    except Exception:
                        pass
                print("Topmost (Auto-Cleanup) removed for all selected windows.")
    elif SYSTEM == "Darwin":
        print("macOS note: True always-on-top for foreign app windows is not generally available system-wide.")
        windows = list_windows_macos()
        chosen = choose_windows_multi(windows)
        if not chosen:
            print("Cancelled.")
            return
        print("\nSelected (no topmost action on macOS):")
        for w in chosen:
            print(f'• \"{_truncate(w.title)}\" ({w.app}, PID {w.pid})')
    else:
        print("Unsupported system.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled.")
