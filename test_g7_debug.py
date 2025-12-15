#!/usr/bin/env python3
"""Debug G7 bass logic"""

import sys
sys.path.insert(0, '/home/ganten/Ivory-2.0')

# Test what the bass detection logic does
notes = {48, 55, 59, 62, 65}  # C3 G3 B3 D4 F4
print(f"Notes: {sorted(notes)}")

lowest_note = min(notes)
lowest_octave_top = lowest_note + 12
print(f"Lowest note: {lowest_note}")
print(f"Lowest octave top: {lowest_octave_top}")

bass_pcs = set()
for note in notes:
    if note < lowest_octave_top:
        bass_pcs.add(note % 12)
        print(f"  Bass note: {note} (PC={note % 12})")

print(f"Bass PCs: {bass_pcs}")

best_root_pc = 7  # G
allowed_bass = {best_root_pc, (best_root_pc + 5) % 12, (best_root_pc + 7) % 12}
print(f"Allowed bass (for G root): {allowed_bass}")
print(f"Is bass subset of allowed? {bass_pcs.issubset(allowed_bass)}")
