#!/usr/bin/env python3
"""
Chord Detection Module for MIDI Monitor
Detects chords from active MIDI notes using music theory patterns
"""

from typing import Set, Optional, List, Tuple
from collections import Counter

# MIDI note names (pitch classes)
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
NOTE_NAMES_FLAT = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']

# Default preference for note naming (can be 'sharp' or 'flat')
PREFER_FLATS = True

# Chord patterns: intervals from root (in semitones)
# Structure: 'name': (intervals, essential_intervals, optional_intervals)
# essential_intervals: Must be present for positive ID (3rd, 7th usually)
# optional_intervals: Can be omitted (root, 5th often optional in jazz)
CHORD_PATTERNS = {
    # Triads
    'major': [0, 4, 7],
    'minor': [0, 3, 7],
    'diminished': [0, 3, 6],
    'augmented': [0, 4, 8],
    'sus2': [0, 2, 7],
    'sus4': [0, 5, 7],

    # Sus extended chords (no 3rd)
    '7sus4': [0, 5, 7, 10],                # Dom7sus4: root, 4th, 5th, m7
    '7sus2': [0, 2, 7, 10],                # Dom7sus2: root, 2nd, 5th, m7
    '9sus': [0, 2, 5, 10],                 # 9sus (no 5th): C D F Bb
    '9sus_with5': [0, 2, 5, 7, 10],        # 9sus with 5th: C D F G Bb
    '13sus': [0, 2, 5, 9, 10],             # 13sus (no 5th): C D F A Bb
    '13sus_with5': [0, 2, 5, 7, 9, 10],    # 13sus with 5th: C D F G A Bb
    '7sus13': [0, 2, 5, 9, 10],            # Dom7sus with 9 and 13: C D F A Bb (alias for 13sus)
    'sus13': [0, 2, 5, 9],                 # Sus with 13 (no 7th): C D F A

    # 7th chords (half-diminished before other m7 chords for priority)
    'half_diminished7': [0, 3, 6, 10],     # MUST come before minor6 to avoid conflicts
    'half_diminished11': [0, 3, 6, 10, 5], # Half-diminished with 11th (E G Bb D A)
    'half_diminished11_no3': [0, 5, 6, 10], # Half-diminished 11 without 3rd (E Bb D A)
    'major7': [0, 4, 7, 11],
    'major7#5': [0, 4, 8, 11],             # Augmented major 7th (C E G# B)
    'minor7': [0, 3, 7, 10],
    'dominant7': [0, 4, 7, 10],
    'diminished7': [0, 3, 6, 9],
    'diminished7_no_b5': [0, 3, 9],        # Diminished7 without dim5 (C Eb A)
    'diminished7_no_m3': [0, 6, 9],        # Diminished7 without m3 (C F# A)
    'diminished_major7': [0, 3, 6, 11],    # Diminished major 7th (dim triad + M7)
    '7b13_no5': [0, 4, 10, 8],             # 7b13 without 5th (BEFORE aug7 for priority)
    'augmented7': [0, 4, 8, 10],
    'minor_major7': [0, 3, 7, 11],         # Minor-major 7th (jazz)
    'minor_major9': [0, 2, 3, 7, 11],      # Minor-major 7th with 9 (C Eb G B D)
    'minor_major9_no5': [0, 2, 3, 11],     # Minor-major 9 without 5th (C D Eb B)

    # Extended chords
    'major9': [0, 4, 7, 11, 2],
    'minor9': [0, 3, 7, 10, 2],
    'dominant9': [0, 4, 7, 10, 2],
    'major11': [0, 4, 7, 11, 2, 5],        # Major 11th with natural 11
    'major9#11': [0, 4, 7, 11, 2, 6],      # Major 9 with sharp 11 (C E G B D F#) - MUST come before Δ7#11
    'major7#11': [0, 4, 7, 11, 6],         # Major 7 with sharp 11 without 9 (C E G B F#)
    'major7#11_no5': [0, 4, 6, 11],        # Major 7#11 without 5th (FABE: F A B E)
    'major7#11_shell': [0, 6, 11],         # Sparse voicing: root, #11, maj7 (no 3rd, no 5th) (FBE: F B E)
    'minor11': [0, 3, 7, 10, 2, 5],
    'minor11_no5': [0, 3, 10, 2, 5],       # Minor 11th without 5th
    'minor11_no9': [0, 3, 5, 7, 10],       # Minor 11th with 5th but no 9 (Eb Gb Ab Bb Db)
    'minor11_shell': [0, 3, 5, 10],        # Minor 11th shell: root, m3, P4, m7 (F# A B E)
    'major13': [0, 4, 7, 11, 2, 5, 9],     # Major 13th with natural 11
    'major13#11': [0, 4, 7, 11, 2, 6, 9],  # Major 13th with sharp 11
    'minor13': [0, 3, 7, 10, 2, 5, 9],     # Minor 13th
    'dominant11': [0, 4, 7, 10, 2, 5],     # Dominant 11th
    # ALTERED 13th chords MUST come BEFORE regular dominant13 for priority
    '13b9': [0, 1, 4, 7, 9, 10],       # Dominant13 with b9: C Db E G A Bb (NO 11!)
    '13b9_no5': [0, 1, 4, 9, 10],      # Dominant13 with b9 without 5th
    'dominant13': [0, 4, 7, 10, 2, 5, 9],  # Dominant 13th
    # Shell voicings for 13th chords (MUST come before 6th chords for priority)
    '13_shell': [0, 4, 10, 9],             # Dom13 shell: root, M3, m7, 13 (no 5th, no 9, no 11)
    '13_no5_no11': [0, 4, 10, 2, 9],       # Dom13: root, M3, m7, 9, 13 (no 5th, no 11)
    '13_no5': [0, 4, 10, 2, 5, 9],         # Dom13: root, M3, m7, 9, 11, 13 (no 5th)

    # Dominant 7#11 voicings
    '7#11_no5': [0, 4, 10, 6],             # Dom7#11 without 5th: root, M3, m7, #11 (C E Bb F#)
    '7#11_no3_no5': [0, 10, 2, 6],         # Dom7#11 without 3rd and 5th: root, m7, 9, #11 (C Bb D F#)
    '13#11_no3_no5': [0, 10, 2, 6, 9],     # Dom13#11 without 3rd and 5th: root, m7, 9, #11, 13 (C Bb D F# A)
    '13#11_no3': [0, 7, 10, 2, 6, 9],      # Dom13#11 without 3rd: root, 5th, m7, 9, #11, 13 (C G Bb D F# A)
    '13#11_no9_no5': [0, 4, 6, 9, 10],     # Dom13#11 without 9 and 5th: root, M3, #11, 13, m7 (C Bb E F# A)
    '13#11_no5': [0, 4, 10, 2, 6, 9],      # Dom13#11 without 5th: root, M3, m7, 9, #11, 13 (full voicing)

    # Altered dominant chords (specific patterns before generic "altered")
    # With 5th
    '7b9': [0, 4, 7, 10, 1],           # Dominant7 with flat 9
    '7#9': [0, 4, 7, 10, 3],           # Dominant7 with sharp 9
    '7#11': [0, 4, 7, 10, 6],          # Dominant7 with sharp 11
    '7b13': [0, 4, 7, 10, 8],          # Dominant7 with flat 13
    '7b9#11': [0, 4, 7, 10, 1, 6],     # Dominant7 with b9 and #11
    '7#9#11': [0, 4, 7, 10, 3, 6],     # Dominant7 with #9 and #11
    '7b9b13': [0, 4, 7, 10, 1, 8],     # Dominant7 with b9 and b13
    '7#9b13': [0, 4, 7, 10, 3, 8],     # Dominant7 with #9 and b13
    '7#11b13': [0, 4, 7, 10, 6, 8],    # Dominant7 with #11 and b13
    '7b9#11b13': [0, 4, 7, 10, 1, 6, 8],  # Dominant7 with b9, #11, b13
    '7#9#11b13': [0, 4, 7, 10, 3, 6, 8],  # Dominant7 with #9, #11, b13
    '7b9#9': [0, 4, 7, 10, 1, 3],      # Dominant7 with both b9 and #9
    '7b9#9#11': [0, 4, 7, 10, 1, 3, 6], # Dominant7 with b9, #9, #11
    '7b9#9b13': [0, 4, 7, 10, 1, 3, 8], # Dominant7 with b9, #9, b13
    '9b13': [0, 4, 7, 10, 2, 8],       # Dominant9 with b13 (natural 9 + b13)
    # Without 5th (shell voicings) - MUST come after full voicings
    '7b9_no5': [0, 4, 10, 1],          # Dominant7 b9 without 5th (C E Bb Db)
    '9b13_no5': [0, 4, 10, 2, 8],      # Dominant9 b13 without 5th (C E Bb D Ab)
    '7#11_shell': [0, 10, 2, 6, 9],     # 7#11 shell: root, m7, 9, #11, 13 (no 3rd, no 5th)
    '7#11_no3': [0, 7, 10, 6],          # 7#11 without 3rd: root, 5th, m7, #11
    '7#9#11_shell': [0, 10, 3, 6, 9],   # 7#9#11 shell: root, m7, #9, #11, 13 (no 3rd, no 5th)
    '7b9#11_shell': [0, 10, 1, 6, 9],   # 7b9#11 shell: root, m7, b9, #11, 13 (no 3rd, no 5th)
    '7b9#11_no3': [0, 7, 10, 1, 6],     # 7b9#11 without 3rd
    '7b9#11_no5': [0, 4, 10, 1, 6],     # 7b9#11 without 5th (has 3rd)
    '7b9#11_13_no5': [0, 1, 4, 6, 9, 10], # 7b9#11 with 13, without 5th (D F# C Eb Ab B)
    '7b9b13_no5': [0, 4, 10, 1, 8],     # 7b9b13 without 5th
    '7#9b13_no5': [0, 4, 10, 3, 8],     # 7#9b13 without 5th
    '7b9#9_no5': [0, 4, 10, 1, 3],      # 7b9#9 without 5th
    # Generic altered (last resort)
    'altered': [0, 4, 7, 10, 1, 3, 6, 8],  # Fully altered (b9, #9, #11, b13)

    # Add chords
    'add9': [0, 4, 7, 2],
    'minor_add9': [0, 3, 7, 2],      # Minor add9 (C Eb G D)
    '6': [0, 4, 7, 9],
    '6_no5': [0, 4, 9],          # Major 6th without 5th (C E A)
    '6add4': [0, 4, 5, 7, 9],    # Major 6th with added 4th (C E F G A)
    '6add4_no5': [0, 4, 5, 9],   # Major 6th with added 4th without 5th (C E F A)
    '6_9': [0, 4, 7, 9, 2],      # Major 6/9 (jazz voicing)
    '6_9_no5': [0, 4, 9, 2],     # 6/9 without 5th (common jazz voicing)
    '6_9_no3': [0, 2, 7, 9],     # 6/9 without 3rd (C G A D)
    'major7_6_9': [0, 4, 7, 9, 11, 2],  # Major7 with 6/9 (C E G A B D)
    'minor6': [0, 3, 7, 9],
    'minor6_no5': [0, 3, 9],     # Minor 6th without 5th (C Eb A)
    'minor6_9': [0, 3, 7, 9, 2], # Minor 6/9
    'minor6_9_no5': [0, 2, 3, 9], # Minor 6/9 without 5th (C D Eb A, e.g., Bb C Db G = Bbm6/9 no5)
    'add11': [0, 4, 7, 5],

    # Power chord (just root and 5th)
    '5': [0, 7],
}

# Essential intervals for chord quality identification
# 3rd and 7th are most important in jazz harmony
ESSENTIAL_INTERVALS = {
    # Triads
    'major': [4],           # Major 3rd defines major quality
    'minor': [3],           # Minor 3rd defines minor quality
    'diminished': [3, 6],   # m3 + dim5
    'augmented': [4, 8],    # M3 + aug5
    'sus2': [2],            # 2nd (no 3rd)
    'sus4': [5],            # 4th (no 3rd)
    '5': [7],               # Just 5th (no 3rd)

    # 7th chords
    'major7': [4, 11],      # M3 + M7
    'major7#5': [4, 11],    # M3 + M7 (aug5 is characteristic)
    'minor7': [3, 10],      # m3 + m7
    'dominant7': [4, 10],   # M3 + m7 (most important in jazz)
    'diminished7': [3, 9],  # m3 + dim7
    'diminished7_no_b5': [3, 9],  # m3 + dim7 (dim5 missing)
    'diminished7_no_m3': [6, 9],  # dim5 + dim7 (m3 missing)
    'diminished_major7': [3, 6, 11],  # m3 + dim5 + M7
    'half_diminished7': [3, 10],  # m3 + m7 (with dim5 = 6)
    'half_diminished11': [6, 10],  # dim5 + m7 (11 is extension)
    'half_diminished11_no3': [6, 10],  # dim5 + m7 (no 3rd, 11 present)
    'augmented7': [4, 10],  # M3 + m7 (with aug5)
    'minor_major7': [3, 11], # m3 + M7
    'minor_major9': [3, 11], # m3 + M7 (9 is extension)
    'minor_major9_no5': [3, 11], # m3 + M7 (9 is extension, no 5th)

    # Extended chords (3rd + 7th essential, extensions are color)
    'major9': [4, 11],      # M3 + M7 (9 is extension)
    'minor9': [3, 10],      # m3 + m7 (9 is extension)
    'dominant9': [4, 10],   # M3 + m7 (9 is extension)
    'major11': [4, 11],     # M3 + M7
    'major9#11': [4, 11, 6],   # M3 + M7 + #11 (ALL essential - must have #11)
    'major7#11': [4, 11, 6],   # M3 + M7 + #11 (ALL essential)
    'major7#11_no5': [4, 11, 6],  # M3 + M7 + #11 (ALL essential, no 5th)
    'major7#11_shell': [6, 11],  # #11 + M7 (no 3rd, sparse voicing)
    'minor11': [3, 10],     # m3 + m7
    'minor11_no5': [3, 10], # m3 + m7
    'minor11_no9': [3, 10], # m3 + m7 (no 9)
    'minor11_shell': [3, 10],   # m3 + m7 (no 5th, 11 instead of 9)
    'major13': [4, 11],     # M3 + M7
    'major13#11': [4, 11],  # M3 + M7
    'minor13': [3, 10],     # m3 + m7
    'dominant11': [4, 10],  # M3 + m7
    'dominant13': [4, 10],  # M3 + m7
    # Shell voicings for 13th chords
    '13_shell': [4, 10],    # M3 + m7 (13 is extension)
    '13_no5_no11': [4, 10], # M3 + m7
    '13_no5': [4, 10],      # M3 + m7

    # Dominant 7#11 voicings
    '7#11_no5': [4, 10],    # M3 + m7 (#11 is extension)
    '7#11_no3_no5': [10, 6],    # m7 + #11 (no 3rd)
    '13#11_no3_no5': [10, 6],  # m7 + #11 (13 and 9 are extensions)
    '13#11_no3': [10, 2, 6],   # m7 + 9 + #11 (no 3rd, so 9 is essential)
    '13#11_no9_no5': [4, 10],  # M3 + m7 (#11 and 13 are extensions)
    '13#11_no5': [4, 10],      # M3 + m7 (9, #11, 13 are extensions)

    # Sus chords (no 3rd, 2nd or 4th essential)
    '7sus4': [5, 10],       # 4th + m7
    '7sus2': [2, 10],       # 2nd + m7
    '9sus': [2, 5, 10],     # 2nd + 4th + m7
    '9sus_with5': [2, 5, 10],  # 2nd + 4th + m7 (with 5th)
    '13sus': [2, 10],       # 2nd + m7 (4th, 13 are extensions)
    '13sus_with5': [2, 10], # 2nd + m7 (4th, 5th, 13 are extensions)
    '7sus13': [2, 10],      # 2nd + m7 (9 and 13 are extensions)
    'sus13': [2, 9],        # 2nd + 13 (no 7th)

    # Altered dominants (3rd + 7th essential)
    '7b9': [4, 10],
    '7#9': [4, 10],
    '7#11': [4, 10],
    '7b13': [4, 10],
    '7b9#11': [4, 6, 10],  # M3, #11, m7 all essential
    '7#9#11': [4, 3, 6, 10],  # M3, #9, #11, m7 all essential
    '7b9b13': [4, 10],
    '7#9b13': [4, 10],
    '7#11b13': [4, 10],
    '7b9#11b13': [4, 10],
    '7#9#11b13': [4, 10],
    '7b9#9': [4, 10],
    '7b9#9#11': [4, 10],
    '7b9#9b13': [4, 10],
    '9b13': [4, 10],           # M3 + m7 (9 and b13 are extensions)
    '13b9': [4, 10],           # M3 + m7 (b9 and 13 are extensions)
    '13b9_no5': [4, 10],       # M3 + m7 (b9 and 13 are extensions, no 5th)
    '7b9_no5': [4, 10],        # M3 + m7
    '9b13_no5': [4, 10],       # M3 + m7
    # Shell voicings (no 3rd - m7 and characteristic interval essential)
    '7#11_shell': [10, 6],      # m7 + #11
    '7#11_no3': [10, 6],        # m7 + #11
    '7#9#11_shell': [10, 3, 6],    # m7 + #9 + #11
    '7b9#11_shell': [10, 1, 6],    # m7 + b9 + #11
    '7b9#11_no3': [10, 1, 6],      # m7 + b9 + #11
    '7b9#11_no5': [4, 10, 1, 6],   # M3 + m7 + b9 + #11 (all essential)
    '7b9#11_13_no5': [4, 10, 1, 6],  # M3 + m7 + b9 + #11 (13 is extension)
    # Shell voicings (no 5th)
    '7b13_no5': [4, 10],    # M3 + m7
    '7b9b13_no5': [4, 10],  # M3 + m7
    '7#9b13_no5': [4, 10],  # M3 + m7
    '7b9#9_no5': [4, 10],
    'altered': [4, 10],

    # 6th chords (3rd + 6th define the sound)
    '6': [4, 9],           # M3 + M6
    '6_no5': [4, 9],       # M3 + M6 (no 5th)
    '6add4': [4, 9],       # M3 + M6 (add4 is extension)
    '6add4_no5': [4, 9],   # M3 + M6 (no 5th)
    '6_9': [4, 9],         # M3 + M6 (9 is extension)
    '6_9_no5': [4, 9],     # M3 + M6
    '6_9_no3': [9, 2],     # M6 + M9 (no 3rd - special case)
    'major7_6_9': [4, 11, 9],  # M3 + M7 + M6
    'minor6': [3, 9],      # m3 + M6
    'minor6_no5': [3, 9],  # m3 + M6
    'minor6_9': [3, 9],    # m3 + M6
    'minor6_9_no5': [3, 9],  # m3 + M6 (9 is extension)

    # Add chords
    'add9': [4],           # M3 (with added 9)
    'minor_add9': [3],     # m3 (with added 9)
    'add11': [4],          # M3 (with added 11)
}

# Optional intervals (can be omitted without changing chord identity)
OPTIONAL_INTERVALS = {
    # Root is often omitted in jazz (bass plays it)
    # 5th is often omitted (doesn't define chord quality)

    # Triads
    'major': [0, 7],        # Root and 5th optional
    'minor': [0, 7],
    'diminished': [0],      # Root optional, but dim5 is essential
    'augmented': [0],       # Root optional, but aug5 is essential
    'sus2': [0, 7],         # Root and 5th optional
    'sus4': [0, 7],         # Root and 5th optional
    '5': [0],               # Root can be omitted

    # 7th chords
    'major7': [0, 7],       # Root and 5th optional
    'major7#5': [0],        # Root optional, aug5 is essential
    'minor7': [0, 7],
    'dominant7': [0, 7],    # Very common to omit root and/or 5th
    'diminished7': [0],
    'diminished7_no_b5': [0, 6],  # Root and dim5 optional (missing dim5 is ok)
    'diminished7_no_m3': [0, 3],  # Root and m3 optional (missing m3 is ok)
    'diminished_major7': [0],  # Root optional, dim5 is essential
    'half_diminished7': [0],
    'augmented7': [0],
    'minor_major7': [0, 7],
    'minor_major9': [0, 7, 2],  # Root, 5th, and 9 can be omitted
    'minor_major9_no5': [0, 2],  # Root and 9 can be omitted (5th already missing)

    # Extended chords (root and 5th optional, sometimes even 9/11/13)
    'major9': [0, 7],
    'minor9': [0, 7],
    'dominant9': [0, 7],
    'major11': [0, 7],
    'major7#11': [0, 7, 2],    # 9 can be omitted
    'major7#11_no5': [0, 2],   # Root and 9 optional, 5th already absent
    'major7#11_shell': [0, 4, 7, 2],  # Root, 3rd, 5th, 9 all optional (sparse voicing)
    'major9#11': [0, 7],       # Root and 5th optional
    'minor11': [0, 7],
    'minor11_no5': [0],        # Root optional, 5th already absent
    'minor11_shell': [0, 2],   # Root and 9 optional (has 11 instead of 9)
    'major13': [0, 7, 5],      # 11 can be omitted
    'major13#11': [0, 7],
    'minor13': [0, 7, 5],      # 11 often omitted (same as dominant13)
    'dominant11': [0, 7],
    'dominant13': [0, 7, 5],   # 11 often omitted
    # Shell voicings for 13th chords
    '13_shell': [0, 7],        # Root and 5th optional (5th already absent)
    '13_no5_no11': [0, 7],     # Root and 5th optional
    '13_no5': [0, 7],          # Root and 5th optional

    # Sus chords (root and 5th optional)
    '7sus4': [0, 7],           # Root and 5th optional
    '7sus2': [0, 7],           # Root and 5th optional
    '7sus13': [0, 7, 5],       # Root, 5th, and 11 optional
    'sus13': [0, 7, 5],        # Root, 5th, and 11 optional

    # Altered dominants (root and 5th optional)
    '7b9': [0, 7],
    '7#9': [0, 7],
    '7#11': [0, 7],
    '7b13': [0, 7],
    '7b9#11': [0, 7],
    '7#9#11': [0, 7],
    '7b9b13': [0, 7],
    '7#9b13': [0, 7],
    '7#11b13': [0, 7],
    '7b9#11b13': [0, 7],
    '7#9#11b13': [0, 7],
    '7b9#9': [0, 7],
    '7b9#9#11': [0, 7],
    '7b9#9b13': [0, 7],
    '9b13': [0, 7],            # Root and 5th optional (9 and b13 are characteristic)
    '7b9_no5': [0],            # Root optional, 5th already absent
    '9b13_no5': [0],           # Root optional, 5th already absent
    # Shell voicings (no 3rd/5th - root and extensions optional)
    '7#11_shell': [0, 2, 9],    # Root, 9, 13 optional (m7 + #11 essential)
    '7#11_no3': [0, 2, 9],      # Root, 9, 13 optional
    '7#9#11_shell': [0, 6, 9],  # Root, #11, 13 optional (m7 + #9 essential)
    '7b9#11_shell': [0, 6, 9],  # Root, #11, 13 optional (m7 + b9 essential)
    '7b9#11_no3': [0, 6, 9],    # Root, #11, 13 optional
    '7b9#11_no5': [0],          # Root optional, 5th already omitted
    '13#11_no3_no5': [0, 2, 9], # Root, 9, 13 optional (m7 + #11 essential)
    '13#11_no3': [0, 7, 9],     # Root, 5th, 13 optional (m7 + 9 + #11 essential)
    '13#11_no9_no5': [0, 6, 9], # Root, #11, 13 optional (M3 + m7 essential)
    '13#11_no5': [0, 6, 9],     # Root, #11, 13 optional (M3 + m7 + 9 essential)
    # Shell voicings (root optional, 5th already omitted)
    '7b9b13_no5': [0],
    '7#9b13_no5': [0],
    '7b9#9_no5': [0],
    'altered': [0, 7],

    # 6th chords (root optional, 5th optional)
    '6': [0, 7],
    '6_no5': [0],          # Root optional, 5th already absent
    '6add4': [0, 7],       # Root and 5th optional
    '6add4_no5': [0],      # Root optional, 5th already absent
    '6_9': [0, 7],
    '6_9_no5': [0],
    '6_9_no3': [0, 7],     # Root and 5th optional, 3rd already absent
    'minor6': [0, 7],
    'minor6_no5': [0],
    'minor6_9': [0, 7],
    'minor6_9_no5': [0],  # Root optional, 5th already absent

    # Add chords
    'add9': [0, 7],
    'minor_add9': [0, 7],
    'add11': [0, 7],
}

# Interval names (for 2-note detection) - abbreviated
INTERVAL_NAMES = {
    0: 'P1',   # Perfect unison
    1: 'm2',   # Minor 2nd
    2: 'M2',   # Major 2nd
    3: 'm3',   # Minor 3rd
    4: 'M3',   # Major 3rd
    5: 'P4',   # Perfect 4th
    6: 'd5',   # Diminished 5th (tritone)
    7: 'P5',   # Perfect 5th
    8: 'm6',   # Minor 6th
    9: 'M6',   # Major 6th
    10: 'm7',  # Minor 7th
    11: 'M7',  # Major 7th
    12: 'P8',  # Perfect octave
    13: 'm9',  # Minor 9th
    14: 'M9',  # Major 9th
    15: 'm10', # Minor 10th
    16: 'M10', # Major 10th
    17: 'P11', # Perfect 11th
    18: 'A11', # Augmented 11th
    19: 'P12', # Perfect 12th
    20: 'm13', # Minor 13th
    21: 'M13', # Major 13th
}

# Scale patterns: intervals from root (in semitones)
SCALE_PATTERNS = {
    # Major modes (7 notes)
    'Ionian': [0, 2, 4, 5, 7, 9, 11],           # Major scale (W W H W W W H)
    'Dorian': [0, 2, 3, 5, 7, 9, 10],           # Dorian mode
    'Phrygian': [0, 1, 3, 5, 7, 8, 10],         # Phrygian mode
    'Lydian': [0, 2, 4, 6, 7, 9, 11],           # Lydian mode
    'Mixolydian': [0, 2, 4, 5, 7, 9, 10],       # Mixolydian mode
    'Aeolian': [0, 2, 3, 5, 7, 8, 10],          # Natural minor / Aeolian mode
    'Locrian': [0, 1, 3, 5, 6, 8, 10],          # Locrian mode

    # Melodic minor modes (7 notes)
    'Melodic Minor': [0, 2, 3, 5, 7, 9, 11],    # Melodic minor (jazz minor)
    'Dorian b2': [0, 1, 3, 5, 7, 9, 10],        # Dorian b2 (Phrygian #6)
    'Lydian Augmented': [0, 2, 4, 6, 8, 9, 11], # Lydian Augmented
    'Lydian Dominant': [0, 2, 4, 6, 7, 9, 10],  # Lydian Dominant (Acoustic scale)
    'Mixolydian b6': [0, 2, 4, 5, 7, 8, 10],    # Mixolydian b6 (Aeolian Dominant)
    'Locrian #2': [0, 2, 3, 5, 6, 8, 10],       # Locrian #2 (Half-diminished)
    'Altered': [0, 1, 3, 4, 6, 8, 10],          # Altered scale (Super Locrian)

    # Harmonic minor modes (7 notes)
    'Harmonic Minor': [0, 2, 3, 5, 7, 8, 11],   # Harmonic minor
    'Locrian #6': [0, 1, 3, 5, 6, 9, 10],       # Locrian #6
    'Ionian #5': [0, 2, 4, 5, 8, 9, 11],        # Ionian #5 (Ionian Augmented)
    'Dorian #4': [0, 2, 3, 6, 7, 9, 10],        # Dorian #4 (Ukrainian Dorian)
    'Phrygian Dominant': [0, 1, 4, 5, 7, 8, 10],# Phrygian Dominant
    'Lydian #2': [0, 3, 4, 6, 7, 9, 11],        # Lydian #2
    'Altered Diminished': [0, 1, 3, 4, 6, 8, 9],# Altered Diminished (Ultra Locrian)

    # Pentatonic scales (5 notes)
    'Major Pentatonic': [0, 2, 4, 7, 9],        # Major pentatonic (e.g., C D E G A)
    'Minor Pentatonic': [0, 3, 5, 7, 10],       # Minor pentatonic (e.g., C Eb F G Bb)

    # Blues scales (6 notes)
    'Major Blues': [0, 2, 3, 4, 7, 9],          # Major blues (major pent + b3)
    'Minor Blues': [0, 3, 5, 6, 7, 10],         # Minor blues (minor pent + b5)

    # Symmetrical scales
    'Whole Tone': [0, 2, 4, 6, 8, 10],          # Whole tone (6 notes, all whole steps)
    'Whole-Half Diminished': [0, 2, 3, 5, 6, 8, 9, 11],  # Diminished scale (8 notes, W-H pattern)
    'Half-Whole Diminished': [0, 1, 3, 4, 6, 7, 9, 10],  # Dominant diminished (8 notes, H-W pattern)
}

# Inversion names
INVERSION_NAMES = {
    0: '',           # Root position
    1: '/3rd',       # First inversion (3rd in bass)
    2: '/5th',       # Second inversion (5th in bass)
    3: '/7th',       # Third inversion (7th in bass)
}

class ChordDetector:
    """Detect chords from active MIDI notes"""

    def __init__(self, prefer_flats=True):
        self.min_notes_for_chord = 2  # Minimum notes to detect a chord
        self.max_notes_for_chord = 7   # Maximum notes to consider
        self.prefer_flats = prefer_flats  # Preference for flat vs sharp note names

    def set_note_preference(self, prefer_flats):
        """Set preference for flat or sharp note names"""
        self.prefer_flats = prefer_flats

    def get_note_name(self, pitch_class):
        """Get note name based on preference"""
        if self.prefer_flats:
            return NOTE_NAMES_FLAT[pitch_class]
        else:
            return NOTE_NAMES[pitch_class]

    def is_clustered(self, active_notes: Set[int]) -> bool:
        """
        Check if notes form a clustered/scale-like pattern (adjacent notes)
        vs. spread intervalically (chord voicing).

        Returns True if notes are mostly adjacent (scale-like),
        False if they're spread with gaps (chord-like).
        """
        if len(active_notes) < 5:
            return False

        # Sort all active notes
        sorted_notes = sorted(active_notes)

        # Count adjacent pairs (notes within 1-2 semitones of each other)
        adjacent_count = 0
        gap_count = 0

        for i in range(len(sorted_notes) - 1):
            interval = sorted_notes[i + 1] - sorted_notes[i]
            if interval <= 2:  # Whole step or half step
                adjacent_count += 1
            elif interval >= 3:  # Skip (3rd or larger)
                gap_count += 1

        # If more than 60% of intervals are adjacent, it's a scale pattern
        total_intervals = len(sorted_notes) - 1
        if total_intervals == 0:
            return False

        adjacency_ratio = adjacent_count / total_intervals
        return adjacency_ratio >= 0.6

    def detect_interval(self, active_notes: Set[int]) -> Optional[str]:
        """
        Detect interval between two notes

        Args:
            active_notes: Set of exactly 2 MIDI note numbers

        Returns:
            Interval name string (e.g., "C (P5)") or None
        """
        if len(active_notes) != 2:
            return None

        # Get the two notes
        notes = sorted(list(active_notes))
        lower_note = notes[0]
        upper_note = notes[1]

        # Calculate interval in semitones
        interval_semitones = upper_note - lower_note

        # Get note names
        lower_name = self.get_note_name(lower_note % 12)
        upper_name = self.get_note_name(upper_note % 12)

        # Get interval name
        interval_name = INTERVAL_NAMES.get(interval_semitones, f'{interval_semitones} semitones')

        # Format: "Root (interval)"
        return f"{lower_name} ({interval_name})"

    def detect_chord(self, active_notes: Set[int], lowest_note: Optional[int] = None) -> Optional[str]:
        """
        Detect chord from active MIDI notes using ChordieApp's algorithm

        Algorithm reverse-engineered from ChordieApp.exe binary analysis:

        PRIMARY RULE: "Fretboards with a higher percentage of matching notes
                       compared against the original MIDI input will be placed
                       towards the front of the list of possible fretboards."

        SECONDARY RULE: "Fretboards whose highest note matches the highest note
                         in the Midi input will be placed towards the front of
                         the list of possible fretboards."

        Implementation:
        - Try ALL pitch classes as potential roots
        - Score each interpretation: percentage_match (primary) + bonuses - penalties
        - Return highest scoring interpretation

        Args:
            active_notes: Set of MIDI note numbers (0-127) currently active
            lowest_note: Not used (kept for compatibility)

        Returns:
            Chord name string (e.g., "C", "Am", "F#dim7") or None
        """
        if len(active_notes) < self.min_notes_for_chord:
            return None

        # For exactly 2 notes, detect interval instead of chord
        if len(active_notes) == 2:
            return self.detect_interval(active_notes)

        # NEW REQUIREMENT: Minimum pitch class requirement        # If we have only 2 unique pitch classes, return None (no chord)
        # Examples: C C F# C (only C and F#), C C Bb (only C and Bb)
        pitch_classes_unique = set(note % 12 for note in active_notes)
        if len(pitch_classes_unique) < 3:
            return None

        # Save original active_notes for scale detection (before it gets modified)
        original_active_notes = active_notes.copy()

        # Convert to pitch classes
        pitch_classes_all = sorted(set(note % 12 for note in active_notes))

        # IMPROVED SCALE DETECTION LOGIC (v2.0):
        # Check for scales when:
        # 1. Notes span at least one octave (>= 12 semitones) from lowest to highest, AND
        # 2. Notes are connected via steps/half-steps (clustered pattern), AND
        # 3. We have 5+ unique pitch classes
        # This prioritizes scale detection for stepwise patterns with octave+ span
        should_check_scale_later = False
        chord_span_early = max(active_notes) - min(active_notes)
        if len(pitch_classes_all) >= 5:
            # Check if notes span at least one octave AND are clustered (stepwise)
            if chord_span_early >= 12 and self.is_clustered(active_notes):
                should_check_scale_later = True
            # Also check for scales within one octave if highly clustered (backwards compat)
            elif chord_span_early < 12 and self.is_clustered(active_notes):
                should_check_scale_later = True

        # If we have 7 unique pitch classes (and not clustered), check if it's a 13th chord
        if len(pitch_classes_all) == 7:
            lowest_note = min(active_notes)
            lowest_pc = lowest_note % 12

            # Check if the lowest note forms a chord with 3rd and 7th
            # (13th chords have 3rd + 7th + extensions)
            intervals_from_lowest = set((pc - lowest_pc) % 12 for pc in pitch_classes_all)
            has_third = (3 in intervals_from_lowest or 4 in intervals_from_lowest)
            has_seventh = (10 in intervals_from_lowest or 11 in intervals_from_lowest)

            # If lowest note doesn't form a chord, try scale detection as fallback
            if not (has_third and has_seventh):
                scale = self.detect_scale(active_notes)
                if scale and scale.startswith(self.get_note_name(lowest_pc)):
                    return scale
            # If lowest note DOES form a chord (3rd+7th), continue with chord detection
            # (13th chords will be detected below)


        # Try chord detection

        if len(active_notes) > self.max_notes_for_chord:
            # Too many notes - might be multiple chords or noise
            # Take the most common pitch classes
            pitch_classes = [note % 12 for note in active_notes]
            pc_counter = Counter(pitch_classes)
            # Take top 7 most common
            most_common = [pc for pc, _ in pc_counter.most_common(7)]
            active_notes = {note for note in active_notes if note % 12 in most_common}
        
        # Convert to pitch classes (ignore octave)
        pitch_classes = sorted(set(note % 12 for note in active_notes))

        if len(pitch_classes) < 2:
            return None

        # CRITICAL VALIDATION: Filter chords with interval conflicts from BASS
        # Rule: If bass has both M3+m3 OR both m7+M7, reject UNLESS upper structure forms valid chord
        # Example: C Eb F# A E (from C: has m3=Eb and M3=E) - should be filtered
        # Example: C Db Eb Fb (from C: has m3=Eb and M3=E, but Db Eb E = DbmΔ9) - allow as DbmΔ9/C
        # Get highest and lowest notes early for use in pre-detection filter
        highest_note_for_validation = max(active_notes)
        highest_pc_for_validation = highest_note_for_validation % 12
        lowest_note_for_validation = min(active_notes)
        lowest_pc_for_validation = lowest_note_for_validation % 12
        intervals_from_bass = set((pc - lowest_pc_for_validation) % 12 for pc in pitch_classes)

        has_m3_and_M3_from_bass = (3 in intervals_from_bass and 4 in intervals_from_bass)
        has_m7_and_M7_from_bass = (10 in intervals_from_bass and 11 in intervals_from_bass)

        if has_m3_and_M3_from_bass or has_m7_and_M7_from_bass:
            # Check if a valid chord can be formed from a NON-BASS root (using all pitch classes)
            # Example: C Db Eb E - from Db: [0, 2, 3, 11] = DbmΔ9, so allow as DbmΔ9/C
            # CRITICAL: Reject altered dominants with #9/#11 ONLY if detected from NON-BASS root
            # Reason: #9 is enharmonic with b3, creating M3+m3 conflicts from bass
            # Valid altered dominants CAN exist with root in bass (e.g., G7(#9) = G B D F A#)
            # but the M3+m3 conflict must come from the altered extensions, not from the bass
            non_bass_pcs = [pc for pc in pitch_classes if pc != lowest_pc_for_validation]
            if len(non_bass_pcs) >= 2:  # Need at least 2 non-bass notes to form a chord
                # Try to detect chord from all pitch classes with non-bass roots
                slash_chord_valid = False
                valid_chord_type = None
                found_altered_from_non_bass = False
                for potential_root in non_bass_pcs:
                    intervals_from_potential = sorted((pc - potential_root) % 12 for pc in pitch_classes)
                    # Check if this matches any chord pattern
                    for chord_type, pattern in CHORD_PATTERNS.items():
                        if set(pattern) == set(intervals_from_potential):
                            # Found a match from NON-BASS root - check if it's an altered dominant
                            chord_type_str = str(chord_type)
                            if '#9' in chord_type_str or '#11' in chord_type_str:
                                # Altered dominant from NON-BASS root with M3+m3 conflicts from bass
                                # Mark this but continue checking other roots
                                found_altered_from_non_bass = True
                                break
                            # Valid non-altered chord from non-bass root
                            slash_chord_valid = True
                            valid_chord_type = chord_type
                            break
                    if slash_chord_valid:
                        break

                # If we only found altered dominants from non-bass roots, reject
                if found_altered_from_non_bass and not slash_chord_valid:
                    return None
                
                if not slash_chord_valid and not found_altered_from_non_bass:
                    # No valid chord from non-bass root - reject this chord entirely
                    return None
                # else: Valid slash chord exists from non-bass root
                # Find which non-bass root has the valid chord and detect it
                valid_slash_root_pre = None
                for potential_root in non_bass_pcs:
                    intervals_from_potential_pre = sorted((pc - potential_root) % 12 for pc in pitch_classes)
                    for chord_type_pre, pattern_pre in CHORD_PATTERNS.items():
                        if set(pattern_pre) == set(intervals_from_potential_pre):
                            valid_slash_root_pre = potential_root
                            break
                    if valid_slash_root_pre is not None:
                        break
                
                if valid_slash_root_pre is not None:
                    # Detect the chord from the valid non-bass root
                    # We need to calculate has_global_dominant_quality first
                    has_global_dominant_quality_pre = False
                    for potential_root_pre in pitch_classes:
                        m3_above_pre = (potential_root_pre + 4) % 12
                        m7_above_pre = (potential_root_pre + 10) % 12
                        if m3_above_pre in pitch_classes and m7_above_pre in pitch_classes:
                            has_global_dominant_quality_pre = True
                            break
                    
                    intervals_from_valid_root_pre = sorted((pc - valid_slash_root_pre) % 12 for pc in pitch_classes)
                    slash_match_result_pre = self._match_chord_pattern(intervals_from_valid_root_pre, valid_slash_root_pre, active_notes,
                                                                       highest_note_for_validation, highest_pc_for_validation, lowest_pc_for_validation, has_global_dominant_quality_pre)
                    if slash_match_result_pre:
                        slash_chord_name_pre, slash_score_pre = slash_match_result_pre
                        bass_note_name_pre = self.get_note_name(lowest_pc_for_validation)
                        return f"{slash_chord_name_pre}/{bass_note_name_pre}"
                # If we can't detect the slash chord, continue with normal detection
            else:
                # Too few non-bass notes - reject
                return None

        # CRITICAL EARLY SPECIAL CASE: m6 slash chord pattern
        # When we have exactly 4 notes with intervals [0, 1, 7, 10] from bass
        # This is almost certainly a m6 chord from the note at interval 10
        # Example: C Bb Db G = Bbm6/C
        if len(pitch_classes) == 4:
            lowest_note_early = min(active_notes)
            lowest_pc_early = lowest_note_early % 12
            intervals_from_lowest_early = sorted((pc - lowest_pc_early) % 12 for pc in pitch_classes)

            if intervals_from_lowest_early == [0, 1, 7, 10]:
                # Root is at interval 10 (m7 above bass)
                root_pc_early = (lowest_pc_early + 10) % 12
                root_name_early = self.get_note_name(root_pc_early)
                bass_name_early = self.get_note_name(lowest_pc_early)
                return f"{root_name_early}m6/{bass_name_early}"

        # CRITICAL EARLY SPECIAL CASE 1b: 5-note m6 slash chord pattern
        # When we have exactly 5 notes with intervals [0, 1, 5, 7, 10] from bass
        # This is almost certainly a m6 chord with added P4/11
        # Example: C Bb Db F G = Bbm6/C (Bb Db F G is Bbm6, C is bass)
        if len(pitch_classes) == 5:
            lowest_note_early1b = min(active_notes)
            lowest_pc_early1b = lowest_note_early1b % 12
            intervals_from_lowest_early1b = sorted((pc - lowest_pc_early1b) % 12 for pc in pitch_classes)

            if intervals_from_lowest_early1b == [0, 1, 5, 7, 10]:
                # Root is at interval 10 (m7 above bass)
                root_pc_early1b = (lowest_pc_early1b + 10) % 12
                root_name_early1b = self.get_note_name(root_pc_early1b)
                bass_name_early1b = self.get_note_name(lowest_pc_early1b)
                return f"{root_name_early1b}m6/{bass_name_early1b}"

        # CRITICAL EARLY SPECIAL CASE 2: dim7 upper structure for 7b9 chords
        # When we have 5 notes and 4 of them form a dim7 chord with the lowest note separate
        # First check if it's a 7b9 chord (upper structure contains 3, 5, b7, b9 of bass)
        # Example: C E G Bb Db - upper structure E G Bb Db contains M3, P5, m7, b9 of C = C7b9
        # Otherwise: C D F Ab Cb = Ddim7/C (D F Ab Cb is dim7, C is bass)
        if len(pitch_classes) == 5:
            lowest_note_early2 = min(active_notes)
            lowest_pc_early2 = lowest_note_early2 % 12

            # Try to find a dim7 chord in the remaining 4 notes
            remaining_pcs = [pc for pc in pitch_classes if pc != lowest_pc_early2]
            if len(remaining_pcs) == 4:
                # Check if these 4 notes form a dim7 from any root
                for potential_dim7_root in remaining_pcs:
                    intervals_from_dim7_root = sorted((pc - potential_dim7_root) % 12 for pc in remaining_pcs)
                    if intervals_from_dim7_root == [0, 3, 6, 9]:
                        # Found a dim7! Now check if it's actually a 7b9 from the bass
                        # Check if upper structure contains: M3 (4), P5 (7), m7 (10), b9 (1) from bass
                        intervals_from_bass = set((pc - lowest_pc_early2) % 12 for pc in remaining_pcs)
                        has_major_third = 4 in intervals_from_bass
                        has_perfect_fifth = 7 in intervals_from_bass
                        has_minor_seventh = 10 in intervals_from_bass
                        has_flat_nine = 1 in intervals_from_bass

                        # If upper structure contains 3, 5, b7, and b9 of bass, it's a 7b9 chord
                        if has_major_third and has_perfect_fifth and has_minor_seventh and has_flat_nine:
                            # This is a 7b9 chord from the bass note!
                            root_name_7b9 = self.get_note_name(lowest_pc_early2)
                            return f"{root_name_7b9}7b9"
                        else:
                            # Not a 7b9, keep as dim7 slash chord
                            root_name_dim7 = self.get_note_name(potential_dim7_root)
                            bass_name_dim7 = self.get_note_name(lowest_pc_early2)
                            return f"{root_name_dim7}dim7/{bass_name_dim7}"

        # CRITICAL EARLY SPECIAL CASE 3: half-diminished 7th vs minor 6th
        # m7b5 and m6 are enharmonic: Gm7b5 (G Bb Db F) = Bbm6 (Bb Db F G)
        # Prefer m6 interpretation UNLESS the m7b5 root is in the bass
        # Example: G Bb Db F = Gm7b5 (G in bass, keep as m7b5)
        #          Bb Db F G = Bbm6 (Bb in bass, prefer m6)
        #          C Bb Db G = Bbm6/C (C in bass, interpret as m6 with slash)
        if len(pitch_classes) == 4:
            lowest_note_halfdim = min(active_notes)
            lowest_pc_halfdim = lowest_note_halfdim % 12

            # Try all pitch classes as potential half-dim7 roots
            for potential_halfdim_root in pitch_classes:
                intervals_from_halfdim = sorted((pc - potential_halfdim_root) % 12 for pc in pitch_classes)
                if intervals_from_halfdim == [0, 3, 6, 10]:
                    # Found a half-dim7 pattern!
                    # If the m7b5 root is in the bass, use m7b5
                    if potential_halfdim_root == lowest_pc_halfdim:
                        root_name_halfdim = self.get_note_name(potential_halfdim_root)
                        return f"{root_name_halfdim}hdim7"
                    else:
                        # Root is NOT in bass - prefer m6 interpretation
                        # The m6 root is the note at interval 3 (m3) above the m7b5 root
                        # Example: Gm7b5 (G Bb Db F) = Bbm6 (Bb Db F G)
                        m6_root_pc = (potential_halfdim_root + 3) % 12
                        m6_root_name = self.get_note_name(m6_root_pc)

                        # If the m6 root is in the bass, it's just a m6 chord
                        if m6_root_pc == lowest_pc_halfdim:
                            return f"{m6_root_name}m6"
                        else:
                            # Different bass note - slash chord
                            bass_name = self.get_note_name(lowest_pc_halfdim)
                            return f"{m6_root_name}m6/{bass_name}"

        # Get highest and lowest notes for matching and inversion detection
        highest_note = max(active_notes)
        highest_pc = highest_note % 12
        lowest_note = min(active_notes)
        lowest_pc = lowest_note % 12

        # Note: Interval conflict checking (M3+m3, M7+m7) is done per-pattern
        # in _match_chord_pattern to allow valid chords like DbmΔ9/C
        # (which has M3+m3 from C but is valid from Db)

        # GLOBAL dominant quality check: Check if ANY pitch class forms dominant quality
        # A chord has dominant quality if it contains some root + M3 above that root + m7 above that root
        # This prevents m6 interpretations from overwhelming dominant 7th chords
        has_global_dominant_quality = False
        for potential_root in pitch_classes:
            m3_above = (potential_root + 4) % 12
            m7_above = (potential_root + 10) % 12
            if m3_above in pitch_classes and m7_above in pitch_classes:
                has_global_dominant_quality = True
                break

        # Try ALL pitch classes as potential roots (like ChordieApp)
        # This allows detecting inversions and finding best match regardless of bass
        best_match = None
        best_score = 0.0
        best_root_pc = None

        DEBUG = False  # Set to True to enable debugging
        
        # DEBUG: Test 1c debugging
        debug_test1c = False
        if len(active_notes) == 5 and lowest_pc == 2:  # D in bass, 5 notes
            test_pcs = sorted(set(n % 12 for n in active_notes))
            if test_pcs == [0, 2, 4, 7]:  # C, D, E, G
                d_count = sum(1 for n in active_notes if n % 12 == 2)
                if d_count == 2:  # D doubled
                    debug_test1c = True
                    DEBUG = True
                    print(f"\n=== DEBUG TEST 1c: D E G C D (D doubled) ===")
                    print(f"active_notes: {sorted(active_notes)}")
                    print(f"pitch_classes: {sorted(pitch_classes)}")
                    print(f"lowest_pc: {lowest_pc} (D)")
        
        if DEBUG:
            print(f"DEBUG: has_global_dominant_quality = {has_global_dominant_quality}")

        for root_pc in pitch_classes:
            # Calculate intervals from this root
            intervals = sorted((pc - root_pc) % 12 for pc in pitch_classes)

            if DEBUG and root_pc == 0:  # Only debug C as root
                print(f"DEBUG: Trying root_pc={root_pc} ({self.get_note_name(root_pc)}), intervals={intervals}")

            # Match against chord patterns with ChordieApp-inspired scoring
            match_result = self._match_chord_pattern(intervals, root_pc, active_notes, highest_note, highest_pc, lowest_pc, has_global_dominant_quality)

            if match_result:
                chord_name, score = match_result
                if DEBUG:
                    print(f"DEBUG: root_pc={root_pc} ({self.get_note_name(root_pc)}): {chord_name}, score={score}")
                if score > best_score:
                    best_score = score
                    best_match = chord_name
                    best_root_pc = root_pc
                    if DEBUG:
                        print(f"DEBUG:   -> NEW BEST! best_match={best_match}, best_score={best_score}")

        # SPECIAL RULE: For extended chords (9/11/13), root=bass always wins
        # If best match is an extended chord but root is NOT bass, check if bass-as-root also gives extended chord
        if best_match and best_root_pc is not None and best_root_pc != lowest_pc:
            # Check if best match is an extended chord
            is_extended = ('9' in best_match or '11' in best_match or '13' in best_match)
            if is_extended:
                # Try detection with bass note as root
                intervals_from_bass = sorted((pc - lowest_pc) % 12 for pc in pitch_classes)
                bass_match_result = self._match_chord_pattern(intervals_from_bass, lowest_pc, active_notes,
                                                              highest_note, highest_pc, lowest_pc, has_global_dominant_quality)
                if bass_match_result:
                    bass_chord_name, bass_score = bass_match_result
                    # Check if bass interpretation is also an extended chord
                    bass_is_extended = ('9' in bass_chord_name or '11' in bass_chord_name or '13' in bass_chord_name)
                    if bass_is_extended:
                        # Bass-as-root wins for extended chords
                        if DEBUG:
                            print(f"DEBUG: EXTENDED CHORD OVERRIDE - switching from {best_match} to {bass_chord_name} (bass note priority)")
                        best_match = bass_chord_name
                        best_root_pc = lowest_pc
                        best_score = bass_score

        # SPECIAL RULE: Prefer clear triad/7th slash chords over complex bass chords
        # If best match from bass is complex/ambiguous (like G6/9), check if any non-bass note
        # forms a clear triad or 7th chord. If yes, prefer the slash chord.
        # User directive: "if notes form a clear triad/7th from a non-bass note, prefer that as a slash chord"
        if best_match and best_root_pc is not None and best_root_pc == lowest_pc:
            # Define "complex" chords - chords that are ambiguous or would be rejected by validation
            # Include: 6/9 chords, add9, sus13, and chords that might lack a 3rd
            intervals_from_bass = sorted(set((pc - lowest_pc) % 12 for pc in pitch_classes))
            has_third_from_bass = (3 in intervals_from_bass or 4 in intervals_from_bass)

            # Check if bass chord is complex or missing 3rd
            # EXCEPTION: #11 chords and dim chords are allowed to not have a 3rd (special cases)
            # NOTE: add9, add11, and 6/9 are NOT complex - they're legitimate chords that should not be overridden
            complex_patterns = ['sus13']
            is_sharp11_chord = '#11' in best_match
            is_dim_chord = 'dim' in best_match.lower() or '°' in best_match
            is_complex_bass_chord = (any(pattern in best_match for pattern in complex_patterns) or
                                    (not has_third_from_bass and not is_sharp11_chord and not is_dim_chord))

            if is_complex_bass_chord:
                if DEBUG:
                    print(f"DEBUG: Complex bass chord detected: {best_match}, checking for clear slash chord alternatives")

                # Try each non-bass pitch class as root
                best_clear_slash = None
                best_clear_score = 0
                best_clear_root = None

                for root_pc in pitch_classes:
                    if root_pc == lowest_pc:
                        continue  # Skip bass note

                    # Calculate intervals from this non-bass root
                    intervals_from_non_bass = sorted((pc - root_pc) % 12 for pc in pitch_classes)
                    non_bass_match = self._match_chord_pattern(intervals_from_non_bass, root_pc, active_notes,
                                                               highest_note, highest_pc, lowest_pc, has_global_dominant_quality)

                    if non_bass_match:
                        non_bass_chord, non_bass_score = non_bass_match

                        # CRITICAL: Check for add9 FIRST before other clear chords
                        # Example: D E G C D should be Cadd9/D, not Em7/D
                        # BUT: D E G C (D not doubled) should be C/D, not Cadd9/D
                        is_add9_clear = 'add9' in non_bass_chord
                        if is_add9_clear:
                            # Check if add9 is a perfect match (no missing/extra intervals)
                            intervals_from_add9_root = sorted((pc - root_pc) % 12 for pc in pitch_classes)
                            add9_pattern = CHORD_PATTERNS.get('add9', [0, 2, 4, 7])
                            if set(intervals_from_add9_root) == set(add9_pattern):
                                # Perfect add9 match - BUT only prefer if 9th is doubled
                                # Check if the 9th (interval 2) is doubled
                                ninth_pc_add9 = (root_pc + 2) % 12
                                ninth_count_add9 = sum(1 for note in active_notes if note % 12 == ninth_pc_add9)
                                bass_is_ninth_add9 = (lowest_pc == ninth_pc_add9)
                                
                                if bass_is_ninth_add9 and ninth_count_add9 > 1:
                                    # 9th is doubled - prefer add9
                                    if DEBUG:
                                        print(f"DEBUG:   FOUND PERFECT add9 match with DOUBLED 9th: {non_bass_chord} (score {non_bass_score})")
                                        print(f"DEBUG:   PREFERRING add9 (perfect match, doubled 9th) over other clear chords")
                                    best_clear_slash = non_bass_chord
                                    best_clear_score = non_bass_score + 10000.0  # Huge boost to beat everything
                                    best_clear_root = root_pc
                                    # Don't check other roots - add9 wins
                                    break
                                elif DEBUG:
                                    print(f"DEBUG:   Found add9 but 9th NOT doubled (count={ninth_count_add9}), allowing simplification")
                        
                        # Check if this is a "clear" chord: basic triads or 7th chords
                        # Extract just the chord quality (remove the root note name)
                        chord_quality = non_bass_chord.replace(self.get_note_name(root_pc), '').strip()

                        # Define "clear" chord qualities: major, minor, aug, dim triads, and basic 7ths
                        clear_qualities = ['', 'm', 'maj7', 'm7', 'dim', 'dim7', 'aug']
                        # Also allow dominant 7 (just "7" without alterations)
                        is_clear_dom7 = (chord_quality == '7' or
                                        (chord_quality.startswith('7') and not any(c in chord_quality for c in ['b', '#', '(', 'add'])))

                        is_clear = chord_quality in clear_qualities or is_clear_dom7

                        if is_clear:
                            if DEBUG:
                                print(f"DEBUG:   Found clear chord from non-bass: {non_bass_chord} (score {non_bass_score})")
                            if non_bass_score > best_clear_score:
                                best_clear_slash = non_bass_chord
                                best_clear_score = non_bass_score
                                best_clear_root = root_pc

                # If we found a clear chord from a non-bass note, prefer it as a slash chord
                if best_clear_slash:
                    if DEBUG:
                        print(f"DEBUG: CLEAR SLASH CHORD OVERRIDE - switching from {best_match} (bass) to {best_clear_slash} (slash) for clarity")
                    best_match = best_clear_slash
                    best_root_pc = best_clear_root
                    best_score = best_clear_score

        # Special detection: diminished 7th + note M3 below = dominant 7(b9)
        # Example: F + Adim7 (A C Eb Gb) = F7(b9), or F A C Eb = F7(b9)
        # Rule: if we have a dim7 chord and one of the dim7 notes is M3 above another note,
        # that note becomes the root of a 7(b9) chord
        if len(pitch_classes) == 4 or len(pitch_classes) == 5:
            # Check all notes as potential 7(b9) roots
            for potential_root in pitch_classes:
                # Look for a note that is M3 above potential_root
                m3_above = (potential_root + 4) % 12
                if m3_above in pitch_classes:
                    # Check if the notes form a dim7 starting from m3_above
                    # If we have 4 notes, check if they form dim7
                    # If we have 5 notes, check if removing potential_root leaves dim7
                    if len(pitch_classes) == 5:
                        remaining_pcs = [pc for pc in pitch_classes if pc != potential_root]
                    else:
                        remaining_pcs = list(pitch_classes)

                    # Check if these form a dim7 chord with m3_above as root
                    dim_intervals = sorted((pc - m3_above) % 12 for pc in remaining_pcs)
                    if len(dim_intervals) == 4 and dim_intervals == [0, 3, 6, 9]:
                        # This is a dim7 chord, and potential_root is M3 below
                        # Check if potential_root's b7 is in the dim7
                        b7_of_root = (potential_root + 10) % 12
                        if b7_of_root in remaining_pcs:
                            # Force detection as 7(b9)
                            intervals_from_root = sorted((pc - potential_root) % 12 for pc in pitch_classes)
                            match_7b9 = self._match_chord_pattern(intervals_from_root, potential_root,
                                                                 active_notes, highest_note, highest_pc, lowest_pc, has_global_dominant_quality)
                            if match_7b9:
                                chord_name_7b9, score_7b9 = match_7b9
                                if '7(b9)' in chord_name_7b9 or '7' in chord_name_7b9:
                                    # Use this detection
                                    best_match = chord_name_7b9
                                    best_root_pc = potential_root
                                    best_score = score_7b9
                                    break

                if best_match and '7(b9)' in best_match:
                    break

        # Special handling for diminished chords (dim and dim7)
        # dim7 is symmetrical - any note can be root
        # Triadic dim should use bass note as root (user preference)
        # Skip this if we already detected as 7(b9) above
        if best_match and not '7(b9)' in best_match:
            is_triadic_dim = self._match_chord_type(best_match, 'diminished')
            is_dim7 = self._match_chord_type(best_match, 'diminished7')

            if is_triadic_dim or is_dim7:
                if best_root_pc != lowest_pc:
                    if is_triadic_dim:
                        # For triadic diminished, use bass note as root
                        # Reconstruct chord name with new root
                        new_root_name = self.get_note_name(lowest_pc)
                        best_match = f"{new_root_name}dim"
                        best_root_pc = lowest_pc
                    elif is_dim7:
                        # For dim7, re-detect with lowest note as root
                        intervals_from_lowest = sorted((pc - lowest_pc) % 12 for pc in pitch_classes)
                        match_from_lowest = self._match_chord_pattern(intervals_from_lowest, lowest_pc,
                                                                      active_notes, highest_note, highest_pc, lowest_pc, has_global_dominant_quality)
                        if match_from_lowest:
                            chord_name_from_lowest, score_from_lowest = match_from_lowest
                            # Only use if it's also a diminished7 chord
                            if self._match_chord_type(chord_name_from_lowest, 'diminished7'):
                                best_match = chord_name_from_lowest
                                best_root_pc = lowest_pc

        # Special handling for augmented chords (augmented and augmented7)
        # These are symmetrical - always use the lowest note as root, no inversions
        if best_match:
            if (self._match_chord_type(best_match, 'augmented') or
                self._match_chord_type(best_match, 'augmented7')):
                if best_root_pc != lowest_pc:
                    # Re-detect with lowest note as root
                    intervals_from_lowest = sorted((pc - lowest_pc) % 12 for pc in pitch_classes)
                    match_from_lowest = self._match_chord_pattern(intervals_from_lowest, lowest_pc,
                                                                  active_notes, highest_note, highest_pc, lowest_pc, has_global_dominant_quality)
                    if match_from_lowest:
                        chord_name_from_lowest, score_from_lowest = match_from_lowest
                        # Only use if it's also an augmented chord
                        if (self._match_chord_type(chord_name_from_lowest, 'augmented') or
                            self._match_chord_type(chord_name_from_lowest, 'augmented7')):
                            best_match = chord_name_from_lowest
                            best_root_pc = lowest_pc

        # CRITICAL NEW REQUIREMENT: Am7/C = C6 enharmonic conversion
        # When a minor 7th chord has its m3 in the bass, reinterpret as major 6th from the bass note
        # Example: Am7 (A C E G) with C in bass → C6 (C E G A)
        # This is the enharmonic relationship: m7 chord = 6 chord from the m3
        if best_match and best_root_pc is not None and lowest_pc != best_root_pc:
            # Check if current chord is minor7
            if self._match_chord_type(best_match, 'minor7'):
                # Check if bass note is the m3 of the root (interval 3)
                bass_interval = (lowest_pc - best_root_pc) % 12
                if bass_interval == 3:  # m3
                    # Reinterpret as major 6 chord from the bass note
                    # The intervals from the new root (bass note):
                    # Old: Am7 = A(0) C(3) E(7) G(10)
                    # New: C6  = C(0) E(4) G(7) A(9)
                    best_root_pc = lowest_pc
                    root_name = self.get_note_name(best_root_pc)
                    best_match = f"{root_name}6"

        # Add bass note if different from root (slash chord detection)
        if best_match and best_root_pc is not None and lowest_pc != best_root_pc:
            bass_interval_from_root = (lowest_pc - best_root_pc) % 12

            # ROOT DOUBLING CHECK
            # If the chord root appears MORE THAN ONCE in the voicing (is doubled/repeated), skip slash notation
            # User rule: "A G A C E → Am7" (A repeated), but "G A C E → Am/G" (A not repeated)
            # Example: A2 G2 A3 C4 E4 → Am7 (A appears at 45 and 57, doubled)
            # Example: E3 F3 A3 C4 → F/E (F appears only at 53, not doubled)
            skip_slash_for_root_doubling = False
            root_count = sum(1 for note in active_notes if note % 12 == best_root_pc)
            if root_count > 1:
                skip_slash_for_root_doubling = True
                if DEBUG:
                    print(f"DEBUG: Root pitch class {best_root_pc} appears {root_count} times (doubled) - skipping slash notation")
            elif DEBUG:
                print(f"DEBUG: Root pitch class {best_root_pc} appears only {root_count} time (not doubled) - slash chord allowed")

            # NEW REQUIREMENT: For DOMINANT chords, if bass consists only of octaves/fifths
            # of the root (like C C, C G, C G C), ignore the bass and keep the chord as-is
            # Example: G7(b9,b13) with C G C in bass → G7(b9,b13) (not G7(b9,b13)/C)
            skip_slash_for_dominant_bass = False
            is_dominant = ('7' in best_match and 'Δ7' not in best_match and 'm7' not in best_match and
                          'dim7' not in best_match and 'ø7' not in best_match)

            # For dominant chords, fifth can be above (interval 7) or below (interval 5 = P4 up = P5 down)
            # Example: G7 with C bass - C is P4 above G (interval 5) but also P5 below G
            # Also check for root (interval 0)
            if is_dominant and bass_interval_from_root in [0, 5, 7]:  # Root, P4 (5th below), or P5 in bass
                # Check if ALL bass notes are just root/5th octaves
                # Consider "bass" as the lowest octave
                lowest_note = min(active_notes)
                lowest_octave_top = lowest_note + 12
                bass_pcs = set()
                for note in active_notes:
                    if note < lowest_octave_top:
                        bass_pcs.add(note % 12)

                # Check if bass only contains root and/or 5th (P5 above or P4 above=P5 below)
                allowed_bass = {best_root_pc, (best_root_pc + 5) % 12, (best_root_pc + 7) % 12}
                if bass_pcs.issubset(allowed_bass):
                    # Bass is only octaves/fifths - skip slash notation entirely
                    skip_slash_for_dominant_bass = True

            # Determine if we should skip slash notation
            if skip_slash_for_root_doubling:
                # Chord root is doubled in the voicing - skip slash entirely (root doubling rule)
                skip_slash = True
            elif skip_slash_for_dominant_bass:
                # Dominant chord with only octaves/fifths in bass - skip slash entirely
                skip_slash = True
            else:
                # Normal slash chord logic continues below
                # For extended chords (9, 11, 13) where lowest note is in the upper structure,
                # don't show as slash chord - it's just an inversion
                # Extended chords (9, 11, 13) but NOT add9 - add9 inversions should show slash chords
                is_extended = (('9' in best_match or '11' in best_match or '13' in best_match) and
                              'add9' not in best_match)
                is_altered = ('b9' in best_match or '#9' in best_match or 'b13' in best_match or '#11' in best_match)

                # Special case: 6/9 chords with root a whole step above bass should show slash
                # Example: Bb6/9 with C in bass = Bb6/C
                is_six_nine = ('6/9' in best_match or '(6/9)' in best_match)
                if is_six_nine and bass_interval_from_root == 2:
                    # Don't skip slash for 6/9 with 9 in bass
                    skip_slash = False
                else:
                    skip_slash = (is_extended and bass_interval_from_root in [2, 5, 7, 9, 10]) or \
                                (is_altered and bass_interval_from_root in [1, 3, 6, 8])  # b9, #9, #11, b13

            # For diminished and augmented chords, never show inversions (they're symmetrical)
            # Only skip slash for dim7 and augmented (symmetrical chords)
            # Triadic diminished should use bass note as root
            is_dim7 = self._match_chord_type(best_match, 'diminished7')
            is_augmented = (self._match_chord_type(best_match, 'augmented') or
                          self._match_chord_type(best_match, 'augmented7'))
            if is_dim7 or is_augmented:
                skip_slash = True

            if not skip_slash:
                intervals_from_root = sorted((pc - best_root_pc) % 12 for pc in pitch_classes)

                # Find the best matching pattern for current chord
                best_pattern = None
                for chord_type, pattern in CHORD_PATTERNS.items():
                    if self._match_chord_type(best_match, chord_type):
                        best_pattern = pattern
                        break

                # Decide whether to simplify based on what the bass note represents
                should_simplify = True
                # Flag to prevent overriding special case decisions
                special_case_no_simplify = False
                # Initialize essential intervals
                essential_intervals = {0, 3, 4, 6, 7, 8}

                # Special case: Don't simplify for specific voicing patterns (C Bb D F G → Bb6/9/C)
                # When we have the exact pattern [0, 2, 5, 7, 10] from lowest and detecting 6/9 chord
                pitch_classes_set_for_check = sorted(set(note % 12 for note in active_notes))
                intervals_from_lowest_for_check = sorted((pc - lowest_pc) % 12 for pc in pitch_classes_set_for_check)

                # For [0, 2, 5, 7, 10] or [0, 2, 7, 10] from C, check voicing to decide Bb6/C vs Gm7/C
                if intervals_from_lowest_for_check in [[0, 2, 5, 7, 10], [0, 2, 7, 10]]:
                    # Get the notes in order from lowest to highest
                    sorted_notes = sorted(active_notes)
                    # Get the second note (first note above bass)
                    if len(sorted_notes) >= 2:
                        second_pc = sorted_notes[1] % 12
                        second_interval = (second_pc - lowest_pc) % 12

                        # If second note is Bb (10 semitones above C bass), it's Bb6/C (1st inversion voicing)
                        # C Bb D F G or C Bb D G has Bb as the second note
                        if second_interval == 10:
                            # This is Bb6/C (Gm7 or Gm in 1st inversion over C) - don't simplify
                            should_simplify = False
                            special_case_no_simplify = True
                        # Any other voicing is Gm7/C or Gm/C
                        else:
                            # Don't simplify - keep as Gm7/C or Gm/C slash chord
                            should_simplify = False
                            special_case_no_simplify = True

                # Don't simplify extended chords (9th, 11th, 13th) if bass is part of the chord
                # These are sophisticated voicings that should be preserved
                is_extended_chord = ('9' in best_match or '11' in best_match or '13' in best_match or '6/9' in best_match)
                if is_extended_chord and best_pattern and bass_interval_from_root in best_pattern:
                    should_simplify = False
                elif best_pattern and bass_interval_from_root in best_pattern:
                    # Bass is part of the chord pattern, check if it's essential or an extension
                    pass  # essential_intervals already initialized above

                # For diminished major 7th chords, all intervals are essential (don't simplify)
                if self._match_chord_type(best_match, 'diminished_major7'):
                    essential_intervals.update([6, 11])  # dim5 and M7 are essential for dimΔ7

                # For half-diminished 7th chords, all intervals are essential (don't simplify to dim slash)
                if self._match_chord_type(best_match, 'half_diminished7'):
                    essential_intervals.update([3, 6, 10])  # m3, dim5, and m7 are all essential for m7b5

                # For dominant 7th and altered dominant chords, m7 (10) is essential
                # Check for dominant chords (have M3+m7, not half-dim or minor7)
                is_dominant = (best_match.endswith('7') or '7(' in best_match or best_match.endswith('13')) and \
                              'Δ7' not in best_match and 'dim7' not in best_match and \
                              'ø7' not in best_match and 'm7' not in best_match
                if is_dominant:
                    essential_intervals.add(10)  # m7 is essential for dominant chords

                if not special_case_no_simplify:
                    if bass_interval_from_root in essential_intervals:
                        # Bass is essential (e.g., F7/A where A is the 3rd) - don't simplify
                        # EXCEPTION: For major/minor triads (but NOT add9), try simplification to see if we get sus chord
                        # Example 1: Eb major (Eb G Bb) with F → might be Eb2/G (Eb F Bb with G bass)
                        # NEVER simplify add9 chords - preserve the extension notation
                        # Example 2: Cadd9 (C E G D) with D bass → should stay as Cadd9/D, not simplify to C/D
                        if best_match and 'add9' in best_match:
                            # Never simplify add9 chords - preserve inversion notation
                            should_simplify = False
                        elif best_match and (best_match.endswith('m') or
                                         (len(best_match) <= 2 and not best_match.endswith('7') and
                                          not best_match.endswith('6'))):
                            # This is a basic triad (not add9) - allow simplification
                            # to potentially find a sus chord
                            should_simplify = True
                        else:
                            should_simplify = False
                    else:
                        # Bass is an extension (e.g., D7/C where C is the 7th) - try simplification
                        # BUT check add9 doubling rule first
                        is_add9_check = 'add9' in best_match
                        if is_add9_check:
                            # Check if 9th is doubled
                            ninth_interval_check = 2
                            ninth_pc_check = (best_root_pc + ninth_interval_check) % 12
                            bass_is_ninth_check = (lowest_pc == ninth_pc_check)
                            ninth_count_check = sum(1 for note in active_notes if note % 12 == ninth_pc_check)
                            
                            if bass_is_ninth_check and ninth_count_check > 1:
                                # 9th is in bass AND doubled - preserve add9 notation
                                should_simplify = False
                            elif bass_is_ninth_check and ninth_count_check == 1:
                                # 9th is only in bass - allow simplification
                                should_simplify = True
                            else:
                                # 9th is not in bass - preserve add9 notation
                                should_simplify = False
                        else:
                            should_simplify = True

                # Special case: Never simplify sus2 or sus4 chords
                # Example: Eb2/G should stay as Eb2/G, not simplify to Eb/G
                is_sus = best_match.endswith('2') or best_match.endswith('4') or \
                         'sus2' in best_match or 'sus4' in best_match or 'sus13' in best_match
                if is_sus:
                    should_simplify = False

                # Special case: Only preserve add9 notation if the 9th is doubled
                # Rule: If 9th appears only in bass → simplify to triad (C/D)
                #       If 9th appears in both bass and upper structure → preserve add9 (Cadd9/D)
                #       Root position add9 chords always preserve notation (Cadd9)
                # Example: D E G C (D only in bass) → C/D
                # Example: D E G C D (D doubled) → Cadd9/D
                # Example: C D E G (root position) → Cadd9 (always preserved)
                is_add9 = 'add9' in best_match
                if is_add9:
                    # Root position add9 chords always preserve notation
                    if best_root_pc == lowest_pc:
                        should_simplify = False
                    else:
                        # Slash chord - check if 9th is doubled (already checked above, but double-check here)
                        # For add9 pattern [0, 4, 7, 2], interval 2 is the 9th
                        ninth_interval = 2  # 9th is 2 semitones above root
                        ninth_pc = (best_root_pc + ninth_interval) % 12
                        
                        # Count how many times the 9th appears
                        ninth_count = sum(1 for note in active_notes if note % 12 == ninth_pc)
                        
                        # Check if bass is the 9th
                        bass_is_ninth = (lowest_pc == ninth_pc)
                        
                        if bass_is_ninth and ninth_count > 1:
                            # 9th is in bass AND doubled in upper structure - preserve add9 notation
                            should_simplify = False
                        elif bass_is_ninth and ninth_count == 1:
                            # 9th is only in bass (not doubled) - allow simplification to triad
                            should_simplify = True
                        else:
                            # 9th is not in bass - preserve add9 notation (e.g., Cadd9/E)
                            should_simplify = False

                # NEW REQUIREMENT: For 7th chords in slash notation, simplify to triad
                # if the 7TH note is not doubled (appears only once)
                # Example: Bb C E G (Bb appears once) → C/Bb
                # Example: Bb Bb C E G (Bb appears twice) → C7/Bb
                # The 7th is a weak note if only played once, so we simplify
                if not special_case_no_simplify and not is_sus and '7' in best_match and 'Δ7' not in best_match and 'm7' not in best_match and 'dim7' not in best_match:
                    # Find the 7th note (10 or 11 semitones above root)
                    seventh_pc = None
                    if (best_root_pc + 10) % 12 in pitch_classes:
                        seventh_pc = (best_root_pc + 10) % 12  # m7
                    elif (best_root_pc + 11) % 12 in pitch_classes:
                        seventh_pc = (best_root_pc + 11) % 12  # M7

                    if seventh_pc is not None:
                        # Count how many times the 7TH appears
                        seventh_count = sum(1 for note in active_notes if note % 12 == seventh_pc)
                        if seventh_count == 1:
                            # 7th appears only once - simplify to triad
                            should_simplify = True
                        else:
                            # 7th is doubled - keep as 7th chord
                            should_simplify = False

                # NEVER simplify add9 chords - preserve inversion notation
                # Final check: if add9 and 9th is doubled in bass, don't simplify
                is_add9_final = 'add9' in best_match
                skip_add9_simplify = False
                
                # DEBUG: Test 1c debugging
                debug_test1c = False
                if len(active_notes) == 5 and lowest_pc == 2:  # D in bass, 5 notes
                    test_pcs = sorted(set(n % 12 for n in active_notes))
                    if test_pcs == [0, 2, 4, 7]:  # C, D, E, G
                        d_count = sum(1 for n in active_notes if n % 12 == 2)
                        if d_count == 2:  # D doubled
                            debug_test1c = True
                            print(f"\n=== DEBUG TEST 1c: D E G C D (D doubled) ===")
                            print(f"best_match: {best_match}")
                            print(f"best_root_pc: {best_root_pc}, lowest_pc: {lowest_pc}")
                            print(f"is_add9_final: {is_add9_final}")
                            print(f"active_notes: {sorted(active_notes)}")
                            print(f"pitch_classes: {sorted(pitch_classes)}")
                
                if is_add9_final and best_root_pc != lowest_pc:
                    # Check if 9th is doubled
                    ninth_interval_final = 2
                    ninth_pc_final = (best_root_pc + ninth_interval_final) % 12
                    bass_is_ninth_final = (lowest_pc == ninth_pc_final)
                    ninth_count_final = sum(1 for note in active_notes if note % 12 == ninth_pc_final)
                    
                    if bass_is_ninth_final and ninth_count_final > 1:
                        # 9th is doubled - don't simplify, skip simplification entirely
                        should_simplify = False
                        skip_add9_simplify = True
                        if debug_test1c:
                            print(f"CHECK 1: 9th is doubled! bass_is_ninth_final={bass_is_ninth_final}, ninth_count_final={ninth_count_final}")
                            print(f"  Setting should_simplify=False, skip_add9_simplify=True")
                    elif bass_is_ninth_final and ninth_count_final == 1:
                        # 9th is only in bass - allow simplification
                        should_simplify = True
                        if debug_test1c:
                            print(f"CHECK 1: 9th only in bass. bass_is_ninth_final={bass_is_ninth_final}, ninth_count_final={ninth_count_final}")
                            print(f"  Setting should_simplify=True")
                    else:
                        # 9th is not in bass - don't simplify
                        should_simplify = False
                        skip_add9_simplify = True
                        if debug_test1c:
                            print(f"CHECK 1: 9th not in bass. bass_is_ninth_final={bass_is_ninth_final}, ninth_count_final={ninth_count_final}")
                            print(f"  Setting should_simplify=False, skip_add9_simplify=True")
                
                # Only proceed with simplification if should_simplify is True AND we're not skipping add9 simplification
                # Also check again if add9 with doubled 9th - if so, skip simplification entirely
                is_add9_before_simplify = 'add9' in best_match
                if is_add9_before_simplify and best_root_pc != lowest_pc:
                    ninth_interval_before = 2
                    ninth_pc_before = (best_root_pc + ninth_interval_before) % 12
                    bass_is_ninth_before = (lowest_pc == ninth_pc_before)
                    ninth_count_before = sum(1 for note in active_notes if note % 12 == ninth_pc_before)
                    if bass_is_ninth_before and ninth_count_before > 1:
                        # 9th is doubled - skip simplification entirely, keep add9 notation
                        skip_add9_simplify = True
                        should_simplify = False
                    elif bass_is_ninth_before and ninth_count_before == 1:
                        # 9th is only in bass - allow simplification
                        skip_add9_simplify = False
                        should_simplify = True
                    else:
                        # 9th is not in bass - skip simplification, keep add9 notation
                        skip_add9_simplify = True
                        should_simplify = False
                
                # Only simplify if all conditions are met AND we're not skipping add9 simplification
                # CRITICAL: If add9 with doubled 9th, NEVER simplify - skip this entire block
                if debug_test1c:
                    print(f"\nBEFORE SIMPLIFICATION BLOCK:")
                    print(f"  skip_add9_simplify: {skip_add9_simplify}")
                    print(f"  should_simplify: {should_simplify}")
                    print(f"  'add9' not in best_match: {'add9' not in best_match}")
                    print(f"  Condition result: {not skip_add9_simplify and should_simplify and 'add9' not in best_match}")
                
                if not skip_add9_simplify and should_simplify and 'add9' not in best_match:
                    if debug_test1c:
                        print(f"  ENTERING simplification block!")
                    # Try detecting chord without the bass note for simpler interpretation
                    # This handles cases like "D7/C" -> "D/C"
                    notes_without_bass = {note for note in active_notes if note % 12 != lowest_pc}

                    # Don't simplify if we only have 2 notes left and current is a good triad
                    # Example: E G C → C/E (don't simplify to G4/E just because G C forms a sus4 shell)
                    if len(notes_without_bass) < 3 and len(pitch_classes) == 3:
                        should_simplify = False

                    if len(notes_without_bass) >= 2 and should_simplify:
                        # Detect chord from remaining notes
                        alt_chord = self._detect_chord_simple(notes_without_bass)
                        if debug_test1c:
                            print(f"\n  INSIDE SIMPLIFICATION BLOCK:")
                            print(f"    notes_without_bass: {sorted(notes_without_bass)}")
                            print(f"    alt_chord detected: {alt_chord}")

                        if alt_chord:
                            # CRITICAL: Check if best_match is add9 with doubled 9th BEFORE any simplification
                            # This check must happen here because best_match might have been detected as add9
                            if 'add9' in best_match and best_root_pc != lowest_pc:
                                if debug_test1c:
                                    print(f"    CHECK 2: best_match contains 'add9' and root != bass")
                                ninth_interval_final_check = 2
                                ninth_pc_final_check = (best_root_pc + ninth_interval_final_check) % 12
                                bass_is_ninth_final_check = (lowest_pc == ninth_pc_final_check)
                                ninth_count_final_check = sum(1 for note in active_notes if note % 12 == ninth_pc_final_check)
                                if debug_test1c:
                                    print(f"      ninth_pc_final_check: {ninth_pc_final_check} (should be 2 for D)")
                                    print(f"      bass_is_ninth_final_check: {bass_is_ninth_final_check}")
                                    print(f"      ninth_count_final_check: {ninth_count_final_check}")
                                if bass_is_ninth_final_check and ninth_count_final_check > 1:
                                    # 9th is doubled - skip ALL simplification, keep best_match as Cadd9
                                    # Don't enter the simplification logic below
                                    alt_chord = None  # Prevent simplification by making alt_chord None
                                    if debug_test1c:
                                        print(f"      CHECK 2 RESULT: 9th is doubled! Setting alt_chord=None")
                            
                            # Only proceed with simplification logic if alt_chord is not None
                            if debug_test1c:
                                print(f"    alt_chord after check: {alt_chord}")
                            if alt_chord:
                                if debug_test1c:
                                    print(f"    PROCEEDING with simplification logic (alt_chord is not None)")
                                # Don't simplify sus2/sus4 chords to major/minor triads
                                alt_is_sus = alt_chord.endswith('2') or alt_chord.endswith('4') or \
                                            'sus2' in alt_chord or 'sus4' in alt_chord

                                # Check if current is a basic triad (just note name, or note name + accidental)
                                # Examples: C, Cm, Eb, F#, Bb
                                import re
                                current_is_basic = bool(re.match(r'^[A-G][b#]?m?$', best_match))

                                # Special case: If current is add9 and alt is sus4, check if upper structure can be sus2
                                # Example: Ebadd9 with upper structure Bb Eb F detected as Bb4 → try to re-detect as Eb2
                                current_is_add9 = 'add9' in best_match
                                if current_is_add9 and alt_is_sus and alt_chord.endswith('4'):
                                    # Check if these notes can form sus2 from the same root as current (add9)
                                    # Get the root of the current chord (e.g., Eb from Ebadd9)
                                    current_root_name = best_match.split('add')[0]
                                    # Check if alt_chord can be reinterpreted as sus2 from current root
                                    if current_root_name + '2' in [self.get_note_name(pc % 12) + '2'
                                                                   for pc in set(note % 12 for note in notes_without_bass)]:
                                        # Try to detect as sus2 from the current root
                                        # Re-detect forcing the original root
                                        upper_pcs = sorted(set(note % 12 for note in notes_without_bass))
                                        # Check if original root + sus2 pattern matches
                                        for pc in upper_pcs:
                                            if self.get_note_name(pc) == current_root_name:
                                                # Found the root, check if it forms sus2
                                                upper_intervals = sorted((n - pc) % 12 for n in upper_pcs)
                                                if upper_intervals == [0, 2, 7]:  # Perfect sus2 pattern
                                                    alt_chord = current_root_name + '2'
                                                    break

                                # Check if the alternative is simpler/better
                                # Prefer simpler chords (triads over 7ths, 7ths over extended)
                                current_complexity = self._chord_complexity(best_match)
                                alt_complexity = self._chord_complexity(alt_chord)

                                # Only preserve add9 notation if 9th is doubled (when bass is 9th)
                                # Example: D E G C (D only in bass) → C/D (simplified)
                                # Example: D E G C D (D doubled) → Cadd9/D (preserved)
                                # CRITICAL: Check add9 doubling BEFORE any other simplification logic
                                add9_handled = False
                                if current_is_add9:
                                    # Check if bass is the 9th and if it's doubled
                                    ninth_interval_simplify = 2
                                    ninth_pc_simplify = (best_root_pc + ninth_interval_simplify) % 12
                                    bass_is_ninth_simplify = (lowest_pc == ninth_pc_simplify)
                                    ninth_count_simplify = sum(1 for note in active_notes if note % 12 == ninth_pc_simplify)
                                    
                                    if bass_is_ninth_simplify and ninth_count_simplify > 1:
                                        # 9th is in bass AND doubled - preserve add9 notation, skip ALL simplification
                                        # Don't change best_match - keep it as Cadd9
                                        add9_handled = True  # Prevent all further simplification
                                        if debug_test1c:
                                            print(f"      CHECK 3: 9th doubled! bass_is_ninth_simplify={bass_is_ninth_simplify}, ninth_count_simplify={ninth_count_simplify}")
                                            print(f"        Setting add9_handled=True, best_match stays: {best_match}")
                                    elif bass_is_ninth_simplify and ninth_count_simplify == 1:
                                        # 9th is only in bass - allow simplification
                                        best_match = alt_chord
                                        add9_handled = True  # Mark as handled
                                    else:
                                        # 9th is not in bass - preserve add9 notation, skip all simplification
                                        add9_handled = True  # Prevent all further simplification
                                
                                # Only proceed with other simplification logic if add9 was NOT handled
                                # CRITICAL: If add9_handled is True, skip ALL simplification logic
                                if not add9_handled:
                                    if not current_is_add9:
                                        # If alternative is sus2 and current is add9, prefer sus2
                                        # Example: Ebadd9/G with upper Bb Eb F → prefer Eb2/G over Ebadd9/G
                                        if alt_is_sus and alt_chord.endswith('2') and current_is_add9:
                                            # Prefer sus2 over add9 for slash chord simplification
                                            best_match = alt_chord
                                        # If alternative is sus and current is a basic triad, prefer sus
                                        elif alt_is_sus and current_is_basic:
                                            # Keep the sus chord, don't use the simpler triad
                                            best_match = alt_chord
                                        # Otherwise use normal simplification logic
                                        elif alt_complexity <= current_complexity:
                                            best_match = alt_chord
                                    # If current_is_add9 and add9_handled is False, something went wrong
                                    # This shouldn't happen, but if it does, don't simplify

                # Add bass note only if we didn't skip slash notation
                bass_note_name = self.get_note_name(lowest_pc)
                if debug_test1c:
                    print(f"\nFINAL STEP:")
                    print(f"  best_match before adding bass: {best_match}")
                    print(f"  bass_note_name: {bass_note_name}")
                best_match = f"{best_match}/{bass_note_name}"
                if debug_test1c:
                    print(f"  best_match after adding bass: {best_match}")
                    print(f"=== END DEBUG TEST 1c ===\n")

        # =====================================================================
        # CHORD VALIDATION - Reject invalid or bad sounding voicings
        # =====================================================================
        # CRITICAL: Re-check M3+m3/m7+M7 filtering AFTER detection
        # The pre-detection filter checks for exact matches, but we also need to check
        # if the detected chord has interval conflicts from the bass
        # Check if bass has interval conflicts
        intervals_from_bass_final = set((pc - lowest_pc) % 12 for pc in pitch_classes)
        has_m3_and_M3_from_bass_final = (3 in intervals_from_bass_final and 4 in intervals_from_bass_final)
        has_m7_and_M7_from_bass_final = (10 in intervals_from_bass_final and 11 in intervals_from_bass_final)
        
        if best_match and best_root_pc is not None and (has_m3_and_M3_from_bass_final or has_m7_and_M7_from_bass_final):
            intervals_from_bass_check = set((pc - lowest_pc) % 12 for pc in pitch_classes)
            has_m3_and_M3_from_bass_check = (3 in intervals_from_bass_check and 4 in intervals_from_bass_check)
            has_m7_and_M7_from_bass_check = (10 in intervals_from_bass_check and 11 in intervals_from_bass_check)
            
            if has_m3_and_M3_from_bass_check or has_m7_and_M7_from_bass_check:
                # Detected chord is from bass root and has interval conflicts
                # Check if a valid chord can be formed from non-bass roots
                non_bass_pcs_check = [pc for pc in pitch_classes if pc != lowest_pc]
                if len(non_bass_pcs_check) >= 2:
                    slash_chord_valid_check = False
                    for potential_root in non_bass_pcs_check:
                        intervals_from_potential_check = sorted((pc - potential_root) % 12 for pc in pitch_classes)
                        for chord_type_check, pattern_check in CHORD_PATTERNS.items():
                            if set(pattern_check) == set(intervals_from_potential_check):
                                slash_chord_valid_check = True
                                break
                        if slash_chord_valid_check:
                            break
                    
                    if not slash_chord_valid_check:
                        # No valid chord from non-bass root - reject ANY chord (bass-root or slash)
                        return None
                    
                    # CRITICAL: Even if a valid slash chord exists, check if the interval conflicts
                    # from the bass are too severe. Some chords like Gb7(#9,#11)/C with M3+m3 from C
                    # should still be rejected because the conflicts are musically impossible.
                    # Exception: Allow if the slash chord is a clear, musically valid interpretation
                    # like DbmΔ9/C where the conflicts are resolved by the slash chord structure
                    
                    # Find the valid slash chord root and type
                    valid_slash_root = None
                    valid_slash_chord_type = None
                    for potential_root in non_bass_pcs_check:
                        intervals_from_potential_check = sorted((pc - potential_root) % 12 for pc in pitch_classes)
                        for chord_type_check, pattern_check in CHORD_PATTERNS.items():
                            if set(pattern_check) == set(intervals_from_potential_check):
                                valid_slash_root = potential_root
                                valid_slash_chord_type = chord_type_check
                                break
                        if valid_slash_root is not None:
                            break
                    
                    # CRITICAL: Check if ANY valid slash chord (or detected chord) is an altered dominant with conflicts
                    # Reject altered dominants with #9/#11 when bass has M3+m3 conflicts
                    # These are often misdetections when there are interval conflicts from bass
                    # Check both the valid slash chord type AND the detected chord
                    # CRITICAL: Reject ANY altered dominant with #9/#11 when bass has M3+m3 conflicts
                    should_reject_altered = False
                    
                    # Check valid slash chord type first (this catches the case where we find a valid slash chord)
                    if valid_slash_chord_type:
                        chord_type_str = str(valid_slash_chord_type)
                        if '#9' in chord_type_str or '#11' in chord_type_str:
                            should_reject_altered = True
                    
                    # Also check the detected chord name (catches if best_match is already a slash chord)
                    if best_match:
                        if '#9' in best_match or '#11' in best_match:
                            should_reject_altered = True
                    
                    # CRITICAL: Reject altered dominants from non-bass roots when bass has M3+m3 conflicts
                    # The issue: #9 is enharmonic with b3 (minor 3rd), so C Eb E creates confusion
                    # Rule: If bass has M3+m3 conflicts AND we detect an altered dominant from a non-bass root,
                    # reject it because the bass note shouldn't be the root of an altered dominant interpretation
                    # Example: C Eb F# A C E → Gb7(#9,#11)/C is wrong because C (with M3+m3) disqualifies Gb7
                    # Valid altered dominants should have the root in the bass or a chord tone in the bass
                    if should_reject_altered and has_m3_and_M3_from_bass_check:
                        # Check if the detected chord is from a non-bass root (slash chord)
                        # If best_root_pc != lowest_pc, we're detecting an altered dominant from a non-bass root
                        # with M3+m3 conflicts from the bass - this is invalid
                        # CRITICAL: The bass note having M3+m3 conflicts disqualifies it from being a valid
                        # bass note for an altered dominant interpretation from a different root
                        if best_root_pc != lowest_pc:
                            # Altered dominant from non-bass root with M3+m3 conflicts from bass - reject
                            # Example: C Eb F# A C E → Gb7(#9,#11)/C is wrong because C has M3+m3 conflicts
                            return None
                        # If best_root_pc == lowest_pc, the altered dominant is from the bass root
                        # This might be valid, but if bass has M3+m3 conflicts, it's still problematic
                        # However, we should be more lenient here - let it through if it's from bass root
                        # The pre-detection filter should have caught invalid bass-root interpretations
                    
                    # If detected chord is from bass root, re-detect from the valid non-bass root
                    if best_root_pc == lowest_pc:
                        if valid_slash_root is not None:
                            # Re-detect from the valid non-bass root
                            intervals_from_valid_root = sorted((pc - valid_slash_root) % 12 for pc in pitch_classes)
                            slash_match_result = self._match_chord_pattern(intervals_from_valid_root, valid_slash_root, active_notes,
                                                                          highest_note, highest_pc, lowest_pc, has_global_dominant_quality)
                            if slash_match_result:
                                slash_chord_name, slash_score = slash_match_result
                                bass_note_name = self.get_note_name(lowest_pc)
                                return f"{slash_chord_name}/{bass_note_name}"
                        
                        # If we can't re-detect, reject the bass-root interpretation
                        return None
                    else:
                        # Detected chord is already a slash chord from non-bass root
                        # Check if it matches one of the valid non-bass roots
                        # If not, reject it (it's an invalid interpretation)
                        detected_is_valid_slash = False
                        detected_chord_type = None
                        for potential_root in non_bass_pcs_check:
                            intervals_from_potential_check = sorted((pc - potential_root) % 12 for pc in pitch_classes)
                            for chord_type_check, pattern_check in CHORD_PATTERNS.items():
                                if set(pattern_check) == set(intervals_from_potential_check) and potential_root == best_root_pc:
                                    detected_is_valid_slash = True
                                    detected_chord_type = chord_type_check
                                    # Found the matching chord type - break out of inner loop
                                    break
                            if detected_is_valid_slash:
                                break
                        
                        if not detected_is_valid_slash:
                            # Detected slash chord doesn't match any valid non-bass root - reject
                            return None
                        
                        # CRITICAL: Check if the detected slash chord is an altered dominant with conflicts
                        # Reject altered dominants with #9/#11 when bass has M3+m3 conflicts
                        # This prevents misdetections like Gb7(#9,#11)/C when C has both M3 and m3
                        chord_type_str = str(detected_chord_type) if detected_chord_type else ''
                        has_sharp9_or_11_in_type = ('#9' in chord_type_str or '#11' in chord_type_str)
                        has_sharp9_or_11_in_name = best_match and ('#9' in best_match or '#11' in best_match)
                        
                        if (has_sharp9_or_11_in_type or has_sharp9_or_11_in_name) and has_m3_and_M3_from_bass_check:
                            # Altered dominants with #9/#11 when bass has M3+m3 are likely misdetections
                            return None
        
        if best_match and best_root_pc is not None:
            # Validate from the detected CHORD ROOT (not the bass note)
            # This allows valid inversions like C7/Bb while rejecting truly invalid chords
            intervals_from_root = sorted(set((pc - best_root_pc) % 12 for pc in pitch_classes))

            # VALIDATION 1: Reject chords missing the 3rd (except special cases)
            # Chords that don't need a 3rd: sus2, sus4, power chords, 5 chords
            has_third = (3 in intervals_from_root or 4 in intervals_from_root)
            is_sus_chord = 'sus' in best_match.lower()
            is_power_chord = best_match.endswith('5') and len(best_match) <= 3  # C5, F#5, etc.
            # Also check for slash chords with questionable upper structures
            is_slash_chord = '/' in best_match

            # For slash chords, also validate from bass to catch bad interpretations
            if is_slash_chord:
                intervals_from_bass = sorted(set((pc - lowest_pc) % 12 for pc in pitch_classes))
                has_third_from_bass = (3 in intervals_from_bass or 4 in intervals_from_bass)

                # Reject slash chords that are musically questionable:
                # 1. If BOTH the chord root AND the bass lack a 3rd
                if not has_third and not has_third_from_bass and not is_sus_chord and not is_power_chord:
                    return None

                # 2. If it's an add9 slash chord with very few notes (likely misinterpretation)
                # Example: "C Bb Db" → "Bbm(add9)/C" is questionable with only 3 pitch classes
                if 'add9' in best_match and len(pitch_classes) <= 3:
                    # Too few notes for a meaningful add9 slash chord - reject
                    return None
            elif not has_third and not is_sus_chord and not is_power_chord:
                # Non-slash chords: reject if missing 3rd
                # EXCEPTION 1: Allow diminished chords without 3rd (dim7 can omit m3)
                # EXCEPTION 2: Allow #11 chords without 3rd (3rd is "implied sonically" by the 9th)
                #              BUT only if interval 6 (#11) is actually present
                is_dim_chord = 'dim' in best_match.lower() or '°' in best_match
                has_sharp11_interval = 6 in intervals_from_root
                is_sharp11_chord = '#11' in best_match and has_sharp11_interval
                if DEBUG:
                    print(f"DEBUG: VALIDATION - has_third={has_third}, best_match={best_match}, is_dim_chord={is_dim_chord}, is_sharp11_chord={is_sharp11_chord}, has_sharp11_interval={has_sharp11_interval}")
                if not is_dim_chord and not is_sharp11_chord:
                    if DEBUG:
                        print(f"DEBUG: REJECTED - no 3rd and not dim/sharp11 chord")
                    return None

            # VALIDATION 2: Reject major chords with natural 11 (dissonant avoid note)
            # Major chord has M3 (4 semitones), natural 11 is perfect 4th (5 semitones)
            # This creates a harsh dissonance: M3 + P4 = m9
            # EXCEPTION 1: If the natural 11 is ONLY in the bass (like G7 with C in bass),
            # allow it - the user wants bass octaves/fifths to not affect the chord
            # EXCEPTION 2: add11 chords explicitly want the natural 11
            has_major_third = 4 in intervals_from_root
            has_natural_11 = 5 in intervals_from_root
            is_major_quality = not ('m' in best_match or 'dim' in best_match or 'sus' in best_match)
            is_add11 = 'add11' in best_match

            if has_major_third and has_natural_11 and is_major_quality and not is_add11:
                # Check if the natural 11 appears anywhere other than the lowest note
                # EXCEPTION: If P4 ONLY appears as the bass note (like G7 with C bass), allow it
                # REJECT: If P4 appears anywhere else in the voicing (like CΔ11 with F)
                p4_pc = (best_root_pc + 5) % 12  # The P4 note
                lowest_note = min(active_notes)

                # Check if P4 appears in upper structure (not just as lowest bass note)
                p4_in_upper_structure = any(note % 12 == p4_pc and note != lowest_note for note in active_notes)

                if p4_in_upper_structure:
                    # Natural 11 appears in upper structure - bad voicing, reject
                    if DEBUG:
                        print(f"DEBUG: REJECTED - major chord with natural 11 in upper structure")
                    return None
                # else: Natural 11 only as bass note - allow it

            # VALIDATION 3: Reject add9 chords missing the 5th
            # add9 chords require root, 3rd, 5th, and 9th
            # Without the 5th, it's incomplete
            is_add9 = 'add9' in best_match
            has_fifth = 7 in intervals_from_root
            if is_add9 and not has_fifth:
                if DEBUG:
                    print(f"DEBUG: REJECTED - add9 chord missing 5th")
                return None

        # IMPROVED SCALE DETECTION (v2.0):
        # For stepwise patterns spanning an octave or more, PREFER scales over chords
        # This ensures F Ionian (F G A Bb C D E F) is detected as a scale, not as chords
        # Use original_active_notes since active_notes may have been modified
        if should_check_scale_later:
            chord_span = max(original_active_notes) - min(original_active_notes)

            # Try scale detection
            scale = self.detect_scale(original_active_notes)
            if scale:
                # Scale detected!
                # EXCEPTION: If a 13th chord was detected, prefer chord over scale
                # 13th chords are 7-note chords that can look like modes
                if best_match and ('13' in best_match or 'm13' in best_match):
                    return best_match  # Prefer 13th chord over scale

                # If span >= 12 semitones (one octave+), ALWAYS prefer scale
                if chord_span >= 12:
                    return scale
                # If span < 12, prefer scale only for highly clustered patterns
                # (allows some chord interpretations for compact voicings)
                else:
                    return scale

            # No scale found - return the chord interpretation
            if DEBUG:
                print(f"DEBUG: FINAL RETURN (no scale): {best_match}")
            return best_match

        if DEBUG:
            print(f"DEBUG: FINAL RETURN: {best_match}")
        return best_match

    def _match_chord_type(self, chord_name: str, chord_type: str) -> bool:
        """
        Check if a chord name matches a chord type
        Used to find the pattern for a detected chord
        """
        if not chord_name:
            return False

        # Remove bass note if present
        if '/' in chord_name:
            chord_name = chord_name.split('/')[0]

        # Get the root and quality
        # Check 2-char note names first (like Bb, Db), then 1-char (like C, D)
        quality = None
        if len(chord_name) >= 2 and chord_name[:2] in NOTE_NAMES_FLAT + NOTE_NAMES:
            quality = chord_name[2:]
        elif len(chord_name) >= 1 and chord_name[:1] in NOTE_NAMES + NOTE_NAMES_FLAT:
            quality = chord_name[1:]
        else:
            return False

        # Map quality to chord type
        quality_map = {
            '': 'major',
            'm': 'minor',
            'dim': 'diminished',
            'aug': 'augmented',
            '2': 'sus2',
            '4': 'sus4',
            '7sus4': '7sus4',
            '7sus2': '7sus2',
            '7sus13': '7sus13',
            'sus13': 'sus13',
            'Δ7': 'major7',
            'Δ7#5': 'major7#5',
            'm7': 'minor7',
            'mΔ7': 'minor_major7',
            'mΔ7(9)': 'minor_major9',
            '7': 'dominant7',
            'dim7': 'diminished7',
            'dimΔ7': 'diminished_major7',
            'ø7': 'half_diminished7',
            '9': 'dominant9',
            '11': 'dominant11',
            '13': 'dominant13',
            'Δ9': 'major9',
            'm9': 'minor9',
            'Δ11': 'major11',
            'Δ7#11': 'major7#11',
            'm11': 'minor11',
            'Δ13': 'major13',
            'Δ13#11': 'major13#11',
            'm13': 'minor13',
            '7alt': 'altered',
            '5': '5',
            '6': '6',
            '6/9': '6_9',
            'm6': 'minor6',
            'm6/9': 'minor6_9',
            'add9': 'add9',
            'add11': 'add11',
        }

        # Add patterns for shell voicings
        if quality == '13':
            # Could be any 13 variant
            return chord_type in ['dominant13', '13_shell', '13_no5_no11', '13_no5']

        return quality_map.get(quality) == chord_type

    def _detect_chord_simple(self, active_notes: Set[int]) -> Optional[str]:
        """
        Simplified chord detection for slash chord analysis
        Returns just the chord name without bass note
        """
        if len(active_notes) < 2:
            return None

        pitch_classes = sorted(set(note % 12 for note in active_notes))
        if len(pitch_classes) < 2:
            return None

        highest_note = max(active_notes)
        highest_pc = highest_note % 12
        lowest_note = min(active_notes)
        lowest_pc = lowest_note % 12

        # GLOBAL dominant quality check
        has_global_dominant_quality = False
        for potential_root in pitch_classes:
            m3_above = (potential_root + 4) % 12
            m7_above = (potential_root + 10) % 12
            if m3_above in pitch_classes and m7_above in pitch_classes:
                has_global_dominant_quality = True
                break

        best_match = None
        best_score = 0.0

        for root_pc in pitch_classes:
            intervals = sorted((pc - root_pc) % 12 for pc in pitch_classes)
            match_result = self._match_chord_pattern(intervals, root_pc, active_notes, highest_note, highest_pc, lowest_pc, has_global_dominant_quality)

            if match_result:
                chord_name, score = match_result
                if score > best_score:
                    best_score = score
                    best_match = chord_name

        return best_match

    def _chord_complexity(self, chord_name: str) -> int:
        """
        Calculate complexity of a chord for slash chord simplification
        Lower number = simpler chord (preferred)

        Hierarchy:
        - Triads (C, Cm, Cdim, Caug): 1
        - 7th chords (C7, Cmaj7, Cm7): 2
        - 9th chords (C9, Cmaj9): 3
        - 11th chords (C11, Cmaj11): 4
        - 13th chords (C13, Cmaj13): 5
        - Add chords (Cadd9, C6add4): 3
        """
        if not chord_name:
            return 999

        # Remove bass note if present
        if '/' in chord_name:
            chord_name = chord_name.split('/')[0]

        # Check complexity based on chord extensions
        if '13' in chord_name:
            return 5
        elif '11' in chord_name:
            return 4
        elif '9' in chord_name or '6/9' in chord_name:
            return 3
        elif 'add' in chord_name or '6' in chord_name:
            return 3
        elif '7' in chord_name or 'Δ7' in chord_name or 'ø7' in chord_name:
            return 2
        else:
            # Triads (major, minor, dim, aug, sus)
            return 1

    def _match_chord_pattern(self, intervals: List[int], root_pc: int,
                            active_notes: Set[int],
                            highest_note: Optional[int] = None, highest_pc: Optional[int] = None,
                            lowest_pc: Optional[int] = None, has_global_dominant_quality: bool = False) -> Optional[Tuple[str, float]]:
        """
        Match intervals against chord patterns with jazz-aware scoring

        Improved Algorithm for Jazz Voicings:
        1. ESSENTIAL INTERVALS: Must have 3rd and/or 7th (defines chord quality)
        2. OPTIONAL INTERVALS: Root and 5th can be omitted (common in jazz)
        3. WEIGHTED SCORING: Essential notes count more than optional notes
        4. PENALTY REDUCTION: No harsh penalty for missing root/5th

        Returns:
            Tuple of (chord_name, score) or None
            Score is higher for better matches (0-100+ scale)
        """
        best_match = None
        best_score = 0.0

        # Count unique pitch classes in input (not total MIDI notes with octave duplicates)
        input_pitch_class_count = len(set(note % 12 for note in active_notes))
        intervals_set = set(intervals)

        DEBUG_PATTERN = False  # Debug pattern matching

        for chord_type, pattern in CHORD_PATTERNS.items():
            pattern_set = set(pattern)

            # Calculate matching notes
            matched_intervals = pattern_set & intervals_set
            matched_count = len(matched_intervals)
            extra_intervals = intervals_set - pattern_set
            extra_count = len(extra_intervals)
            missing_intervals = pattern_set - intervals_set
            missing_count = len(missing_intervals)

            # Get essential and optional intervals for this chord type
            essential = set(ESSENTIAL_INTERVALS.get(chord_type, []))
            optional = set(OPTIONAL_INTERVALS.get(chord_type, []))

            if DEBUG_PATTERN and chord_type == 'diminished7_no_m3':
                print(f"      Found diminished7_no_m3! pattern={pattern}, matched={matched_count}, missing={missing_count}, extra={extra_count}")
                print(f"      essential={essential}, optional={optional}")

            # Check if essential intervals are present (CRITICAL for jazz)
            essential_matched = essential & matched_intervals
            essential_missing = essential - matched_intervals

            if DEBUG_PATTERN and chord_type == 'diminished7_no_m3':
                print(f"      essential_matched={essential_matched}, essential_missing={essential_missing}")

            # For altered dominants with specific tensions (#11, #9), require ALL essential intervals
            # This prevents 7b9#11 from matching when #11 is missing
            if chord_type in ['7b9#11', '7#9#11', '7#9#11_shell',
                             '7b9#11_shell', '7b9#11_no3'] and len(essential_missing) > 0:
                # Missing essential intervals for specific altered chord - skip
                if DEBUG_PATTERN and chord_type == 'diminished7_no_m3':
                    print(f"      SKIPPED: specific altered chord with missing essential")
                continue

            # 9 chords MUST have ALL essential intervals (3rd AND 7th)
            # This prevents add9 chords from being detected as 9 chords
            if chord_type in ['major9', 'minor9', 'dominant9', 'minor_major9', 'minor_major9_no5'] and len(essential_missing) > 0:
                # Missing essential interval (missing 3rd or 7th) - this is add9, not a 9 chord
                if DEBUG_PATTERN and chord_type == 'diminished7_no_m3':
                    print(f"      SKIPPED: 9 chord missing essential (probably add9)")
                continue

            # NOTE: Interval conflict checking (M3+m3, M7+m7) is now done globally from bass
            # at the start of detect_chord() to allow valid slash chords like DbmΔ9/C

            # Must have at least ONE essential interval (unless it's a simple triad with 2+ notes)
            if len(essential) > 0 and len(essential_matched) == 0:
                # No essential intervals matched - skip this chord type
                if DEBUG_PATTERN and chord_type == 'diminished7_no_m3':
                    print(f"      SKIPPED: no essential intervals matched")
                continue

            # If we have essential intervals, require at least 2 total matched notes
            if matched_count < 2:
                if DEBUG_PATTERN and chord_type == 'diminished7_no_m3':
                    print(f"      SKIPPED: matched_count < 2")
                continue

            # IMPROVED SCORING FOR JAZZ VOICINGS:

            # 1. Essential interval bonus (PRIMARY FACTOR for jazz)
            # Having the 3rd and 7th is more important than percentage match
            essential_score = 0.0
            if len(essential) > 0:
                # Score based on how many essential intervals we have
                essential_percentage = len(essential_matched) / len(essential)
                essential_score = essential_percentage * 60.0  # Up to 60 points for all essential notes
            else:
                # For chords without defined essential intervals, use basic matching
                essential_score = 30.0

            # 2. Percentage of matching notes (secondary factor)
            # This helps distinguish between similar chord types
            percentage_match = 0.0
            if input_pitch_class_count > 0:
                percentage_match = (matched_count / input_pitch_class_count) * 40.0  # Up to 40 points

            # 3. Highest note matching bonus
            highest_note_bonus = 0.0
            if highest_pc is not None:
                highest_interval = (highest_pc - root_pc) % 12
                if highest_interval in pattern_set:
                    highest_note_bonus = 10.0

            # 4. Completeness bonus - prefer exact matches
            completeness_bonus = 0.0
            if missing_count == 0 and extra_count == 0:
                # Perfect match - all pattern notes present, no extra notes
                completeness_bonus = 30.0  # Increased to strongly prefer exact matches
                # Extra bonus for perfect matches on altered dominants
                if chord_type in ['7b13_no5', '7b9b13_no5', '7#9b13_no5', '7b9#11_no5',
                                 '7b9', '7#9', '7b13', '7b9b13', '7#9b13', '7#11b13',
                                 '7b9#11', '7#9#11']:
                    completeness_bonus = 60.0  # Even higher for altered dominants
                # Extra bonus for diminished major 7th (rare chord, should be preferred when exact match)
                if chord_type == 'diminished_major7':
                    completeness_bonus = 500.0  # Very high to beat m6 interpretations
                # Extra bonus for half-diminished7 (common jazz chord, should beat minor slash chords and dim triads)
                if chord_type == 'half_diminished7':
                    completeness_bonus = 700.0  # Extremely high to beat Ebm/C and Ddim/C interpretations
                # Extra bonus for major7(6/9) to beat simpler 6/9 interpretations
                if chord_type == 'major7_6_9':
                    completeness_bonus = 200.0  # High bonus to prefer maj7(6/9) over 6/9
            elif missing_count == 0:
                # All pattern notes present (extensions allowed)
                completeness_bonus = 10.0

            # 4b. Major 7th bonus - chords with M7 in their PATTERN should beat add9 interpretations
            # User rule: "ANY chord with a M7 (interval 11) automatically preferred over add9"
            # Applied to all M7 chords regardless of root position
            # Combined with root_in_bass_bonus to balance root position vs M7 quality
            major_seventh_bonus = 0.0
            # Check if: pattern has M7, actual intervals have M7, not add9
            if 11 in pattern_set and 11 in intervals_set and chord_type not in ['add9', 'minor_add9']:
                # M7 chord - boost to beat add9 interpretations from same root
                major_seventh_bonus = 50.0  # Moderate boost to prefer M7 over add9

            # 5. Penalties (REDUCED for jazz)
            # Extra notes penalty (notes not in chord pattern)
            extra_penalty = extra_count * 3.0

            # Missing notes penalty (JAZZ-AWARE)
            missing_penalty = 0.0

            # Check what's missing
            optional_missing = optional & missing_intervals
            required_missing = missing_intervals - optional - essential  # Notes that aren't essential or optional

            # Missing essential intervals (3rd, 7th) - HEAVY penalty
            if len(essential_missing) > 0:
                missing_penalty += len(essential_missing) * 40.0  # Very important!

            # Missing optional intervals (root, 5th) - LIGHT penalty or none
            # In jazz, missing root/5th is perfectly acceptable
            missing_penalty += len(optional_missing) * 1.0  # Minimal penalty

            # Missing other required intervals (not essential, not optional) - MEDIUM penalty
            missing_penalty += len(required_missing) * 8.0

            # 6. Rootless voicing bonus
            # If root is missing but we have 3rd and 7th, give bonus (common jazz voicing)
            rootless_bonus = 0.0
            if 0 in missing_intervals and len(essential_matched) == len(essential) and len(essential) >= 2:
                rootless_bonus = 15.0  # Reward rootless voicings with all essential notes

            # 7. Root in bass bonus (for root position preference)
            # If the root IS the lowest note, give bonus
            root_in_bass_bonus = 0.0
            if root_pc == lowest_pc and 0 in matched_intervals:
                # Root position bonus - balanced to prefer root position without breaking inversions
                # This ensures root position chords (like Cadd11) beat slash alternatives (like FΔ7/C)
                # but still allows proper inversion detection (like Cadd9/E)
                root_in_bass_bonus = 60.0

                # BIGGER bonus for extended chords (9, 11, 13) with root in bass
                # These complex chords need strong root indication
                # EXCLUDE: sus chords (not true extensions) and 6/9 chords (6th chords, not 13th)
                # ONLY apply if chord is a good match (missing at most 1 interval)
                # IMPORTANT: The defining extension (9/11/13) must be present!
                is_sus_type = 'sus' in chord_type
                is_six_nine = '6_9' in chord_type or '6/9' in chord_type
                is_true_extended = (chord_type in ['dominant9', 'dominant11', 'dominant13',
                                                    'major9', 'major11', 'major13',
                                                    'minor9', 'minor11', 'minor13',
                                                    'minor_major9', 'half_diminished11'] or
                                   chord_type.startswith('minor9') or chord_type.startswith('minor11') or chord_type.startswith('minor13'))

                # Check if the defining extension interval is actually present
                has_9th = 2 in matched_intervals
                has_11th = 5 in matched_intervals
                has_13th = 9 in matched_intervals
                extension_present = True  # Default for non-extended chords
                if '9' in chord_type and not '11' in chord_type and not '13' in chord_type:
                    extension_present = has_9th
                elif '11' in chord_type and not '13' in chord_type:
                    extension_present = has_11th  # 11th chords should have 11th
                elif '13' in chord_type:
                    extension_present = has_13th  # 13th chords should have 13th

                if not is_sus_type and not is_six_nine and is_true_extended and missing_count <= 1 and extension_present:
                    root_in_bass_bonus += 200.0  # Extra bonus for extended chords

                # Special bonus for diminished7 chords when root is in bass
                # Since all 4 notes in dim7 are equivalent, prefer the bass note as root
                # Only apply when it's a good match to avoid false positives
                is_dim7 = chord_type in ['diminished7', 'diminished7_no_b5', 'diminished7_no_m3']
                if is_dim7 and missing_count <= 1 and extra_count == 0:
                    root_in_bass_bonus += 500.0  # Strong preference for bass note as root

            # 8. Characteristic interval bonus (dim5, aug5, altered tensions)
            # Chords with unusual intervals are more specific and should be preferred
            characteristic_bonus = 0.0
            if 6 in matched_intervals or 8 in matched_intervals:
                # Has dim5 or aug5 - more characteristic than perfect 5th
                characteristic_bonus = 10.0

            # Additional bonus for altered dominants with multiple tensions
            if chord_type in ['7#11_shell', '7#11_no3', '7#9#11_shell',
                             '7b9#11_shell', '7b9#11_no3']:
                # Altered dominant shell voicings - boost to compete with simpler chords
                # These are sophisticated jazz voicings that should be preferred when present
                # Need strong bonus to overcome missing 3rd penalty
                characteristic_bonus += 50.0

            # 9. Dominant quality detection (M3 + m7 present)
            # When we have both M3 (4) and m7 (10), this is dominant quality
            # Strongly penalize 6th chord interpretations in this case
            # Use GLOBAL check (any root forms dominant) OR local check (this root forms dominant)
            dominant_quality_adjustment = 0.0
            has_major_third = 4 in intervals_set
            has_minor_seventh = 10 in intervals_set
            has_dominant_quality = has_global_dominant_quality or (has_major_third and has_minor_seventh)

            # HUGE bonus for DOMINANT chords with root in bass OCTAVE (NEW REQUIREMENT)
            # This handles cases like G7(b9,b13) with C G C in bass where G is only in bass
            # Without this, F7(#11) might score higher because F appears in upper structure
            # IMPORTANT: Only apply when bass consists primarily of root/5ths (not many different notes)
            # This prevents overriding bad voicing detection (e.g., Cmaj7(9,11))
            is_dominant_chord = ('7' in chord_type and 'm7' not in chord_type and
                                'Δ7' not in chord_type and 'maj7' not in chord_type and
                                'dim7' not in chord_type and 'ø7' not in chord_type and
                                'half_diminished' not in chord_type)
            if is_dominant_chord and has_major_third and has_minor_seventh and 0 in matched_intervals:
                # Check if root is in bass octave AND bass is simple (only root/5ths)
                lowest_note = min(active_notes)
                lowest_octave_top = lowest_note + 12
                root_in_bass_octave = any(note % 12 == root_pc and note < lowest_octave_top for note in active_notes)

                # Get bass pitch classes
                bass_pcs = set(note % 12 for note in active_notes if note < lowest_octave_top)
                allowed_bass = {root_pc, (root_pc + 5) % 12, (root_pc + 7) % 12}
                bass_is_simple = bass_pcs.issubset(allowed_bass) and len(bass_pcs) <= 2

                if root_in_bass_octave and bass_is_simple:
                    # This is a dominant chord with root in bass octave AND simple bass - strongly prefer it!
                    root_in_bass_bonus += 300.0  # Huge bonus to beat other interpretations

            if has_dominant_quality:
                # This is dominant quality (either from this root or from another root in the chord)
                if chord_type.startswith('6') or chord_type.startswith('minor6') or chord_type == 'diminished7' or chord_type == 'diminished':
                    # Penalize 6th chord, m6, and dim interpretations when dominant quality is present
                    dominant_quality_adjustment = -500.0  # VERY heavy penalty to beat m6 slash chord bonuses
                elif (chord_type.startswith('13') or chord_type.startswith('dominant') or
                      chord_type == 'dominant7' or chord_type.startswith('7') or chord_type.startswith('9')):
                    # Bonus for dominant chord interpretations (7, 9, 13, dominant, etc.)
                    if chord_type == 'dominant7' and missing_count == 0 and extra_count == 0:
                        # Perfect match for dominant7 with dominant quality - HUGE bonus
                        dominant_quality_adjustment = 600.0
                    elif chord_type == '7b9_no5' and missing_count == 0 and extra_count == 0:
                        # Perfect match for 7b9_no5 with dominant quality - HUGE bonus
                        dominant_quality_adjustment = 600.0
                    else:
                        dominant_quality_adjustment = 50.0

            # 10. Special pattern bonuses for specific note groupings
            special_pattern_bonus = 0.0

            # Special case #1: C E Ab Bb → C7(b13)
            # Exact pattern [0, 4, 8, 10] as 7b13_no5 should be strongly preferred
            if chord_type == '7b13_no5' and intervals == [0, 4, 8, 10]:
                special_pattern_bonus = 100.0  # Strong boost for this exact pattern

            # Special case #1b: G7(b9,b13) - G F Ab Cb Eb
            # Exact pattern [0, 1, 4, 8, 10] as 7b9b13_no5
            if chord_type == '7b9b13_no5' and intervals == [0, 1, 4, 8, 10]:
                special_pattern_bonus = 150.0  # Strong boost for this exact pattern

            # Special case #1c: G7(#9,b13) - G F Bb Cb Eb
            # Exact pattern [0, 3, 4, 8, 10] as 7#9b13_no5
            if chord_type == '7#9b13_no5' and intervals == [0, 3, 4, 8, 10]:
                special_pattern_bonus = 150.0  # Strong boost for this exact pattern

            # Special case #1d: C7(b9,#11) - C Bb Db E F#
            # Exact pattern [0, 1, 4, 6, 10] as 7b9#11_no5
            if chord_type == '7b9#11_no5' and intervals == [0, 1, 4, 6, 10]:
                special_pattern_bonus = 400.0  # Very strong boost to beat 13#11 interpretations

            # Special case #1e: C13(b9) - C Db E G A Bb
            # Exact pattern [0, 1, 4, 7, 9, 10] as 13b9
            if chord_type == '13b9' and intervals == [0, 1, 4, 7, 9, 10]:
                special_pattern_bonus = 500.0  # Very strong boost to beat regular C13

            # Special handling for m6 slash chord pattern: bass + [1, 7, 10] = X Xb/bass
            # Example: C Bb Db G from C has intervals [0, 1, 7, 10], should be Bbm6/C
            # BUT: Don't boost m6 if we have dominant quality (M3 + m7 present)
            pitch_classes_set_special = sorted(set(note % 12 for note in active_notes))
            intervals_from_lowest_special = sorted((pc - lowest_pc) % 12 for pc in pitch_classes_set_special)
            if intervals_from_lowest_special == [0, 1, 7, 10] and not has_global_dominant_quality:  # Specific m6 slash pattern
                # Check if current interpretation is from a note other than bass
                # and has m3 + M6 (minor6 quality)
                if chord_type in ['minor6', 'minor6_no5', 'minor6_9_no5'] and root_pc != lowest_pc:
                    special_pattern_bonus = 1500.0  # Extremely strong boost for this exact case

            # Penalize triadic diminished when we have 4+ notes (probably m6 or other chord)
            unique_pcs_for_dim_check = len(set(note % 12 for note in active_notes))
            if chord_type == 'diminished' and unique_pcs_for_dim_check >= 4:
                special_pattern_bonus = -1000.0  # Very strongly penalize dim triads with extra notes

            # Special case #1e: C E A → C6 (not Am/C)
            # Prefer 6th chord interpretation over minor triad inversion when root is in bass
            if chord_type in ['6_no5', '6'] and root_pc == lowest_pc and intervals == [0, 4, 9]:
                special_pattern_bonus = 100.0  # Strong boost to prefer 6th over minor inversion

            # Special case #1f: add9 chords - boost perfect matches to prefer over simple triads
            # Example: C D E G should be Cadd9, not C (major triad)
            # Example: D E G C (span < octave) should be Cadd9/D, not C/D or D9sus
            if chord_type == 'add9' and missing_count == 0 and extra_count == 0:
                # Perfect add9 match - give bonus to beat simple triad interpretations
                # Start with high base bonus to ensure add9 beats major triad
                special_pattern_bonus = 200.0  # High boost to prefer add9 over major triad
                # Check if this is a slash chord (root != bass)
                if root_pc != lowest_pc:
                    # Check if this could be 9sus from the bass
                    intervals_from_lowest_check = sorted((pc - lowest_pc) % 12 for pc in set(note % 12 for note in active_notes))
                    if intervals_from_lowest_check == [0, 2, 5, 10]:
                        # This is the 9sus pattern from bass
                        # Check if the add9 interpretation has a complete major/minor triad (M3 or m3 + P5)
                        # For add9: root, M3, P5, 9
                        has_major_third = (4 in intervals)  # M3 from root
                        has_minor_third = (3 in intervals)  # m3 from root
                        has_perfect_fifth = (7 in intervals)  # P5 from root

                        if (has_major_third or has_minor_third) and has_perfect_fifth:
                            # Has M3/m3 and P5 - BUT check if all triad tones are actually present
                            # We need root + 3rd + 5th all present in the chord
                            # The intervals list is from the add9 root, so if 0, 3/4, and 7 are all present, it's complete
                            triad_complete = (0 in intervals) and (3 in intervals or 4 in intervals) and (7 in intervals)

                            if triad_complete:
                                # ALL three triad notes present - strong triadic center
                                # Example: D E G C = Cadd9 has C(0) E(4) G(7) all present
                                # Check if bass is part of the triad (not just the 9th)
                                # Triad intervals from root: [0, 3/4, 7]
                                bass_interval_from_root = (lowest_pc - root_pc) % 12
                                bass_is_triad_tone = bass_interval_from_root in [0, 3, 4, 7]

                                if not bass_is_triad_tone:
                                    # Bass is NOT part of the triad (it's the 9th)
                                    # Key: check interval from bass to highest note
                                    highest_interval_from_bass = (max(active_notes) - min(active_notes))

                                    if highest_interval_from_bass < 12:
                                        # All within octave from bass - complete triad with added 9th in bass
                                        # D E G C: D to C = 10 semitones (minor 7th) < 12 → Cadd9/D
                                        special_pattern_bonus = 6200.0  # Beat 9sus when span >= 12 (6000 + base)
                                    else:
                                        # Spread beyond octave from bass - prefer 9sus interpretation
                                        # C Bb D F: C to F (octave up) >= 12 → loses to C9sus
                                        special_pattern_bonus = 150.0  # Lose to 9sus
                                else:
                                    # Bass IS part of the triad - less clear slash chord
                                    special_pattern_bonus = 4200.0  # Might lose to 9sus
                            else:
                                # Triad incomplete - don't strongly prefer this interpretation
                                special_pattern_bonus = 150.0
                        else:
                            # No triad - don't boost
                            special_pattern_bonus = 150.0
                    else:
                        # Not a 9sus pattern from bass - standard add9 boost
                        special_pattern_bonus = 200.0  # High boost to prefer add9
                else:
                    # Root in bass - standard add9 boost
                    special_pattern_bonus = 200.0  # High boost to prefer add9

            # Special case #1f0: minor_add9 perfect match should beat minor triad inversions
            # Example: G C D Eb should be Cmadd9/G, not Cm/G
            if chord_type == 'minor_add9' and missing_count == 0 and extra_count == 0:
                # Perfect match - boost to beat minor triad with inversion bonus (+35.0)
                special_pattern_bonus = 50.0  # Enough to beat Cm inversion bonus plus buffer

            # Special case #1f1: m6 slash chords should beat dim interpretations
            # Example: C Bb Db G = Bbm6/C (not Gdim/C)
            # Specific pattern: when intervals are [0, 2, 3, 9] (m6_no5 with added 9) from root with different bass
            # BUT: Don't boost m6 if we have dominant quality (M3 + m7 present)
            if chord_type in ['minor6', 'minor6_no5', 'minor6_9', 'minor6_9_no5'] and root_pc != lowest_pc and not has_global_dominant_quality:
                # This is a slash chord with m6 quality - boost heavily to beat dim
                unique_pcs_m6_check = len(set(note % 12 for note in active_notes))
                if 3 in intervals_set and 9 in intervals_set and unique_pcs_m6_check == 4:  # m3 + M6 present, exactly 4 notes
                    # Extra strong boost for this specific pattern
                    if intervals == [0, 2, 3, 9]:  # Exact pattern like Bbm6 with added 9
                        special_pattern_bonus = 600.0  # Extremely strong boost for exact m6 pattern
                    else:
                        special_pattern_bonus = 400.0  # Very strong boost for m6 slash chords (4 notes only)

            # Special case #1f2: half-diminished7 should beat 7#11 when it's a perfect match
            # Example: Ab Cb D F# should be Abø7, not Ab7#11
            if chord_type == 'half_diminished7' and intervals == [0, 3, 6, 10]:
                if missing_count == 0 and extra_count == 0:
                    special_pattern_bonus = 180.0  # Beat 7#11 interpretations

            # Special case #1g: sus2/sus4 chords - boost when detected
            # This ensures sus chords are preferred over triads when the sus intervals are present
            # Only boost if it's a good match (all essential intervals present AND pattern matches well)
            # BUT don't boost sus4 if it can also be sus2 from a different root
            if (chord_type in ['sus2', 'sus4'] and root_pc == lowest_pc and
                len(essential_missing) == 0 and missing_count <= 1 and extra_count == 0):
                # Check if we already set a bonus/penalty for sus2 vs sus4 preference
                if special_pattern_bonus == 0.0:
                    # No preference set yet - give general sus chord boost
                    special_pattern_bonus = 80.0  # Boost sus chords in root position

            # Special case #2: Major extended chords (maj7#11, maj9#11, maj13#11)
            # These should beat altered dominants when all notes are present AND #11 is present
            if chord_type in ['major7#11', 'major7#11_no5', 'major9#11', 'major13#11']:
                # Only boost if #11 (6) is actually present
                if 6 in intervals_set:
                    # Perfect match gets massive bonus
                    if missing_count == 0 and extra_count == 0:
                        special_pattern_bonus = 250.0  # Beat all altered dominants
                    # Even without perfect match, boost significantly
                    elif missing_count <= 1:
                        special_pattern_bonus = 150.0

            # Special case #2b: F A B E → F maj7#11 (not B7#11)
            # Exact pattern [0, 4, 6, 11] as major7#11_no5
            if chord_type == 'major7#11_no5' and intervals == [0, 4, 6, 11]:
                special_pattern_bonus = 300.0  # Very strong boost to beat B7#11

            # Special case #2c: 6/9 chords should beat m11 interpretations but lose to maj7(6/9)
            # ONLY apply this bonus when root is in bass AND M6 (9) is present
            # Without M6, it's not a 6/9 chord - penalize heavily
            if chord_type in ['6_9', '6_9_no5']:
                if 9 in intervals_set and 2 in intervals_set and root_pc == lowest_pc:
                    if missing_count == 0 and extra_count == 0:
                        special_pattern_bonus = 9000.0  # Beat Am11 (8000) but lose to maj7(6/9) (10000)
                    elif missing_count <= 1:
                        special_pattern_bonus = 220.0
                elif 9 not in intervals_set:
                    # No M6 means this is NOT a 6/9 chord - heavily penalize
                    special_pattern_bonus = -300.0
            elif chord_type == '6_9_no3':
                if 9 in intervals_set and 2 in intervals_set and root_pc == lowest_pc:
                    if missing_count == 0 and extra_count == 0:
                        special_pattern_bonus = 290.0
                    elif missing_count <= 1:
                        special_pattern_bonus = 220.0

            # Special case #2c2: minor6/9 chords should beat major6/9 when m3 is present
            if chord_type in ['minor6_9', 'minor6_9_no5']:
                if 9 in intervals_set and 2 in intervals_set and 3 in intervals_set and root_pc == lowest_pc:
                    if missing_count == 0 and extra_count == 0:
                        special_pattern_bonus = 9500.0  # Beat major 6/9 (9000) when m3 is clearly present

            # Special case #2d: major7(6/9) should beat m11 interpretations and simpler chords
            # ONLY when root is in bass (to avoid breaking Cm11 quintal voicings)
            if chord_type == 'major7_6_9':
                if missing_count == 0 and extra_count == 0 and root_pc == lowest_pc:
                    special_pattern_bonus = 10000.0  # Huge bonus to beat Am11 (8000) and all other interpretations
                elif 9 not in intervals_set:
                    special_pattern_bonus = -300.0

            # Special case #2c2: minor6 chords should beat m7b5/half-diminished interpretations
            # When we have m3 + M6, prefer m6 over m7b5
            # BUT: Don't apply for 3-note chords (could be diminished from another root)
            # ONLY apply to EXACTLY 4-note chords to avoid breaking 13#11 and other extended chords
            unique_pcs = len(set(note % 12 for note in active_notes))
            if 3 in intervals_set and 9 in intervals_set and unique_pcs == 4:  # m3 + M6 present, exactly 4 notes
                if chord_type in ['minor6', 'minor6_no5', 'minor6_9', 'minor6_9_no5']:
                    # Extra bonus for actual m6 chord types
                    if missing_count == 0 and extra_count == 0:
                        special_pattern_bonus = 450.0  # Beat m7b5 and dim interpretations strongly
                    elif missing_count <= 1 and extra_count <= 2:
                        special_pattern_bonus = 410.0  # Beat m7b5 and dim interpretations
                else:
                    # General bonus for any chord with m3 + M6 intervals
                    special_pattern_bonus = 380.0  # Boost m3+M6 combinations over dim

            # Special case #2d: 13th chord shells should beat major7#11 from different roots
            # When root is in bass and we have dominant quality (M3 + m7 + 13)
            if chord_type in ['13_shell', '13_no5_no11', '13_no5'] and root_pc == lowest_pc:
                # Check if we have the essential intervals for 13 chord: M3, m7, 13
                if 4 in intervals_set and 10 in intervals_set and 9 in intervals_set:
                    if missing_count == 0 and extra_count == 0:
                        special_pattern_bonus = 250.0  # Beat major7#11 from other roots
                    elif missing_count <= 1:
                        special_pattern_bonus = 180.0

            # Special case #2e: E A Bb D → Em7b5(11) (specific voicing with A as 2nd note)
            # Check if this is the specific voicing: E in bass, A as 2nd note, pattern [0, 5, 6, 10]
            if chord_type == 'half_diminished11_no3' and intervals == [0, 5, 6, 10]:
                # Check voicing - A (interval 5) must be the second note above E bass
                sorted_notes = sorted(active_notes)
                if len(sorted_notes) >= 2 and root_pc == lowest_pc:
                    second_pc = sorted_notes[1] % 12
                    second_interval = (second_pc - lowest_pc) % 12
                    if second_interval == 5:  # A is second note above E
                        special_pattern_bonus = 300.0  # Very strong boost for this specific voicing

            # Calculate intervals from lowest note (needed for multiple special cases below)
            pitch_classes_set = sorted(set(note % 12 for note in active_notes))
            intervals_from_lowest = sorted((pc - lowest_pc) % 12 for pc in pitch_classes_set)

            # Special case #2f: Dominant 7#11 and 13#11 voicings should beat other interpretations
            if chord_type in ['7#11_no5', '7#11_no3_no5', '13#11_no3_no5', '13#11_no9_no5', '13#11_no5'] and root_pc == lowest_pc:
                if 10 in intervals_set and 6 in intervals_set:  # m7 and #11 present
                    if missing_count == 0 and extra_count == 0:
                        special_pattern_bonus = 250.0  # Beat other interpretations
                    elif missing_count <= 1:
                        special_pattern_bonus = 180.0

            # Special case #2g: minor11 chords beat scale interpretations
            if chord_type in ['minor11', 'minor11_no5', 'minor11_no9', 'minor11_shell']:
                if missing_count == 0 and extra_count == 0:
                    special_pattern_bonus = 8000.0  # Huge bonus to beat scale detection (6000), but lose to Cmaj7(6/9) (10000)

            # Special case #2h: 9sus and 13sus chords with root in bass beat slash chord interpretations
            if chord_type in ['9sus', '9sus_with5', '13sus', '13sus_with5']:
                if missing_count == 0 and extra_count == 0 and root_pc == lowest_pc:
                    # Root in bass - check span from bass to highest note
                    highest_interval_from_bass = (max(active_notes) - min(active_notes))
                    if highest_interval_from_bass >= 12:
                        # Spread beyond octave from bass - strong 9sus voicing
                        # C Bb D F: C to F (octave up) >= 12 → C9sus
                        special_pattern_bonus = 6400.0  # Beat add9/bass within octave (6200 + base)
                    else:
                        # Within octave from bass - weaker, let add9 triad interpretation win
                        # C Bb D F: if all within octave from C, might be ambiguous
                        special_pattern_bonus = 150.0  # Lose to add9/bass with complete triad

            # Special case #2i: 7b9#11 with extensions should beat scale/other interpretations
            if chord_type == '7b9#11_13_no5' and missing_count == 0 and extra_count == 0:
                special_pattern_bonus = 260.0  # Beat altered interpretations from other roots

            # Special case #2i2: 9b13 with root in bass should beat other interpretations
            if chord_type in ['9b13', '9b13_no5']:
                if missing_count == 0 and extra_count == 0 and root_pc == lowest_pc:
                    special_pattern_bonus = 250.0  # Beat altered interpretations from other roots

            # Special case #2j: dominant9 with root in bass beats other interpretations
            if chord_type == 'dominant9' and root_pc == lowest_pc:
                if missing_count <= 1 and extra_count == 0:  # Allow missing 5th
                    special_pattern_bonus = 200.0  # Beat BbΔ7#11 interpretation (base ~197)

            # Special case #2k: C Bb D F G OR C Bb D G → Bb6/C (Gm7/Gm in 1st inversion over C)
            # ONLY these exact voicings should be Bb6/C - any other arrangement is Gm7/C or Gm/C

            # Check if this is EXACTLY C Bb D F G or C Bb D G with Bb as 2nd note above C
            is_bb6_over_c_voicing = False
            if intervals_from_lowest in [[0, 2, 5, 7, 10], [0, 2, 7, 10]]:
                # Check voicing - Bb must be the second note above C bass
                sorted_notes = sorted(active_notes)
                if len(sorted_notes) >= 2:
                    second_pc = sorted_notes[1] % 12
                    second_interval = (second_pc - lowest_pc) % 12
                    if second_interval == 10:  # Bb is second note above C
                        is_bb6_over_c_voicing = True

            # Apply bonuses/penalties based on voicing
            if is_bb6_over_c_voicing:
                # This is the 1st inversion voicing - prefer Bb6
                if chord_type == '6' and (root_pc - lowest_pc) % 12 == 10:
                    special_pattern_bonus = 250.0  # Very strong boost for Bb6 with C in bass
                # Penalize Bb6/9 - we want Bb6 not Bb6/9
                elif chord_type in ['6_9', '6_9_no5'] and (root_pc - lowest_pc) % 12 == 10:
                    special_pattern_bonus = -100.0
                # Penalize Gm7/Gm interpretation for this specific voicing
                elif chord_type in ['minor7', 'minor']:
                    special_pattern_bonus = -200.0
            else:
                # Not the 1st inversion voicing - prefer Gm7/C or Gm/C
                if intervals_from_lowest in [[0, 2, 5, 7, 10], [0, 2, 7, 10]]:
                    # These intervals but different voicing - prefer Gm7/Gm over Bb6
                    # The root must be G (interval 7 from C bass) for this to apply
                    root_interval_from_bass = (root_pc - lowest_pc) % 12
                    if chord_type in ['minor7', 'minor'] and root_interval_from_bass == 7:
                        special_pattern_bonus = 200.0  # Boost Gm7/C or Gm/C
                    elif chord_type == '6' and root_interval_from_bass == 10:
                        special_pattern_bonus = -200.0  # Penalize Bb6/C for non-1st-inversion

            # When the specific pattern [0, 2, 4, 7, 9] is present (Bb in bass, same notes):
            if intervals == [0, 2, 4, 7, 9] and chord_type == '6':
                # This is the Bb6 pattern (C Bb D F G with Bb lowest)
                special_pattern_bonus = 200.0  # Very strong boost for this specific voicing

            # 11. Inversion bonus for triads and 7th chords
            # When bass is a chord tone (not root), it's an inversion
            inversion_bonus = 0.0
            bass_interval = (lowest_pc - root_pc) % 12
            is_triad = chord_type in ['major', 'minor', 'diminished', 'augmented']
            is_seventh = chord_type in ['major7', 'minor7', 'dominant7', 'diminished7',
                                        'diminished_major7', 'half_diminished7', 'augmented7',
                                        'minor_major7'] or \
                         (chord_type.startswith('7') and ('b9' in chord_type or '#9' in chord_type or
                          '#11' in chord_type or 'b13' in chord_type or chord_type == 'altered'))
            is_sixth_chord = chord_type in ['6', '6_no5', 'minor6', 'minor6_no5',
                                            '6_9', '6_9_no5', '6_9_no3', 'minor6_9',
                                            '6add4', '6add4_no5']

            # If this is a triad interpretation and bass is the 3rd or 5th
            if is_triad and bass_interval in [3, 4, 7]:  # m3, M3, or P5
                # This is an inversion - give strong bonus
                inversion_bonus = 35.0

            # If this is a 7th chord and bass is a chord tone (3rd, 5th, or 7th)
            elif is_seventh and bass_interval in pattern_set and bass_interval != 0:
                # 7th chord inversion - give bonus
                inversion_bonus = 40.0  # Slightly higher than triad to prefer complete harmony

            # If this is a 6th chord but could be a minor triad inversion, penalize
            if is_sixth_chord and bass_interval == 0 and lowest_pc is not None and highest_pc is not None:
                # Check if there's a potential minor triad with bass as the 3rd
                # For Eb6: bass=Eb(3), contains Eb(0) G(4) C(9)
                # Could be Cm: C(0) Eb(3) G(7) with Eb in bass
                pitch_classes = sorted(set(note % 12 for note in active_notes))
                potential_root_pc = (lowest_pc - 3) % 12  # Assume bass is m3 of a minor chord
                potential_intervals = sorted((pc - potential_root_pc) % 12 for pc in pitch_classes)

                if set([0, 3, 7]).issubset(set(potential_intervals)):
                    # Yes, this could be a minor triad in first inversion
                    # Check voicing: simple 3-note triad vs 4+ note voicing
                    sixth_interval = 9  # Major 6th from root
                    sixth_pc = (root_pc + sixth_interval) % 12

                    # Only prefer 6th chord if:
                    # 1. The 6th is the highest note, AND
                    # 2. There are 4+ notes (indicating doubled notes/fuller voicing)
                    if highest_pc == sixth_pc and len(active_notes) >= 4:
                        # 6th is highest in a fuller voicing - prefer 6th chord
                        inversion_bonus = 45.0
                    else:
                        # Simple triad or 6th not highest - prefer minor triad inversion
                        inversion_bonus = -40.0

            # Calculate final score
            score = (essential_score + percentage_match + highest_note_bonus +
                    completeness_bonus + major_seventh_bonus + rootless_bonus + root_in_bass_bonus +
                    characteristic_bonus + dominant_quality_adjustment + special_pattern_bonus +
                    inversion_bonus - extra_penalty - missing_penalty)

            if DEBUG_PATTERN and chord_type == 'diminished7_no_m3':
                print(f"      SCORED: score={score:.1f}, best_score={best_score:.1f}")

            # Accept if we have at least 2 matching notes and reasonable score
            if score > best_score and matched_count >= 2 and score > 10.0:
                best_score = score

                if DEBUG_PATTERN and chord_type == 'diminished7_no_m3':
                    print(f"      ACCEPTED as new best!")

                DEBUG_INNER = False  # Debug flag for inner loop
                if DEBUG_INNER and score > 100:  # Show all high-scoring patterns
                    print(f"    SCORE BREAKDOWN: chord_type={chord_type}, root={self.get_note_name(root_pc)}")
                    print(f"      essential={essential_score:.1f}, pct={percentage_match:.1f}, highest={highest_note_bonus:.1f}")
                    print(f"      completeness={completeness_bonus:.1f}, rootless={rootless_bonus:.1f}, root_in_bass={root_in_bass_bonus:.1f}")
                    print(f"      characteristic={characteristic_bonus:.1f}, dominant_adj={dominant_quality_adjustment:.1f}")
                    print(f"      special={special_pattern_bonus:.1f}, inversion={inversion_bonus:.1f}")
                    print(f"      extra_pen={extra_penalty:.1f}, missing_pen={missing_penalty:.1f}")
                    print(f"      TOTAL SCORE={score:.1f}")

                # REMOVED: Am7 → C6 conversion in closed voicings
                # This was causing issues where Am7 would incorrectly show as C6
                # Users expect Am7 to remain Am7 regardless of voicing

                # Build chord name
                root_name = self.get_note_name(root_pc)

                # Format chord name based on type
                if chord_type == 'major':
                    chord_name = root_name
                elif chord_type == 'minor':
                    chord_name = f"{root_name}m"
                elif chord_type == 'diminished':
                    chord_name = f"{root_name}dim"
                elif chord_type == 'augmented':
                    chord_name = f"{root_name}aug"
                elif chord_type == 'sus2':
                    chord_name = f"{root_name}2"
                elif chord_type == 'sus4':
                    chord_name = f"{root_name}4"
                elif chord_type == '7sus4':
                    chord_name = f"{root_name}7sus4"
                elif chord_type == '7sus2':
                    chord_name = f"{root_name}7sus2"
                elif chord_type == '9sus':
                    chord_name = f"{root_name}9(sus)"
                elif chord_type == '9sus_with5':
                    chord_name = f"{root_name}9(sus)"
                elif chord_type == '13sus':
                    chord_name = f"{root_name}13(sus)"
                elif chord_type == '13sus_with5':
                    chord_name = f"{root_name}13(sus)"
                elif chord_type == '7sus13':
                    chord_name = f"{root_name}7sus13"
                elif chord_type == 'sus13':
                    chord_name = f"{root_name}sus13"
                elif chord_type == 'major7':
                    chord_name = f"{root_name}Δ7"
                elif chord_type == 'major7#5':
                    chord_name = f"{root_name}Δ7#5"
                elif chord_type == 'minor7':
                    chord_name = f"{root_name}m7"
                elif chord_type == 'minor_major7':
                    chord_name = f"{root_name}mΔ7"
                elif chord_type == 'minor_major9':
                    chord_name = f"{root_name}mΔ7(9)"
                elif chord_type == 'minor_major9_no5':
                    chord_name = f"{root_name}mΔ9"
                elif chord_type == 'dominant7':
                    chord_name = f"{root_name}7"
                elif chord_type == 'diminished7' or chord_type == 'diminished7_no_b5' or chord_type == 'diminished7_no_m3':
                    # Check if it's a diminished triad (3 notes) or dim7 (4 notes)
                    # Count unique pitch classes
                    unique_pcs = set((note % 12) for note in active_notes)
                    if len(unique_pcs) == 3:
                        # Diminished triad (C Eb Gb)
                        chord_name = f"{root_name}dim"
                    else:
                        # Diminished 7th (C Eb Gb Bbb)
                        chord_name = f"{root_name}dim7"
                elif chord_type == 'diminished_major7':
                    chord_name = f"{root_name}dimΔ7"
                elif chord_type == 'half_diminished7':
                    chord_name = f"{root_name}hdim7"
                elif chord_type == 'half_diminished11':
                    chord_name = f"{root_name}hdim7(11)"
                elif chord_type == 'half_diminished11_no3':
                    chord_name = f"{root_name}hdim7(11)"
                elif chord_type == 'dominant9':
                    chord_name = f"{root_name}9"
                elif chord_type == 'dominant11':
                    chord_name = f"{root_name}11"
                elif chord_type == 'dominant13':
                    chord_name = f"{root_name}13"
                # Shell voicings for 13th chords (display same as full voicings)
                elif chord_type == '13_shell':
                    chord_name = f"{root_name}13"
                elif chord_type == '13_no5_no11':
                    chord_name = f"{root_name}13"
                elif chord_type == '13_no5':
                    chord_name = f"{root_name}13"
                # Dominant 7#11 and 13#11 voicings
                elif chord_type == '7#11_no5':
                    chord_name = f"{root_name}7(#11)"
                elif chord_type == '7#11_no3_no5':
                    chord_name = f"{root_name}7(#11)"
                elif chord_type == '13#11_no3_no5':
                    chord_name = f"{root_name}13(#11)"
                elif chord_type == '13#11_no3':
                    chord_name = f"{root_name}13(#11)"
                elif chord_type == '13#11_no9_no5':
                    chord_name = f"{root_name}13(#11)"
                elif chord_type == '13#11_no5':
                    chord_name = f"{root_name}13(#11)"
                elif chord_type == 'major9':
                    chord_name = f"{root_name}Δ9"
                elif chord_type == 'minor9':
                    chord_name = f"{root_name}m9"
                elif chord_type == 'major11':
                    chord_name = f"{root_name}Δ11"
                elif chord_type == 'major7#11':
                    chord_name = f"{root_name}Δ7(#11)"
                elif chord_type == 'major7#11_no5':
                    chord_name = f"{root_name}Δ7(#11)"
                elif chord_type == 'major7#11_shell':
                    chord_name = f"{root_name}Δ7(#11)"
                elif chord_type == 'major9#11':
                    chord_name = f"{root_name}Δ9(#11)"
                elif chord_type == 'minor11':
                    chord_name = f"{root_name}m11"
                elif chord_type == 'minor11_no5':
                    chord_name = f"{root_name}m11"
                elif chord_type == 'minor11_no9':
                    chord_name = f"{root_name}m11"
                elif chord_type == 'minor11_shell':
                    chord_name = f"{root_name}m11"
                elif chord_type == 'major13':
                    chord_name = f"{root_name}Δ13"
                elif chord_type == 'major13#11':
                    chord_name = f"{root_name}Δ13#11"
                elif chord_type == 'minor13':
                    chord_name = f"{root_name}m13"
                elif chord_type == 'altered':
                    chord_name = f"{root_name}7alt"
                elif chord_type == '7b9' or chord_type == '7b9_no5':
                    chord_name = f"{root_name}7(b9)"
                elif chord_type == '7#9':
                    chord_name = f"{root_name}7(#9)"
                elif chord_type == '7#11':
                    chord_name = f"{root_name}7(#11)"
                elif chord_type == '7#11_shell' or chord_type == '7#11_no3':
                    chord_name = f"{root_name}7(#11)"
                elif chord_type == '7b13':
                    chord_name = f"{root_name}7(b13)"
                elif chord_type == '9b13' or chord_type == '9b13_no5':
                    chord_name = f"{root_name}9(b13)"
                elif chord_type == '13b9' or chord_type == '13b9_no5':
                    chord_name = f"{root_name}13(b9)"
                elif chord_type == '7b9#11':
                    chord_name = f"{root_name}7(b9,#11)"
                elif chord_type == '7b9#11_shell' or chord_type == '7b9#11_no3' or chord_type == '7b9#11_no5' or chord_type == '7b9#11_13_no5':
                    chord_name = f"{root_name}7(b9,#11)"
                elif chord_type == '7#9#11':
                    chord_name = f"{root_name}7(#9,#11)"
                elif chord_type == '7#9#11_shell':
                    chord_name = f"{root_name}7(#9,#11)"
                elif chord_type == '7b9b13':
                    chord_name = f"{root_name}7(b9,b13)"
                elif chord_type == '7#9b13':
                    chord_name = f"{root_name}7(#9,b13)"
                elif chord_type == '7#11b13':
                    chord_name = f"{root_name}7(#11,b13)"
                elif chord_type == '7b9#11b13':
                    chord_name = f"{root_name}7(b9,#11,b13)"
                elif chord_type == '7#9#11b13':
                    chord_name = f"{root_name}7(#9,#11,b13)"
                elif chord_type == '7b9#9':
                    chord_name = f"{root_name}7(b9,#9)"
                elif chord_type == '7b9#9#11':
                    chord_name = f"{root_name}7(b9,#9,#11)"
                elif chord_type == '7b9#9b13':
                    chord_name = f"{root_name}7(b9,#9,b13)"
                # Shell voicings (display same as full voicings)
                elif chord_type == '7b13_no5':
                    chord_name = f"{root_name}7(b13)"
                elif chord_type == '7#9b13_no5':
                    chord_name = f"{root_name}7(#9,b13)"
                elif chord_type == '7b9b13_no5':
                    chord_name = f"{root_name}7(b9,b13)"
                elif chord_type == '7b9#9_no5':
                    chord_name = f"{root_name}7(b9,#9)"
                elif chord_type == '5':
                    chord_name = f"{root_name}5"
                elif chord_type == '6':
                    chord_name = f"{root_name}6"
                elif chord_type == '6_no5':
                    chord_name = f"{root_name}6"
                elif chord_type == '6add4':
                    chord_name = f"{root_name}6add4"
                elif chord_type == '6add4_no5':
                    chord_name = f"{root_name}6add4"
                elif chord_type == '6_9':
                    chord_name = f"{root_name}6/9"
                elif chord_type == '6_9_no5':
                    chord_name = f"{root_name}6/9"
                elif chord_type == '6_9_no3':
                    chord_name = f"{root_name}6/9"
                elif chord_type == 'major7_6_9':
                    chord_name = f"{root_name}maj7(6/9)"
                elif chord_type == 'minor6':
                    chord_name = f"{root_name}m6"
                elif chord_type == 'minor6_no5':
                    chord_name = f"{root_name}m6"
                elif chord_type == 'minor6_9':
                    chord_name = f"{root_name}m6/9"
                elif chord_type == 'minor6_9_no5':
                    chord_name = f"{root_name}m6/9"
                elif chord_type == 'add9':
                    chord_name = f"{root_name}add9"
                elif chord_type == 'minor_add9':
                    chord_name = f"{root_name}madd9"
                elif chord_type == 'add11':
                    chord_name = f"{root_name}add11"
                else:
                    chord_name = f"{root_name}{chord_type}"

                best_match = (chord_name, score)

        return best_match
    
    def detect_scale(self, active_notes: Set[int]) -> Optional[str]:
        """
        Detect scale from active MIDI notes

        Args:
            active_notes: Set of MIDI note numbers (0-127) currently active

        Returns:
            Scale name string (e.g., "C Ionian", "D Dorian") or None
        """
        if len(active_notes) < 5:  # Need at least 5 notes for scale detection
            return None

        # Convert to pitch classes (ignore octave)
        pitch_classes = sorted(set(note % 12 for note in active_notes))

        if len(pitch_classes) < 5:  # Need at least 5 unique pitch classes
            return None

        # Get lowest note (most likely the root/tonic)
        lowest_note = min(active_notes)
        lowest_pc = lowest_note % 12

        # Check if notes are clustered (important for pentatonic/blues/whole tone scales)
        is_clustered = self.is_clustered(active_notes)

        # Check if notes are within one octave
        scale_span = max(active_notes) - min(active_notes)
        is_within_octave = scale_span < 12

        # Scales that should only be detected when clustered OR within one octave
        clustered_only_scales = {
            'Major Pentatonic', 'Minor Pentatonic',
            'Major Blues', 'Minor Blues',
            'Whole Tone'
        }

        # Try all pitch classes as potential roots, but prefer the lowest note
        best_match = None
        best_score = 0

        for root_pc in pitch_classes:
            # Calculate intervals from this root
            intervals = sorted((pc - root_pc) % 12 for pc in pitch_classes)

            # Match against scale patterns
            for scale_name, pattern in SCALE_PATTERNS.items():
                # Skip clustered-only scales if notes are not clustered AND not within one octave
                if scale_name in clustered_only_scales and not (is_clustered or is_within_octave):
                    continue

                # For Whole Tone, require at least 6 notes
                if scale_name == 'Whole Tone' and len(pitch_classes) < 6:
                    continue

                pattern_set = set(pattern)
                intervals_set = set(intervals)

                # Check if all pattern notes are present
                if pattern_set.issubset(intervals_set):
                    # Calculate match quality
                    matched = len(pattern_set)
                    extra = len(intervals_set - pattern_set)

                    # STRICT REQUIREMENT: ALL scales must be exact matches (no extra notes allowed)
                    # Scales should only match when ALL and ONLY the scale notes are present
                    # This prevents detecting pentatonic when extra notes break the scale pattern
                    if extra > 0:
                        continue  # Skip this match - scales must be exact

                    # Perfect match (no extra notes) gets HUGE score to beat chord interpretations
                    if extra == 0:
                        score = 5000 + matched  # Massive boost for perfect scale/mode matches

                        # Extra bonuses for important mode categories
                        # Major modes (Ionian through Locrian)
                        major_modes = {'Ionian', 'Dorian', 'Phrygian', 'Lydian', 'Mixolydian', 'Aeolian', 'Locrian'}
                        # Melodic minor modes
                        melodic_minor_modes = {'Melodic Minor', 'Dorian b2', 'Lydian Augmented', 'Lydian Dominant',
                                              'Mixolydian b6', 'Locrian #2', 'Altered'}
                        # Harmonic minor modes
                        harmonic_minor_modes = {'Harmonic Minor', 'Locrian #6', 'Ionian #5', 'Dorian #4',
                                               'Phrygian Dominant', 'Lydian #2', 'Altered Diminished'}

                        if scale_name in major_modes:
                            score += 1000  # Huge bonus for perfect major mode match
                        elif scale_name in melodic_minor_modes:
                            score += 1000  # Huge bonus for perfect melodic minor mode match
                        elif scale_name in harmonic_minor_modes:
                            score += 1000  # Huge bonus for perfect harmonic minor mode match
                    else:
                        # Allow some extra notes but penalize
                        score = matched * 10 - extra * 5

                    # Bonus for matching the lowest note as root (most likely tonic)
                    if root_pc == lowest_pc:
                        score += 500  # Strong preference for lowest note as root

                    if score > best_score:
                        best_score = score
                        root_name = self.get_note_name(root_pc)
                        best_match = f"{root_name} {scale_name}"

        return best_match

def test_chord_detector():
    """Test the chord detector with example chords"""
    detector = ChordDetector()

    # Test cases: (MIDI notes, expected chord)
    test_cases = [
        # Intervals (2 notes) - just interval names, no note names
        ({60, 64}, "M3"),  # C4, E4 - Major 3rd
        ({60, 67}, "P5"),  # C4, G4 - Perfect 5th
        ({60, 69}, "M6"),  # C4, A4 - Major 6th

        # Triads
        ({60, 64, 67}, "C"),  # C major: C4, E4, G4
        ({60, 63, 67}, "Cm"),  # C minor: C4, Eb4, G4
        ({60, 63, 66}, "Cdim"),  # C diminished: C4, Eb4, Gb4

        # 6th chords
        ({60, 64, 69}, "C6"),  # C6 without 5th: C4, E4, A4
        ({60, 64, 67, 69}, "C6"),  # C6 with 5th: C4, E4, G4, A4
        ({60, 64, 69, 74}, "C6/9"),  # C6/9 without 5th: C, E, A, D
        ({63, 67, 72}, "Eb6"),  # Eb6 without 5th: Eb, G, C (should NOT be Cm/Eb)

        # 7th chords
        ({67, 71, 74, 77}, "G7"),  # G7 (dominant 7th): G4, B4, D5, F5
        ({62, 66, 69, 73}, "DΔ7"),  # DΔ7: D4, F#4, A4, C#5
        ({60, 63, 67, 71}, "CmΔ7"),  # CmΔ7: C, Eb, G, B (no parentheses)
        ({60, 63, 67, 71, 74}, "CmΔ7(9)"),  # CmΔ7(9): C, Eb, G, B, D
        ({60, 64, 68, 71}, "CΔ7#5"),  # CΔ7#5: C, E, G#, B (augmented major 7th)
        ({60, 67, 69, 74}, "C6/9"),  # C6/9 without 3rd: C, G, A, D
        ({71, 74, 77, 81}, "Bø7"),  # Bø7 (half-diminished): B, D, F, A

        # Jazz voicings without root (but with 5th to imply harmony)
        ({64, 67, 70, 60}, "C7"),  # E + G + Bb + C (no 5th priority but root present)
        ({64, 67, 71, 60}, "CΔ7"),  # E + G + B + C (Δ7 voicing, root in bass)

        # Extended chords
        ({60, 64, 67, 71, 74, 78}, "CΔ7#11"),  # C Δ7#11: C, E, G, B, D, F# (sharp 11)
        ({60, 78, 71}, "CΔ7#11"),  # Sparse voicing: C, F#, B (root, #11, maj7)
        ({60, 64, 67, 71, 74, 77, 81}, "CΔ13"),  # C Δ13: C, E, G, B, D, F, A
        ({60, 63, 67, 70, 74, 77, 81}, "Cm13"),  # C m13: C, Eb, G, Bb, D, F, A

        # Altered dominants
        ({60, 64, 67, 70, 63}, "C7(#9)"),  # C7(#9): C, E, G, Bb, D# (63 = Eb/D#)
        ({60, 64, 67, 70, 61}, "C7(b9)"),  # C7(b9): C, E, G, Bb, Db (61 = Db/C#)
        ({60, 64, 70, 78}, "C7(#11)"),  # C7(#11): C, E, Bb, F# (no 5th, has #11)
        ({67, 71, 77, 70, 75}, "G7(#9b13)"),  # G7(#9b13): G, B, F, Bb(#9), Eb(b13) no 5th

        # Scales (7 unique pitch classes)
        ({65, 67, 69, 70, 72, 74, 76}, "F Ionian"),  # F Ionian: F, G, A, Bb, C, D, E
        ({60, 62, 63, 65, 67, 68, 70}, "C Aeolian"),  # C Aeolian (natural minor): C, D, Eb, F, G, Ab, Bb
        ({62, 64, 65, 67, 69, 71, 72}, "D Dorian"),  # D Dorian: D, E, F, G, A, B, C
    ]

    print("Testing Chord Detector (Jazz-Aware Algorithm):")
    print("=" * 60)

    passed = 0
    failed = 0
    for notes, expected in test_cases:
        detected = detector.detect_chord(notes)
        if detected == expected:
            status = "✓"
            passed += 1
        else:
            status = "✗"
            failed += 1
        print(f"{status} Notes: {sorted(notes)}")
        print(f"  Expected: {expected}, Got: {detected}")

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

if __name__ == "__main__":
    test_chord_detector()


