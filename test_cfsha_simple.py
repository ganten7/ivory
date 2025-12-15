#!/usr/bin/env python3
"""Simple test for C F# A"""

import sys
sys.path.insert(0, '/home/ganten/Ivory-2.0')

from chord_detector_v2 import ChordDetector

def midi_notes(note_names_string):
    """Convert note names to MIDI numbers"""
    note_map = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11,
                'Cb': 11, 'Db': 1, 'Eb': 3, 'Gb': 6, 'Ab': 8, 'Bb': 10,
                'C#': 1, 'D#': 3, 'F#': 6, 'G#': 8, 'A#': 10}

    notes = note_names_string.strip().split()
    result = []

    for note in notes:
        if note[-1].isdigit():
            octave = int(note[-1])
            note_name = note[:-1]
        else:
            octave = 4
            note_name = note

        if note_name in note_map:
            midi_num = note_map[note_name] + (octave + 1) * 12
            result.append(midi_num)

    return set(result)

# Test C F# A
notes = midi_notes('C F# A')
print(f"Testing: C F# A")
print(f"MIDI notes: {sorted(notes)}")
print()

detector = ChordDetector()
result = detector.detect_chord(notes)

print()
print(f"Result: {result}")
