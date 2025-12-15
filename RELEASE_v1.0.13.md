# Ivory v1.0.13 Release Notes

## What's New

### Bug Fixes
- **Fixed Windows icon**: Window title bar now shows proper Ivory icon instead of placeholder
- **Fixed software center metadata**: Icon and screenshots now display correctly in GNOME Software
- **Keytoggle defaults to OFF**: Key toggle is now disabled by default on first launch

### Improvements
- **Enhanced metadata**: Proper AppStream metadata with screenshots and descriptions
- **Repository support**: Full Debian repository structure for easy installation
- **Better icon support**: Icons available in all standard sizes (16x16 to 256x256)

### Technical Changes
- Updated AppStream ID to reverse DNS format (`com.ivory.app`)
- Fixed screenshot URLs to use GitHub raw content
- Added Windows ICO icon file with multiple sizes
- Improved package metadata structure

## Installation

### Linux (Debian/Ubuntu)
```bash
# Add repository
echo "deb [trusted=yes] file:///path/to/Ivory/repo stable main" | sudo tee /etc/apt/sources.list.d/ivory.list
sudo apt update
sudo apt install ivory
```

Or install directly:
```bash
sudo dpkg -i ivory_1.0.13_all.deb
sudo apt-get install -f
```

### Windows
Download `Ivory-Windows-v1.0.13.exe` and run the installer.

### macOS
Download `Ivory-macOS-v1.0.13.zip`, extract, and run `Ivory.app`.

## Full Changelog

### Version 1.0.13
- Fixed altered dominant filtering with M3+m3 conflicts
- Improved add9 slash chord simplification logic
- All 11 test cases passing (100%)
- Full transposability in all 12 keys
- Altered dominants correctly filtered when detected from non-bass roots
- Add9 notation preserved only when 9th is doubled in slash chords
- Keytoggle now defaults to OFF
- Windows icon fixed
- Software center metadata fixed

## Known Issues
None at this time.

## Credits
Ivory Development Team


