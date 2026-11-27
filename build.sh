#!/usr/bin/env bash
# Regenerate every deliverable in the kit.
set -euo pipefail
cd "$(dirname "$0")"
PY=/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
$PY banners/kit/tools/build.py
$PY banners/kit/tools/preview.py
$PY guide/build_guide.py
