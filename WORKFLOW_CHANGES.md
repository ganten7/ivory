# GitHub Actions Workflow Changes for v1.0.13

## Overview
This document describes the changes made to `.github/workflows/release.yml` to support building and releasing Ivory v1.0.13 across Linux, Windows, and macOS platforms.

## Changes Made

### 1. Linux Build Improvements

#### Problem
The initial workflow expected a complete `ivory_1.0.13_all/` directory structure to exist in the repository, which caused build failures if any files were missing.

#### Solution
Made the Linux build process more robust by:

- **Auto-creating directory structure**: The workflow now creates all necessary directories if they don't exist:
  ```
  - ivory_1.0.13_all/DEBIAN/
  - ivory_1.0.13_all/usr/bin/
  - ivory_1.0.13_all/usr/share/applications/
  - ivory_1.0.13_all/usr/share/metainfo/
  - ivory_1.0.13_all/usr/share/appdata/
  - ivory_1.0.13_all/usr/share/icons/hicolor/{16x16,32x32,48x48,64x64,128x128}/apps/
  ```

- **Auto-generating control file**: If `DEBIAN/control` doesn't exist, the workflow creates it with default values:
  - Package: ivory
  - Version: 1.0.13
  - Dependencies: python3, python3-pyqt5, python3-mido, python3-rtmidi

- **Graceful metadata handling**: The workflow copies metadata files (desktop, metainfo, appdata) if they exist, but doesn't fail if they're missing.

- **Icon size generation**: If smaller icon sizes are missing, they're automatically generated from the 128x128 version using PIL/Pillow.

#### YAML Syntax Fix
- **Issue**: Initial implementation used heredoc syntax (`<< 'CONTROL_EOF'`) which YAML interpreted as a merge key operator, causing syntax errors.
- **Fix**: Replaced heredoc with `printf` command to write the control file content directly, avoiding YAML parsing conflicts.

### 2. Windows Build

#### Requirements
- `screenshots/icon.ico` - Multi-size Windows icon (16x16, 32x32, 48x48, 64x64, 128x128, 256x256)
- `build_scripts/build_windows.spec` - PyInstaller spec file configured to use `icon.ico`
- Source files: `ivory_v2.py`, `chord_detector_v2.py`

#### Process
1. Installs build dependencies from `build_scripts/requirements.txt`
2. Runs PyInstaller using `build_windows.spec`
3. Renames output to `Ivory-Windows-v1.0.13.exe`
4. Packages as artifact

### 3. macOS Build

#### Requirements
- `screenshots/icon.iconset/` - macOS iconset directory containing all required icon sizes
- `build_scripts/build_macos.spec` - PyInstaller spec file configured to use `icon.icns`
- Source files: `ivory_v2.py`, `chord_detector_v2.py`

#### Process
1. Converts `icon.iconset` to `icon.icns` using `iconutil` if needed
2. Installs build dependencies from `build_scripts/requirements.txt`
3. Runs PyInstaller using `build_macos.spec`
4. Creates `Ivory.app` bundle
5. Zips the app bundle as `Ivory-macOS-v1.0.13.zip`
6. Packages as artifact

## Workflow Trigger

The workflow triggers automatically when a tag matching `v*.*.*` is pushed to the repository:

```yaml
on:
  push:
    tags:
      - 'v*.*.*'
```

## Build Matrix

The workflow uses a build matrix to build for all three platforms in parallel:

- **ubuntu-latest**: Builds `.deb` package
- **windows-latest**: Builds `.exe` executable
- **macos-latest**: Builds `.zip` containing `.app` bundle

## Release Process

After all builds complete successfully:

1. All artifacts are downloaded
2. A GitHub Release is created using the tag name
3. Release notes are read from `RELEASE_v1.0.13.md`
4. Artifacts and screenshots are attached to the release

## Files Required in Repository

### Source Files
- `ivory_v2.py` - Main application
- `chord_detector_v2.py` - Chord detection module

### Build Configuration
- `build_scripts/build_windows.spec` - Windows PyInstaller config
- `build_scripts/build_macos.spec` - macOS PyInstaller config
- `build_scripts/requirements.txt` - Python dependencies

### Icons
- `screenshots/icon.ico` - Windows icon (multi-size)
- `screenshots/icon.iconset/` - macOS iconset directory
- `screenshots/icon.png` - Source icon (used for Linux)

### Package Structure (Linux)
- `ivory_1.0.13_all/DEBIAN/control` - Debian package metadata
- `ivory_1.0.13_all/usr/share/applications/ivory.desktop` - Desktop entry
- `ivory_1.0.13_all/usr/share/metainfo/ivory.metainfo.xml` - AppStream metadata
- `ivory_1.0.13_all/usr/share/appdata/ivory.appdata.xml` - AppStream metadata (legacy)
- `ivory_1.0.13_all/usr/share/icons/hicolor/*/apps/ivory.png` - Application icons

### Release Documentation
- `RELEASE_v1.0.13.md` - Release notes (used in GitHub Release)

## Troubleshooting

### Build Failures

1. **Linux build fails**: Check that source files exist and package structure is valid
2. **Windows build fails**: Verify `icon.ico` exists and `build_windows.spec` is correct
3. **macOS build fails**: Ensure `icon.iconset` directory exists and contains all required sizes

### YAML Syntax Errors

- Avoid heredoc syntax (`<<`) in YAML files
- Use `printf` or multi-line strings with proper indentation
- Validate YAML before committing: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml'))"`

### Missing Files

The workflow is designed to be resilient to missing files:
- Linux: Creates default control file if missing
- Windows/macOS: Will fail if required files are missing (by design)

## Version Updates

To update for a new version:

1. Update version number in:
   - `ivory_1.0.13_all/DEBIAN/control`
   - `build_scripts/build_macos.spec` (CFBundleVersion, CFBundleShortVersionString)
   - `.github/workflows/release.yml` (artifact names, version references)
   - `RELEASE_v1.0.13.md` (create new file for new version)

2. Update package directory name if needed (e.g., `ivory_1.0.14_all/`)

3. Update workflow matrix to reference new version

4. Create and push new tag (e.g., `v1.0.14`)

## Related Files

- `.github/workflows/release.yml` - Main workflow file
- `release-v1.0.13.sh` - Helper script to commit changes and create tag
- `RELEASE_v1.0.13.md` - Release notes

## History

- **v1.0.13**: Initial workflow implementation with cross-platform support
  - Fixed YAML syntax error (heredoc → printf)
  - Made Linux build robust with auto-creation of missing files
  - Added Windows icon support (icon.ico)
  - Added macOS iconset support (icon.iconset)

