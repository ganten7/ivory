#!/usr/bin/env python3
"""Test the actual G7(b9,b13) case"""

import sys
sys.path.insert(0, '/home/ganten/Ivory-2.0')

from chord_detector_v2 import ChordDetector

detector = ChordDetector()

# G7(b9,b13) with C G C in bass
notes = {36, 43, 48, 56, 59, 63, 65}  # C2 G2 C3 Ab3 B3 Eb4 F4
print("G7(b9,b13) with C G C bass")
print(f"MIDI notes: {sorted(notes)}")

# Break down the notes
note_names = {
    36: 'C2', 43: 'G2', 48: 'C3',
    56: 'Ab3', 59: 'B3', 63: 'Eb4', 65: 'F4'
}
print(f"Note names: {[note_names[n] for n in sorted(notes)]}")

# Get pitch classes
pcs = sorted(set(n % 12 for n in notes))
print(f"Pitch classes: {pcs}")

# Intervals from G (7)
intervals_g = sorted((pc - 7) % 12 for pc in pcs)
print(f"Intervals from G: {intervals_g}")
print(f"Should be: [0(G), 4(B), 5(C), 8(Eb), 10(F), 1(Ab)]")

result = detector.detect_chord(notes)
print(f"\nResult: {result}")
print(f"Expected: G7(b9,b13) or G7")

# Check what's in the bass octave
lowest_note = min(notes)
lowest_octave_top = lowest_note + 12
bass_notes = [n for n in notes if n < lowest_octave_top]
print(f"\nBass octave notes: {bass_notes}")
bass_pcs = set(n % 12 for n in bass_notes)
print(f"Bass pitch classes: {bass_pcs}")

# Check if bass is only root/5th of G
allowed_bass = {7, 0, 2}  # G (root), C (P4/P5), D (P5 above C)
print(f"Allowed bass for G: {allowed_bass}")
print(f"Is bass subset? {bass_pcs.issubset(allowed_bass)}")
