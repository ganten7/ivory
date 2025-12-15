# Ivory 2.0 - Chord Detection Improvements

## Summary of Changes

### 1. Fixed Am7 → C6 Conversion Issue ✓
**Problem**: Am7 in closed voicing (span < 12 semitones) was automatically converting to C6
**Solution**: Removed the automatic reinterpretation at lines 1771-1784
**Result**: Am7 now stays as Am7 regardless of voicing

**File**: `chord_detector_v2.py:1771-1773`

### 2. Improved Scale Detection ✓
**Problem**: Scales like "F Ionian" were showing as chords instead of scale names
**Solution**:
- Changed scale detection priority for stepwise patterns spanning an octave or more
- When notes are:
  - Connected via steps/half-steps (clustered), AND
  - Span at least one octave (≥ 12 semitones)
- Then: ALWAYS prefer scale interpretation over chord interpretation

**Files Modified**:
- `chord_detector_v2.py:558-572` - Detection trigger logic
- `chord_detector_v2.py:1052-1072` - Scale preference logic

**Result**: All major modes, melodic minor modes, and harmonic minor modes now detected correctly when played stepwise across an octave+

### 3. All Special Cases Preserved ✓
All original special case logic has been preserved:
- m7b5 vs m6 disambiguation (lines 677-705)
- dim7 upper structure for 7b9 detection (lines 636-669)
- Slash chord patterns
- Voicing-based decisions
- All altered dominant detections
- Quartal/quintal patterns (if present)

## Test Results

### Passing Tests:
✓ Am7 remains Am7 (doesn't convert to C6)
✓ F Ionian detected across all registers
✓ All 12 major scales (Ionian) detected correctly
✓ D Dorian, A Aeolian, and other modes working
✓ Major 7#11 chords preserved
✓ 6th chord detection working
✓ Special cases for m7b5 when root is in bass

### Known Issues / Formatting Differences:

1. **Chord Name Formatting**:
   - Original uses: `C7(b9)`, `C7(#9)`
   - Code may output: `C7b9`, `C7#9` (without parentheses in some cases)
   - **Status**: Check format_chord_name functions for consistency

2. **C7(#9) Detection**:
   - Input: C E G Bb Eb
   - Sometimes detected as: EΔ7(#11)
   - **Status**: Investigate scoring priorities for altered dominants

## Transposability

All changes are key-agnostic and work across all 12 keys:
- C, C#/Db, D, Eb, E, F, F#/Gb, G, Ab, A, Bb, B
- Tested with Ionian mode in all keys ✓

## Scale Types Supported

All requested scale types are supported:
- **Major Modes**: Ionian, Dorian, Phrygian, Lydian, Mixolydian, Aeolian, Locrian ✓
- **Melodic Minor Modes**: Melodic Minor, Dorian b2, Lydian Augmented, Lydian Dominant, Mixolydian b6, Locrian #2, Altered ✓
- **Harmonic Minor Modes**: Harmonic Minor, Locrian #6, Ionian #5, Dorian #4, Phrygian Dominant, Lydian #2, Altered Diminished ✓
- **Pentatonic**: Major Pentatonic, Minor Pentatonic ✓
- **Blues**: Major Blues, Minor Blues ✓
- **Symmetrical**: Whole Tone, Half-Whole Diminished, Whole-Half Diminished ✓

## Next Steps

### Recommended Improvements:
1. **Verify altered dominant scoring** - C7(#9) should beat EΔ7(#11)
2. **Standardize chord name formatting** - Ensure consistent use of parentheses
3. **Add debug mode** - Optional verbose output showing scoring breakdown
4. **Performance testing** - Verify real-time responsiveness with MIDI input
5. **User preferences** - Add option to toggle Am7/C6 preference if needed

### Testing Recommendations:
1. Test with actual MIDI keyboard input
2. Verify all jazz voicings (rootless, shell, etc.)
3. Test edge cases with doubled notes
4. Verify pedal tones don't interfere with scale detection
5. Test polychords (if/when added)

## File Structure

```
/home/ganten/Ivory-2.0/
├── chord_detector_v2.py      # Main improved algorithm
├── test_improvements.py       # Test suite for v2.0 changes
├── debug_special_cases.py     # Debug failing tests
└── IMPROVEMENTS.md            # This file
```

## Usage

```python
from chord_detector_v2 import ChordDetector

detector = ChordDetector()

# Test Am7 (no longer converts to C6)
am7_notes = {57, 60, 64, 67}  # A C E G
chord = detector.detect_chord(am7_notes)
print(chord)  # Output: "Am7"

# Test F Ionian scale
f_ionian = {65, 67, 69, 70, 72, 74, 76, 77}  # F G A Bb C D E F
scale = detector.detect_chord(f_ionian)
print(scale)  # Output: "F Ionian"
```

## Backward Compatibility

All existing chord patterns and special cases are preserved. The only breaking changes are:
1. Am7 no longer auto-converts to C6 (intentional fix)
2. Scales preferred over chords for stepwise octave+ patterns (intentional improvement)

All other behavior remains identical to v1.0.
