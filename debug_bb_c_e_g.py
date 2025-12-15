#!/usr/bin/env python3
"""Debug why Bb C E G shows as C/Bb instead of C7/Bb"""

import sys
sys.path.insert(0, '/home/ganten/Ivory-2.0')

from chord_detector_v2 import ChordDetector

detector = ChordDetector()

# Bb C E G - should be C7/Bb
notes1 = {58, 60, 64, 67}  # Bb3 C4 E4 G4
print("Test 1: Bb C E G (should be C7/Bb)")
print(f"Notes: {sorted(notes1)}")
print(f"Pitch classes: {sorted(set(n % 12 for n in notes1))}")
result1 = detector.detect_chord(notes1)
print(f"Result: {result1}")
print()

# Bb Bb C E G - correctly shows as C7/Bb
notes2 = {46, 58, 60, 64, 67}  # Bb2 Bb3 C4 E4 G4
print("Test 2: Bb Bb C E G (correctly shows C7/Bb)")
print(f"Notes: {sorted(notes2)}")
print(f"Pitch classes: {sorted(set(n % 12 for n in notes2))}")
result2 = detector.detect_chord(notes2)
print(f"Result: {result2}")
print()

print("Both should show C7/Bb")
print("The only difference is the doubled Bb in test 2")
