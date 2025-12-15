#!/usr/bin/env python3
"""Test just the upper structure of G7(b9,b13)"""

import sys
sys.path.insert(0, '/home/ganten/Ivory-2.0')

from chord_detector_v2 import ChordDetector

detector = ChordDetector()

print("="*80)
print("Test 1: Full chord with C G C bass")
full = {36, 43, 48, 56, 59, 63, 65}  # C2 G2 C3 Ab3 B3 Eb4 F4
print(f"Notes: {sorted(full)}")
print(f"PCs: {sorted(set(n % 12 for n in full))}")
result_full = detector.detect_chord(full)
print(f"Result: {result_full}\n")

print("="*80)
print("Test 2: Upper structure only (Ab B Eb F)")
upper = {56, 59, 63, 65}  # Ab3 B3 Eb4 F4
print(f"Notes: {sorted(upper)}")
print(f"PCs: {sorted(set(n % 12 for n in upper))}")
result_upper = detector.detect_chord(upper)
print(f"Result: {result_upper}\n")

print("="*80)
print("Test 3: With G in upper (G Ab B Eb F)")
with_g = {55, 56, 59, 63, 65}  # G3 Ab3 B3 Eb4 F4
print(f"Notes: {sorted(with_g)}")
print(f"PCs: {sorted(set(n % 12 for n in with_g))}")
result_g = detector.detect_chord(with_g)
print(f"Result: {result_g}\n")

print("="*80)
print("Test 4: G7(b9,b13) without any C (G Ab B Eb F)")
no_c = {55, 56, 59, 63, 65}  # G3 Ab3 B3 Eb4 F4
print(f"Notes: {sorted(no_c)}")
print(f"PCs: {sorted(set(n % 12 for n in no_c))}")
result_no_c = detector.detect_chord(no_c)
print(f"Result: {result_no_c}\n")
