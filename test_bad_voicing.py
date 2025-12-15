#!/usr/bin/env python3
"""Debug C E G B D F bad voicing"""

import sys
sys.path.insert(0, '/home/ganten/Ivory-2.0')

from chord_detector_v2 import ChordDetector

detector = ChordDetector()

# C E G B D F - should be None (natural 11 with major)
notes = {60, 62, 64, 65, 67, 71}  # C4 D4 E4 F4 G4 B4
print("Notes: C4 D4 E4 F4 G4 B4")
print(f"MIDI: {sorted(notes)}")
print(f"PCs: {sorted(set(n % 12 for n in notes))}")

# From C: C D E F G B = Cmaj7(9,11) - natural 11 is bad!
# From G: G B D F + C E = G7(9,11) or G9(11) - dominant can have 11

result = detector.detect_chord(notes)
print(f"\nResult: {result}")
print(f"Expected: None (bad voicing - natural 11 with major chord)")

if result == "G7/C" or (result and "G" in result):
    print("\nProblem: Detected as G-based chord instead of C-based chord")
    print("The bass boost for G7 is too strong!")
    print("Should prefer Cmaj7(9,11) interpretation and reject it as bad voicing")
