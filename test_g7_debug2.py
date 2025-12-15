#!/usr/bin/env python3
"""Debug what notes remain after bass filtering"""

notes = {36, 43, 48, 56, 59, 63, 65}
print(f"Original notes: {sorted(notes)}")
print(f"Note names: C2(36) G2(43) C3(48) Ab3(56) B3(59) Eb4(63) F4(65)")

lowest_note = min(notes)
lowest_octave_top = lowest_note + 12
print(f"\nLowest octave: {lowest_note} to {lowest_octave_top}")

bass_notes = {note for note in notes if note < lowest_octave_top}
upper_notes = {note for note in notes if note >= lowest_octave_top}
print(f"Bass notes: {sorted(bass_notes)}")
print(f"Upper notes: {sorted(upper_notes)}")

bass_pcs = set(note % 12 for note in bass_notes)
all_pcs = set(note % 12 for note in notes)
print(f"\nBass PCs: {bass_pcs}")
print(f"All PCs: {all_pcs}")

# Check dominant for G=7
root = 7
m3 = 11
m7 = 5
print(f"\nFor root G(7): M3={m3} (B), m7={m7} (F)")
print(f"M3 in all_pcs: {m3 in all_pcs}")
print(f"m7 in all_pcs: {m7 in all_pcs}")

allowed_bass = {7, 0, 2}
print(f"Allowed bass for G: {allowed_bass}")
print(f"Bass is subset: {bass_pcs.issubset(allowed_bass)}")

# Filter bass
notes_to_remove = set()
for note in bass_notes:
    if note % 12 in allowed_bass:
        notes_to_remove.add(note)
        print(f"Removing bass note: {note} (PC={note % 12})")

remaining = notes - notes_to_remove
print(f"\nRemaining notes: {sorted(remaining)}")
remaining_pcs = set(note % 12 for note in remaining)
print(f"Remaining PCs: {remaining_pcs}")
print(f"\nProblem: G(7) was in bass and got removed!")
print(f"Without G, the chord can't be detected as G7")
