"""Audit certificate schema, hashes, and standards-compliant JSON."""

import hashlib
import json

from core.audit_certificate import build_audit_certificate, certificate_json


def test_raw_input_certificate_hashes_exact_bytes_and_records_metrics_and_versions():
    raw = b"exposure,outcome\n1,1\n0,0\n"
    certificate = build_audit_certificate(
        input_bytes=raw, source_name="cohort.csv",
        parameters={"counts": [1, 0, 0, 1], "alpha": 0.05},
        metrics={"odds_ratio": 1.0},
    )
    assert certificate["input"]["sha256"] == hashlib.sha256(raw).hexdigest()
    assert certificate["input"]["md5_integrity_compatibility"] == hashlib.md5(raw, usedforsecurity=False).hexdigest()
    assert certificate["input"]["checksum_scope"] == "exact uploaded input-file bytes"
    assert certificate["calculated_metrics"]["odds_ratio"] == 1.0
    assert certificate["dependencies"]["python"]
    assert certificate["certificate_schema"] == "jouriepi.audit_certificate.v1"


def test_certificate_uses_explicit_canonical_scope_when_raw_bytes_not_available():
    payload = certificate_json(parameters={"counts": [1, 2, 3, 4]}, metrics={"estimate": float("inf")},
                              additional_inputs=[{"source_name": "scores.csv", "sha256": "abc123"}])
    decoded = json.loads(payload)
    assert decoded["input"]["checksum_scope"].startswith("canonical analysis-parameter JSON")
    assert decoded["calculated_metrics"]["estimate"] == "Infinity"
    assert decoded["additional_inputs"][0]["source_name"] == "scores.csv"
    assert "does not by itself establish" in decoded["regulatory_note"]
