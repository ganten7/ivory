# Ivory Build Compatibility Guide

## Overview

This document provides comprehensive guidance on ensuring successful builds across all platforms (Linux, Windows, macOS) and maintaining compatibility with user requirements.

**Last Updated:** December 16, 2025  
**Current Status:** ✅ All platforms building successfully (v1.1)

---

## Critical Build Requirements

### 1. Python Syntax Validation

**CRITICAL:** Always validate Python syntax before committing changes.

```bash
# Check syntax before committing
python3 -m py_compile ivory_v2.py
# OR
python3 -c "import ast; ast.parse(open('ivory_v2.py').read())"
```

**Common Syntax Errors to Avoid:**
- **Try blocks without except/finally:** Every `try:` block MUST have a matching `except:` or `finally:` clause
- **Indentation errors:** Ensure consistent indentation (4 spaces) within try/except blocks
- **Missing colons:** All control structures (if, for, while, try, except, def, class) must end with `:`

**Example of CORRECT syntax:**
```python
try:
    self.update_timer = QTimer()
    self.update_timer.timeout.connect(self.update_gui)
    self.update_timer.start(50)
except Exception as e:
    import traceback
    print(f"Warning: Failed to start update timer: {e}", file=sys.stderr)
    print(traceback.format_exc(), file=sys.stderr)
```

**Example of INCORRECT syntax (will break builds):**
```python
try:
    self.update_timer = QTimer()
self.update_timer.timeout.connect(self.update_gui)  # WRONG: Not indented, no except clause
self.update_timer.start(50)
```

---

## Workflow Structure (GitHub Actions)

### Current Working Configuration

The workflow file `.github/workflows/release.yml` uses the following structure that has been proven to work:

#### Key Components:

1. **Version Extraction:**
   - Extract version in a separate step: `echo "VERSION=${GITHUB_REF#refs/tags/v}" >> $GITHUB_OUTPUT`
   - Pass as environment variable: `env: VERSION: ${{ steps.get_version.outputs.VERSION }}`
   - Use `$VERSION` (not `${VERSION}`) in build commands for better shell compatibility

2. **Platform-Specific Build Commands:**

   **Linux:**
   - Builds `.deb` package directly in workflow (no external script)
   - Uses `dpkg-deb --build` command
   - Extracts VERSION from tag in build_command

   **Windows:**
   - Uses PowerShell syntax (default shell on Windows runners)
   - Runs PyInstaller from `build_scripts/build_windows.spec`
   - Uses `$env:VERSION` for PowerShell variable expansion

   **macOS:**
   - Uses bash syntax (default shell on macOS runners)
   - Runs PyInstaller from `build_scripts/build_macos.spec`
   - Uses `$VERSION` for bash variable expansion

3. **Dependencies Installation:**
   - Separate "Install dependencies" step runs before build
   - Installs from `build_scripts/requirements.txt`
   - Also installed again in build_command (redundant but safe)

#### Workflow Pattern (DO NOT DEVIATE):

```yaml
steps:
  - name: Checkout code
  - name: Set up Python
  - name: Install dependencies
    run: |
      python -m pip install --upgrade pip
      pip install -r build_scripts/requirements.txt
  - name: Get version from tag
    id: get_version
    run: echo "VERSION=${GITHUB_REF#refs/tags/v}" >> $GITHUB_OUTPUT
  - name: Build for platform
    run: ${{ matrix.build_command }}
    env:
      VERSION: ${{ steps.get_version.outputs.VERSION }}
```

---

## PyInstaller Spec Files

### Windows (`build_scripts/build_windows.spec`)

**Critical Settings:**
- `upx=False` - UPX compression causes PKG archive corruption
- `console=True` - Enable console for debugging (can be False for production)
- `hiddenimports` must include:
  - `chord_detector_v2`
  - `mido`, `mido.backends.rtmidi`, `rtmidi`
  - `PyQt5.QtCore`, `PyQt5.QtGui`, `PyQt5.QtWidgets`, `PyQt5.sip`
- `collect_submodules('mido')` and `collect_submodules('rtmidi')` - Required for dynamic imports
- `excludes` should include: `tkinter`, `matplotlib`, `numpy`, `scipy`, `pandas`

### macOS (`build_scripts/build_macos.spec`)

**Critical Settings:**
- Uses `--onedir` mode (not `--onefile`)
- `upx=False` in both `EXE` and `COLLECT` sections
- Same `hiddenimports` as Windows
- Additional `excludes` for unnecessary PyQt5 modules:
  - `PyQt5.QtBluetooth`, `PyQt5.QtNfc`, `PyQt5.QtWebSockets`, etc.

---

## User Requirements Compatibility

### ✅ Implemented Requirements

1. **MIDI Input Support**
   - Real-time MIDI note detection
   - Sustain pedal support
   - Multiple MIDI device support
   - Graceful handling when MIDI devices unavailable

2. **Chord Detection**
   - Advanced jazz chord detection (100+ patterns)
   - Support for triads, 7th chords, extensions, alterations
   - Inversions and slash chords
   - Interval detection (2-note intervals)
   - Scale detection (all modes of major, pentatonic scales)

3. **User Interface**
   - 88-key piano visualization
   - Dark/light mode themes
   - Customizable colors
   - Click-to-toggle notes (works without MIDI)
   - Right-click context menu

4. **Error Handling**
   - App launches successfully without MIDI devices
   - Friendly warning dialogs (not critical errors)
   - Crash logging to user's Desktop
   - Graceful degradation when dependencies missing

5. **Cross-Platform Compatibility**
   - Linux: `.deb` package
   - Windows: `.exe` executable
   - macOS: `.app` bundle (ZIP distribution)

### ⚠️ Known Limitations

1. **Windows Console Window**
   - Currently set to `console=True` for debugging
   - Can be changed to `console=False` for production builds

2. **macOS Code Signing**
   - App bundles are not code-signed
   - Users may need to allow unsigned apps in System Preferences

3. **MIDI Backend**
   - Requires `python-rtmidi` which needs native compilation
   - May require system dependencies on some platforms

---

## Pre-Build Checklist

Before pushing a tag or creating a release, verify:

### 1. Python Syntax
```bash
python3 -m py_compile ivory_v2.py
python3 -m py_compile chord_detector_v2.py
```

### 2. Import Validation
```bash
python3 -c "import ivory_v2; import chord_detector_v2"
```

### 3. Spec File Validation
- Verify `build_scripts/build_windows.spec` exists and is valid
- Verify `build_scripts/build_macos.spec` exists and is valid
- Check that all `hiddenimports` are present
- Verify `upx=False` is set

### 4. Workflow File Validation
- Verify `.github/workflows/release.yml` follows the working pattern
- Check that version extraction step exists
- Verify environment variable is passed to build step
- Ensure no shell field conflicts (let GitHub Actions use defaults)

### 5. Requirements File
- Verify `build_scripts/requirements.txt` exists
- Check that all dependencies are listed with correct versions

### 6. File Structure
```
Ivory/
├── ivory_v2.py                    # Main application
├── chord_detector_v2.py           # Chord detection module
├── build_scripts/
│   ├── requirements.txt           # Python dependencies
│   ├── build_windows.spec         # Windows PyInstaller spec
│   └── build_macos.spec           # macOS PyInstaller spec
└── .github/workflows/release.yml  # CI/CD workflow
```

---

## Build Process

### Triggering a Build

1. **Create and push a tag:**
   ```bash
   git tag v1.X.X
   git push origin v1.X.X
   ```

2. **Monitor GitHub Actions:**
   - Go to Actions tab in GitHub repository
   - Watch for all three platform builds to complete
   - Check for any errors or warnings

3. **Verify Artifacts:**
   - Linux: `ivory_X.X.X_all.deb`
   - Windows: `Ivory-Windows-vX.X.X.exe`
   - macOS: `Ivory-macOS-vX.X.X.zip`

### Build Troubleshooting

#### If Linux Build Fails:
- Check `dpkg-deb` command syntax
- Verify all required directories exist
- Check file permissions

#### If Windows Build Fails:
- Verify PowerShell syntax in build_command
- Check PyInstaller spec file for errors
- Ensure all hidden imports are listed

#### If macOS Build Fails:
- Check Python syntax (most common issue)
- Verify bash syntax in build_command
- Check PyInstaller spec file
- Ensure `--onedir` mode is used (not `--onefile`)

---

## Testing Checklist

### Before Release

- [ ] All three platforms build successfully
- [ ] Python syntax validated
- [ ] Import statements work
- [ ] Spec files are correct
- [ ] Workflow file follows working pattern
- [ ] Version extraction works correctly
- [ ] Artifacts are created and named correctly

### Post-Build Testing

#### Linux:
- [ ] `.deb` package installs without errors
- [ ] Application launches successfully
- [ ] MIDI input works (if device available)
- [ ] Click-to-toggle works
- [ ] Chord detection functions correctly

#### Windows:
- [ ] `.exe` launches without errors
- [ ] No console window appears (if `console=False`)
- [ ] MIDI input works (if device available)
- [ ] Click-to-toggle works
- [ ] Chord detection functions correctly
- [ ] Crash logs write to Desktop if errors occur

#### macOS:
- [ ] `.app` bundle launches successfully
- [ ] No code signing errors (or user can bypass)
- [ ] MIDI input works (if device available)
- [ ] Click-to-toggle works
- [ ] Chord detection functions correctly

---

## Common Issues and Solutions

### Issue: Syntax Error During PyInstaller Analysis

**Symptom:** `SyntaxError: expected 'except' or 'finally' block`

**Solution:**
- Check all `try:` blocks have matching `except:` or `finally:` clauses
- Verify indentation is correct (4 spaces)
- Run `python3 -m py_compile ivory_v2.py` before committing

### Issue: ModuleNotFoundError for mido.backends.rtmidi

**Symptom:** Windows/macOS builds succeed but app crashes with import error

**Solution:**
- Ensure `hiddenimports` includes `mido.backends.rtmidi`
- Add `collect_submodules('mido')` and `collect_submodules('rtmidi')`
- Verify `python-rtmidi` is in requirements.txt

### Issue: Windows EXE Crashes Silently

**Symptom:** EXE opens briefly then closes without error

**Solution:**
- Set `console=True` temporarily to see errors
- Check crash logs on Desktop
- Verify all dependencies are included in spec file
- Ensure error handling doesn't call `sys.exit(1)` before showing dialogs

### Issue: macOS Build Fails with "VERSIO" Error

**Symptom:** Build fails with error about VERSION variable

**Solution:**
- Ensure "Get version from tag" step exists
- Verify VERSION is passed as environment variable
- Use `$VERSION` (not `${VERSION}`) in bash commands
- Use `$env:VERSION` in PowerShell commands

### Issue: Linux Build Fails with dpkg-deb Warnings

**Symptom:** Build fails due to ownership warnings

**Solution:**
- Use `--root-owner-group` flag
- Filter out warning messages: `2>&1 | grep -vE "(warning|hint):"`
- Verify `.deb` file is created even if warnings occur

---

## Version History

### v1.1 (Current)
- ✅ Fixed syntax error in `ivory_v2.py` (update_timer try block)
- ✅ Fixed workflow to use environment variables correctly
- ✅ All platforms building successfully
- ✅ Improved error handling and crash logging

### v1.0.1 (Reference)
- ✅ Working build configuration
- ✅ Hardcoded version numbers in workflow
- ✅ Simple, straightforward build commands

---

## Maintenance Notes

### When Adding New Dependencies

1. Add to `build_scripts/requirements.txt`
2. Add to `hiddenimports` in both spec files if needed
3. Test build on all platforms
4. Update this document

### When Modifying Python Code

1. Always run syntax check before committing
2. Test imports work correctly
3. Verify error handling doesn't break builds
4. Check that MIDI error handling allows app to run without MIDI

### When Modifying Workflow

1. Test with a test tag first
2. Verify version extraction works
3. Check that environment variables are passed correctly
4. Ensure shell compatibility (bash for Linux/Mac, PowerShell for Windows)

---

## Contact and Support

For build issues or compatibility questions, refer to:
- GitHub Issues: https://github.com/ganten7/ivory/issues
- Build logs: GitHub Actions tab
- Crash logs: User's Desktop (if app crashes)

---

**Remember:** The most common build failure is Python syntax errors. Always validate syntax before pushing changes!
