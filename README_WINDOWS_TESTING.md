# Ivory PyQt5 - Windows Testing Guide

This is a Windows-compatible version of Ivory using PyQt5 instead of GTK3. The keyboard rendering will look identical, but window chrome and menus will use native Windows styling.

## Installation

### Prerequisites
- Python 3.6 or higher
- Windows 7 or later
- A MIDI keyboard or MIDI device

### Step 1: Install Python
If you don't have Python installed:
1. Download Python from https://www.python.org/downloads/
2. During installation, check "Add Python to PATH"
3. Verify installation: Open Command Prompt and run `python --version`

### Step 2: Install Dependencies
Open Command Prompt or PowerShell and run:

```bash
pip install -r requirements_pyqt5.txt
```

Or install individually:
```bash
pip install PyQt5 mido python-rtmidi
```

**Note for Windows**: `python-rtmidi` uses Windows MIDI APIs natively, so no additional drivers are needed.

### Step 3: Run Ivory
```bash
python ivory_pyqt5.py
```

Or if you want to specify a MIDI port:
```bash
python ivory_pyqt5.py -p "Your MIDI Device Name"
```

To list available MIDI ports:
```bash
python ivory_pyqt5.py -l
```

## Features

All features from the GTK3 version are available:
- ✅ Full 88-key keyboard visualization
- ✅ Advanced chord detection (100+ chord types)
- ✅ Detachable chord display window
- ✅ Dark mode
- ✅ Customizable colors
- ✅ Sustain pedal visualization
- ✅ MIDI device selection

## Differences from GTK3 Version

1. **Window Appearance**: Uses native Windows window styling (title bar, borders)
2. **Menus**: Uses native Windows context menus
3. **Color Dialogs**: Uses Windows native color picker
4. **Settings Location**: Settings are stored in `%USERPROFILE%\.config\ivory\settings.json`

## Keyboard Shortcuts

- **Right-click**: Open context menu
- **Ctrl+Q**: Quit (standard Windows)

## Troubleshooting

### "No MIDI input ports found"
- Make sure your MIDI device is connected
- Check Device Manager to verify Windows recognizes your MIDI device
- Try unplugging and replugging your MIDI device
- Some USB MIDI devices need drivers - check manufacturer's website

### "PyQt5 not found"
- Make sure you installed PyQt5: `pip install PyQt5`
- Try: `python -m pip install PyQt5`

### "mido not found"
- Install mido: `pip install mido python-rtmidi`
- On Windows, `python-rtmidi` uses native Windows MIDI APIs

### Application won't start
- Check Python version: `python --version` (needs 3.6+)
- Try running from Command Prompt to see error messages
- Make sure all dependencies are installed

## Building a Standalone .exe (Optional)

If you want to create a standalone executable:

1. Install PyInstaller:
```bash
pip install pyinstaller
```

2. Build executable:
```bash
pyinstaller --onefile --windowed --name ivory ivory_pyqt5.py
```

3. The executable will be in the `dist` folder

**Note**: The executable will be large (~50-100MB) because it bundles Python and PyQt5.

## Testing Checklist

Please test the following:

- [ ] Application launches successfully
- [ ] MIDI keyboard is detected and notes are displayed
- [ ] Chord detection works correctly
- [ ] Right-click context menu appears
- [ ] Color pickers work
- [ ] Dark mode toggle works
- [ ] Detach chord window works
- [ ] Settings are saved and restored
- [ ] Application closes cleanly

## Reporting Issues

If you encounter any issues, please report:
1. Windows version (e.g., Windows 10, Windows 11)
2. Python version (`python --version`)
3. Error messages (if any)
4. Steps to reproduce the issue
5. MIDI device name/model

## Visual Comparison

The keyboard rendering itself will look **identical** to the GTK3 version. The only visual differences will be:
- Window title bar (native Windows style)
- Context menus (native Windows style)
- Color picker dialog (native Windows style)

The actual piano keyboard drawing is pixel-perfect identical.


