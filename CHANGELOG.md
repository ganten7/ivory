# Changelog

All notable changes to Ivory will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-13

### Added
- Full 88-key MIDI keyboard visualization (A0 to C8)
- Advanced chord detection engine with 100+ chord types
- Support for triads (major, minor, diminished, augmented)
- Support for 7th chords (major 7, minor 7, dominant 7, half-diminished, diminished 7)
- Support for extended chords (9, 11, 13)
- Support for altered dominants (b9, #9, #11, b13, and combinations)
- C9(b13) chord type detection
- Add chord support (add9, add11)
- Suspended chord support (sus2, sus4, 9sus, 13sus)
- 6/9 chord detection
- Automatic inversion detection
- Slash chord notation
- Scale detection for clustered notes
- Detachable chord display window
- Dark mode support
- Sustain pedal visualization
- Customizable note colors
- MIDI device selection
- Settings persistence
- Native GNOME/GTK3 integration
- Cross-platform support (Linux, Windows, macOS)

### Fixed
- Minor 6th vs major 6th conflicts in closed voicings
- 9sus vs add9 ambiguity resolution using chord span
- Minor add9 slash chord notation (e.g., Cm(add9)/G)
- Proper inversion bonuses for triads and 7th chords
- Rootless voicing detection
- Scale vs chord detection for clustered notes

### Changed
- Chord labels now use parenthetical notation
  - Major add9: Cadd9 → C(add9)
  - Minor add9: Cmadd9 → Cm(add9)
  - Sus chords: C9sus → C9(sus)
  - Dominant alterations: C7b9 → C7(b9), C7b9#11 → C7(b9,#11)

## [Unreleased]

### Planned Features
- Polychord detection
- Quartal harmony support
- Recording and playback
- MIDI output (chord suggestions)
- Learning mode with interactive tutorials
- Cloud sync for settings
- Plugin system for custom chord patterns

---

[1.0.0]: https://github.com/ganten7/ivory/releases/tag/v1.0.0
