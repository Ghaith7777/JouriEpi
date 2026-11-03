"""Canonical, machine-readable integrity and calculation provenance certificate."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import md5, sha256
from importlib import metadata
import json
import math
import platform
from typing import Any, Mapping


def _safe(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _safe({k: getattr(value, k) for k in value.__dataclass_fields__})
    if isinstance(value, Mapping):
        return {str(k): _safe(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_safe(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return "Infinity" if value > 0 else "-Infinity" if value < 0 else None
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "not installed"


def build_audit_certificate(
    *, parameters: Mapping[str, Any], metrics: Mapping[str, Any],
    input_bytes: bytes | None = None, source_name: str = "analysis-input",
    source_md5: str | None = None, source_sha256: str | None = None,
    metadata_fields: Mapping[str, Any] | None = None,
    additional_inputs: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Create a deterministic-provenance JSON payload with input checksums.

    If raw file bytes are available, both checksums are computed from those exact
    bytes. Otherwise, the certificate hashes a canonical JSON representation of
    the supplied parameters and clearly records that narrower checksum scope.
    MD5 is included for compatibility only; SHA-256 is the primary integrity hash.
    """
    if input_bytes is not None:
        digest_md5 = md5(input_bytes, usedforsecurity=False).hexdigest()
        digest_sha256 = sha256(input_bytes).hexdigest()
        checksum_scope = "exact uploaded input-file bytes"
    elif source_md5 and source_sha256:
        digest_md5, digest_sha256 = source_md5, source_sha256
        checksum_scope = "exact uploaded input-file bytes (hashes computed at ingestion)"
    else:
        canonical = json.dumps(_safe(dict(parameters)), sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        digest_md5 = md5(canonical, usedforsecurity=False).hexdigest()
        digest_sha256 = sha256(canonical).hexdigest()
        checksum_scope = "canonical analysis-parameter JSON; raw source bytes were not retained"
    return {
        "certificate_schema": "jouriepi.audit_certificate.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "application": "JouriEpi: Clinical Epidemiological & Causal Inference Suite",
        "offline_processing": True,
        "input": {"source_name": source_name, "checksum_scope": checksum_scope,
                  "md5_integrity_compatibility": digest_md5, "sha256": digest_sha256},
        "additional_inputs": _safe(additional_inputs or []),
        "parameters": _safe(dict(parameters)),
        "calculated_metrics": _safe(dict(metrics)),
        "dependencies": {"python": platform.python_version(), **{
            name: _version(name) for name in ("pandas", "streamlit", "scipy", "statsmodels", "python-docx", "Pillow", "openpyxl")}},
        "regulatory_note": "Integrity/provenance artifact only. Exporting this JSON does not by itself establish FDA 21 CFR Part 11, GCP, electronic-signature, validation, access-control, or retention compliance.",
    }


def certificate_json(**kwargs: Any) -> str:
    """Serialize a certificate as stable, standards-compliant JSON."""
    return json.dumps(build_audit_certificate(**kwargs), indent=2, sort_keys=True, allow_nan=False)

