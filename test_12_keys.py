#!/usr/bin/env python3
"""
Test key requirements across all 12 keys to ensure transposability
"""

import sys
sys.path.insert(0, '/home/ganten/Ivory-2.0')

from chord_detector_v2 import ChordDetector

detector = ChordDetector()

# Note names to MIDI (C4=60)
NOTE_MAP = {'C': 0, 'Db': 1, 'D': 2, 'Eb': 3, 'E': 4, 'F': 5,
            'F#': 6, 'Gb': 6, 'G': 7, 'Ab': 8, 'A': 9, 'Bb': 10, 'B': 11}

def transpose_midi(notes, semitones):
    """Transpose a set of MIDI notes by semitones"""
    return {note + semitones for note in notes}

def test_all_keys():
    """Test key requirements in all 12 keys"""

    print("=" * 80)
    print("IVORY 2.0 - 12-KEY TRANSPOSABILITY TEST")
    print("=" * 80)

    total_tests = 0
    passed_tests = 0
    failed_tests = []

    # Test 1: Am7/C = C6 (minor 7th with m3 in bass = major 6th)
    print("\n" + "=" * 80)
    print("TEST 1: m7/m3 = 6 (Am7/C = C6 pattern)")
    print("=" * 80)

    # Am7/C = C A C E G (C3 A3 C4 E4 G4)
    base_notes = {48, 57, 60, 64, 67}

    for semitones in range(12):
        notes = transpose_midi(base_notes, semitones)
        result = detector.detect_chord(notes)

        # Expected root is C + semitones (with enharmonic equivalent)
        expected_roots = [
            ['C'], ['Db', 'C#'], ['D'], ['Eb', 'D#'], ['E'], ['F'],
            ['F#', 'Gb'], ['G'], ['Ab', 'G#'], ['A'], ['Bb', 'A#'], ['B']
        ][semitones]
        expected_root = expected_roots[0]

        total_tests += 1
        # Check if result matches any enharmonic equivalent
        success = any(result == f"{root}6" for root in expected_roots)
        if success:
            passed_tests += 1
            print(f"✓ {expected_root}: {result}")
        else:
            failed_tests.append(f"{expected_root}6 test: expected {expected_root}6, got {result}")
            print(f"✗ {expected_root}: expected {expected_root}6, got {result}")

    # Test 2: G7(b9,b13) with root in bass
    print("\n" + "=" * 80)
    print("TEST 2: G7(b9,b13) with root in bass")
    print("=" * 80)

    # G7(b9,b13): G2 G3 Ab3 B3 Eb4 F4
    base_notes = {43, 55, 56, 59, 63, 65}

    for semitones in range(12):
        notes = transpose_midi(base_notes, semitones)
        result = detector.detect_chord(notes)

        # Expected root is G + semitones (with enharmonic equivalent)
        expected_roots = [
            ['G'], ['Ab', 'G#'], ['A'], ['Bb', 'A#'], ['B'], ['C'],
            ['Db', 'C#'], ['D'], ['Eb', 'D#'], ['E'], ['F'], ['F#', 'Gb']
        ][semitones]
        expected_root = expected_roots[0]
        # Accept either X7 or X7(b9,b13) or X7(b9) or X7(b13)

        total_tests += 1
        success = result and any(root in result for root in expected_roots) and '/' not in result
        if success:
            passed_tests += 1
            print(f"✓ {expected_root}: {result}")
        else:
            failed_tests.append(f"{expected_root}7 test: expected {expected_root}7 (no slash), got {result}")
            print(f"✗ {expected_root}: expected {expected_root}7 (no slash), got {result}")

    # Test 3: C13(b9) = C G Bb Db E A
    print("\n" + "=" * 80)
    print("TEST 3: 13(b9) chord pattern")
    print("=" * 80)

    # C13(b9): C4 Db4 E4 G4 A4 Bb4
    base_notes = {60, 61, 64, 67, 69, 70}

    for semitones in range(12):
        notes = transpose_midi(base_notes, semitones)
        result = detector.detect_chord(notes)

        # Expected root is C + semitones (with enharmonic equivalent)
        expected_roots = [
            ['C'], ['Db', 'C#'], ['D'], ['Eb', 'D#'], ['E'], ['F'],
            ['F#', 'Gb'], ['G'], ['Ab', 'G#'], ['A'], ['Bb', 'A#'], ['B']
        ][semitones]
        expected_root = expected_roots[0]

        total_tests += 1
        success = any(result == f"{root}13(b9)" for root in expected_roots)
        if success:
            passed_tests += 1
            print(f"✓ {expected_root}: {result}")
        else:
            failed_tests.append(f"{expected_root}13(b9) test: expected {expected_root}13(b9), got {result}")
            print(f"✗ {expected_root}: expected {expected_root}13(b9), got {result}")

    # Test 4: Bad voicing rejection (maj7 + natural 11)
    print("\n" + "=" * 80)
    print("TEST 4: Bad voicing rejection (major + natural 11)")
    print("=" * 80)

    # C E G B D F: C4 D4 E4 F4 G4 B4
    base_notes = {60, 62, 64, 65, 67, 71}

    for semitones in range(12):
        notes = transpose_midi(base_notes, semitones)
        result = detector.detect_chord(notes)

        # Expected is None for all keys
        expected_root = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B'][semitones]

        total_tests += 1
        if result is None:
            passed_tests += 1
            print(f"✓ {expected_root}: None (rejected)")
        else:
            failed_tests.append(f"{expected_root} bad voicing: expected None, got {result}")
            print(f"✗ {expected_root}: expected None, got {result}")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}/{total_tests}")
    print(f"Failed: {len(failed_tests)}/{total_tests}")

    if failed_tests:
        print("\nFailed tests:")
        for failure in failed_tests:
            print(f"  - {failure}")
    else:
        print("\n🎉 All transposability tests passed!")

    return len(failed_tests) == 0

if __name__ == "__main__":
    success = test_all_keys()
    sys.exit(0 if success else 1)
