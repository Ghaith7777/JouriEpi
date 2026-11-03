"""Safe, checksummed .jepi workspace serialization (JSON metadata + ZIP payload).

No pickle is used. DataFrames are stored as CSV, binary assets as bytes, and all
payload members are SHA-256 verified before any state is returned to the caller.
The archive is compressed and integrity-checked, not encrypted; users should use
an encrypted local disk/container when workspace confidentiality at rest is needed.
"""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO, StringIO
import json
from pathlib import PurePosixPath
from typing import Any, Mapping
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile

FORMAT_VERSION = "jouriepi-workspace-v1"
MAX_ARCHIVE_BYTES = 100 * 1024 * 1024
MAX_MEMBER_BYTES = 50 * 1024 * 1024


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, Mapping):
        return {str(k): _json_safe(v) for k, v in value.items() if not str(k).startswith("_")}
    return str(value)


def save_workspace(state: Mapping[str, Any], *, metadata: Mapping[str, Any] | None = None) -> bytes:
    """Serialize selected session state, DataFrames, and uploaded binary assets."""
    payload: dict[str, bytes] = {}
    values: dict[str, Any] = {}
    for key, value in state.items():
        if str(key).startswith("_") or key in {"institutional_logo_upload"}:
            continue
        try:
            import pandas as pd
            is_frame = isinstance(value, pd.DataFrame)
        except ImportError:
            is_frame = False
        if is_frame:
            member = f"dataframes/{key}.csv"
            payload[member] = value.to_csv(index=False).encode("utf-8-sig")
            values[key] = {"type": "dataframe_csv", "member": member}
        elif isinstance(value, (bytes, bytearray, memoryview)):
            member = f"assets/{key}.bin"
            payload[member] = bytes(value)
            values[key] = {"type": "bytes", "member": member}
        else:
            try:
                json.dumps(_json_safe(value), allow_nan=False)
                values[key] = {"type": "json", "value": _json_safe(value)}
            except (TypeError, ValueError):
                continue
    hashes = {name: sha256(content).hexdigest() for name, content in sorted(payload.items())}
    manifest = {"format": FORMAT_VERSION, "metadata": _json_safe(dict(metadata or {})),
                "state": values, "payload_sha256": hashes}
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    manifest["manifest_sha256"] = sha256(canonical).hexdigest()
    out = BytesIO()
    with ZipFile(out, "w", compression=ZIP_DEFLATED, compresslevel=6) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, sort_keys=True, indent=2, allow_nan=False))
        for name, content in payload.items():
            archive.writestr(name, content)
    result = out.getvalue()
    if len(result) > MAX_ARCHIVE_BYTES:
        raise ValueError("workspace exceeds the 100 MiB compressed size limit")
    return result


def load_workspace(data: bytes | bytearray | memoryview) -> dict[str, Any]:
    """Validate a .jepi archive and return session values without mutating UI state."""
    raw = bytes(data)
    if not raw or len(raw) > MAX_ARCHIVE_BYTES:
        raise ValueError("workspace is empty or exceeds the 100 MiB compressed size limit")
    try:
        archive = ZipFile(BytesIO(raw), "r")
    except (BadZipFile, OSError) as exc:
        raise ValueError("file is not a valid JouriEpi workspace archive") from exc
    with archive:
        infos = archive.infolist()
        names = [i.filename for i in infos]
        if len(names) != len(set(names)) or any(PurePosixPath(n).is_absolute() or ".." in PurePosixPath(n).parts for n in names):
            raise ValueError("workspace contains duplicate or unsafe archive paths")
        if any(i.file_size > MAX_MEMBER_BYTES for i in infos) or sum(i.file_size for i in infos) > MAX_ARCHIVE_BYTES:
            raise ValueError("workspace contains an oversized payload")
        if "manifest.json" not in names:
            raise ValueError("workspace manifest is missing")
        try:
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError) as exc:
            raise ValueError("workspace manifest is invalid") from exc
        if manifest.get("format") != FORMAT_VERSION:
            raise ValueError("unsupported JouriEpi workspace format")
        supplied_hash = manifest.pop("manifest_sha256", None)
        canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        if not supplied_hash or sha256(canonical).hexdigest() != supplied_hash:
            raise ValueError("workspace manifest checksum mismatch")
        payload: dict[str, bytes] = {}
        for name, expected in manifest.get("payload_sha256", {}).items():
            if name not in names or name == "manifest.json":
                raise ValueError(f"workspace payload member is missing: {name}")
            content = archive.read(name)
            if sha256(content).hexdigest() != expected:
                raise ValueError(f"workspace payload checksum mismatch: {name}")
            payload[name] = content
        state: dict[str, Any] = {}
        for key, descriptor in manifest.get("state", {}).items():
            kind = descriptor.get("type")
            if kind == "json":
                state[key] = descriptor.get("value")
            elif kind == "bytes":
                state[key] = payload[descriptor["member"]]
            elif kind == "dataframe_csv":
                import pandas as pd
                state[key] = pd.read_csv(StringIO(payload[descriptor["member"]].decode("utf-8-sig")))
            else:
                raise ValueError(f"unsupported workspace value type for {key}")
        state["_workspace_metadata"] = manifest.get("metadata", {})
        return state
