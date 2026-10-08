#!/usr/bin/env python

import ctypes
from ctypes import wintypes
import random
import time

import pyautogui

INTERVAL = 20  # seconds between moves
GLIDE = 0.5  # seconds the cursor takes to glide to its new spot


def monitors():
    """(left, top, right, bottom) of every active monitor, re-read each call."""
    rects = []

    def add(hmon, hdc, rect, data):
        r = rect.contents
        rects.append((r.left, r.top, r.right, r.bottom))
        return True

    callback = ctypes.WINFUNCTYPE(
        ctypes.c_int, wintypes.HMONITOR, wintypes.HDC,
        ctypes.POINTER(wintypes.RECT), wintypes.LPARAM,
    )(add)
    ctypes.windll.user32.EnumDisplayMonitors(None, None, callback, 0)
    return rects


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]


def idle_seconds():
    """Seconds since the last real mouse or keyboard input (our own moves don't count)."""
    info = LASTINPUTINFO(ctypes.sizeof(LASTINPUTINFO))
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info))
    return ((ctypes.windll.kernel32.GetTickCount() - info.dwTime) & 0xFFFFFFFF) / 1000


print("Monitors:", monitors())
print("Press Ctrl+C to stop.")

try:
    for _ in range(1000):
        time.sleep(INTERVAL)
        if idle_seconds() < INTERVAL:
            print("You're using the computer, skipping this move.")
            continue
        left, top, right, bottom = random.choice(monitors())
        x = random.randrange(left, right)
        y = random.randrange(top, bottom)
        pyautogui.moveTo(x, y, duration=GLIDE)
        print(f"Moved to x={x}, y={y}")
except KeyboardInterrupt:
    pass

print("Script stopped.")
