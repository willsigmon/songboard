# Song.link Clipboard Watcher for macOS

Auto-converts popular music links (Spotify, Apple Music, YouTube, Tidal, etc.) to universal Song.link URLs on your clipboard.

## Installation

### 1. Save the script
```bash
mkdir -p ~/Scripts
curl -o ~/Scripts/songlink_clipboard_watcher.py https://raw.githubusercontent.com/willsigmon/songboard/main/songlink_clipboard_watcher.py
chmod +x ~/Scripts/songlink_clipboard_watcher.py
```

Or manually save this as `~/Scripts/songlink_clipboard_watcher.py`:

```python
#!/usr/bin/env python3
"""Watch the macOS clipboard and replace music streaming URLs with Song.link."""
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
SONG_HOSTS = {
    "open.spotify.com",
    "play.spotify.com",
    "music.apple.com",
    "geo.music.apple.com",
    "itunes.apple.com",
    "music.youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "youtu.be",
    "listen.tidal.com",
    "tidal.com",
    "www.deezer.com",
    "deezer.com",
    "m.deezer.com",
    "soundcloud.com",
    "m.soundcloud.com",
    "www.soundcloud.com",
    "music.amazon.com",
    "music.amazon.co.uk",
    "music.amazon.ca",
}
SONG_HOST_PREFIXES = (
    "music.amazon.",
)
SONG_HOST_SUFFIXES = (
    ".bandcamp.com",
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
    """True if the clipboard text is a music link we want to rewrite."""
    if not value.startswith("http"):
        return False
    if value.startswith("https://song.link"):
        return False
    parsed = urllib.parse.urlparse(value)
    host = parsed.netloc.split(":")[0].lower()
    if host in SONG_HOSTS:
        return True
    for prefix in SONG_HOST_PREFIXES:
        if host.startswith(prefix):
            return True
    for suffix in SONG_HOST_SUFFIXES:
        if host.endswith(suffix):
            return True
    return False


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
```

### 2. Create a LaunchAgent (auto-start on login)
```bash
mkdir -p ~/Library/LaunchAgents
cat > ~/Library/LaunchAgents/com.songlink.clipboard.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.songlink.clipboard</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/$USER/Scripts/songlink_clipboard_watcher.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardErrorPath</key>
    <string>/tmp/songlink.err</string>
    <key>StandardOutPath</key>
    <string>/tmp/songlink.out</string>
</dict>
</plist>
EOF
```

This plist uses `$USER` so it is portable across accounts.

### 3. Load the LaunchAgent
```bash
launchctl load ~/Library/LaunchAgents/com.songlink.clipboard.plist
```

> On first launch, macOS may ask you to allow `/usr/bin/python3` under **System Settings → Privacy & Security → Accessibility**. Approve it to unlock instant Command+C detection. If you decline, Songboard falls back to a gentle 0.2 s polling loop.

## Verify it's running
```bash
ps aux | grep songlink_clipboard_watcher
```

## Stop/Start/Uninstall

**Stop running:**
```bash
launchctl unload ~/Library/LaunchAgents/com.songlink.clipboard.plist
```

**Start again:**
```bash
launchctl load ~/Library/LaunchAgents/com.songlink.clipboard.plist
```

**Uninstall completely:**
```bash
launchctl unload ~/Library/LaunchAgents/com.songlink.clipboard.plist
rm ~/Library/LaunchAgents/com.songlink.clipboard.plist
rm ~/Scripts/songlink_clipboard_watcher.py
```

## How it works
- Listens for Command+C events via the macOS Accessibility API (with a 0.2 s polling fallback)
- Detects major streaming links (Spotify, Apple Music, YouTube, Tidal, Amazon Music, Deezer, SoundCloud, Bandcamp, and more)
- Converts them to universal `song.link/...` format
- Works transparently—just copy a music link and it auto-converts

Enjoy universal music links! 🎵
