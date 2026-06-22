#!/usr/bin/env bash
#
# Build and publish treecap to PyPI using twine.
#
# Usage:
#   ./publish.sh            # build, check, upload to real PyPI
#   ./publish.sh --test     # upload to TestPyPI instead (safe dry-run target)
#   ./publish.sh --build    # build + check only, no upload
#
# Auth: twine reads credentials from ~/.pypirc, or from the env vars
#   TWINE_USERNAME=__token__
#   TWINE_PASSWORD=pypi-<your-api-token>
# Create a token at https://pypi.org/manage/account/token/
#
set -euo pipefail

# Always run from the directory this script lives in.
cd "$(dirname "$0")"

TARGET="pypi"
UPLOAD=1

for arg in "$@"; do
  case "$arg" in
    --test)  TARGET="testpypi" ;;
    --build) UPLOAD=0 ;;
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
