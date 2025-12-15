# Ivory v1.0.1 Release Notes

## Screenshots

### Cm11 - Minor 11th Chord Detection
![Cm11 Chord](screenshots/Cm11.png)
*Ivory detecting a Cm11 chord - demonstrating extended chord recognition*

### D7(b9,#11) - Complex Altered Dominant
![D7(b9,#11) Chord](screenshots/D7%20(b9,%23%2311).png)
*Advanced altered dominant detection: D7 with both b9 and #11 alterations*

### Ebm11 - Extended Minor Chord
![Ebm11 Chord](screenshots/Ebm11.png)
*Ebm11 chord detection showcasing Ivory's comprehensive minor chord patterns*

---

## What's New in v1.0.1

### User-Friendly Enhancements

#### 🎹 Toggleable Piano Keys (Windowed Mode)
- New context menu option: "Enable/Disable Key Toggle"
- Located as option #10, directly under "Use Sharps"
- Click any piano key to toggle it on/off for chord testing
- Works seamlessly with MIDI input
- Only available in windowed mode (disabled in borderless to prevent interference with window dragging)
- Setting persists across sessions

#### 🎛️ Improved MIDI Device Detection
- Friendly notification when no MIDI devices are detected on startup
- Dialog message: "No midi devices found. You can still use the piano to find chords by enabling Key Toggle in the right-click menu."
- "Don't show again" checkbox option - preference is saved
- MIDI remains fully integrated and required (mido library)
- App continues to function with clickable keys when no MIDI device is present

### Advanced Chord Detection Features

#### 🎵 100+ Chord Patterns Supported
- Major, minor, diminished, augmented triads
- All 7th chord types (maj7, m7, 7, m7b5, dim7, etc.)
- Extended chords (9ths, 11ths, 13ths)
- Altered dominants: 7(b9), 7(#9), 7(#11), 7(b13), and combinations
- Special voicings: 6, 6/9, add9, sus2, sus4
- Shell voicings and slash chord notation

#### 🎼 Smart Chord Recognition
- **Enharmonic conversion**: Am7/C correctly detected as C6
- **Bass note handling**: G7(b9,b13) with bass octaves recognized properly
- **Extended patterns**: C13(b9), C13(#11) support
- **Bad voicing rejection**: Detects and rejects dissonant combinations (e.g., major + natural 11)
- **Root doubling logic**: Intelligent slash chord vs. regular chord determination
- **Transposability**: All patterns work correctly in all 12 keys

### Interface Features

- **Dark/Light mode** with customizable colors
- **Borderless window mode** with click-to-drag
- **Detachable chord window** with adjustable height
- **88-key visualization** with real-time highlighting
- **Sustain pedal support** (MIDI CC64)
- **Prefer flats/sharps** option for chord naming

## Installation

### Download

Download the Debian package:
- **ivory_1.0.1_all.deb** (for Debian/Ubuntu-based distributions)

### Install

```bash
# Remove old version if installed
sudo dpkg -r ivory

# Install v1.0.1
sudo dpkg -i ivory_1.0.1_all.deb

# If dependency issues occur
sudo apt-get install -f
```

### Launch

Launch Ivory via:
- **Application Menu**: Look for "Ivory" in Audio/MIDI category
- **Terminal**: `python3 /usr/bin/ivory`
- **Command**: `ivory` (if /usr/bin is in PATH)

## Requirements

### System Requirements
- **OS**: Linux (Debian/Ubuntu or compatible distributions)
- **Python**: 3.6 or higher

### Dependencies
All dependencies are automatically installed:
- `python3`
- `python3-pyqt5` (GUI framework)
- `python3-mido` (MIDI handling - required)
- `python3-rtmidi` (MIDI backend - required)

## Usage

### With MIDI Keyboard
1. Connect your MIDI keyboard
2. Launch Ivory
3. Play notes - they'll be highlighted on the virtual keyboard
4. Chord name appears above the keyboard
5. Use sustain pedal for sustained notes

### Without MIDI Keyboard
1. Launch Ivory
2. Right-click anywhere on the window
3. Select "Enable Key Toggle" from the context menu
4. Click piano keys to toggle them on/off
5. Chord name updates as you click

### Context Menu Options
1. Toggle Dark Mode
2. Toggle Chord Detection
3. Use Sharps (instead of flats)
4. Select MIDI Input
5. Customize Colors
6. Toggle Borderless Mode
7. Toggle Chord Window (detach/attach)
8. Reset to Defaults
9. About
10. **Enable/Disable Key Toggle** (NEW in v1.0.1, windowed mode only)

## Testing

All features have been thoroughly tested:
- ✅ 12/12 user requirements passing
- ✅ 48/48 transposability tests passing (all patterns work in all 12 keys)
- ✅ 11/11 extended requirements passing
- ✅ No existing functionality broken

Test suites available in the repository:
- `test_user_requirements.py`
- `test_12_keys.py`
- `test_new_requirements.py`

## Known Issues & Limitations

- Click-to-toggle only available in windowed mode (by design - prevents conflict with borderless window dragging)
- Debian/Ubuntu Linux only (cross-platform support planned)
- Requires MIDI libraries even if no MIDI device is connected

## Technical Details

### File Structure
```
/usr/bin/ivory              # Main application
/usr/bin/chord_detector_v2.py  # Chord detection engine
/usr/share/applications/ivory.desktop  # Desktop entry
/usr/share/icons/hicolor/*/apps/ivory.png  # Application icons
```

### Settings Location
User settings are saved to:
```
~/.config/ivory/settings.json
```

Settings include:
- Dark mode preference
- Color customization
- Window size and mode
- MIDI warning preference
- Key toggle enabled state
- And more...

## Support & Feedback

For issues, questions, or feature requests, please use the GitHub issue tracker.

## License

MIT License

---

**Ivory v1.0.1** - Advanced MIDI keyboard monitor with professional chord detection.
