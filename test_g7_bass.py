#!/usr/bin/env python3
"""Test G7 with C in bass"""

import sys
sys.path.insert(0, '/home/ganten/Ivory-2.0')

from chord_detector_v2 import ChordDetector

detector = ChordDetector()

# Simple test: G7 with C in bass
# G7 = G B D F, add C (the 5th) in bass
g7_simple = {48, 55, 59, 62, 65}  # C3 G3 B3 D4 F4
print("Test 1: Simple G7 with C in bass")
print(f"Notes: C3 G3 B3 D4 F4")
print(f"MIDI: {sorted(g7_simple)}")
result1 = detector.detect_chord(g7_simple)
print(f"Result: {result1}")
print(f"Expected: G7 (C is the 5th, should be ignored)")
print()

# G7 with C G C in bass (octaves and fifth)
g7_bass = {36, 43, 48, 55, 59, 62, 65}  # C2 G2 C3 G3 B3 D4 F4
print("Test 2: G7 with C G C in bass")
print(f"Notes: C2 G2 C3 G3 B3 D4 F4")
print(f"MIDI: {sorted(g7_bass)}")
result2 = detector.detect_chord(g7_bass)
print(f"Result: {result2}")
print(f"Expected: G7 (C G C are octaves/fifths, should be ignored)")
print()

# Just G7 in root position for reference
g7_root = {55, 59, 62, 65}  # G3 B3 D4 F4
print("Test 3: G7 in root position (reference)")
print(f"Notes: G3 B3 D4 F4")
print(f"MIDI: {sorted(g7_root)}")
result3 = detector.detect_chord(g7_root)
print(f"Result: {result3}")
print(f"Expected: G7")
