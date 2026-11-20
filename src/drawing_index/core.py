"""Parse drawing file names and build an index of the latest revisions."""
from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from pathlib import Path

NAME_RE = re.compile(
    r"^(?P<number>[A-Z]{1,2}-\d{3}[A-Z]?)_(?P<title>[^_]+)_Rev(?P<rev>[A-Za-z0-9]+)$"
)
EXTENSIONS = {".pdf", ".dwg", ".dxf", ".rvt", ".png"}
DISCIPLINES = {
    "G": "General",
    "C": "Civil",
    "A": "Architectural",
    "S": "Structural",
    "M": "Mechanical",
    "E": "Electrical",
    "P": "Plumbing",
    "FP": "Fire Protection",
    "T": "Telecom",
}


@dataclass(frozen=True)
class Drawing:
    """One drawing file: sheet number, title, revision and file name."""

    number: str
    title: str
    revision: str
    filename: str

    @property
    def discipline(self) -> str:
        """Discipline name taken from the letters before the dash."""
        return DISCIPLINES.get(self.number.split("-")[0], "Other")


def revision_key(rev: str) -> tuple[int, int, str]:
    """Sort key: letters A < B < Z < AA, then plain numbers by value."""
    if rev.isdigit():
        return (1, int(rev), "")
    return (0, len(rev), rev.upper())


def parse_filename(filename: str) -> Drawing | None:
    """Return a Drawing for a valid file name, or None when it does not match."""
    path = Path(filename)
    if path.suffix.lower() not in EXTENSIONS:
        return None
    match = NAME_RE.match(path.stem)
    if not match:
        return None
    title = match["title"].replace("-", " ")
    return Drawing(match["number"], title, match["rev"].upper(), path.name)


def scan_folder(folder: Path) -> tuple[list[Drawing], list[str]]:
    """Return (drawings, skipped file names) for every file in the folder tree."""
    drawings: list[Drawing] = []
    skipped: list[str] = []
    for path in sorted(p for p in Path(folder).rglob("*") if p.is_file()):
        drawing = parse_filename(path.name)
        if drawing:
            drawings.append(drawing)
        else:
            skipped.append(path.name)
    return drawings, skipped


def latest_only(drawings: list[Drawing]) -> list[Drawing]:
    """Keep only the highest revision of each sheet number."""
    best: dict[str, Drawing] = {}
    for d in drawings:
        current = best.get(d.number)
        if current is None or revision_key(d.revision) > revision_key(current.revision):
            best[d.number] = d
    return list(best.values())


def sort_drawings(drawings: list[Drawing]) -> list[Drawing]:
    """Order by sheet number, then by revision."""
    return sorted(drawings, key=lambda d: (d.number, revision_key(d.revision)))


def to_markdown(drawings: list[Drawing]) -> str:
    """Render the index as a Markdown table."""
    lines = [
        "| Sheet | Title | Rev | Discipline |",
        "|-------|-------|-----|------------|",
    ]
    for d in drawings:
        lines.append(f"| {d.number} | {d.title} | {d.revision} | {d.discipline} |")
    return "\n".join(lines)


def to_csv(drawings: list[Drawing]) -> str:
    """Render the index as CSV text."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["sheet", "title", "revision", "discipline", "file"])
    for d in drawings:
        writer.writerow([d.number, d.title, d.revision, d.discipline, d.filename])
    return buffer.getvalue().rstrip("\n")
