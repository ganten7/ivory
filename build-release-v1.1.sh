#!/bin/bash
# Build Ivory for all platforms: Linux (.deb), Windows (.exe), macOS (.zip)
# Version can be set via VERSION environment variable, defaults to 1.1
# Set BUILD_PLATFORM environment variable to "linux", "windows", "macos", or "all" (default: "all")

set -e

VERSION="${VERSION:-1.1}"
RELEASE_DIR="release-artifacts"
BUILD_DIR="build-release-v1.1"

echo "=========================================="
echo "Building Ivory v${VERSION} for All Platforms"
echo "=========================================="
echo ""

# Clean previous builds
if [ -d "$BUILD_DIR" ]; then
    echo "Cleaning previous build directory..."
    rm -rf "$BUILD_DIR"
fi

mkdir -p "$BUILD_DIR"
mkdir -p "$RELEASE_DIR/ivory-linux"
mkdir -p "$RELEASE_DIR/ivory-windows"
mkdir -p "$RELEASE_DIR/ivory-macos"

# ============================================
# 1. BUILD LINUX .deb PACKAGE
# ============================================
echo "=========================================="
echo "1. Building Linux .deb package..."
echo "=========================================="

PACKAGE_NAME="ivory_${VERSION}_all"
DEB_BUILD_DIR="${BUILD_DIR}/${PACKAGE_NAME}"

# Create package structure
mkdir -p "${DEB_BUILD_DIR}/DEBIAN"
mkdir -p "${DEB_BUILD_DIR}/usr/bin"
mkdir -p "${DEB_BUILD_DIR}/usr/share/applications"
mkdir -p "${DEB_BUILD_DIR}/usr/share/icons/hicolor/16x16/apps"
mkdir -p "${DEB_BUILD_DIR}/usr/share/icons/hicolor/32x32/apps"
mkdir -p "${DEB_BUILD_DIR}/usr/share/icons/hicolor/48x48/apps"
mkdir -p "${DEB_BUILD_DIR}/usr/share/icons/hicolor/128x128/apps"
mkdir -p "${DEB_BUILD_DIR}/usr/share/metainfo"

# Create DEBIAN/control
cat > "${DEB_BUILD_DIR}/DEBIAN/control" << EOF
Package: ivory
Version: ${VERSION}
Section: sound
Priority: optional
Architecture: all
Depends: python3, python3-pyqt5, python3-mido, python3-rtmidi
Maintainer: Ivory Development Team
Description: MIDI Keyboard Monitor with Advanced Chord Detection v${VERSION}
 Ivory is a real-time MIDI keyboard monitor and chord detection application.
 Features:
  - Real-time visualization of 88-key piano keyboard
  - Advanced jazz chord detection with 100+ chord patterns
  - MIDI input support with sustain pedal
  - Click-to-toggle notes for testing without MIDI keyboard
  - Dark/light mode themes
  - Customizable colors
  - Cross-platform (Linux, Windows, macOS)
 .
 Version ${VERSION} improvements:
  - Fixed interval detection (2-note intervals now work)
  - Fixed scale detection for all modes of major
  - Fixed Major and Minor Pentatonic scale detection
  - Enhanced extended chord detection (maj9, maj13#11, m9, m13)
  - Improved slash chord notation for inversions
  - Better dominant 13#11 detection
  - Windows compatibility fixes (os.fork() check)
  - All critical user requirements implemented
EOF

# Copy application files
cp ivory_v2.py "${DEB_BUILD_DIR}/usr/bin/ivory"
cp chord_detector_v2.py "${DEB_BUILD_DIR}/usr/bin/chord_detector_v2.py"
chmod +x "${DEB_BUILD_DIR}/usr/bin/ivory"

# Create desktop file
cat > "${DEB_BUILD_DIR}/usr/share/applications/ivory.desktop" << EOF
[Desktop Entry]
Name=Ivory
Comment=MIDI Keyboard Monitor with Advanced Chord Detection
Exec=/usr/bin/ivory
Icon=ivory
Terminal=false
Type=Application
Categories=AudioVideo;Audio;Music;
Keywords=midi;keyboard;piano;chord;detection;music;
EOF

# Copy icons
if [ -d "screenshots/icon.iconset" ]; then
    if [ -f "screenshots/icon.iconset/icon_16x16.png" ]; then
        cp screenshots/icon.iconset/icon_16x16.png "${DEB_BUILD_DIR}/usr/share/icons/hicolor/16x16/apps/ivory.png" 2>/dev/null || true
    fi
    if [ -f "screenshots/icon.iconset/icon_32x32.png" ]; then
        cp screenshots/icon.iconset/icon_32x32.png "${DEB_BUILD_DIR}/usr/share/icons/hicolor/32x32/apps/ivory.png" 2>/dev/null || true
    fi
    if [ -f "screenshots/icon.iconset/icon_48x48.png" ]; then
        cp screenshots/icon.iconset/icon_48x48.png "${DEB_BUILD_DIR}/usr/share/icons/hicolor/48x48/apps/ivory.png" 2>/dev/null || true
    fi
    if [ -f "screenshots/icon.iconset/icon_128x128.png" ]; then
        cp screenshots/icon.iconset/icon_128x128.png "${DEB_BUILD_DIR}/usr/share/icons/hicolor/128x128/apps/ivory.png" 2>/dev/null || true
    fi
fi

# Create metainfo
cat > "${DEB_BUILD_DIR}/usr/share/metainfo/ivory.metainfo.xml" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>com.ivory.app</id>
  <name>Ivory</name>
  <summary>MIDI Keyboard Monitor with Advanced Chord Detection</summary>
  <description>
    <p>Ivory is a real-time MIDI keyboard monitor and chord detection application.</p>
    <p>Features:</p>
    <ul>
      <li>Real-time visualization of 88-key piano keyboard</li>
      <li>Advanced jazz chord detection with 100+ chord patterns</li>
      <li>MIDI input support with sustain pedal</li>
      <li>Click-to-toggle notes for testing without MIDI keyboard</li>
      <li>Dark/light mode themes</li>
      <li>Customizable colors</li>
    </ul>
    <p>Version ${VERSION} includes fixes for interval detection, scale detection, and extended chords.</p>
  </description>
  <screenshots>
    <screenshot type="default">
      <image>https://raw.githubusercontent.com/ganten/ivory/master/screenshots/Cm11.png</image>
      <caption>Ivory detecting a Cm11 chord</caption>
    </screenshot>
    <screenshot>
      <image>https://raw.githubusercontent.com/ganten/ivory/master/screenshots/D7-b9-11.png</image>
      <caption>Ivory detecting an altered dominant chord D7(b9,#11)</caption>
    </screenshot>
    <screenshot>
      <image>https://raw.githubusercontent.com/ganten/ivory/master/screenshots/Ebm11.png</image>
      <caption>Ivory detecting an Ebm11 chord</caption>
    </screenshot>
  </screenshots>
  <launchable type="desktop-id">ivory.desktop</launchable>
  <provides>
    <binary>ivory</binary>
  </provides>
  <releases>
    <release version="${VERSION}" date="$(date +%Y-%m-%d)">
      <description>
        <p>Version ${VERSION} improvements:</p>
        <ul>
          <li>Fixed interval detection (2-note intervals)</li>
          <li>Fixed scale detection for all modes of major</li>
          <li>Fixed Major and Minor Pentatonic scales</li>
          <li>Enhanced extended chord detection</li>
          <li>Windows compatibility fixes</li>
        </ul>
      </description>
    </release>
  </releases>
  <categories>
    <category>Audio</category>
    <category>Music</category>
  </categories>
  <keywords>
    <keyword>midi</keyword>
    <keyword>piano</keyword>
    <keyword>keyboard</keyword>
    <keyword>chord</keyword>
    <keyword>music</keyword>
    <keyword>detection</keyword>
    <keyword>jazz</keyword>
    <keyword>harmony</keyword>
  </keywords>
</component>
EOF

# Build .deb (use --root-owner-group for GitHub Actions compatibility)
dpkg-deb --build --root-owner-group "${DEB_BUILD_DIR}" "${RELEASE_DIR}/ivory-linux/ivory_${VERSION}_all.deb" || {
    echo "ERROR: dpkg-deb failed"
    echo "Trying without --root-owner-group..."
    dpkg-deb --build "${DEB_BUILD_DIR}" "${RELEASE_DIR}/ivory-linux/ivory_${VERSION}_all.deb"
}

echo "✓ Linux .deb built: ${RELEASE_DIR}/ivory-linux/ivory_${VERSION}_all.deb"
echo ""

# ============================================
# 2. BUILD WINDOWS .exe PACKAGE (optional)
# ============================================
BUILD_PLATFORM="${BUILD_PLATFORM:-all}"
if [ "$BUILD_PLATFORM" = "all" ] || [ "$BUILD_PLATFORM" = "windows" ]; then
    echo "=========================================="
    echo "2. Building Windows .exe package..."
    echo "=========================================="

    if command -v pyinstaller >/dev/null 2>&1; then
        cd build_scripts
        pyinstaller --clean build_windows.spec || {
            echo "⚠ Windows build failed - continuing..."
            cd ..
        }
        cd ..
        
        if [ -f "build_scripts/dist/Ivory.exe" ]; then
            cp "build_scripts/dist/Ivory.exe" "${RELEASE_DIR}/ivory-windows/Ivory-Windows-v${VERSION}.exe"
            echo "✓ Windows .exe built: ${RELEASE_DIR}/ivory-windows/Ivory-Windows-v${VERSION}.exe"
        elif [ -f "build_scripts/dist/Ivory/Ivory.exe" ]; then
            cp "build_scripts/dist/Ivory/Ivory.exe" "${RELEASE_DIR}/ivory-windows/Ivory-Windows-v${VERSION}.exe"
            echo "✓ Windows .exe built: ${RELEASE_DIR}/ivory-windows/Ivory-Windows-v${VERSION}.exe"
        else
            echo "⚠ Windows build failed - pyinstaller output may have errors"
        fi
    else
        echo "⚠ pyinstaller not found - skipping Windows build"
        echo "  Install with: pip install pyinstaller"
    fi
    echo ""
fi

# ============================================
# 3. BUILD macOS .zip PACKAGE (optional)
# ============================================
if [ "$BUILD_PLATFORM" = "all" ] || [ "$BUILD_PLATFORM" = "macos" ]; then
    echo "=========================================="
    echo "3. Building macOS .zip package..."
    echo "=========================================="

    if command -v pyinstaller >/dev/null 2>&1; then
        cd build_scripts
        pyinstaller --clean build_macos.spec || {
            echo "⚠ macOS build failed - continuing..."
            cd ..
        }
        cd ..
        
        if [ -d "build_scripts/dist/Ivory.app" ]; then
            cd build_scripts/dist
            zip -r "../../${RELEASE_DIR}/ivory-macos/Ivory-macOS-v${VERSION}.zip" Ivory.app >/dev/null 2>&1 || {
                echo "⚠ ZIP creation failed"
                cd ../..
            }
            cd ../..
            if [ -f "${RELEASE_DIR}/ivory-macos/Ivory-macOS-v${VERSION}.zip" ]; then
                echo "✓ macOS .zip built: ${RELEASE_DIR}/ivory-macos/Ivory-macOS-v${VERSION}.zip"
            fi
        else
            echo "⚠ macOS build failed - checking dist directory..."
            ls -la build_scripts/dist/ 2>/dev/null || true
        fi
    else
        echo "⚠ pyinstaller not found - skipping macOS build"
        echo "  Install with: pip install pyinstaller"
    fi
    echo ""
fi

# ============================================
# SUMMARY
# ============================================
echo "=========================================="
echo "Build Summary"
echo "=========================================="
echo ""
echo "Built packages for Ivory v${VERSION}:"
echo ""
# Use find instead of ls with globs to avoid quote issues
if find "${RELEASE_DIR}/ivory-linux" -name "*.deb" -type f 2>/dev/null | head -1 | read deb_file; then
    ls -lh "$deb_file" | awk '{print "  Linux:   " $9 " (" $5 ")"}'
else
    echo "  Linux:   (not built)"
fi
if find "${RELEASE_DIR}/ivory-windows" -name "*.exe" -type f 2>/dev/null | head -1 | read exe_file; then
    ls -lh "$exe_file" | awk '{print "  Windows: " $9 " (" $5 ")"}'
else
    echo "  Windows: (not built)"
fi
if find "${RELEASE_DIR}/ivory-macos" -name "*.zip" -type f 2>/dev/null | head -1 | read zip_file; then
    ls -lh "$zip_file" | awk '{print "  macOS:   " $9 " (" $5 ")"}'
else
    echo "  macOS:   (not built)"
fi
echo ""
echo "All artifacts are in: ${RELEASE_DIR}/"
echo ""

