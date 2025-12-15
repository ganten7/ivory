#!/usr/bin/env python3
"""Debug C13(b9) detection"""

import sys
sys.path.insert(0, '/home/ganten/Ivory-2.0')

from chord_detector_v2 import ChordDetector

detector = ChordDetector()

# C G Bb Db E A = C13(b9)
notes = {60, 61, 64, 67, 69, 70}  # C Db E G A Bb
print("Test: C G Bb Db E A (should be C13(b9))")
print(f"Notes: {sorted(notes)}")
pcs = sorted(set(n % 12 for n in notes))
print(f"Pitch classes: {pcs}")
print(f"From C (0): {[(pc - 0) % 12 for pc in pcs]}")
result = detector.detect_chord(notes)
print(f"Result: {result}")
print()

# Check what patterns would match
print("Expected pattern for C13(b9): [0, 1, 4, 7, 9, 10]")
print(f"Actual intervals:             {sorted((pc - 0) % 12 for pc in pcs)}")
