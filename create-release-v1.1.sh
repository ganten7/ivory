#!/bin/bash
# Create Git release for v1.1
# This script commits changes, creates tag, and prepares release

set -e

VERSION="1.1"
TAG="v${VERSION}"

echo "=========================================="
echo "Creating Release ${TAG}"
echo "=========================================="
echo ""

# Check we're on the right branch
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: ${CURRENT_BRANCH}"
echo ""

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "Uncommitted changes detected:"
    git status --short
    echo ""
    read -p "Commit these changes? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add -A
        git commit -m "Release v${VERSION}: Interval detection, scale detection fixes, Windows compatibility

- Fixed interval detection (2-note intervals now work)
- Fixed scale detection for all modes of major
- Fixed Major and Minor Pentatonic scale detection
- Enhanced extended chord detection (maj9, maj13#11, m9, m13)
- Improved slash chord notation for inversions
- Windows compatibility fixes (os.fork() check)
- Updated README with correct screenshot paths
- Added comprehensive release notes"
    else
        echo "Skipped commit. Please commit changes manually before creating release."
        exit 1
    fi
fi

# Check if tag already exists
if git rev-parse "${TAG}" >/dev/null 2>&1; then
    echo "⚠ Tag ${TAG} already exists!"
    read -p "Delete and recreate? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git tag -d "${TAG}"
        git push origin ":refs/tags/${TAG}" 2>/dev/null || true
    else
        echo "Aborted."
        exit 1
    fi
fi

# Create tag
echo "Creating tag ${TAG}..."
git tag -a "${TAG}" -m "Release v${VERSION}

Major Features:
- Interval detection for 2-note inputs
- Complete scale detection (all modes of major, pentatonic)
- Enhanced extended chord detection
- Windows compatibility fixes

See RELEASE_v1.1.md for full changelog."

echo "✓ Tag created: ${TAG}"
echo ""

# Show what will be pushed
echo "Ready to push:"
echo "  Branch: ${CURRENT_BRANCH}"
echo "  Tag: ${TAG}"
echo ""
read -p "Push to GitHub? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Pushing branch..."
    git push origin "${CURRENT_BRANCH}"
    
    echo "Pushing tag..."
    git push origin "${TAG}"
    
    echo ""
    echo "=========================================="
    echo "✓ Release ${TAG} pushed to GitHub!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "1. Go to GitHub: https://github.com/ganten/ivory/releases/new"
    echo "2. Select tag: ${TAG}"
    echo "3. Title: Release v${VERSION}"
    echo "4. Copy contents of RELEASE_v1.1.md as release notes"
    echo "5. Upload artifacts from release-artifacts/:"
    echo "   - ivory-linux/ivory_${VERSION}_all.deb"
    echo "   - ivory-windows/Ivory-Windows-v${VERSION}.exe"
    echo "   - ivory-macos/Ivory-macOS-v${VERSION}.zip"
    echo ""
else
    echo "Skipped push. Run manually:"
    echo "  git push origin ${CURRENT_BRANCH}"
    echo "  git push origin ${TAG}"
fi

