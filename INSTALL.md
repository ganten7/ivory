# Ivory Installation Instructions

## Remove Old Version

First, remove any old Ivory package:

```bash
sudo dpkg -r ivory
```

## Install Ivory v1.0.1

Install the new package:

```bash
sudo dpkg -i ivory_1.0.1_all.deb
```

If there are dependency issues, run:

```bash
sudo apt-get install -f
```

## Launch Ivory

You can launch Ivory from:
- Application menu: Look for "Ivory" in the Audio/MIDI category
- Terminal: `python3 /usr/bin/ivory`
- Command: `ivory` (if /usr/bin is in your PATH)

## Features

### MIDI Input
- Ivory will automatically detect and connect to your MIDI keyboard
- Sustain pedal (CC64) is fully supported
- All 88 keys are displayed

### Click-to-Toggle (Windowed Mode)
- Click on any piano key to toggle it on/off
- This works simultaneously with MIDI input
- Perfect for testing chords without a MIDI keyboard

### Chord Detection
- Improved algorithm with 100+ chord patterns
- Better detection of altered dominants (b9, #9, #11, b13)
- Enhanced slash chord recognition
- Bad voicing rejection (e.g., major + natural 11)
- All 12 keys fully supported

## New in Version 1.0.1

1. **Toggleable Piano Keys**:
   - Click piano keys to toggle them on/off (windowed mode)
   - Enable/Disable via context menu (option #10)
   - Perfect for testing chords without MIDI keyboard

2. **MIDI Device Detection**:
   - Friendly notification when no MIDI devices detected
   - "Don't show again" option for the warning
   - App works with clickable keys when no MIDI present

3. **Enhanced Chord Detection**:
   - 100+ chord patterns supported
   - Am7/C correctly detected as C6
   - G7(b9,b13), C13(b9), C13(#11) patterns
   - Bad voicing detection and rejection
   - Root doubling logic for slash chords

4. **100% Test Coverage**: All requirements tested across all 12 keys

## Testing

Test files are available in `/home/ganten/Ivory-2.0/`:
- `test_user_requirements.py` - Full test suite (12/12 passing)
- `test_12_keys.py` - Transposability test (48/48 passing)
