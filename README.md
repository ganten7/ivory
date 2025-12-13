# Ivory 🎹

**Professional MIDI Keyboard Monitor with Advanced Chord Detection**

![Ivory](icons/ivory.png)

Ivory is a full-featured MIDI keyboard monitor that displays all 88 keys with real-time chord detection. Perfect for musicians, producers, and anyone learning music theory.

## ✨ Features

- **88-Key Visualization**: Full piano keyboard display from A0 to C8
- **Advanced Chord Detection**: Recognizes triads, 7ths, extensions (9, 11, 13), alterations, inversions, and slash chords
- **Detachable Chord Display**: Separate window for chord names
- **Dark Mode**: Easy on the eyes during long sessions
- **Sustain Pedal Visualization**: See which notes are sustained
- **Customizable Colors**: Personalize your keyboard appearance
- **Multi-Platform**: Linux, Windows, macOS

## 🎵 Chord Detection

Ivory's chord detector is incredibly sophisticated, supporting:

- **Triads**: Major, minor, diminished, augmented
- **7th Chords**: Major 7, minor 7, dominant 7, half-diminished, diminished 7
- **Extended Chords**: 9ths, 11ths, 13ths
- **Altered Dominants**: b9, #9, #11, b13, and combinations
- **Special Chords**: 6/9, add9, sus chords, altered chords
- **Inversions & Slash Chords**: Automatically detected

### New in v1.0.1
- ✨ C9(b13) detection
- ✨ Improved slash chord notation for minor add9 inversions
- ✨ Enhanced label formatting with parentheses

## 🚀 Quick Start

### Linux (Debian/Ubuntu)
```bash
sudo dpkg -i ivory_1.0.1_all.deb
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
sudo apt-get install python3 python3-gi gir1.2-gtk-3.0 python3-cairo python3-gi-cairo libasound2-dev
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

### Linux .deb Package
```bash
./build-deb.sh
```

### Windows .exe
Automatic via GitHub Actions on release.

### macOS .app
Automatic via GitHub Actions on release.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

MIT License - see LICENSE file for details.

## 👤 Author

**Ganten**
- GitHub: [@ganten7](https://github.com/ganten7)
- Email: ganten7@github.com

## 🙏 Acknowledgments

- Courier Prime font for beautiful monospaced text
- GTK3 for native GNOME integration
- The open-source music community

## 📸 Screenshots

Coming soon!

## 🔗 Links

- [Homepage](https://github.com/ganten7/ivory)
- [Issues](https://github.com/ganten7/ivory/issues)
- [Releases](https://github.com/ganten7/ivory/releases)

---

Made with ❤️ by Ganten
