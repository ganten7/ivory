#!/usr/bin/env python3
"""Debug C13(b9) scoring"""

import sys
sys.path.insert(0, '/home/ganten/Ivory-2.0')

from chord_detector_v2 import ChordDetector

# Temporarily enable debug mode by monkey-patching
detector = ChordDetector()

# C G Bb Db E A = C13(b9)
notes = {60, 61, 64, 67, 69, 70}

# Modify the detector to print scores
original_match = detector._match_chord_pattern

def debug_match(intervals, root_pc, active_notes, highest_note=None, highest_pc=None, lowest_pc=None, has_global_dominant_quality=False):
    result = original_match(intervals, root_pc, active_notes, highest_note, highest_pc, lowest_pc, has_global_dominant_quality)
    if result and root_pc == 0:  # Only for C root
        chord_name, score = result
        if '13' in chord_name or 'C7' in chord_name:
            print(f"  {chord_name:25s} score={score:.1f}")
    return result

detector._match_chord_pattern = debug_match

print("Scores for root=C:")
result = detector.detect_chord(notes)
print(f"\nFinal result: {result}")
