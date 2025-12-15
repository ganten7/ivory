# Ivory 🎹

**Simple MIDI Keyboard Monitor with Advanced Chord Detection**

![Ivory](icons/ivory.png)

Ivory is a cross-platform MIDI keyboard monitor that displays all 88 keys with real-time chord detection. Perfect for musicians, producers, and anyone learning music theory.

## ✨ Features

- **88-Key Visualization**: Full piano keyboard display from A0 to C8
- **Advanced Chord Detection**: Recognizes triads, 7ths, extensions (9, 11, 13), alterations, inversions, and slash chords
- **Detachable Chord Display**: Independent window for chord names (supports borderless mode)
- **Dark Mode**: Theme-aware UI with ivory-on-black or black-on-ivory styling
- **Window Size Presets**: 50%, 75%, 100%, 125%, 150%, 175%, 200%
- **Borderless Mode**: Frameless window with drag support
- **Sustain Pedal Visualization**: See which notes are sustained
- **Customizable Colors**: Personalize your keyboard appearance
- **Settings Persistence**: All preferences saved between sessions
- **Multi-Platform**: Linux (.deb), Windows (.exe), macOS (.app) via PyQt5

## 🎵 Chord Detection

Ivory's chord detector is incredibly sophisticated, supporting:

- **Triads**: Major, minor, diminished, augmented
- **7th Chords**: Major 7, minor 7, dominant 7, half-diminished, diminished 7
- **Extended Chords**: 9ths, 11ths, 13ths
- **Altered Dominants**: b9, #9, #11, b13, and combinations
- **Special Chords**: 6/9, add9, sus chords, altered chords
- **Inversions & Slash Chords**: Automatically detected

### New in v1.0.0 (PyQt5)
- ✨ Complete PyQt5 migration for cross-platform support
- ✨ Borderless window mode with drag support
- ✨ Window size presets (50%-200%)
- ✨ Theme-aware context menus (dark/light mode)
- ✨ Courier New font throughout
- ✨ Independent detachable chord window

## 🚀 Quick Start

### Linux (Debian/Ubuntu)
```bash
sudo dpkg -i ivory_1.0.0_all.deb
ivory
```

### Windows
Download and run `ivory.exe` from the [releases page](https://github.com/ganten7/ivory/releases).

### macOS
Download `Ivory.app` from the [releases page](https://github.com/ganten7/ivory/releases).

## 📦 Installation

### From Source
```bash
git clone https://github.com/ganten7/ivory.git
cd ivory
python3 ivory.py
```

### Dependencies (Linux)
```bash
sudo apt-get install python3 python3-pyqt5 python3-pyqt5.qtsvg
pip install -r requirements_pyqt5.txt
```

### Dependencies (Windows/macOS)
```bash
pip install -r requirements_pyqt5.txt
```

## 🎹 Usage

1. Launch Ivory
2. Select your MIDI input device from the menu
3. Start playing!
4. Enable chord detection to see chord names
5. Detach the chord window for a floating display

## ⌨️ Keyboard Shortcuts

- **Ctrl+D**: Toggle dark mode
- **Ctrl+C**: Toggle chord detection
- **Ctrl+W**: Toggle chord window
- **Ctrl+Q**: Quit

## 🛠️ Building

Builds are automated via GitHub Actions when you push a version tag (e.g., `v1.0.0`).

### Manual Build (Linux)
```bash
# Install dependencies
sudo apt-get install python3-pyqt5 python3-pyqt5.qtsvg
pip install -r requirements_pyqt5.txt

# Run directly
python3 ivory.py
```

### Manual Build (Windows)
```bash
pip install -r requirements_pyqt5.txt pyinstaller
pyinstaller --onefile --windowed --name ivory --icon=icons/ivory.png --add-data "chord_detector.py;." ivory.py
```

### Manual Build (macOS)
```bash
pip install -r requirements_pyqt5.txt pyinstaller
pyinstaller --onefile --windowed --name Ivory --icon=icons/ivory.png --add-data "chord_detector.py:." ivory.py
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

MIT License - see LICENSE file for details.

## 👤 Author

**Ganten**
- GitHub: [@ganten7](https://github.com/ganten7)
- Email: ganten7@github.com

## 🙏 Acknowledgments

- Courier New font for monospaced text
- PyQt5 for cross-platform GUI framework
- The open-source music community

## 📸 Screenshots

### Cm11 - Minor 11th Chord Detection
![Cm11 Chord](https://github.com/ganten7/ivory/releases/download/v1.0.1/Cm11.png)
*Ivory detecting a Cm11 chord - demonstrating extended chord recognition*

### D7(b9,#11) - Complex Altered Dominant
![D7(b9,#11) Chord](https://github.com/ganten7/ivory/releases/download/v1.0.1/D7-b9-11.png)
*Advanced altered dominant detection: D7 with both b9 and #11 alterations*

### Ebm11 - Extended Minor Chord
![Ebm11 Chord](https://github.com/ganten7/ivory/releases/download/v1.0.1/Ebm11.png)
*Ebm11 chord detection showcasing Ivory's comprehensive minor chord patterns*

## 🔗 Links

- [Homepage](https://github.com/ganten7/ivory)
- [Issues](https://github.com/ganten7/ivory/issues)
- [Releases](https://github.com/ganten7/ivory/releases)

---

Made with ❤️ by Ganten
