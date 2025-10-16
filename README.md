# Songboard · Song.link Clipboard Watcher for macOS

![Platform](https://img.shields.io/badge/platform-macOS-black?style=flat-square) ![Python](https://img.shields.io/badge/python-3%2B-blue?style=flat-square) ![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)

Turn every Spotify or Apple Music URL you copy into a universal [Song.link](https://song.link) share in a blink. Songboard watches your clipboard so you can drop perfect, platform-agnostic links anywhere—texts, tweets, group chats, you name it.

> 🎉 Built for creators, curators, and anyone tired of “do you have this on *my* streaming service?”

![Songboard social preview](docs/social-preview.png)

---

## ✨ What you get
- Instant Song.link conversion for Spotify, Apple Music, iTunes, and geo.apple domains
- Hands-free background agent that launches at login and stays invisible
- Safe retries and loop protection so your clipboard never flips back and forth
- Tiny, dependency-free Python script (fits anywhere)

---

## 🚀 Quick start

> Requires macOS with Python 3 (preinstalled on modern macOS versions).

```bash
# 1. Drop the watcher script on your machine
mkdir -p ~/Scripts
curl -o ~/Scripts/songlink_clipboard_watcher.py https://raw.githubusercontent.com/willsigmon/songboard/main/songlink_clipboard_watcher.py
chmod +x ~/Scripts/songlink_clipboard_watcher.py

# 2. Install a LaunchAgent so it auto-starts on login
mkdir -p ~/Library/LaunchAgents
cat > ~/Library/LaunchAgents/com.songlink.clipboard.plist <<'EOF'
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

# 3. Fire it up
launchctl load ~/Library/LaunchAgents/com.songlink.clipboard.plist
```

Copy any Spotify or Apple Music track URL. Your clipboard immediately holds `https://song.link/...` ready to share everywhere.

---

## 🧠 Pro tips
- Pause the agent with `launchctl unload ~/Library/LaunchAgents/com.songlink.clipboard.plist` and reload when you’re ready again.
- Want to watch other services? Update `SONG_DOMAINS` in `songlink_clipboard_watcher.py`.
- For debugging, tail `/tmp/songlink.err` while you test new changes.

---

## 💡 Behind the scenes
- Polls the clipboard every 200 ms using `pbpaste`/`pbcopy`
- Guards against double-processing so you don’t lose the original link
- Retries gracefully if macOS rejects a clipboard write
- Lives in [`songlink_clipboard_watcher.py`](songlink_clipboard_watcher.py) (≈120 lines)

Peek at the full walkthrough in [`songlink-setup.md`](songlink-setup.md) for extra installation context and uninstall instructions.

---

## 📸 Share-ready assets
- Upload `docs/social-preview.png` as the GitHub social preview (Settings → General → Social preview) and reuse it anywhere you share Songboard.
- Suggested caption: *“Songboard auto-turns every music link I copy into a universal Song.link URL. One click, every streaming service. Grab it here → https://github.com/willsigmon/songboard.”*
- Want motion? Drop a 5–10 second screen recording into `docs/` and link it from the README or your post.

---

## 🗺️ Roadmap ideas
- Optional menu bar indicator
- Global keyboard shortcut to toggle the watcher
- Support for YouTube Music, Tidal, and Amazon Music

Open an issue or submit a PR if you want to help push these forward.

---

## 📝 License

Released under the [MIT License](LICENSE). Have fun, share broadly, and let us know where you drop your first universal link!
