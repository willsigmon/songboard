# Song.link Clipboard Watcher for macOS

Auto-converts Spotify/Apple Music links to universal Song.link URLs on your clipboard.

## Installation

### 1. Save the script
```bash
mkdir -p ~/Scripts
curl -o ~/Scripts/songlink_clipboard_watcher.py https://raw.githubusercontent.com/willsigmon/songboard/main/songlink_clipboard_watcher.py
chmod +x ~/Scripts/songlink_clipboard_watcher.py
```

Or copy `songlink_clipboard_watcher.py` to `~/Scripts/`.

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
        <string>/Users/YOUR_USERNAME/Scripts/songlink_clipboard_watcher.py</string>
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

Replace `YOUR_USERNAME` with your actual username.

### 3. Load the LaunchAgent
```bash
launchctl load ~/Library/LaunchAgents/com.songlink.clipboard.plist
```

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
- Polls clipboard every 0.2 seconds
- Detects Spotify, Apple Music, or iTunes URLs
- Converts them to universal `song.link/...` format
- Works transparently—just copy a music link and it auto-converts

Enjoy universal music links! 🎵
