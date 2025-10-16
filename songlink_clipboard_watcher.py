#!/usr/bin/env python3
"""Watch the macOS clipboard and replace Spotify/Apple Music track URLs with Song.link."""
from __future__ import annotations

import subprocess
import sys
import time
import urllib.parse
from dataclasses import dataclass
from typing import Optional


POLL_INTERVAL_SECONDS = 0.2
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


def run_loop() -> None:
    state = ClipboardState()
    while True:
        try:
            current = read_clipboard()
        except Exception:
            time.sleep(POLL_INTERVAL_SECONDS)
            continue

        if current == state.last_seen_value:
            time.sleep(POLL_INTERVAL_SECONDS)
            continue
        state.last_seen_value = current

        if looks_like_music_link(current):
            # Avoid flip-flopping if we already processed this exact source URL.
            if current == state.last_converted_source:
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            song_link = convert_to_songlink(current)
            try:
                write_clipboard(song_link)
            except Exception:
                # If we fail to write, try again next loop.
                state.last_seen_value = None
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            state.last_seen_value = song_link
            state.last_converted_source = current

        time.sleep(POLL_INTERVAL_SECONDS)


def main() -> None:
    while True:
        try:
            run_loop()
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception:
            # Sleep briefly before retrying to avoid tight crash cycles.
            time.sleep(1.0)


if __name__ == "__main__":
    main()
