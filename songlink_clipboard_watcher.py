#!/usr/bin/env python3
"""Watch the macOS clipboard and replace Spotify/Apple Music track URLs with Song.link."""
from __future__ import annotations

import subprocess
import sys
import time
import urllib.parse
import threading
from dataclasses import dataclass, field
from typing import Optional


POLL_INTERVAL_SECONDS = 0.2
COPY_PROCESS_DELAY_SECONDS = 0.05
COPY_KEYCODE = 8  # macOS virtual keycode for the "c" key on ANSI layouts.
SONG_DOMAINS = (
    "open.spotify.com",
    "music.apple.com",
    "geo.music.apple.com",
    "itunes.apple.com",
)


@dataclass
class ClipboardState:
    last_seen_value: Optional[str] = None
    last_converted_source: Optional[str] = None
    pending_timer: Optional[threading.Timer] = field(default=None, repr=False, compare=False)


def log(message: str) -> None:
    """Emit a lightweight log line to stderr."""
    print(f"[songboard] {message}", file=sys.stderr)


def read_clipboard() -> str:
    """Return the current clipboard contents as text."""
    result = subprocess.run(
        ["pbpaste"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "pbpaste failed")
    return result.stdout.strip()


def write_clipboard(value: str) -> None:
    """Replace the clipboard contents with value."""
    process = subprocess.Popen(
        ["pbcopy"],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    stderr = process.communicate(value)[1]
    if process.returncode != 0:
        raise RuntimeError(stderr.strip() or "pbcopy failed")


def looks_like_music_link(value: str) -> bool:
    """True if the clipboard text is a Spotify or Apple Music link we want to rewrite."""
    if not value.startswith("http"):
        return False
    if value.startswith("https://song.link"):
        return False
    parsed = urllib.parse.urlparse(value)
    return parsed.netloc in SONG_DOMAINS


def convert_to_songlink(value: str) -> str:
    """Return the Song.link URL for a source music URL."""
    encoded = urllib.parse.quote(value, safe="")
    return f"https://song.link/{encoded}"


def process_clipboard(state: ClipboardState) -> None:
    """Read the clipboard and convert supported music links."""
    try:
        current = read_clipboard()
    except Exception:
        return

    if current == state.last_seen_value:
        return
    state.last_seen_value = current

    if looks_like_music_link(current):
        # Avoid flip-flopping if we already processed this exact source URL.
        if current == state.last_converted_source:
            return

        song_link = convert_to_songlink(current)
        try:
            write_clipboard(song_link)
        except Exception:
            # If we fail to write, try again next loop.
            state.last_seen_value = None
            return

        state.last_seen_value = song_link
        state.last_converted_source = current


def schedule_clipboard_processing(state: ClipboardState) -> None:
    """Schedule a clipboard check shortly after a copy event fires."""
    if state.pending_timer and state.pending_timer.is_alive():
        return

    def _run() -> None:
        state.pending_timer = None
        process_clipboard(state)

    timer = threading.Timer(COPY_PROCESS_DELAY_SECONDS, _run)
    timer.daemon = True
    timer.start()
    state.pending_timer = timer


def run_event_listener(state: ClipboardState) -> bool:
    """Listen for Command+C key presses via an event tap. Returns True if running."""
    try:
        import Quartz
    except ImportError:
        log("Quartz framework unavailable; falling back to timed polling.")
        return False

    event_tap = None

    def callback(proxy, type_, event, refcon):
        nonlocal event_tap
        if type_ in (
            Quartz.kCGEventTapDisabledByTimeout,
            Quartz.kCGEventTapDisabledByUserInput,
        ):
            Quartz.CGEventTapEnable(event_tap, True)
            return event
        if type_ != Quartz.kCGEventKeyDown:
            return event

        flags = Quartz.CGEventGetFlags(event)
        if not (flags & Quartz.kCGEventFlagMaskCommand):
            return event

        keycode = Quartz.CGEventGetIntegerValueField(
            event, Quartz.kCGKeyboardEventKeycode
        )
        if keycode == COPY_KEYCODE:
            schedule_clipboard_processing(state)
        return event

    event_mask = 1 << Quartz.kCGEventKeyDown
    event_tap = Quartz.CGEventTapCreate(
        Quartz.kCGSessionEventTap,
        Quartz.kCGHeadInsertEventTap,
        Quartz.kCGEventTapOptionDefault,
        event_mask,
        callback,
        None,
    )

    if event_tap is None:
        log(
            "Unable to access Command+C events. Grant accessibility permissions or "
            "allow the first prompt, then restart Songboard."
        )
        return False

    run_loop_source = Quartz.CFMachPortCreateRunLoopSource(None, event_tap, 0)
    Quartz.CFRunLoopAddSource(
        Quartz.CFRunLoopGetCurrent(),
        run_loop_source,
        Quartz.kCFRunLoopCommonModes,
    )
    Quartz.CGEventTapEnable(event_tap, True)
    log("Listening for Command+C events. (You may be prompted for Accessibility access.)")

    try:
        Quartz.CFRunLoopRun()
    except KeyboardInterrupt:
        sys.exit(0)

    return True


def run_polling(state: ClipboardState) -> None:
    """Fallback loop that polls the clipboard at a fixed interval."""
    while True:
        process_clipboard(state)
        time.sleep(POLL_INTERVAL_SECONDS)


def main() -> None:
    state = ClipboardState()
    if run_event_listener(state):
        return

    while True:
        try:
            run_polling(state)
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception:
            # Sleep briefly before retrying to avoid tight crash cycles.
            time.sleep(1.0)


if __name__ == "__main__":
    main()
