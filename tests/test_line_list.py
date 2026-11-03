import pandas as pd
import pytest
from pathlib import Path
from io import BytesIO

from core.io_loader import aggregate_line_list
from core.io_loader import load_table, load_uploaded_table
from core.linelist import clean_linelist, outbreak_case_counts


def test_line_list_layout_and_reference_categories():
    frame = pd.DataFrame({"exposure": ["yes", "yes", "no", "no"],
                          "outcome": ["case", "control", "case", "control"]})
    assert aggregate_line_list(frame, "exposure", "outcome", "yes", "case") == (1, 1, 1, 1)


def test_line_list_rejects_missing_values():
    frame = pd.DataFrame({"exposure": ["yes", None], "outcome": ["case", "control"]})
    with pytest.raises(ValueError):
        aggregate_line_list(frame, "exposure", "outcome", "yes", "case")


def test_line_list_rejects_nonbinary_categories():
    frame = pd.DataFrame({"exposure": ["yes", "no", "maybe"], "outcome": ["case", "control", "case"]})
    with pytest.raises(ValueError):
        aggregate_line_list(frame, "exposure", "outcome", "yes", "case")


def test_line_list_rejects_empty_frame():
    frame = pd.DataFrame({"exposure": pd.Series(dtype=str), "outcome": pd.Series(dtype=str)})
    with pytest.raises(ValueError):
        aggregate_line_list(frame, "exposure", "outcome", "yes", "case")


def test_line_list_rejects_same_column_for_exposure_and_outcome():
    frame = pd.DataFrame({"status": ["yes", "no"]})
    with pytest.raises(ValueError):
        aggregate_line_list(frame, "status", "status", "yes", "no")


def test_load_csv_and_reject_missing_file(tmp_path: Path):
    path = tmp_path / "line-list.csv"
    path.write_text("exposure,outcome\nyes,case\nno,control\n", encoding="utf-8")
    loaded = load_table(path)
    assert list(loaded.columns) == ["exposure", "outcome"]
    with pytest.raises(FileNotFoundError):
        load_table(tmp_path / "missing.csv")


def test_load_table_rejects_unsupported_extension(tmp_path: Path):
    path = tmp_path / "line-list.txt"
    path.write_text("data", encoding="utf-8")
    with pytest.raises(ValueError):
        load_table(path)


def test_csv_loader_rejects_duplicate_raw_headers(tmp_path: Path):
    path = tmp_path / "duplicate.csv"
    path.write_text("status,status\nyes,case\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate column names"):
        load_table(path)


def test_load_xlsx_round_trip(tmp_path: Path):
    path = tmp_path / "line-list.xlsx"
    pd.DataFrame({"exposure": ["yes", "no"], "outcome": ["case", "control"]}).to_excel(path, index=False)
    loaded = load_table(path)
    assert aggregate_line_list(loaded, "exposure", "outcome", "yes", "case") == (1, 0, 0, 1)


def test_excel_loader_rejects_duplicate_raw_headers(tmp_path: Path):
    path = tmp_path / "duplicate.xlsx"
    pd.DataFrame([["status", "status"], ["yes", "case"]]).to_excel(
        path, index=False, header=False
    )
    with pytest.raises(ValueError, match="Duplicate column names"):
        load_table(path)


def test_uploaded_spss_sav_round_trip_stays_local_and_returns_dataframe():
    import pyreadstat
    frame = pd.DataFrame({"exposure": [1, 1, 0, 0], "outcome": [1, 0, 1, 0],
                          "site": ["A", "A", "B", "B"]})
    with __import__("tempfile").TemporaryDirectory() as directory:
        path = Path(directory) / "cohort.sav"
        pyreadstat.write_sav(frame, str(path))
        payload = path.read_bytes()
    loaded = load_uploaded_table(BytesIO(payload), "cohort.sav")
    assert list(loaded.columns) == ["exposure", "outcome", "site"]
    assert aggregate_line_list(loaded, "exposure", "outcome", 1.0, 1.0) == (1, 1, 1, 1)


def test_uploaded_csv_uses_shared_loader_and_rewinds_stream():
    source = BytesIO(b"exposure,outcome\nyes,case\nno,control\n")
    source.read()
    frame = load_uploaded_table(source, "sample.CSV")
    assert aggregate_line_list(frame, "exposure", "outcome", "yes", "case") == (1, 0, 0, 1)


def test_uploaded_loader_rejects_unsupported_extension():
    with pytest.raises(ValueError, match="Supported input formats"):
        load_uploaded_table(BytesIO(b"x"), "sample.txt")


def test_line_list_reference_inversion_is_explicit_and_predictable():
    frame = pd.DataFrame({"exposure": ["yes"] * 4 + ["no"] * 4,
                          "outcome": ["case"] * 3 + ["control"] + ["case"] + ["control"] * 3})
    correct = aggregate_line_list(frame, "exposure", "outcome", "yes", "case")
    inverted_exposure = aggregate_line_list(frame, "exposure", "outcome", "no", "case")
    inverted_outcome = aggregate_line_list(frame, "exposure", "outcome", "yes", "control")
    assert correct == (3, 1, 1, 3)
    assert inverted_exposure == (1, 3, 3, 1)
    assert inverted_outcome == (1, 3, 3, 1)


def test_line_list_rejects_duplicate_column_names():
    frame = pd.DataFrame([["yes", "case", "extra"]], columns=["status", "status", "extra"])
    with pytest.raises(ValueError, match="unique"):
        aggregate_line_list(frame, "status", "extra", "yes", "case")


def test_line_list_rejects_non_scalar_categories_with_actionable_error():
    frame = pd.DataFrame({"exposure": [["yes"], ["no"]], "outcome": ["case", "control"]})
    with pytest.raises(ValueError, match="scalar"):
        aggregate_line_list(frame, "exposure", "outcome", ["yes"], "case")


def test_outbreak_curve_counts_only_selected_cases_in_mixed_case_control_data():
    frame = pd.DataFrame({
        "id": [f"row-{i}" for i in range(20)],
        "onset": [f"2026-01-{(i % 10) + 1:02d}" for i in range(20)],
        "status": ["case"] * 10 + ["control"] * 10,
    })
    cleaned, _ = clean_linelist(frame, ["onset"], ["status"], id_col="id")
    dates, counts, selected_rows = outbreak_case_counts(cleaned, "onset", "status", "case")
    assert sum(counts) == 10
    assert selected_rows == 10
    assert len(dates) == 10
    assert counts == [1] * 10
