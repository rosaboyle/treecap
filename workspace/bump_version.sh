#!/usr/bin/env bash
#
# Bump the treecap version in both places that must stay in sync:
#   - pyproject.toml          (version = "X.Y.Z")
#   - src/treecap/__init__.py (__version__ = "X.Y.Z")
#
# Usage:
#   ./workspace/bump_version.sh patch     # 0.1.0 -> 0.1.1  (default)
#   ./workspace/bump_version.sh minor     # 0.1.0 -> 0.2.0
#   ./workspace/bump_version.sh major     # 0.1.0 -> 1.0.0
#   ./workspace/bump_version.sh 0.4.2     # set an exact version
#
# It only edits the files. Build/publish afterwards with ./publish.sh.
set -euo pipefail

# Always operate from the repo root (parent of this script's dir).
cd "$(dirname "$0")/.."

INIT="src/treecap/__init__.py"
PYPROJECT="pyproject.toml"

# Read the current version from __init__.py.
CURRENT="$(grep -E '^__version__' "$INIT" | sed -E 's/.*"([^"]+)".*/\1/')"
if [[ -z "$CURRENT" ]]; then
  echo "ERROR: could not find __version__ in $INIT" >&2
  exit 1
fi

BUMP="${1:-patch}"

if [[ "$BUMP" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  # Caller passed an explicit X.Y.Z version.
  NEW="$BUMP"
else
  IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT"
  case "$BUMP" in
    major) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
    minor) MINOR=$((MINOR + 1)); PATCH=0 ;;
    patch) PATCH=$((PATCH + 1)) ;;
    *)
      echo "ERROR: unknown bump '$BUMP' (use major|minor|patch or X.Y.Z)" >&2
      exit 2
      ;;
  esac
  NEW="${MAJOR}.${MINOR}.${PATCH}"
fi

if [[ "$NEW" == "$CURRENT" ]]; then
  echo "ERROR: new version equals current version ($CURRENT)" >&2
  exit 3
fi

# Update both files in place (BSD/macOS sed needs the '' after -i).
sed -i '' -E "s/^__version__ = \"[^\"]+\"/__version__ = \"$NEW\"/" "$INIT"
sed -i '' -E "s/^version = \"[^\"]+\"/version = \"$NEW\"/" "$PYPROJECT"

echo "Bumped version: $CURRENT -> $NEW"
echo "  $INIT"
echo "  $PYPROJECT"
echo
echo "Next:"
echo "  ./publish.sh --build   # build + check locally"
echo "  ./publish.sh           # build + upload to PyPI"
