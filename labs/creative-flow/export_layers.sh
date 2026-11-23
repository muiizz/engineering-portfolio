#!/usr/bin/env bash
set -euo pipefail
if [[ $# != 2 ]]; then
  echo "Usage: bash export_layers.sh BRIEF.json NEW_OUTPUT.psd" >&2
  exit 2
fi
brief=$1
output=$2
[[ ! -e "$output" ]]
here=$(cd "$(dirname "$0")" && pwd)
temp=$(mktemp -d)
trap 'rm -rf "$temp"' EXIT
python3 "$here/build.py" "$brief" "$temp/card.html"
mapfile -t colors < <(python3 -c 'import json,sys; b=json.load(open(sys.argv[1])); print(b["background"]); print(b["foreground"])' "$brief")
python3 - "$brief" "$temp/copy.txt" <<'PY'
import json
import sys
import textwrap
from pathlib import Path
brief = json.loads(Path(sys.argv[1]).read_text())
lines = [brief["brand"], "", textwrap.fill(brief["headline"], 35), "", textwrap.fill(brief["copy"], 53)]
Path(sys.argv[2]).write_text("\n".join(lines))
PY
convert -size 1200x630 "xc:${colors[0]}" "$temp/background.png"
convert -size 1060x520 -background none -fill "${colors[1]}" -font DejaVu-Sans -pointsize 36 \
  caption:"$(cat "$temp/copy.txt")" "$temp/label.png"
convert -size 1200x630 xc:none "$temp/label.png" -geometry +70+55 -compose over -composite "$temp/copy.png"
convert "$temp/background.png" "$temp/copy.png" -compose over -composite "$temp/composite.png"
convert "$temp/composite.png" "$temp/background.png" "$temp/copy.png" -alpha set -colorspace sRGB -type TrueColorAlpha -compress None "$temp/export.psd"
cp -n "$temp/export.psd" "$output"
