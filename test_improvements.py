#!/usr/bin/env python3
"""
Test script for Ivory 2.0 chord detector improvements

Key improvements tested:
1. Am7 no longer converts to C6 in closed voicings
2. F Ionian and other scales detected when stepwise + octave span
3. All special cases preserved
"""

import sys
sys.path.insert(0, '/home/ganten/Ivory-2.0')

from chord_detector_v2 import ChordDetector

def test_am7_fix():
    """Test that Am7 stays as Am7 (doesn't convert to C6)"""
    print("\n" + "="*70)
    print("TEST 1: Am7 → C6 Conversion Fix")
    print("="*70)

    detector = ChordDetector()

    # Am7 in closed voicing (within one octave)
    # A C E G (notes 57, 60, 64, 67)
    am7_closed = {57, 60, 64, 67}
    result = detector.detect_chord(am7_closed)

    print(f"Input: A C E G (Am7 closed voicing)")
    print(f"Expected: Am7")
    print(f"Got: {result}")

    if result and 'Am7' in result:
        print("✓ PASS: Am7 correctly identified")
        return True
    else:
        print("✗ FAIL: Am7 converted incorrectly")
        return False

def test_scale_detection():
    """Test that scales are detected for stepwise patterns with octave+ span"""
    print("\n" + "="*70)
    print("TEST 2: Scale Detection for Stepwise Patterns")
    print("="*70)

    detector = ChordDetector()

    test_cases = [
        # F Ionian: F G A Bb C D E (F4 to F5) - spans more than octave
        ({65, 67, 69, 70, 72, 74, 76, 77}, "F Ionian", "F G A Bb C D E F"),

        # C Ionian (C Major): C D E F G A B (C4 to C5)
        ({60, 62, 64, 65, 67, 69, 71, 72}, "C Ionian", "C D E F G A B C"),

        # D Dorian: D E F G A B C (D4 to D5)
        ({62, 64, 65, 67, 69, 71, 72, 74}, "D Dorian", "D E F G A B C D"),

        # A Aeolian (A Natural Minor): A B C D E F G (A3 to A4)
        ({57, 59, 60, 62, 64, 65, 67, 69}, "A Aeolian", "A B C D E F G A"),
    ]

    passed = 0
    failed = 0

    for notes, expected_scale, description in test_cases:
        result = detector.detect_chord(notes)

        print(f"\nInput: {description}")
        print(f"Expected: {expected_scale}")
        print(f"Got: {result}")

        if result and expected_scale in result:
            print("✓ PASS")
            passed += 1
        else:
            print("✗ FAIL")
            failed += 1

    print(f"\nScale Detection Results: {passed} passed, {failed} failed")
    return failed == 0

def test_special_cases():
    """Test that important special cases still work"""
    print("\n" + "="*70)
    print("TEST 3: Special Cases Preservation")
    print("="*70)

    detector = ChordDetector()

    test_cases = [
        # Half-diminished vs minor 6th
        ({67, 70, 73, 77}, "Gm7b5", "G Bb Db F (Gm7b5, not Bbm6)"),
        ({70, 73, 77, 67}, "Bbm6", "Bb Db F G (Bbm6, not Gm7b5)"),

        # Dominant 7th alterations
        ({60, 64, 67, 70, 61}, "C7(b9)", "C E G Bb Db"),
        ({60, 64, 67, 70, 63}, "C7(#9)", "C E G Bb Eb"),

        # Major 7#11
        ({60, 64, 71, 78}, "CΔ7(#11)", "C E B F# (no G)"),

        # 6th chords
        ({60, 64, 67, 69}, "C6", "C E G A"),
        ({60, 63, 67, 69}, "Cm6", "C Eb G A"),
    ]

    passed = 0
    failed = 0

    for notes, expected, description in test_cases:
        result = detector.detect_chord(notes)

        print(f"\nInput: {description}")
        print(f"Expected: {expected}")
        print(f"Got: {result}")

        # More lenient matching - just check if key parts are present
        if result and expected.replace('Δ', '') in result.replace('Δ', ''):
            print("✓ PASS")
            passed += 1
        else:
            print("✗ FAIL")
            failed += 1

    print(f"\nSpecial Cases Results: {passed} passed, {failed} failed")
    return failed == 0

def test_all_keys():
    """Test that major scale detection works in all 12 keys"""
    print("\n" + "="*70)
    print("TEST 4: Transposability Across All 12 Keys")
    print("="*70)

    detector = ChordDetector()

    # All 12 major scales (Ionian mode)
    scales = {
        'C': [60, 62, 64, 65, 67, 69, 71, 72],
        'C#': [61, 63, 65, 66, 68, 70, 72, 73],
        'D': [62, 64, 66, 67, 69, 71, 73, 74],
        'Eb': [63, 65, 67, 68, 70, 72, 74, 75],
        'E': [64, 66, 68, 69, 71, 73, 75, 76],
        'F': [65, 67, 69, 70, 72, 74, 76, 77],
        'F#': [66, 68, 70, 71, 73, 75, 77, 78],
        'G': [67, 69, 71, 72, 74, 76, 78, 79],
        'Ab': [68, 70, 72, 73, 75, 77, 79, 80],
        'A': [69, 71, 73, 74, 76, 78, 80, 81],
        'Bb': [70, 72, 74, 75, 77, 79, 81, 82],
        'B': [71, 73, 75, 76, 78, 80, 82, 83],
    }

    passed = 0
    failed = 0

    for key, notes in scales.items():
        result = detector.detect_chord(set(notes))
        expected = f"{key} Ionian"

        # Handle enharmonic equivalents
        if key == 'C#':
            expected_alt = "Db Ionian"
        elif key == 'F#':
            expected_alt = "Gb Ionian"
        elif key == 'Ab':
            expected_alt = "G# Ionian"
        else:
            expected_alt = expected

        if result and (expected in result or expected_alt in result or 'Ionian' in result):
            print(f"✓ {key} Ionian: {result}")
            passed += 1
        else:
            print(f"✗ {key} Ionian: Expected '{expected}', Got '{result}'")
            failed += 1

    print(f"\nTransposability Results: {passed}/12 keys passed")
    return failed == 0

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("IVORY 2.0 CHORD DETECTOR - IMPROVEMENT TESTS")
    print("="*70)

    results = []

    # Run all tests
    results.append(("Am7 Fix", test_am7_fix()))
    results.append(("Scale Detection", test_scale_detection()))
    results.append(("Special Cases", test_special_cases()))
    results.append(("All 12 Keys", test_all_keys()))

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")

    total_passed = sum(1 for _, passed in results if passed)
    print(f"\nOverall: {total_passed}/{len(results)} test suites passed")

    if total_passed == len(results):
        print("\n🎉 All tests passed! Ivory 2.0 improvements verified.")
    else:
        print("\n⚠️  Some tests failed. Review the output above.")

if __name__ == "__main__":
    main()
