#!/usr/bin/env python3
"""Debug script for special case failures"""

import sys
sys.path.insert(0, '/home/ganten/Ivory-2.0')

from chord_detector_v2 import ChordDetector

detector = ChordDetector()

print("\n" + "="*70)
print("DEBUGGING SPECIAL CASE FAILURES")
print("="*70)

# Issue 1: Bbm6 detected as Gm7b5
print("\n1. Bbm6 vs Gm7b5:")
print("-" * 70)
bbm6_notes = {70, 73, 77, 67}  # Bb Db F G
print(f"Notes: {sorted(bbm6_notes)} (Bb=70, Db=73, F=77, G=67)")
print(f"Intervals from Bb(70): {sorted((n - 70) % 12 for n in bbm6_notes)}")
print(f"Expected: Bbm6 (Bb=root, Db=m3, F=P5, G=M6)")

result = detector.detect_chord(bbm6_notes)
print(f"Got: {result}")

# Check if this is the early special case issue
print("\nThis chord should trigger the m7b5 vs m6 early special case")
print("at lines 677-703 in the original code.")

# Issue 2: C7(b9) notation
print("\n2. C7(b9) notation:")
print("-" * 70)
c7b9_notes = {60, 64, 67, 70, 61}  # C E G Bb Db
print(f"Notes: {sorted(c7b9_notes)} (C=60, E=64, G=67, Bb=70, Db=61)")
result = detector.detect_chord(c7b9_notes)
print(f"Expected: C7(b9)")
print(f"Got: {result}")

# Issue 3: C7(#9) detected as EΔ7(#11)
print("\n3. C7(#9) detection:")
print("-" * 70)
c7sharp9_notes = {60, 64, 67, 70, 63}  # C E G Bb Eb(#9)
print(f"Notes: {sorted(c7sharp9_notes)} (C=60, E=64, G=67, Bb=70, Eb=63)")
print(f"Intervals from C: {sorted((n - 60) % 12 for n in c7sharp9_notes)}")
print(f"Expected: C7(#9) (C=root, E=M3, G=P5, Bb=m7, Eb=#9)")

result = detector.detect_chord(c7sharp9_notes)
print(f"Got: {result}")

print("\nThis might be getting detected as E root with F# (#11)")
print(f"Intervals from E(64): {sorted((n - 64) % 12 for n in c7sharp9_notes)}")
