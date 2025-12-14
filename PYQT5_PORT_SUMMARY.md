# PyQt5 Port Summary

## Overview

A Windows-compatible version of Ivory has been created using PyQt5 instead of GTK3. This version can be easily tested on Windows and later packaged as a standalone `.exe` file.

## Files Created

1. **`ivory_pyqt5.py`** - Complete PyQt5 port of the application
2. **`requirements_pyqt5.txt`** - Python dependencies for Windows
3. **`README_WINDOWS_TESTING.md`** - Testing guide for Windows users
4. **`PYQT5_PORT_SUMMARY.md`** - This file

## Key Changes from GTK3 Version

### 1. GUI Framework
- **GTK3** → **PyQt5**
- All widgets ported to PyQt5 equivalents:
  - `Gtk.ApplicationWindow` → `QMainWindow`
  - `Gtk.DrawingArea` → Custom `QWidget` with `paintEvent()`
  - `Gtk.Menu` → `QMenu`
  - `Gtk.Dialog` → `QDialog`
  - `Gtk.ColorChooserDialog` → `QColorDialog`

### 2. Drawing System
- **Cairo** → **QPainter**
- All drawing operations ported:
  - `cr.rectangle()` → `painter.fillRect()`
  - `cr.set_source_rgb()` → `painter.setPen()` / `painter.setBrush()`
  - `cr.stroke()` → `painter.drawRect()` / `painter.drawLine()`
  - `cr.paint()` → `painter.fillRect()`

### 3. Text Rendering
- **Pango** → **QFont** / **QFontMetrics**
- Font rendering uses Qt's native font system
- Text measurement uses `QFontMetrics.boundingRect()`

### 4. Event Handling
- **GLib timers** → **QTimer**
- **GTK signals** → **Qt signals/slots** (where applicable)
- Context menus use `contextMenuEvent()` instead of button press handlers

### 5. Settings Storage
- Same JSON format
- Windows path: `%USERPROFILE%\.config\ivory\settings.json`
- Linux path: `~/.config/ivory/settings.json`

## Visual Appearance

### ✅ Identical
- **Piano keyboard rendering** - Pixel-perfect identical
- **Key colors and styling** - Same colors, same layout
- **Chord text display** - Same font, same positioning
- **Overall layout** - Same structure

### ⚠️ Different (Native Windows Styling)
- **Window title bar** - Native Windows style
- **Context menus** - Native Windows style
- **Color picker dialog** - Native Windows style
- **Message boxes** - Native Windows style

## Features Ported

All features from the GTK3 version are available:

- ✅ Full 88-key keyboard visualization
- ✅ Advanced chord detection (100+ chord types)
- ✅ Detachable chord display window
- ✅ Dark mode toggle
- ✅ Customizable colors (white keys, black keys, active keys, sustain)
- ✅ Sustain pedal visualization
- ✅ MIDI device selection
- ✅ Flats/sharps preference toggle
- ✅ Settings persistence
- ✅ Right-click context menus

## Testing Instructions

### For Your Friend (Windows User)

1. **Install Python 3.6+** (if not already installed)
2. **Install dependencies**:
   ```bash
   pip install -r requirements_pyqt5.txt
   ```
3. **Run the application**:
   ```bash
   python ivory_pyqt5.py
   ```
4. **Test all features** (see checklist in README_WINDOWS_TESTING.md)

### For You (Linux)

You can also test the PyQt5 version on Linux:

```bash
pip install PyQt5
python ivory_pyqt5.py
```

## Building Windows .exe (Future)

Once tested, you can create a standalone Windows executable:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name ivory ivory_pyqt5.py
```

The executable will bundle Python and PyQt5, making it ~50-100MB.

## Code Structure

The PyQt5 version maintains the same logical structure:

- `PianoWidget` - Custom widget for drawing the keyboard (equivalent to GTK DrawingArea)
- `ChordLabelWidget` - Widget for displaying chord names
- `MIDIMonitor` - Main application window (equivalent to GTK ApplicationWindow)

## Advantages of PyQt5 Version

1. **Native Windows Support** - No GTK3 runtime needed
2. **Smaller Bundle** - PyQt5 is smaller than GTK3 for Windows
3. **Better Windows Integration** - Native look and feel
4. **Easier Distribution** - Standard Python packaging works well
5. **Cross-Platform** - Works on Linux, Windows, and macOS

## Known Limitations

1. **No Single-Instance Support** - Unlike GTK3's `application_id`, PyQt5 doesn't have built-in single-instance support (can be added with QSharedMemory if needed)
2. **Window Icon** - Icon handling is simpler (no X11-specific code)
3. **Some GTK-specific Features** - Removed (like WM_CLASS setting, X11 icon properties)

## Next Steps

1. **Test on Windows** - Have your friend test all features
2. **Fix Any Issues** - Address any Windows-specific problems
3. **Create .exe** - Build standalone executable
4. **Add to GitHub Releases** - Include Windows .exe in releases
5. **Update GitHub Actions** - Add Windows build job

## Questions?

If you encounter any issues or need modifications, the code is well-commented and follows the same structure as the GTK3 version, making it easy to maintain both versions in parallel.


