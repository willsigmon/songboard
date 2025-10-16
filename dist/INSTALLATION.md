# Songboard Installation

Thanks for grabbing Songboard! Follow these steps on macOS:

## 1. Copy Songboard into place
1. Open Terminal.
2. Run:
   ```bash
   mkdir -p ~/Scripts
   cp songlink_clipboard_watcher.py ~/Scripts/
   chmod +x ~/Scripts/songlink_clipboard_watcher.py
   ```

## 2. Install the LaunchAgent (auto-start on login)
1. Still in Terminal, create the LaunchAgent:
   ```bash
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
   ```

## 3. Launch Songboard
```bash
launchctl load ~/Library/LaunchAgents/com.songlink.clipboard.plist
```

> On first launch, macOS may prompt you to allow `/usr/bin/python3` (Songboard) under **System Settings → Privacy & Security → Accessibility**. Approve it to enable instant Command+C detection. If you skip the prompt, Songboard falls back to a gentle polling mode.

Songboard now watches your clipboard. Copy any supported music link (Spotify, Apple Music, YouTube, Tidal, Amazon Music, Deezer, SoundCloud, Bandcamp, etc.) and it instantly becomes a universal `https://song.link/...` URL.

## Troubleshooting
- Pause Songboard: `launchctl unload ~/Library/LaunchAgents/com.songlink.clipboard.plist`
- Resume Songboard: `launchctl load ~/Library/LaunchAgents/com.songlink.clipboard.plist`
- Logs: check `/tmp/songlink.err` for errors
- No conversions happening? Add `/usr/bin/python3` to **Accessibility** permissions and reload the LaunchAgent.

Enjoy universal music links!
