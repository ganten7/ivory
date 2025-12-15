# Click-to-Toggle Testing Mode

Ivory 2.0 includes a **click-to-toggle** feature that allows you to test chord detection without a physical MIDI keyboard!

## How to Use

### Quick Start
```bash
cd /home/ganten/Ivory-2.0
./run_clickable.sh
```

Or manually:
```bash
cd /home/ganten/Ivory-2.0
python3 ivory_v2.py
```

### How It Works

1. **Click any piano key** to toggle it ON/OFF
2. **Watch the chord name** update in real-time
3. **Click again** to turn the note OFF

### Features

- ✅ Click white keys or black keys
- ✅ Multiple notes can be active simultaneously
- ✅ Real-time chord detection using the improved v2.0 algorithm
- ✅ Visual feedback - clicked notes light up
- ✅ No MIDI keyboard required!

## Testing Examples

### Test Am7 Fix
1. Launch the clickable version
2. Click: **A** (white key)
3. Click: **C** (white key)
4. Click: **E** (white key)
5. Click: **G** (white key)
6. **Result**: Should show "Am7" (NOT "C6")

### Test F Ionian Scale
1. Launch the clickable version
2. Click these keys in order (leave them all ON):
   - F, G, A, Bb, C, D, E, F (next octave)
3. **Result**: Should show "F Ionian"

### Test Complex Chords
**Cmaj7#11:**
1. Click: C, E, B, F#
2. **Result**: "CΔ7(#11)"

**C7(b9):**
1. Click: C, E, G, Bb, Db
2. **Result**: "C7(b9)" or "C7b9"

## Tips

- **Start Fresh**: Close and reopen to clear all notes
- **Test Voicings**: Try different octaves - the algorithm should recognize the same chord
- **Compare with Keyboard**: Use this to verify what you're hearing on your MIDI keyboard
- **Scale Testing**: For scales, click notes stepwise across at least one octave

## Keyboard Layout

The visual keyboard shows all 88 keys (A0 to C8):
- **White Keys**: Natural notes (C, D, E, F, G, A, B)
- **Black Keys**: Sharps/Flats (C#/Db, D#/Eb, etc.)
- **Active Notes**: Light up in blue when clicked

## Technical Details

### Implementation
- Mouse clicks are detected on the PianoWidget
- Each click toggles the note in `manual_notes` set
- Active notes update the chord detector in real-time
- No MIDI input required - purely GUI-based

### Signal Flow
```
Mouse Click → _get_note_at_position() → Toggle note
   ↓
note_clicked signal → _on_note_clicked()
   ↓
update_chord_detection() → detect_chord()
   ↓
Display updated chord name
```

## Comparison: Old vs New

### Original Ivory (v1.0)
- Requires MIDI keyboard for testing
- Am7 converts to C6 in closed voicings
- Scales show as chords

### Ivory 2.0 with Click Testing
- Click any keys to test without MIDI
- Am7 stays as Am7 ✓
- Scales detected correctly ✓
- All improvements testable instantly ✓

## Troubleshooting

**Keys don't respond to clicks:**
- Make sure you're clicking the clickable version: `python3 ivory_v2.py`
- Check that `click_enabled = True` in PianoWidget

**Chord doesn't update:**
- Verify chord detection is enabled in settings
- Check console for error messages

**Wrong chord detected:**
- This is probably a real detection issue - please report it!
- Note which notes you clicked and what chord was shown

## Command Reference

```bash
# Run Ivory 2.0 (click-to-toggle always enabled)
cd /home/ganten/Ivory-2.0
python3 ivory_v2.py

# Run original Ivory v1.0 (for comparison)
cd /home/ganten/Ivory
python3 ivory.py
```

---

**Happy Testing!** 🎹✨

Now you can test all the Ivory 2.0 improvements without getting up from your chair!
