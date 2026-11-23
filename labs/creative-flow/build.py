"""Build a reviewable creative asset from a fictional brand brief."""
import argparse
import html
import json
import re
from pathlib import Path

HEX = re.compile(r"#[0-9a-fA-F]{6}")
UNSUPPORTED = re.compile(r"\b(guaranteed|cure|clinically proven)\b", re.IGNORECASE)


def render(brief: dict) -> str:
    fields = ("brand", "headline", "copy", "background", "foreground")
    if any(not isinstance(brief.get(key), str) or not brief[key].strip() for key in fields):
        raise ValueError("Each brief field must contain text")
    if any(not HEX.fullmatch(brief[key]) for key in ("background", "foreground")):
        raise ValueError("Palette values must be six-digit hex colors")
    if UNSUPPORTED.search(" ".join(brief[key] for key in ("brand", "headline", "copy"))):
        raise ValueError("Unsupported claim requires editorial review")
    brand, headline, copy = (html.escape(brief[key]) for key in ("brand", "headline", "copy"))
    return f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{brand} campaign card</title>
<style>
body {{ margin: 0; font: 1.125rem system-ui; }}
main {{ padding: clamp(2rem, 8vw, 7rem); min-height: 26rem;
  background: {brief["background"]}; color: {brief["foreground"]}; }}
h1 {{ max-width: 15ch; font-size: clamp(2rem, 6vw, 5rem); line-height: 1.05; }}
</style>
<main>
  <p>{brand}</p>
  <h1>{headline}</h1>
  <p>{copy}</p>
</main>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("brief", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        brief = json.loads(args.brief.read_text(encoding="utf-8"))
        asset = render(brief)
        if brief.get("review_status") != "approved":
            raise ValueError("Human approval required before export")
        with args.output.open("x", encoding="utf-8") as file:
            file.write(asset)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
