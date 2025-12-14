# Contributing to Ivory

Thank you for your interest in contributing to Ivory! This document provides guidelines and information for contributors.

## Code of Conduct

Be respectful, inclusive, and professional. We're all here to make great music software!

## How to Contribute

### Reporting Bugs

Before creating a bug report, please check the [issue tracker](https://github.com/ganten7/ivory/issues) to avoid duplicates.

When reporting a bug, include:
- **Clear title** describing the issue
- **Steps to reproduce** the problem
- **Expected behavior** vs actual behavior
- **Screenshots** if applicable
- **System information** (OS, Python version, PyQt5 version)
- **MIDI device** being used
- **Chord that was misdetected** (if chord detection issue)

### Suggesting Features

Feature suggestions are welcome! Open an issue with:
- **Clear description** of the feature
- **Use case** - why is this useful?
- **Examples** of how it would work
- **Alternatives** you've considered

### Pull Requests

1. **Fork** the repository
2. **Create a branch** for your feature (`git checkout -b feature/amazing-feature`)
3. **Make your changes**
4. **Test thoroughly**
5. **Commit** with clear messages (`git commit -m 'Add amazing feature'`)
6. **Push** to your branch (`git push origin feature/amazing-feature`)
7. **Open a Pull Request**

#### PR Guidelines

- Keep changes focused (one feature/fix per PR)
- Update documentation if needed
- Add tests for new chord patterns
- Follow the existing code style
- Ensure all tests pass
- Update CHANGELOG.md

## Development Setup

### Prerequisites

```bash
# Linux (Debian/Ubuntu)
sudo apt-get install python3 python3-pyqt5 python3-pyqt5.qtsvg

# Install Python dependencies
pip install -r requirements_pyqt5.txt
```

### Windows/macOS
```bash
pip install -r requirements_pyqt5.txt
```

### Running from Source

```bash
git clone https://github.com/ganten7/ivory.git
cd ivory
python3 ivory.py
```

### Testing

```bash
# Run chord detection tests
python3 -m pytest tests/

# Test specific chord patterns
python3 tests/test_chord_detection.py
```

## Project Structure

```
ivory/
├── ivory.py              # Main application
├── chord_detector.py     # Chord detection engine
├── icons/                # Application icons
├── .github/              # GitHub workflows
│   └── workflows/
│       └── release.yml   # Release automation
├── tests/                # Test suite
├── README.md             # Documentation
├── CHANGELOG.md          # Version history
├── LICENSE               # MIT License
└── CONTRIBUTING.md       # This file
```

## Coding Standards

### Python Style
- Follow [PEP 8](https://pep8.org/)
- Use meaningful variable names
- Add docstrings to functions
- Keep functions focused and small
- Comment complex logic

### Example:
```python
def detect_chord(self, notes):
    """
    Detect chord from MIDI note numbers.

    Args:
        notes: Set of MIDI note numbers (21-108)

    Returns:
        String chord name (e.g., "Cmaj7") or None

    Example:
        >>> detector.detect_chord({60, 64, 67})
        'C'
    """
    # Implementation...
```

## Adding Chord Patterns

To add a new chord type to the detection engine:

### 1. Add Pattern to CHORD_PATTERNS

```python
CHORD_PATTERNS = {
    # ... existing patterns
    'your_chord': [0, intervals...],  # Example: [0, 4, 7, 11]
}
```

### 2. Define Essential Intervals

```python
ESSENTIAL_INTERVALS = {
    # ... existing patterns
    'your_chord': [4, 11],  # M3 + M7 for example
}
```

### 3. Define Optional Intervals

```python
OPTIONAL_INTERVALS = {
    # ... existing patterns
    'your_chord': [0, 7],  # Root and 5th optional
}
```

### 4. Add Chord Name Formatting

```python
# In detect_chord method
elif chord_type == 'your_chord':
    chord_name = f"{root_name}YourChord"
```

### 5. Add Tests

```python
def test_your_chord():
    detector = ChordDetector()
    notes = [60, 64, 67, 71]  # C E G B
    result = detector.detect_chord(notes)
    assert result == "CYourChord"
```

### 6. Document Special Cases

If your chord has special detection rules, add them to the documentation in `/Ivory Info/01_Special_Cases_and_Resolutions.md`.

## Testing Guidelines

### Manual Testing Checklist

When testing chord detection changes:

- [ ] Test with root in bass (root position)
- [ ] Test with 3rd in bass (1st inversion)
- [ ] Test with 5th in bass (2nd inversion)
- [ ] Test with 7th in bass (3rd inversion, if applicable)
- [ ] Test with rootless voicing (omit root)
- [ ] Test with no 5th (shell voicing)
- [ ] Test in different octaves
- [ ] Test with sustained notes
- [ ] Test rapid note changes

### Automated Testing

All chord patterns should have unit tests:

```python
def test_cmaj7():
    detector = ChordDetector()

    # Root position
    assert detector.detect_chord({60, 64, 67, 71}) == "CΔ7"

    # 1st inversion
    assert detector.detect_chord({52, 60, 64, 67}) == "CΔ7/E"

    # Rootless voicing
    assert detector.detect_chord({64, 71, 74}) == "CΔ7"
```

## Documentation

### Code Comments

```python
# Good comment - explains WHY
# Boost m6 chords to beat dim7 interpretations in slash voicings
special_pattern_bonus = 600.0

# Bad comment - explains WHAT (obvious from code)
# Set bonus to 600
special_pattern_bonus = 600.0
```

### Docstrings

All public methods need docstrings:

```python
def _match_chord_pattern(self, intervals, root_pc, active_notes):
    """
    Match intervals against chord patterns with jazz-aware scoring.

    Uses weighted scoring system considering essential intervals
    (3rd, 7th) as more important than optional intervals (root, 5th).

    Args:
        intervals: List of semitone intervals from root
        root_pc: Root pitch class (0-11)
        active_notes: Set of active MIDI note numbers

    Returns:
        Tuple of (chord_name: str, score: float) or None
    """
```

## Release Process

Maintainers will:
1. Update version in `chord_detector.py`
2. Update CHANGELOG.md
3. Create git tag (`v1.x.x`)
4. Push tag (triggers GitHub Actions)
5. GitHub Actions builds .deb, .exe, .dmg
6. Create GitHub release with binaries

## Getting Help

- **Discord**: Coming soon
- **GitHub Discussions**: [Ask questions](https://github.com/ganten7/ivory/discussions)
- **Email**: ganten7@github.com

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Ivory! 🎹
