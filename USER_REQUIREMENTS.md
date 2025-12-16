# User Requirements - Chord Detection Issues & Edge Cases

This document tracks all user-reported chord detection issues, edge cases, and specific voicing requirements.

**Last Updated:** 2025-12-15

---

## Current Issues (Pending Fix)

### 1. Major 9th Chord Detection
**Issue:** Cmaj9 (C E G B D) is detected as CΔ7 instead of CΔ9
- **Notes:** C E G B D
- **Expected:** CΔ9
- **Current Result:** CΔ7
- **Priority:** High

### 2. Major 13#11 Chord Detection
**Issue:** Cmaj13#11 (C E G B D F# A) is detected as CΔ9#11 instead of CΔ13#11
- **Notes:** C E G B D F# A
- **Expected:** CΔ13#11
- **Current Result:** CΔ9#11
- **Priority:** High

### 3. Minor 9th Chord Detection
**Issue:** Cm9 (C Eb G Bb D) is detected as EbΔ7/C instead of Cm9
- **Notes:** C Eb G Bb D
- **Expected:** Cm9
- **Current Result:** EbΔ7/C
- **Priority:** High

### 4. Minor 13th Chord Detection
**Issue:** Cm13 (C Eb G Bb D F A) is detected as Ebmaj9#11 instead of Cm13
- **Notes:** C Eb G Bb D F A
- **Expected:** Cm13
- **Current Result:** Ebmaj9#11 (or scale name)
- **Priority:** High

### 5. Major 7th Third Inversion
**Issue:** Cmaj7/B (B C E G) detects as C/B instead of CΔ7/B
- **Notes:** B C E G
- **Expected:** CΔ7/B
- **Current Result:** C/B
- **Note:** Other inversions of major 7 work correctly
- **Priority:** Medium

### 6. Minor 7th First Inversion
**Issue:** Cm7/G (G Bb C Eb) is detected as Gm11 even though it has Eb
- **Notes:** G Bb C Eb
- **Expected:** Cm7/G
- **Current Result:** Gm11
- **Priority:** Medium

### 7. Minor 7th Third Inversion
**Issue:** Cm7/Bb (Bb C Eb G) should be called Cm7/Bb
- **Notes:** Bb C Eb G
- **Expected:** Cm7/Bb
- **Current Result:** Cm7 (no slash notation)
- **Priority:** Medium

### 8. Dominant 13#11 Detection ✅ FIXED
**Issue:** C13#11 (C Bb E F# A) is detected as C13 instead of C13#11
- **Notes:** C Bb E F# A
- **Expected:** C13#11
- **Previous Result:** C13
- **Status:** ✅ Fixed
- **Priority:** High

### 9. Scale Detection - Modes of Major ✅ FIXED
**Issue:** Modes of Major (Ionian, Dorian, Phrygian, Lydian, Mixolydian, Aeolian, Locrian) are not being detected correctly
- **Examples:**
  - C Ionian (C D E F G A B) - should detect as "C Ionian"
  - D Dorian (D E F G A B C) - should detect as "D Dorian"
  - E Phrygian (E F G A B C D) - should detect as "E Phrygian"
- **Previous Result:** Detected as chords instead of scales
- **Status:** ✅ Fixed - Early scale detection for 7-note patterns prioritizes modes over chords
- **Priority:** High

### 10. Scale Detection - Major Pentatonic ✅ FIXED
**Issue:** Major Pentatonic scales are not being detected correctly
- **Example:** C Major Pentatonic (C D E G A) - should detect as "C Major Pentatonic"
- **Previous Result:** Detected as chords or not detected
- **Status:** ✅ Fixed - Early scale detection for 5-note patterns prioritizes pentatonic scales
- **Priority:** High

### 11. Scale Detection - Minor Pentatonic ✅ FIXED
**Issue:** Minor Pentatonic scales are not being detected correctly
- **Example:** C Minor Pentatonic (C Eb F G Bb) - should detect as "C Minor Pentatonic"
- **Previous Result:** Detected as chords or not detected
- **Status:** ✅ Fixed - Early scale detection for 5-note patterns prioritizes pentatonic scales
- **Priority:** High

### 12. Interval Recognition ✅ FIXED
**Issue:** 2-note intervals are not being detected. They are being filtered out by the algorithm
- **Example:** C and G (Perfect 5th) - should detect as "C (P5)"
- **Example:** C and E (Major 3rd) - should detect as "C (M3)"
- **Previous Result:** Returns None (no detection)
- **Status:** ✅ Fixed - `detect_chord` now calls `detect_interval` for 2-note inputs
- **Priority:** High

---

## Edge Cases (From Previous Sessions)

### Edge Case 1: C7#9 Detection ✅ FIXED
**Issue:** C7#9 (C E G Bb Eb) was detected as EΔ7(#11)
- **Notes:** C E G Bb Eb
- **Expected:** C7#9
- **Previous Result:** EΔ7(#11)
- **Status:** ✅ Fixed with special pattern bonus of 2000.0
- **Fix Location:** `chord_detector_v2.py`, line ~1919

### Edge Case 2: Sus2 Triad ✅ VERIFIED CORRECT
**Issue:** C D E was expected to be Csus2
- **Notes:** C D E
- **Expected:** Csus2
- **Result:** None (rejected)
- **Status:** ✅ Correct behavior - sus2 requires root, 2nd, and 5th (C D G)
- **Note:** Input is incomplete (missing 5th G)

### Edge Case 3: Sus4 Triad ⚠️ NEEDS INVESTIGATION
**Issue:** Csus4 (C F G) was detected as G7sus4/C
- **Notes:** C F G
- **Expected:** Csus4
- **Previous Result:** G7sus4/C or None
- **Status:** ⚠️ Needs investigation - may be validation or scoring issue
- **Attempted Fixes:**
  - Added completeness bonus of 10000.0 for sus4 triads
  - Added special pattern bonus of 10000.0 for sus4
  - Added penalty of 5000.0 for incomplete 7sus4 missing 5th

### Edge Case 4: m6 Slash Chord - Gm6/Bb ✅ FIXED
**Issue:** Gm6/Bb (Bb D E G) was missing slash notation
- **Notes:** Bb D E G
- **Expected:** Gm6/Bb
- **Previous Result:** Gm6
- **Status:** ✅ Fixed - removed m6 from skip_slash condition
- **Fix Location:** `chord_detector_v2.py`, line ~1092-1096

### Edge Case 5: m6 Slash Chord - Gm6/D ✅ FIXED
**Issue:** Gm6/D (D E G Bb) was missing slash notation
- **Notes:** D E G Bb
- **Expected:** Gm6/D
- **Previous Result:** Gm6
- **Status:** ✅ Fixed - same as Edge Case 4

### Edge Case 6: F/G Slash Chord ✅ FIXED
**Issue:** F/G (F A C with G in bass) was missing slash notation
- **Notes:** F A C with G in bass
- **Expected:** F/G
- **Previous Result:** F
- **Status:** ✅ Fixed - slash notation now works for simple triads when bass ≠ root
- **Note:** User clarified F/G and G9sus are enharmonic, prefer G9sus

### Edge Case 7: G/F# Slash Chord ✅ VERIFIED CORRECT
**Issue:** G/F# (G B D with F# in bass) was expected to be G/F#
- **Notes:** G B D with F# in bass
- **Expected:** G/F#
- **Result:** GΔ7
- **Status:** ✅ Correct behavior - user confirmed prefer GΔ7 over G/F# slash chord

---

## Specific Voicings & Test Cases

### Slash Chords
```python
# Major 7th inversions
({64, 67, 71, 60}, "CΔ7/E", "Cmaj7/E: E G B C"),
({67, 60, 64, 71}, "CΔ7/G", "Cmaj7/G: G C E B"),
({71, 60, 64, 67}, "CΔ7/B", "Cmaj7/B: B C E G"),  # ⚠️ Currently fails

# Minor 7th inversions
({67, 70, 60, 63}, "Cm7/G", "Cm7/G: G Bb C Eb"),  # ⚠️ Currently fails
({70, 60, 63, 67}, "Cm7/Bb", "Cm7/Bb: Bb C Eb G"),  # ⚠️ Currently fails

# Dominant 7th inversions
({64, 67, 70, 60}, "C7/E", "C7/E: E G Bb C"),
({67, 60, 64, 70}, "C7/G", "C7/G: G C E Bb"),
({70, 60, 64, 67}, "C7/Bb", "C7/Bb: Bb C E G"),  # Simplifies to C/Bb (intentional)

# Minor 6th inversions
({70, 62, 64, 67}, "Gm6/Bb", "Gm6/Bb: Bb D E G"),  # ✅ Fixed
({62, 64, 67, 70}, "Gm6/D", "Gm6/D: D E G Bb"),  # ✅ Fixed

# Simple triad slash chords
({65, 69, 72, 67}, "F/G", "F/G: F A C with G in bass"),  # ✅ Fixed (prefer G9sus)
```

### Special Voicings
```python
# Add9 chords
({60, 64, 67, 74}, "Cadd9", "Cadd9: C E G D"),
({65, 60, 64, 67, 74}, "Cadd9/F", "Cadd9/F: F C E G D"),  # ✅ Fixed

# Sus chords
({60, 65, 67}, "Csus4", "Csus4: C F G"),  # ⚠️ Needs investigation
({60, 62, 67}, "Csus2", "Csus2: C D G"),  # Requires 5th

# Altered dominants
({60, 64, 67, 70, 61}, "C7b9", "C7b9: C E G Bb Db"),  # ✅ Working
({60, 64, 67, 70, 75}, "C7#9", "C7#9: C E G Bb Eb"),  # ✅ Fixed
({60, 64, 68, 70, 75}, "C7#9b13", "C7#9b13: C E Ab Bb D#"),  # ✅ Fixed
({60, 70, 64, 66, 69}, "C13#11", "C13#11: C Bb E F# A"),  # ⚠️ Currently fails

# Extended chords
({60, 64, 67, 71, 62}, "CΔ9", "Cmaj9: C E G B D"),  # ⚠️ Currently fails
({60, 64, 67, 71, 62, 66, 69}, "CΔ13#11", "Cmaj13#11: C E G B D F# A"),  # ⚠️ Currently fails
({60, 63, 67, 70, 62}, "Cm9", "Cm9: C Eb G Bb D"),  # ⚠️ Currently fails
({60, 63, 67, 70, 62, 65, 69}, "Cm13", "Cm13: C Eb G Bb D F A"),  # ⚠️ Currently fails
```

### Critical Cases
```python
# m6 vs m7b5 distinction
({67, 70, 73, 77}, "Gm7b5", "Gm7b5: G Bb Db F"),  # ✅ Working
({70, 73, 77, 67}, "Bbm6", "Bbm6: Bb Db F G"),  # ✅ Working
({70, 73, 77, 61}, "Bbm6/Db", "Bbm6/Db: Db F G Bb"),  # ✅ Working
({67, 70, 73, 77}, "Gm7b5", "Gm7b5 with G in bass"),  # ✅ Working

# Half-diminished formatting
({71, 74, 77, 81}, "Bm7b5", "Bm7b5: B D F A"),  # Should format as Bø7
({71, 74, 77, 81}, "Bø7", "Half-diminished: B D F A"),  # ✅ Fixed formatting
```

---

## Previous Requirements (Implemented)

### ✅ Am7 → C6 Conversion Fix
**Requirement:** Am7 in closed voicing should stay as Am7, not convert to C6
- **Notes:** A C E G (closed voicing)
- **Expected:** Am7
- **Status:** ✅ Implemented

### ✅ Scale Detection
**Requirement:** Scales should be detected for stepwise patterns with octave+ span
- **Test Cases:**
  - F Ionian: F G A Bb C D E F
  - C Ionian: C D E F G A B C
  - D Dorian: D E F G A B C D
  - A Aeolian: A B C D E F G A
- **Status:** ✅ Implemented

### ✅ Special Cases Preservation
**Requirement:** Important special cases must continue to work
- **Test Cases:**
  - Gm7b5 vs Bbm6 distinction ✅
  - C7b9 detection ✅
  - C7#9 detection ✅
  - CΔ7(#11) detection ✅
  - C6 and Cm6 detection ✅
- **Status:** ✅ All preserved

### ✅ Transposability
**Requirement:** All chord types must work in all 12 keys
- **Test:** Major scales (Ionian mode) in all 12 keys
- **Status:** ✅ All 12 keys passing

### ✅ Add9 Chord with 4th in Bass
**Requirement:** Cadd9/F (F C E G D) should be detected as Cadd9/F, not G7sus4/F
- **Notes:** F C E G D
- **Expected:** Cadd9/F
- **Status:** ✅ Fixed with 10000.0 bonus when bass is 4th of add9 root

### ✅ Dominant Chord Transposability
**Requirement:** All dominant 7th inversions must work in all 12 keys
- **Test Cases:**
  - First inversion (3rd in bass): C7/E, D7/F#, etc.
  - Second inversion (5th in bass): C7/G, D7/A, etc.
  - Third inversion (7th in bass): C7/Bb, D7/C, etc.
- **Status:** ✅ All inversions transposable across all keys

### ✅ C7/Bb Simplification
**Requirement:** C7/Bb should simplify to C/Bb to differentiate from C/B
- **Notes:** Bb C E G
- **Expected:** C/Bb (simplified from C7/Bb)
- **Status:** ✅ Working as intended (intentional simplification)

### ✅ Diminished Chord Formatting
**Requirement:** Diminished triads should display with circle symbol (°)
- **Examples:**
  - Cdim → C°
  - Cdim7 → C°7
  - Chdim7 → Cø7
- **Status:** ✅ Fixed

### ✅ Circle Symbol Spacing
**Requirement:** ° and ø symbols should have proper spacing (8px padding)
- **Status:** ✅ Fixed

### ✅ Click Toggle Default
**Requirement:** Keytoggle should be disabled by default
- **Status:** ✅ Fixed

### ✅ Reset Settings
**Requirement:** "Reset Settings to Default" should properly disable keytoggle
- **Status:** ✅ Fixed

### ✅ Windows Compatibility
**Requirement:** Application should work on Windows (os.fork() check)
- **Status:** ✅ Fixed

---

## Test Cases Summary

```python
test_cases = [
    # Current Issues
    ({60, 64, 67, 71, 62}, "CΔ9", "Cmaj9: C E G B D"),
    ({60, 64, 67, 71, 62, 66, 69}, "CΔ13#11", "Cmaj13#11: C E G B D F# A"),
    ({60, 63, 67, 70, 62}, "Cm9", "Cm9: C Eb G Bb D"),
    ({60, 63, 67, 70, 62, 65, 69}, "Cm13", "Cm13: C Eb G Bb D F A"),
    ({71, 60, 64, 67}, "CΔ7/B", "Cmaj7/B: B C E G"),
    ({67, 70, 60, 63}, "Cm7/G", "Cm7/G: G Bb C Eb"),
    ({70, 60, 63, 67}, "Cm7/Bb", "Cm7/Bb: Bb C Eb G"),
    ({60, 70, 64, 66, 69}, "C13#11", "C13#11: C Bb E F# A"),
    
    # Edge Cases (Fixed)
    ({60, 64, 67, 70, 75}, "C7#9", "C7#9: C E G Bb Eb"),
    ({70, 62, 64, 67}, "Gm6/Bb", "Gm6/Bb: Bb D E G"),
    ({62, 64, 67, 70}, "Gm6/D", "Gm6/D: D E G Bb"),
    
    # Special Voicings
    ({60, 64, 67, 74}, "Cadd9", "Cadd9: C E G D"),
    ({65, 60, 64, 67, 74}, "Cadd9/F", "Cadd9/F: F C E G D"),
    ({60, 65, 67}, "Csus4", "Csus4: C F G"),
    ({60, 62, 67}, "Csus2", "Csus2: C D G"),
    
    # Critical Cases
    ({67, 70, 73, 77}, "Gm7b5", "Gm7b5: G Bb Db F"),
    ({70, 73, 77, 67}, "Bbm6", "Bbm6: Bb Db F G"),
    
    # Altered Dominants
    ({60, 64, 67, 70, 61}, "C7b9", "C7b9: C E G Bb Db"),
    ({60, 64, 68, 70, 75}, "C7#9b13", "C7#9b13: C E Ab Bb D#"),
]
```

---

## Issue Categories

### 1. Extended Chord Detection (High Priority)
- Major 9th chords not detected correctly
- Major 13#11 chords not detected correctly
- Minor 9th chords not detected correctly
- Minor 13th chords not detected correctly
- Dominant 13#11 not detected correctly

### 2. Slash Chord Notation (Medium Priority)
- Major 7th third inversion missing slash notation
- Minor 7th inversions missing slash notation
- Some inversions work, others don't (inconsistency)

### 3. Scoring Priority Issues (High Priority)
- Extended chords losing to simpler interpretations
- Scale detection overriding chord detection
- Major 7th #11 interpretations beating extended chords

### 4. Formatting Issues (Low Priority)
- Most formatting issues resolved
- Circle symbol spacing fixed
- Diminished chord formatting fixed

---

## Status Summary

**Total Issues:** 8 current + 7 edge cases = 15 total  
**Fixed:** 7 edge cases + 11 previous requirements = 18 fixed  
**Pending:** 8 current issues  
**Verified Correct:** 2 edge cases (Sus2, G/F#)

**Overall Progress:** 18/26 resolved (69%)

---

## Release Requirements (v1.1+)

### GNOME Software Center Metadata
- **Screenshots must display in GNOME Software Center**
  - Screenshots must be included in `ivory.metainfo.xml` with proper HTTPS URLs
  - Use GitHub raw URLs for screenshots: `https://raw.githubusercontent.com/ganten/ivory/master/screenshots/[filename].png`
  - Required screenshots: Cm11.png, D7-b9-11.png, Ebm11.png
  - Status: ✅ Fixed in build script

### About Dialog Version Display
- **Version number must be displayed in bottom left of About dialog**
  - Format: "v1.1" (with "v" prefix)
  - Position: Bottom left corner of About dialog
  - Must update automatically when version changes
  - Status: ✅ Fixed in `ivory_v2.py`

### GitHub Actions Workflow & Cross-Platform Builds ✅ IMPLEMENTED
- **Automated multi-platform builds via GitHub Actions**
  - **Trigger:** Pushing a tag matching pattern `v*.*` (e.g., `v1.1`)
  - **Platforms:** Linux (.deb), Windows (.exe), macOS (.zip/.app)
  - **Build Process:**
    - Linux: Uses `ubuntu-latest` runner, builds `.deb` package via `build-release-v1.1.sh`
    - Windows: Uses `windows-latest` runner, builds `.exe` via PyInstaller
    - macOS: Uses `macos-latest` runner, builds `.app` bundle via PyInstaller, zipped for distribution
  - **Version Extraction:** Automatically extracts version from Git tag (e.g., `v1.1` → `1.1`)
  - **Artifacts:** All builds uploaded as artifacts, then combined into a single GitHub Release
  - **Status:** ✅ Implemented in `.github/workflows/release.yml`

### Cross-Platform Compatibility Requirements ✅ IMPLEMENTED
- **Windows Build Compatibility**
  - **Issue:** Windows GitHub Actions runners use PowerShell by default, but build scripts use bash syntax
  - **Solution:** Explicitly set `shell: bash` for all build steps (Windows runners include Git Bash)
  - **Error Handling:** Improved error messages with fallback to Windows `dir` command for debugging
  - **Status:** ✅ Fixed - Windows builds now use bash shell explicitly

- **Linux Build Compatibility**
  - **Requirements:** `dpkg-dev` package for building `.deb` files
  - **Script:** Uses `build-release-v1.1.sh` which accepts `VERSION` environment variable
  - **Output:** Creates `ivory_${VERSION}_all.deb` in `release-artifacts/ivory-linux/`
  - **Status:** ✅ Working - Linux builds use dynamic versioning

- **macOS Build Compatibility**
  - **Requirements:** PyInstaller with macOS-specific spec file (`build_macos.spec`)
  - **Output:** Creates `Ivory.app` bundle, then zips it as `Ivory-macOS-v${VERSION}.zip`
  - **Status:** ✅ Working - macOS builds create proper `.app` bundles

### Build Workflow Details
- **Matrix Strategy:** Uses GitHub Actions matrix to build all platforms in parallel
- **Dependencies:** All platforms install from `build_scripts/requirements.txt`
  - PyQt5>=5.15.0
  - mido>=1.2.10
  - python-rtmidi>=1.4.9
  - pyinstaller>=5.0
- **Release Creation:** Single `release` job combines all artifacts and creates GitHub Release
- **Release Notes:** Automatically uses `RELEASE_${VERSION}.md` file (e.g., `RELEASE_v1.1.md`)
- **Screenshots:** Includes all PNG files from `screenshots/` directory in release

### Platform-Specific Build Notes
- **Linux (.deb):**
  - Requires `dpkg-dev` (installed automatically in workflow)
  - Build script generates GNOME metadata (`metainfo.xml`) with screenshots
  - Package includes desktop file, icon, and AppStream metadata
  
- **Windows (.exe):**
  - Uses PyInstaller with `build_windows.spec`
  - Creates single-file executable (no COLLECT mode)
  - Executable location: `build_scripts/dist/Ivory.exe` (or `build_scripts/dist/Ivory/Ivory.exe`)
  - Icon support: Uses `screenshots/icon.ico` if available
  
- **macOS (.app/.zip):**
  - Uses PyInstaller with `build_macos.spec`
  - Creates `.app` bundle following macOS conventions
  - Bundled as `.zip` for distribution
  - Includes all required dependencies and data files

## Notes

- These issues primarily involve:
  1. Extended chord detection (9th, 13th chords)
  2. Slash chord notation for inversions
  3. Scoring priorities between different chord interpretations
  4. Scale detection overriding chord detection

- Previous fixes are working correctly and should be preserved

- Priority should be given to extended chord detection issues as they affect core functionality
