#!/usr/bin/env python3
"""Debug C F# A detection"""

import sys
sys.path.insert(0, '/home/ganten/Ivory-2.0')

from chord_detector_v2 import ChordDetector, CHORD_PATTERNS, ESSENTIAL_INTERVALS, OPTIONAL_INTERVALS

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

# Calculate intervals from root C (60)
root = 60
intervals = sorted([n % 12 for n in notes])
print(f"Intervals: {intervals}")

# Check which patterns match
print("\n" + "="*80)
print("PATTERN MATCHING:")
print("="*80)

intervals_set = set(intervals)
input_pitch_class_count = len(set(note % 12 for note in notes))

matches = []

for chord_type, pattern in CHORD_PATTERNS.items():
    pattern_set = set(pattern)

    # Calculate matching notes
    matched_intervals = pattern_set & intervals_set
    matched_count = len(matched_intervals)
    extra_intervals = intervals_set - pattern_set
    extra_count = len(extra_intervals)
    missing_intervals = pattern_set - intervals_set
    missing_count = len(missing_intervals)

    # Get essential and optional intervals
    essential = set(ESSENTIAL_INTERVALS.get(chord_type, []))
    optional = set(OPTIONAL_INTERVALS.get(chord_type, []))

    # Check if essential intervals are present
    essential_matched = essential & matched_intervals
    essential_missing = essential - matched_intervals

    # Must have at least ONE essential interval
    if len(essential) > 0 and len(essential_matched) == 0:
        continue

    # If we have essential intervals, require at least 2 total matched notes
    if matched_count < 2:
        continue

    # Calculate score components
    essential_score = 0.0
    if len(essential) > 0:
        essential_percentage = len(essential_matched) / len(essential)
        essential_score = essential_percentage * 60.0
    else:
        essential_score = 30.0

    percentage_match = (matched_count / input_pitch_class_count) * 40.0

    completeness_bonus = 0.0
    if missing_count == 0 and extra_count == 0:
        completeness_bonus = 30.0
    elif missing_count == 0:
        completeness_bonus = 10.0

    extra_penalty = extra_count * 3.0

    optional_missing = optional & missing_intervals
    required_missing = missing_intervals - optional - essential

    missing_penalty = 0.0
    if len(essential_missing) > 0:
        missing_penalty += len(essential_missing) * 40.0
    missing_penalty += len(optional_missing) * 1.0
    missing_penalty += len(required_missing) * 8.0

    total_score = (essential_score + percentage_match + completeness_bonus -
                   extra_penalty - missing_penalty)

    if matched_count >= 2:
        matches.append({
            'type': chord_type,
            'pattern': pattern,
            'matched': matched_count,
            'missing': missing_count,
            'extra': extra_count,
            'essential_matched': len(essential_matched),
            'essential_missing': len(essential_missing),
            'score': total_score,
            'essential_score': essential_score,
            'percentage_match': percentage_match,
            'completeness': completeness_bonus,
            'penalties': extra_penalty + missing_penalty
        })

# Sort by score
matches.sort(key=lambda x: x['score'], reverse=True)

# Show top 10 matches
print(f"\nTop 10 pattern matches:")
for i, match in enumerate(matches[:10], 1):
    print(f"\n{i}. {match['type']}: {match['pattern']}")
    print(f"   Matched: {match['matched']}/{len(CHORD_PATTERNS[match['type']])}")
    print(f"   Missing: {match['missing']}, Extra: {match['extra']}")
    print(f"   Essential: {match['essential_matched']} matched, {match['essential_missing']} missing")
    print(f"   Score: {match['score']:.1f} = ess:{match['essential_score']:.1f} + "
          f"pct:{match['percentage_match']:.1f} + comp:{match['completeness']:.1f} - "
          f"pen:{match['penalties']:.1f}")

# Now test with detector
print("\n" + "="*80)
print("DETECTOR RESULT:")
print("="*80)

detector = ChordDetector()
result = detector.detect_chord(notes)
print(f"Detected: {result}")
