#!/usr/bin/env python3
"""Test G7 with verbose debugging"""

import sys
sys.path.insert(0, '/home/ganten/Ivory-2.0')

from chord_detector_v2 import ChordDetector

# Monkey-patch to add debug output
original_detect = ChordDetector.detect_chord

def debug_detect(self, notes):
    print("\n=== CHORD DETECTION DEBUG ===")
    print(f"Input notes: {sorted(notes)}")
    result = original_detect(notes)
    print(f"Final result: {result}")
    return result

ChordDetector.detect_chord = debug_detect

detector = ChordDetector()

# G7(b9,b13) with C G C in bass
notes = {36, 43, 48, 56, 59, 63, 65}  # C2 G2 C3 Ab3 B3 Eb4 F4
print("Testing: G7(b9,b13) with C G C in bass")
print(f"Notes: C2 G2 C3 Ab3 B3 Eb4 F4")
print(f"Pitch classes: C=0, Eb=3, F=5, G=7, Ab=8, B=11")
print(f"Expected: G7 (root=G, M3=B, m7=F, alterations=Ab,Eb)")

result = detector.detect_chord(notes)
print(f"\n✓ PASS" if 'G' in (result or '') else f"\n✗ FAIL")
