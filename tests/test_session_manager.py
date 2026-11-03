from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED

import pandas as pd
import pytest

from core.session_manager import save_workspace, load_workspace


def test_workspace_round_trip_json_dataframe_and_binary_asset():
    state = {"nav_section": "2×2 Analysis", "a": 12, "dark_mode": True,
             "line_list_dataframe": pd.DataFrame({"exposure": [1, 0], "case": [0, 1]}),
             "institutional_logo_bytes": b"local-logo-bytes"}
    raw = save_workspace(state, metadata={"study_id": "S-1"})
    restored = load_workspace(raw)
    assert restored["nav_section"] == state["nav_section"]
    assert restored["a"] == 12
    pd.testing.assert_frame_equal(restored["line_list_dataframe"], state["line_list_dataframe"])
    assert restored["institutional_logo_bytes"] == b"local-logo-bytes"
    assert restored["_workspace_metadata"] == {"study_id": "S-1"}


def test_workspace_tampering_is_detected():
    raw = save_workspace({"logo": b"original"})
    source = ZipFile(BytesIO(raw))
    out = BytesIO()
    with source, ZipFile(out, "w", ZIP_DEFLATED) as target:
        for name in source.namelist():
            data = source.read(name)
            if name == "assets/logo.bin":
                data = b"tampered"
            target.writestr(name, data)
    with pytest.raises(ValueError, match="checksum mismatch"):
        load_workspace(out.getvalue())


def test_workspace_rejects_invalid_or_oversized_input():
    with pytest.raises(ValueError):
        load_workspace(b"not a zip")
    with pytest.raises(ValueError):
        load_workspace(b"")
