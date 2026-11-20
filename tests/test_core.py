from drawing_index.cli import main
from drawing_index.core import (
    Drawing, latest_only, parse_filename, revision_key, scan_folder, sort_drawings, to_csv, to_markdown,
)


def test_parse_valid():
    d = parse_filename("A-101_Floor-Plan-Level-1_RevC.pdf")
    assert d == Drawing("A-101", "Floor Plan Level 1", "C", "A-101_Floor-Plan-Level-1_RevC.pdf")


def test_parse_two_letter_discipline():
    d = parse_filename("FP-101_Sprinkler-Plan_RevA.dwg")
    assert d and d.discipline == "Fire Protection"


def test_parse_rejects_bad_name():
    assert parse_filename("Final plan v2 (copy).pdf") is None


def test_parse_rejects_bad_extension():
    assert parse_filename("A-101_Plan_RevA.txt") is None


def test_parse_lowercase_revision_is_normalised():
    assert parse_filename("A-101_Plan_Reva.pdf").revision == "A"


def test_revision_order():
    assert revision_key("Z") < revision_key("AA") < revision_key("1") < revision_key("2")


def test_latest_only_keeps_highest():
    ds = [parse_filename(f"A-101_Plan_Rev{r}.pdf") for r in "ACB"]
    assert [d.revision for d in latest_only(ds)] == ["C"]


def test_sort_by_sheet():
    ds = [parse_filename("M-101_X_RevA.pdf"), parse_filename("A-101_X_RevA.pdf")]
    assert [d.number for d in sort_drawings(ds)] == ["A-101", "M-101"]


def test_scan_folder_reports_skipped(tmp_path):
    (tmp_path / "A-101_Plan_RevA.pdf").write_bytes(b"")
    (tmp_path / "readme.txt").write_text("x")
    ds, skipped = scan_folder(tmp_path)
    assert len(ds) == 1 and skipped == ["readme.txt"]


def test_outputs():
    d = [parse_filename("A-101_Plan_RevA.pdf")]
    assert "| A-101 | Plan | A | Architectural |" in to_markdown(d)
    assert to_csv(d).splitlines()[1] == "A-101,Plan,A,Architectural,A-101_Plan_RevA.pdf"


def test_cli_missing_folder(tmp_path):
    assert main([str(tmp_path / "nope")]) == 2


def test_cli_discipline_filter(tmp_path, capsys):
    for n in ["A-101_P_RevA.pdf", "M-101_P_RevA.pdf"]:
        (tmp_path / n).write_bytes(b"")
    assert main([str(tmp_path), "--discipline", "m"]) == 0
    out = capsys.readouterr().out
    assert "M-101" in out and "A-101" not in out


def test_cli_csv_keeps_skipped_note_off_stdout(tmp_path, capsys):
    from drawing_index.cli import main

    (tmp_path / "A-101_Plan_RevA.pdf").write_text("x")
    (tmp_path / "junk.pdf").write_text("x")
    assert main([str(tmp_path), "--format", "csv"]) == 0
    captured = capsys.readouterr()
    assert "skipped" not in captured.out
    assert "junk.pdf" in captured.err
