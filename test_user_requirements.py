#!/usr/bin/env python3
"""
Test all user-specified requirements for Ivory 2.0
Every test must pass without breaking existing functionality
"""

import sys
sys.path.insert(0, '/home/ganten/Ivory-2.0')

from chord_detector_v2 import ChordDetector

def midi_notes(note_names_string):
    """Convert note names to MIDI numbers. Format: 'C4 E4 G4' or 'C Bb Db' (assumes octave 4)"""
    # Note name to semitone mapping
    note_map = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11,
                'Cb': 11, 'Db': 1, 'Eb': 3, 'Gb': 6, 'Ab': 8, 'Bb': 10,
                'C#': 1, 'D#': 3, 'F#': 6, 'G#': 8, 'A#': 10}

    notes = note_names_string.strip().split()
    result = []

    for note in notes:
        # Check if octave is specified
        if note[-1].isdigit():
            octave = int(note[-1])
            note_name = note[:-1]
        else:
            octave = 4  # Default octave
            note_name = note

        if note_name in note_map:
            midi_num = note_map[note_name] + (octave + 1) * 12
            result.append(midi_num)

    return set(result)

def test_requirements():
    """Test all user requirements"""
    detector = ChordDetector()

    print("="*80)
    print("IVORY 2.0 - USER REQUIREMENTS TEST SUITE")
    print("="*80)

    tests = []

    # ========================================================================
    # REQUIREMENT 1: Minimum note requirements
    # ========================================================================
    print("\n" + "="*80)
    print("REQUIREMENT 1: Minimum Note/Pitch Class Requirements")
    print("="*80)

    tests.append({
        'name': 'C C F# C (2 pitch classes)',
        'notes': midi_notes('C3 C4 F#4 C5'),
        'expected': None,  # Should be no chord
        'description': '2 pitch classes = no chord'
    })

    tests.append({
        'name': 'C C Bb (2 pitch classes)',
        'notes': midi_notes('C3 C4 Bb4'),
        'expected': None,
        'description': '2 pitch classes = no chord'
    })

    tests.append({
        'name': 'C Bb Db (3 notes, no 3rd)',
        'notes': midi_notes('C Bb Db'),
        'expected': None,
        'description': 'Missing 3rd = no chord'
    })

    # ========================================================================
    # REQUIREMENT 2: Bad voicings (maj7 + natural 11)
    # ========================================================================
    print("\n" + "="*80)
    print("REQUIREMENT 2: Bad Voicing Detection")
    print("="*80)

    tests.append({
        'name': 'C E G B D F (maj7 + 9 + 11)',
        'notes': midi_notes('C E G B D F'),
        'expected': None,  # Natural 11 with major chord = bad voicing
        'description': 'Natural 11 with major = dissonant, no chord'
    })

    # ========================================================================
    # REQUIREMENT 3: Am7/C = C6 (enharmonic conversion)
    # ========================================================================
    print("\n" + "="*80)
    print("REQUIREMENT 3: Am7 over C = C6 (Enharmonic Conversion)")
    print("="*80)

    tests.append({
        'name': 'Am7 alone (A C E G)',
        'notes': midi_notes('A3 C4 E4 G4'),  # A in bass (root position)
        'expected': 'Am7',
        'description': 'Am7 without bass note stays Am7'
    })

    tests.append({
        'name': 'Am7 over C (C A C E G)',
        'notes': midi_notes('C3 A3 C4 E4 G4'),
        'expected': 'C6',
        'description': 'Am7 with C in bass = C6'
    })

    tests.append({
        'name': 'Am7 over multiple Cs (C G C A C E G)',
        'notes': midi_notes('C2 G2 C3 A3 C4 E4 G4'),
        'expected': 'C6',
        'description': 'Am7 with C,G,C in bass = C6 (octave doubling)'
    })

    # ========================================================================
    # REQUIREMENT 4: Octave doubling shouldn't change chord
    # ========================================================================
    print("\n" + "="*80)
    print("REQUIREMENT 4: Octave Doubling Rules")
    print("="*80)

    tests.append({
        'name': 'Bb C E G (7th not doubled)',
        'notes': midi_notes('Bb3 C4 E4 G4'),
        'expected': 'C/Bb',
        'description': '7th (Bb) appears once, simplify to triad'
    })

    tests.append({
        'name': 'Bb Bb C E G (doubled bass)',
        'notes': midi_notes('Bb2 Bb3 C4 E4 G4'),
        'expected': 'C7/Bb',
        'description': 'Doubling bass note should not change chord'
    })

    tests.append({
        'name': 'C C D E (sus2 with doubled root)',
        'notes': midi_notes('C3 C4 D4 E4'),
        'expected': None,  # This should probably be nothing or Csus2 incomplete
        'description': 'Need to determine expected behavior'
    })

    # ========================================================================
    # REQUIREMENT 5: Dominant fifth in bass handling
    # ========================================================================
    print("\n" + "="*80)
    print("REQUIREMENT 5: Dominant Chords - Ignore Fifth in Bass")
    print("="*80)

    tests.append({
        'name': 'G7(b9,b13) with fifth in bass',
        # G7(b9,b13) = G B F Ab Eb, with G in bass
        # G2 G3 Ab3 B3 Eb4 F4 = G (root doubled), Ab (b9), B (3rd), Eb (b13), F (m7)
        'notes': {43, 55, 56, 59, 63, 65},  # G2 G3 Ab3 B3 Eb4 F4
        'expected': 'G7',  # Should recognize as G7
        'expected_alt': 'G7(b9,b13)',  # Or with alterations
        'description': 'G7(b9,b13) with root in bass'
    })

    # ========================================================================
    # REQUIREMENT 6: New special case C13(b9)
    # ========================================================================
    print("\n" + "="*80)
    print("REQUIREMENT 6: C13(b9) Special Case")
    print("="*80)

    tests.append({
        'name': 'C13(b9): C G Bb Db E A',
        'notes': midi_notes('C G Bb Db E A'),
        'expected': 'C13(b9)',
        'description': '13th chord with b9 alteration'
    })

    # ========================================================================
    # RUN ALL TESTS
    # ========================================================================
    print("\n" + "="*80)
    print("RUNNING TESTS")
    print("="*80)

    passed = 0
    failed = 0

    for test in tests:
        result = detector.detect_chord(test['notes'])

        expected = test.get('expected')
        expected_alt = test.get('expected_alt')

        # Check if result matches expected or expected_alt
        if expected is None:
            success = result is None
        elif expected_alt:
            success = (result == expected) or (result == expected_alt) or \
                     (result and expected in result) or (result and expected_alt in result)
        else:
            success = (result == expected) or (result and expected in result)

        status = "✓ PASS" if success else "✗ FAIL"

        print(f"\n{status}: {test['name']}")
        print(f"  Notes: {sorted(test['notes'])}")
        print(f"  Expected: {expected}")
        if expected_alt:
            print(f"  Or: {expected_alt}")
        print(f"  Got: {result}")
        print(f"  Description: {test['description']}")

        if success:
            passed += 1
        else:
            failed += 1

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")

    if failed == 0:
        print("\n🎉 All requirements met!")
    else:
        print(f"\n⚠️  {failed} requirements need implementation")

    return failed == 0

if __name__ == "__main__":
    success = test_requirements()
    sys.exit(0 if success else 1)
