"""Local CSV/Excel/SPSS ingestion helpers; no network access is used."""

from pathlib import Path
import os
import tempfile
from typing import BinaryIO
import pandas as pd


def _read_table(source: str | Path | BinaryIO, suffix: str) -> pd.DataFrame:
    """Dispatch a local/file-like source and reject duplicate raw headers.

    Pandas normally mangles duplicate headers (for example ``status`` and
    ``status.1``), hiding an ambiguous source file. Inspect the first row
    without header inference before loading the table used by the workflow.
    """
    if suffix == ".csv":
        reader = pd.read_csv
    elif suffix in {".xlsx", ".xlsm", ".xls"}:
        reader = pd.read_excel
    else:
        raise ValueError("Supported input formats are CSV and Excel (.xlsx, .xlsm, .xls)")
    if hasattr(source, "seek"):
        source.seek(0)
    header_frame = reader(source, header=None, nrows=1)
    if header_frame.empty:
        raise ValueError("Input file must contain a header row and at least one data column")
    raw_headers = list(header_frame.iloc[0])
    if pd.Index(raw_headers).has_duplicates:
        raise ValueError("Duplicate column names in the source header; rename them before loading")
    if hasattr(source, "seek"):
        source.seek(0)
    return reader(source)


def load_table(path: str | Path) -> pd.DataFrame:
    """Load a local CSV, Excel or SPSS file, rejecting unsupported extensions."""
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"Input file does not exist: {file_path}")
    if file_path.suffix.lower() == ".sav":
        try:
            import pyreadstat
        except ImportError as exc:
            raise RuntimeError("SPSS .sav support requires the pinned pyreadstat dependency") from exc
        frame, _metadata = pyreadstat.read_sav(str(file_path), apply_value_formats=False)
        if not frame.columns.is_unique:
            raise ValueError("Duplicate column names in the SPSS file; rename them before loading")
        return frame
    return _read_table(file_path, file_path.suffix.lower())


def load_uploaded_table(file_obj: BinaryIO, filename: str) -> pd.DataFrame:
    """Load an uploaded in-memory file using the same parser as local paths.

    The filename is used only to select a supported format; no upload is sent
    to a service. The stream is rewound first so reruns parse from byte zero.
    """
    suffix = Path(filename).suffix.lower()
    if suffix == ".sav":
        try:
            import pyreadstat
        except ImportError as exc:
            raise RuntimeError("SPSS .sav support requires the pinned pyreadstat dependency") from exc
        # pyreadstat's stable reader API accepts a filesystem path. A short-lived
        # local temp file avoids relying on file-like support and is removed even
        # if parsing raises. No upload leaves the local process.
        payload = file_obj.getvalue() if hasattr(file_obj, "getvalue") else file_obj.read()
        with tempfile.NamedTemporaryFile(suffix=".sav", delete=False) as temporary:
            temporary_path = temporary.name
            temporary.write(payload)
            temporary.flush()
        try:
            frame, _metadata = pyreadstat.read_sav(temporary_path, apply_value_formats=False)
        finally:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass
        if not frame.columns.is_unique:
            raise ValueError("Duplicate column names in the SPSS file; rename them before loading")
        return frame
    if suffix not in {".csv", ".xlsx", ".xlsm", ".xls"}:
        raise ValueError("Supported input formats are CSV, Excel (.xlsx, .xlsm, .xls), and SPSS (.sav)")
    if hasattr(file_obj, "seek"):
        file_obj.seek(0)
    return _read_table(file_obj, suffix)


def aggregate_line_list(frame: pd.DataFrame, exposure: str, outcome: str,
                        exposed_value: object, case_value: object) -> tuple[int, int, int, int]:
    """Aggregate a line list to (a,b,c,d), validating both reference categories.

    Row order is exposed then unexposed; columns are case then non-case.
    """
    if not frame.columns.is_unique:
        raise ValueError("Column names must be unique; rename duplicate columns before aggregation")
    for column in (exposure, outcome):
        if column not in frame.columns:
            raise ValueError(f"Missing required column: {column}")
    if exposure == outcome:
        raise ValueError("Exposure and outcome must be different columns")
    if frame[exposure].isna().any() or frame[outcome].isna().any():
        raise ValueError("Missing exposure/outcome values must be resolved before aggregation")
    if frame.empty:
        raise ValueError("Cannot aggregate an empty line list")
    try:
        exposure_values = frame[exposure].unique()
        outcome_values = frame[outcome].unique()
    except TypeError as exc:
        raise ValueError("Exposure and outcome categories must be scalar values") from exc
    if exposed_value not in exposure_values or len(exposure_values) != 2:
        raise ValueError("Exposure must contain exactly two categories, including exposed_value")
    if case_value not in outcome_values or len(outcome_values) != 2:
        raise ValueError("Outcome must contain exactly two categories, including case_value")
    exposed = frame[exposure] == exposed_value
    cases = frame[outcome] == case_value
    return (int((exposed & cases).sum()), int((exposed & ~cases).sum()),
            int((~exposed & cases).sum()), int((~exposed & ~cases).sum()))
