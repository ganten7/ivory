#!/usr/bin/env python3
"""Detailed debug of C13(b9) detection"""

import sys
sys.path.insert(0, '/home/ganten/Ivory-2.0')

from chord_detector_v2 import ChordDetector, CHORD_PATTERNS

detector = ChordDetector()

# C G Bb Db E A = C13(b9)
notes = {60, 61, 64, 67, 69, 70}
pcs = sorted(set(n % 12 for n in notes))

print("Input notes: C G Bb Db E A")
print(f"Pitch classes: {pcs}")
print(f"Intervals from C: {pcs}")
print()

# Check which patterns would match
root_pc = 0  # C
intervals = sorted((pc - root_pc) % 12 for pc in pcs)
intervals_set = set(intervals)

print("Checking patterns that could match:")
print()

matches = []
for chord_type, pattern in CHORD_PATTERNS.items():
    if '13' in chord_type or '7' in chord_type:
        pattern_set = set(pattern)
        matched = pattern_set & intervals_set
        extra = intervals_set - pattern_set
        missing = pattern_set - intervals_set

        if len(matched) >= 4:  # At least 4 notes match
            matches.append((chord_type, len(matched), len(extra), len(missing), pattern))

# Sort by matched count (descending), then extra count (ascending)
matches.sort(key=lambda x: (-x[1], x[2], x[3]))

print(f"Top 10 matching patterns:")
for i, (chord_type, matched_count, extra_count, missing_count, pattern) in enumerate(matches[:10]):
    perfect = "PERFECT!" if extra_count == 0 and missing_count == 0 else ""
    print(f"{i+1}. {chord_type:20s} matched={matched_count} extra={extra_count} missing={missing_count} {perfect}")
    print(f"   Pattern: {pattern}")

print()
print(f"Actual detection result: {detector.detect_chord(notes)}")
