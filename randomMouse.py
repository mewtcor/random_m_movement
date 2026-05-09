#!/usr/bin/env python

import random
import pyautogui
from time import sleep

pyautogui.FAILSAFE = True  # Move mouse to top-left corner to abort

screen_w, screen_h = pyautogui.size()
print(f"Screen size: {screen_w}x{screen_h}")

ITERATIONS = 1000
DELAY = 1.0       # seconds between moves (was 20 — adjust as needed)
DURATION = 0.3    # smooth movement duration in seconds

for count in range(ITERATIONS):
    x = random.randint(0, screen_w - 1)
    y = random.randint(0, screen_h - 1)
    pyautogui.moveTo(x, y, duration=DURATION)
    print(f"[{count+1}/{ITERATIONS}] Moving to ({x}, {y})")
    sleep(DELAY)