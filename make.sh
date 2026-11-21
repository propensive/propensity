#!/bin/sh
# Build Propensity, render the proofs, run the checks.
#
#   ./make.sh          the font: build/Propensity-Regular.ttf and .woff2, proofs in proofs/
#   ./make.sh greek    the unfinished Greek letters, as a separate work-in-progress font
#                      in wip/ with its own proofs; the font itself is not touched
set -e
cd "$(dirname "$0")"
PY=".venv/bin/python -I"
SRC=vendor/marcellus/Marcellus-Regular.ttf
SC=vendor/marcellus-sc/MarcellusSC-Regular.ttf
if [ "$1" = "greek" ]; then
  OUT=wip/Propensity-Greek-WIP.ttf
  $PY tools/build.py "$SRC" "$SC" "$OUT" --greek
  $PY tools/proof.py "$OUT" wip/proofs
  $PY tools/check.py "$SRC" "$OUT"
else
  OUT=build/Propensity-Regular.ttf
  $PY tools/build.py "$SRC" "$SC" "$OUT"
  cp build/OFL.txt license.md    # the licence also sits at the top of the repository
  $PY tools/proof.py "$OUT" proofs
  $PY tools/check.py "$SRC" "$OUT" build/Propensity-Regular.woff2
fi
