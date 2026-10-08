#!/usr/bin/env python

from time import sleep
import ctypes
from ctypes import wintypes
import msvcrt
import random
import threading

import pyautogui


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


print("Monitors:", monitors())
print("Press 's' in this terminal to stop.")

stop_event = threading.Event()


def listen_for_stop():
    while not stop_event.is_set():
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key in (b"s", b"S"):
                stop_event.set()
                print("\nStopping...")
                break
        sleep(0.1)


threading.Thread(target=listen_for_stop, daemon=True).start()

count = 0
while count < 1000 and not stop_event.is_set():
    left, top, right, bottom = random.choice(monitors())
    x = random.randrange(left, right)
    y = random.randrange(top, bottom)
    pyautogui.moveTo(x, y)
    print(f"Moved to x={x}, y={y}")
    if stop_event.wait(20):
        break
    count += 1

print("Script stopped.")
