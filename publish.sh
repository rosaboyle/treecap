#!/usr/bin/env bash
#
# Bump the version, build, and publish treecap to PyPI using twine.
#
# By default it bumps the PATCH version, builds, and uploads to real PyPI.
# The bump keeps these two files in sync:
#   - pyproject.toml          (version = "X.Y.Z")
#   - src/treecap/__init__.py (__version__ = "X.Y.Z")
#
# Usage:
#   ./publish.sh            # bump patch, build, upload to PyPI  (default)
#   ./publish.sh minor      # bump minor, build, upload to PyPI
#   ./publish.sh major      # bump major, build, upload to PyPI
#   ./publish.sh 0.4.2      # set exact version, build, upload to PyPI
#   ./publish.sh --build    # build + check ONLY, no version bump, no upload
#   ./publish.sh --test     # bump patch, build, upload to TestPyPI
#
# Auth: twine reads credentials from ~/.pypirc, or from the env vars
#   TWINE_USERNAME=__token__
#   TWINE_PASSWORD=pypi-<your-api-token>
# Create a token at https://pypi.org/manage/account/token/
#
set -euo pipefail

# Always run from the directory this script lives in.
cd "$(dirname "$0")"

INIT="src/treecap/__init__.py"
PYPROJECT="pyproject.toml"

TARGET="pypi"
UPLOAD=1
DO_BUMP=1
BUMP="patch"   # default bump level

for arg in "$@"; do
  case "$arg" in
    --test)               TARGET="testpypi" ;;
    --build)              UPLOAD=0; DO_BUMP=0 ;;
    major|minor|patch)    BUMP="$arg" ;;
    [0-9]*.[0-9]*.[0-9]*) BUMP="$arg" ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      echo "Unknown option: $arg" >&2
      exit 2
      ;;
  esac
done

if [[ "$DO_BUMP" -eq 1 ]]; then
  CURRENT="$(grep -E '^__version__' "$INIT" | sed -E 's/.*"([^"]+)".*/\1/')"
  if [[ -z "$CURRENT" ]]; then
    echo "ERROR: could not find __version__ in $INIT" >&2
    exit 1
  fi

  if [[ "$BUMP" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    NEW="$BUMP"   # explicit X.Y.Z
  else
    IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT"
    case "$BUMP" in
      major) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
      minor) MINOR=$((MINOR + 1)); PATCH=0 ;;
      patch) PATCH=$((PATCH + 1)) ;;
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
  echo "==> Bumped version: $CURRENT -> $NEW"
fi

echo "==> Cleaning old build artifacts"
rm -rf dist build ./*.egg-info src/*.egg-info

echo "==> Building sdist + wheel"
python -m build

echo "==> Validating metadata"
twine check dist/*

if [[ "$UPLOAD" -eq 0 ]]; then
  echo "==> Build-only mode; skipping upload. Artifacts are in ./dist"
  exit 0
fi

if [[ "$TARGET" == "testpypi" ]]; then
  echo "==> Uploading to TestPyPI"
  twine upload --repository testpypi dist/*
  echo
  echo "Done. Test install with:"
  echo "  pipx install --index-url https://test.pypi.org/simple/ treecap"
else
  echo "==> Uploading to PyPI"
  twine upload dist/*
  echo
  echo "Done. Install with:"
  echo "  pipx install treecap"
fi
