#!/usr/bin/env python3
"""Test new user requirements"""

import sys
sys.path.insert(0, '/home/ganten/Ivory-2.0')

from chord_detector_v2 import ChordDetector

def midi_notes(note_names_string):
    """Convert note names to MIDI numbers. Format: 'C4 E4 G4' or 'C Bb Db' (assumes octave 4)"""
    note_map = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11,
                'Cb': 11, 'Db': 1, 'Eb': 3, 'Gb': 6, 'Ab': 8, 'Bb': 10,
                'C#': 1, 'D#': 3, 'F#': 6, 'G#': 8, 'A#': 10}

    notes = note_names_string.strip().split()
    result = []

    for note in notes:
        if note[-1].isdigit():
            octave = int(note[-1])
            note_name = note[:-1]
        else:
            octave = 4
            note_name = note

        if note_name in note_map:
            midi_num = note_map[note_name] + (octave + 1) * 12
            result.append(midi_num)

    return set(result)

detector = ChordDetector()

print("="*80)
print("NEW USER REQUIREMENTS TEST")
print("="*80)

tests = []

# 1. C Eb G Bb D F A = Cm13
tests.append({
    'name': 'C Eb G Bb D F A',
    'notes': midi_notes('C Eb G Bb D F A'),
    'expected': 'Cm13',
    'description': 'Minor 13th chord'
})

# 2. G A C E = Am/G unless A repeated in bass
tests.append({
    'name': 'G A C E',
    'notes': midi_notes('G3 A3 C4 E4'),
    'expected': 'Am',
    'expected_alt': 'Am/G',
    'description': 'Am over G (no A doubling in bass)'
})

tests.append({
    'name': 'A G A C E',
    'notes': midi_notes('A2 G2 A3 C4 E4'),
    'expected': 'Am7',
    'description': 'Am7 (A repeated in bass)'
})

# 3. C Bb Db E = C7b9
tests.append({
    'name': 'C Bb Db E',
    'notes': midi_notes('C Bb Db E'),
    'expected': 'C7(b9)',
    'description': 'C7b9 (7th + 3rd + b9)'
})

# 4. E F A C = F/E BUT F E F A C = Fmaj7
tests.append({
    'name': 'E F A C',
    'notes': midi_notes('E3 F3 A3 C4'),
    'expected': 'F/E',
    'description': 'F over E (no F doubling)'
})

tests.append({
    'name': 'F E F A C',
    'notes': midi_notes('F2 E2 F3 A3 C4'),
    'expected': 'FΔ7',
    'expected_alt': 'Fmaj7',
    'description': 'Fmaj7 (F repeated in bottom note)'
})

# 5. C (G) Bb D F# A = C7#11
tests.append({
    'name': 'C G Bb D F# A',
    'notes': midi_notes('C G Bb D F# A'),
    'expected': 'C7(#11)',
    'expected_alt': 'C13(#11)',
    'description': 'C7#11 with extensions'
})

# 6. C F# A = C°7 (dim7 without m3)
tests.append({
    'name': 'C F# A',
    'notes': midi_notes('C F# A'),
    'expected': 'C°7',
    'description': 'C diminished 7th (omit 3)'
})

# 7. D E G B = E/D unless E repeated in bottom
tests.append({
    'name': 'D E G B',
    'notes': midi_notes('D3 E3 G3 B3'),
    'expected': 'E/D',
    'expected_alt': 'Em/D',
    'description': 'E minor over D (no E doubling)'
})

tests.append({
    'name': 'E D E G B',
    'notes': midi_notes('E2 D2 E3 G3 B3'),
    'expected': 'Em7',
    'description': 'Em7 (E repeated in bottom note)'
})

# 8. C D E F G A is NOT C major pent
tests.append({
    'name': 'C D E F G A',
    'notes': midi_notes('C D E F G A'),
    'expected': None,  # Should NOT be detected as scale (F is not in C major pent)
    'expected_alt': 'scale',  # Or some chord, but not "C Major Pentatonic"
    'description': 'NOT C major pentatonic (F not in scale)'
})

# Run tests
passed = 0
failed = 0

for test in tests:
    result = detector.detect_chord(test['notes'])
    expected = test.get('expected')
    expected_alt = test.get('expected_alt')

    # Check if result matches
    if expected is None and expected_alt == 'scale':
        # For the scale test, accept anything that's NOT "C Major Pentatonic"
        success = result != "C Major Pentatonic" and result != "C Pentatonic"
    elif expected_alt:
        success = (result == expected) or (result == expected_alt) or \
                 (result and expected in result) or (result and expected_alt in result)
    else:
        success = (result == expected) or (result and expected and expected in result)

    status = "✓ PASS" if success else "✗ FAIL"

    print(f"\n{status}: {test['name']}")
    print(f"  Notes: {sorted(test['notes'])}")
    print(f"  Expected: {expected}", end="")
    if expected_alt:
        print(f" or {expected_alt}", end="")
    print()
    print(f"  Got: {result}")
    print(f"  Description: {test['description']}")

    if success:
        passed += 1
    else:
        failed += 1

print("\n" + "="*80)
print(f"SUMMARY: {passed}/{len(tests)} passed, {failed}/{len(tests)} failed")
print("="*80)
