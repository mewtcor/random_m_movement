#!/usr/bin/env python

import ctypes
from ctypes import wintypes
import random
import signal
import time
import tkinter as tk

import pyautogui

INTERVAL = 20  # seconds idle before moves start, and between moves
GLIDE = 0.5  # seconds the cursor takes to glide to its new spot
MAX_MOVES = 1000

user32 = ctypes.windll.user32


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
    user32.EnumDisplayMonitors(None, None, callback, 0)
    return rects


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]


def idle_seconds():
    """Seconds since the last mouse or keyboard input, including our own nudge."""
    info = LASTINPUTINFO(ctypes.sizeof(LASTINPUTINFO))
    user32.GetLastInputInfo(ctypes.byref(info))
    return ((ctypes.windll.kernel32.GetTickCount() - info.dwTime) & 0xFFFFFFFF) / 1000


def move_mouse():
    left, top, right, bottom = random.choice(monitors())
    x = random.randrange(left, right)
    y = random.randrange(top, bottom)
    pyautogui.moveTo(x, y, duration=GLIDE)
    # The glide alone doesn't count as activity, so Teams would still go Away.
    # A zero-distance mouse event does count, without moving the cursor.
    user32.mouse_event(0x0001, 0, 0, 0, 0)  # MOUSEEVENTF_MOVE
    print(f"Moved to x={x}, y={y}")


def format_duration(seconds):
    h, rest = divmod(int(seconds), 3600)
    m, s = divmod(rest, 60)
    return f"{h}h {m:02d}m {s:02d}s" if h else f"{m}m {s:02d}s"


# Two-frame pixel-art gallop. b = fur, d = ears/tail, k = eye/nose.
DOG_FRAMES = [
    """
    .............dd...
    ............dbbbb.
    ............bbkbb.
    ...........bbbbbbk
    d..........bbbb...
    .d.bbbbbbbbbbbb...
    ..bbbbbbbbbbbbb...
    ...bbbbbbbbbbb....
    ..bb........bb....
    .bb..........bb...
    bb............bb..
    """,
    """
    .............dd...
    d...........dbbbb.
    .d..........bbkbb.
    ..d........bbbbbbk
    ...bbbbbbbbbbbb...
    ..bbbbbbbbbbbbb...
    ...bbbbbbbbbbb....
    ....bb....bb......
    .....bb..bb.......
    ......b..b........
    ..................
    """,
]
DOG_COLORS = {"b": "#d29a5c", "d": "#7a4a26", "k": "#111111"}


class Popup:
    """Small dark card in the bottom-right corner that fades in while you're away."""

    BG, TEXT, DIM = "#1f1f23", "#f2f2f5", "#9a9aa5"
    OPACITY = 0.98

    def __init__(self, root):
        self.root = root
        self.scale = root.winfo_fpixels("1i") / 96  # pixels scale with display DPI
        px = lambda n: round(n * self.scale)

        root.overrideredirect(True)
        root.attributes("-topmost", True, "-alpha", 0.0)
        root.configure(bg=self.BG)
        card = tk.Frame(root, bg=self.BG, padx=px(18), pady=px(12))
        card.pack()
        self._build_dog(card, px(3)).grid(row=0, column=0, rowspan=2, padx=(0, px(14)))
        tk.Label(card, text="Mouse mover is running", fg=self.TEXT, bg=self.BG,
                 font=("Segoe UI Semibold", 10)).grid(row=0, column=1, sticky="w")
        self.elapsed = tk.Label(card, fg=self.DIM, bg=self.BG, font=("Segoe UI", 9))
        self.elapsed.grid(row=1, column=1, sticky="w")

        root.withdraw()
        root.update_idletasks()
        hwnd = user32.GetParent(root.winfo_id())
        # No taskbar button, and never takes focus from what you were doing.
        GWL_EXSTYLE, WS_EX_TOOLWINDOW, WS_EX_NOACTIVATE = -20, 0x80, 0x08000000
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE,
                              user32.GetWindowLongW(hwnd, GWL_EXSTYLE) | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE)
        # Rounded corners on Windows 11 (ignored on Windows 10).
        round_corners = ctypes.c_int(2)  # DWMWCP_ROUND
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 33, ctypes.byref(round_corners), 4)

        self.target = 0.0
        self.fading = False
        self._run_dog(0)

    def _build_dog(self, parent, p):
        """Canvas with one hidden/shown item group per frame, plus ground dashes."""
        frames = [[row.strip() for row in f.strip().splitlines()] for f in DOG_FRAMES]
        cols, rows = len(frames[0][0]), len(frames[0])
        self.dog_width = cols * p
        self.dog = tk.Canvas(parent, width=self.dog_width, height=(rows + 1) * p,
                             bg=self.BG, highlightthickness=0)
        for i, frame in enumerate(frames):
            for r, row in enumerate(frame):
                for c, ch in enumerate(row):
                    if ch != ".":
                        self.dog.create_rectangle(c * p, r * p, (c + 1) * p, (r + 1) * p,
                                                  fill=DOG_COLORS[ch], width=0, tags=f"frame{i}")
        self.dashes = [self.dog.create_rectangle(x, rows * p + p // 2, x + 2 * p, rows * p + p,
                                                 fill=self.DIM, width=0)
                       for x in range(0, self.dog_width, 6 * p)]
        self.step = p
        return self.dog

    def _run_dog(self, frame):
        self.dog.itemconfigure("frame0", state="normal" if frame == 0 else "hidden")
        self.dog.itemconfigure("frame1", state="normal" if frame == 1 else "hidden")
        for dash in self.dashes:  # ground scrolls left so the dog looks like it's moving
            self.dog.move(dash, -self.step, 0)
            if self.dog.coords(dash)[2] <= 0:
                self.dog.move(dash, self.dog_width, 0)
        self.root.after(130, self._run_dog, 1 - frame)

    def show(self, visible, elapsed):
        self.elapsed.config(text=f"Running for {format_duration(elapsed)}")
        self.target = self.OPACITY if visible else 0.0
        if visible and self.root.state() == "withdrawn":
            self._place()
            self.root.deiconify()
        if not self.fading:
            self.fading = True
            self._fade()

    def _place(self):
        """Bottom-right of the main screen's work area, just above the taskbar."""
        area = wintypes.RECT()
        user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(area), 0)  # SPI_GETWORKAREA
        self.root.update_idletasks()
        margin = round(16 * self.scale)
        x = area.right - self.root.winfo_reqwidth() - margin
        y = area.bottom - self.root.winfo_reqheight() - margin
        self.root.geometry(f"+{x}+{y}")

    def _fade(self):
        alpha = float(self.root.attributes("-alpha"))
        if abs(alpha - self.target) <= 0.08:
            self.root.attributes("-alpha", self.target)
            self.fading = False
            if self.target == 0.0:
                self.root.withdraw()
            return
        self.root.attributes("-alpha", alpha + (0.08 if self.target > alpha else -0.08))
        self.root.after(16, self._fade)


def main():
    focused = user32.GetForegroundWindow()
    root = tk.Tk()
    popup = Popup(root)
    root.update()
    user32.SetForegroundWindow(focused)  # Tk grabs focus on startup; hand it back
    # Ctrl+C: close the window on the next tick instead of a traceback.
    signal.signal(signal.SIGINT, lambda *_: root.after(0, root.destroy))

    start = time.monotonic()
    you_active_at = start  # starting the script counts as you being active
    last_nudge = None
    moves = 0

    def tick():
        nonlocal you_active_at, last_nudge, moves
        now = time.monotonic()
        last_input = now - idle_seconds()
        # Our own nudge is input too; anything clearly after it was you.
        if last_nudge is None or last_input > last_nudge + 0.5:
            you_active_at = max(you_active_at, last_input)
        away = now - you_active_at >= INTERVAL

        popup.show(away, now - start)
        if away and (last_nudge is None or now - last_nudge >= INTERVAL):
            move_mouse()
            last_nudge = time.monotonic()
            moves += 1
            if moves >= MAX_MOVES:
                root.destroy()
                return
        root.after(500, tick)

    print("Monitors:", monitors())
    print("Press Ctrl+C to stop.")
    tick()
    root.mainloop()
    print("Script stopped.")


if __name__ == "__main__":
    main()
