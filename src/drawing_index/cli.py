"""Command line entry point."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import latest_only, scan_folder, sort_drawings, to_csv, to_markdown


def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    p = argparse.ArgumentParser(prog="drawing_index", description="Drawing index from file names.")
    p.add_argument("folder", type=Path, help="folder holding the drawing files")
    p.add_argument("--format", choices=["md", "csv"], default="md", help="output format")
    p.add_argument("--all-revisions", action="store_true", help="list every revision, not only the latest")
    p.add_argument("--discipline", help="keep one discipline letter code, for example M")
    p.add_argument("--out", type=Path, help="write to this file instead of the screen")
    return p


def main(argv: list[str] | None = None) -> int:
    """Run the tool and return the exit code."""
    args = build_parser().parse_args(argv)
    if not args.folder.is_dir():
        print(f"error: {args.folder} is not a folder", file=sys.stderr)
        return 2
    drawings, skipped = scan_folder(args.folder)
    if not args.all_revisions:
        drawings = latest_only(drawings)
    if args.discipline:
        prefix = args.discipline.upper() + "-"
        drawings = [d for d in drawings if d.number.startswith(prefix)]
    drawings = sort_drawings(drawings)
    text = to_csv(drawings) if args.format == "csv" else to_markdown(drawings)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
        print(f"wrote {len(drawings)} drawings to {args.out}")
    else:
        print(text)
    if skipped:
        print(f"\nskipped {len(skipped)} file(s) that do not match the naming pattern: "
              + ", ".join(skipped), file=sys.stderr)
    return 0
