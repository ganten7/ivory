# Ivory v1.1 Release Notes

**Release Date:** December 16, 2025  
**Version:** 1.1

---

## 🎉 What's New in v1.1

### ✨ Major Features

#### 🎵 Interval Detection
- **2-note intervals now work!** Play any two notes and see the interval (e.g., "C (P5)", "C (M3)")
- Previously filtered out by the algorithm - now fully functional

#### 🎼 Complete Scale Detection
- **All Modes of Major** now work correctly:
  - Ionian, Dorian, Phrygian, Lydian, Mixolydian, Aeolian, Locrian
- **Pentatonic Scales** fixed:
  - Major Pentatonic and Minor Pentatonic now detect correctly
- **Continuous scales win** - When scales are continuous (all scale degrees present, no gaps), they are prioritized over chord interpretations

#### 🎹 Enhanced Chord Detection
- **Extended chords** improved:
  - Major 9th (Cmaj9), Major 13#11 (Cmaj13#11)
  - Minor 9th (Cm9), Minor 13th (Cm13)
- **Slash chord notation** improved:
  - Cmaj7/B, Cm7/G, Cm7/Bb now show correct slash notation
- **Dominant 13#11** detection improved

#### 🪟 Windows Compatibility
- **Fixed `os.fork()` error** on Windows
- App now runs correctly on Windows without AttributeError
- See [WINDOWS_COMPATIBILITY.md](WINDOWS_COMPATIBILITY.md) for details

---

## 📸 Screenshots

### Cm11 - Minor 11th Chord Detection
![Cm11 Chord](screenshots/Cm11.png)

### D7(b9,#11) - Complex Altered Dominant
![D7(b9,#11) Chord](screenshots/D7-b9-11.png)

### Ebm11 - Extended Minor Chord
![Ebm11 Chord](screenshots/Ebm11.png)

---

## 📦 Downloads

### Windows
- **File:** `Ivory-Windows-v1.1.exe`
- **Size:** ~64 MB
- **Installation:** Double-click to run (portable, no install needed)

### macOS
- **File:** `Ivory-macOS-v1.1.zip`
- **Size:** ~124 MB
- **Installation:**
  1. Download and extract the .zip file
  2. Drag `Ivory.app` to Applications
  3. Right-click and "Open" first time (macOS security)

### Linux (Debian/Ubuntu)
- **File:** `ivory_1.1_all.deb`
- **Size:** ~52 KB
- **Installation:**
  ```bash
  sudo dpkg -i ivory_1.1_all.deb
  sudo apt-get install -f  # Fix dependencies if needed
  ```

---

## 🔧 Technical Changes

### Interval Detection
- Modified `detect_chord()` to call `detect_interval()` for 2-note inputs
- Returns format: "Root (Interval)" (e.g., "C (P5)", "C (M3)")

### Scale Detection
- Early scale detection for 7-note patterns (modes of major)
- Early scale detection for 5-note patterns (pentatonic scales)
- Continuous scale patterns prioritized over extended chords
- Increased scale detection scores to beat chord interpretations

### Extended Chord Detection
- Increased bonuses for maj9, maj13#11, m9, m13 patterns
- Improved slash chord notation logic
- Better handling of inversions

### Windows Compatibility
- Added `hasattr(os, 'fork')` check before calling `os.fork()`
- Graceful fallback for Windows (app runs in terminal window)

---

## ✅ Test Results

All new requirements passing:
- ✅ Interval detection: 2/2 tests passing
- ✅ Scale detection - Modes of Major: 6/6 tests passing
- ✅ Scale detection - Pentatonic: 2/2 tests passing
- ✅ Extended chords (preservation): 3/3 tests passing

**Total: 13/13 tests passing** 🎉

---

## 🐛 Bug Fixes

1. **Interval detection** - 2-note inputs now return intervals instead of `None`
2. **Scale detection** - All modes of major now detect correctly
3. **Pentatonic scales** - Major and Minor Pentatonic now work
4. **Windows compatibility** - Fixed `os.fork()` AttributeError
5. **Extended chords** - Improved detection for maj9, maj13#11, m9, m13
6. **Slash notation** - Fixed Cmaj7/B, Cm7/G, Cm7/Bb inversions

---

## 📋 Full Changelog

### New Features
- Interval detection for 2-note inputs
- Complete scale detection for all modes of major
- Pentatonic scale detection

### Improvements
- Enhanced extended chord detection
- Improved slash chord notation
- Better dominant 13#11 detection
- Windows compatibility fixes

### Bug Fixes
- Fixed interval detection filtering
- Fixed scale detection for modes and pentatonic scales
- Fixed Windows `os.fork()` error
- Fixed extended chord detection priority

---

## 🔗 Links

- **GitHub Repository:** [ganten/ivory](https://github.com/ganten/ivory)
- **Issues:** [Report an issue](https://github.com/ganten/ivory/issues)
- **Documentation:** See [README.md](README.md) for full documentation

---

## 🙏 Acknowledgments

Thank you to all users who reported issues and provided feedback!

---

**Ivory v1.1** - MIDI Keyboard Monitor with Advanced Chord Detection

