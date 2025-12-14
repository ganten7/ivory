# Installation Notes for Windows and macOS

## Windows Installation

If you encounter a "JavaScript error" or "Node.js error" when running `ivory.exe`:

1. **This is a known issue** - The executable may have been incorrectly packaged. Please download the latest build from the releases page.

2. **Alternative: Run from source**
   ```bash
   pip install -r requirements_pyqt5.txt
   python ivory.py
   ```

3. **Check Windows Defender** - Sometimes antivirus software blocks PyInstaller executables. Add an exception if needed.

## macOS Installation

### Installation (ZIP - Recommended)

1. **Download** `Ivory.zip` from the releases page
2. **Double-click** `Ivory.zip` to extract it (or right-click → "Open With" → "Archive Utility")
3. **Drag** `Ivory.app` to your `/Applications` folder
4. **First launch**: Right-click `Ivory.app` → "Open" (to bypass Gatekeeper)
5. When prompted, click **"Open"** again

### Installation (DMG - Alternative)

1. **Download** `Ivory.dmg` from the releases page
2. **Double-click** `Ivory.dmg` to mount it
3. **Drag** `Ivory.app` to the Applications folder shortcut in the DMG window
4. **Eject** the DMG (drag to Trash or right-click → Eject)
5. **First launch**: Right-click `Ivory.app` → "Open" (to bypass Gatekeeper)

### Gatekeeper Warning

macOS may block the application because it's not signed. If you get a "damaged" or "can't be opened" error:

**Option 1 (Easiest):**
- Right-click `Ivory.app` → "Open"
- Click "Open" when prompted

**Option 2 (Terminal):**
```bash
# Remove quarantine attribute
xattr -cr ~/Downloads/Ivory.app

# Or if already in Applications
sudo xattr -rd com.apple.quarantine /Applications/Ivory.app
```

### Run from Source (Recommended for Testing)

```bash
pip3 install -r requirements_pyqt5.txt
python3 ivory.py
```

## Troubleshooting

### Windows: "The application failed to initialize properly"
- Install [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
- Ensure Python 3.6+ is installed (though the .exe should be standalone)

### macOS: "Ivory.app is damaged and can't be opened"
- This is a Gatekeeper issue. Use the methods above to bypass it.
- Or run: `sudo xattr -rd com.apple.quarantine /Applications/Ivory.app`

### Both Platforms: Missing MIDI Input
- Ensure your MIDI device is connected and recognized by the OS
- Check system MIDI settings
- Try selecting a different MIDI input from the application menu
