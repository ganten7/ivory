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

### Gatekeeper Warning

macOS may block the application because it's not signed. To open it:

1. **Right-click** (or Control-click) the `Ivory.dmg` file
2. Select **"Open"** from the context menu
3. When prompted, click **"Open"** again

### Alternative: Remove Quarantine Attribute

If the above doesn't work, open Terminal and run:

```bash
# Navigate to where you downloaded Ivory.dmg
cd ~/Downloads

# Mount the DMG
hdiutil attach Ivory.dmg

# Remove quarantine attribute
xattr -cr /Volumes/Ivory/Ivory.app

# Copy to Applications
cp -R /Volumes/Ivory/Ivory.app /Applications/

# Unmount
hdiutil detach /Volumes/Ivory
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
