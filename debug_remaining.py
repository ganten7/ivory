#!/usr/bin/env python3
"""Debug remaining 3 failures"""

import sys
sys.path.insert(0, '/home/ganten/Ivory-2.0')

from chord_detector_v2 import ChordDetector

detector = ChordDetector()

print("="*80)
print("DEBUGGING REMAINING FAILURES")
print("="*80)

# FAILURE 1: C Bb Db - should be None (missing 3rd)
print("\n1. C Bb Db (should be None - missing 3rd)")
notes1 = {60, 61, 70}  # C Db Bb
print(f"Notes: {sorted(notes1)}")
pcs1 = sorted(set(n % 12 for n in notes1))
print(f"Pitch classes: {pcs1}")
result1 = detector.detect_chord(notes1)
print(f"Result: {result1}")
print(f"Expected: None (no 3rd present)")

# Check if it's being interpreted from a different root
for root_pc in pcs1:
    intervals = sorted((pc - root_pc) % 12 for pc in pcs1)
    has_third = (3 in intervals or 4 in intervals)
    print(f"  From {root_pc}: intervals={intervals}, has_third={has_third}")

# FAILURE 2: G7(b9,b13) with fifth in bass
print("\n2. G7(b9,b13) with C in bass (fifth)")
# C G C F Ab Cb Eb - note the user said C G C F Ab Cb Eb
# Let me parse this more carefully: C(2) G(2) C(3) F(3) Ab(3) Cb(4) Eb(4)
# Actually looking at the test: {36, 43, 48, 53, 56, 63, 71}
notes2 = {36, 43, 48, 53, 56, 63, 71}
print(f"Notes: {sorted(notes2)}")
print(f"Note names: C2 G2 C3 F3 Ab3 Eb4 B4")
pcs2 = sorted(set(n % 12 for n in notes2))
print(f"Pitch classes: {pcs2}")
result2 = detector.detect_chord(notes2)
print(f"Result: {result2}")
print(f"Expected: G7(b9,b13) or similar")

# Check from G
g_pc = 7
intervals_g = sorted((pc - g_pc) % 12 for pc in pcs2)
print(f"  From G(7): intervals={intervals_g}")
print(f"  Should be G dominant with alterations")

# FAILURE 3: C13(b9)
print("\n3. C13(b9): C G Bb Db E A")
notes3 = {60, 61, 64, 67, 69, 70}
print(f"Notes: {sorted(notes3)}")
pcs3 = sorted(set(n % 12 for n in notes3))
print(f"Pitch classes: {pcs3}")
result3 = detector.detect_chord(notes3)
print(f"Result: {result3}")
print(f"Expected: C13(b9)")

# Check intervals
intervals_c = sorted((pc - 0) % 12 for pc in pcs3)
print(f"  From C(0): intervals={intervals_c}")
print(f"  Should match C13(b9) pattern: [0, 1, 4, 7, 9, 10]")
print(f"  Match: {intervals_c == [0, 1, 4, 7, 9, 10]}")
