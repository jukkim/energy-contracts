"""계보 봉투 사본 게이트 — 줄바꿈은 드리프트가 아니고, 내용 변화는 드리프트다 (2026-09-17)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("_vpv", ROOT / "scripts" / "verify_provenance_vendors.py")
V = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V)

BODY = b'"""envelope"""\nX = 1\n\ndef f():\n    return X\n'


def _setup(tmp_path, monkeypatch, vendor_bytes):
    canon = tmp_path / "canon.py"
    canon.write_bytes(BODY)
    vend = tmp_path / "vendor.py"
    vend.write_bytes(vendor_bytes)
    monkeypatch.setattr(V, "_ROOT", tmp_path)
    monkeypatch.setattr(V, "CANON", canon)
    monkeypatch.setattr(V, "VENDORS", (vend,))
    return V.check()


def test_crlf_working_copy_is_not_drift(tmp_path, monkeypatch):
    assert _setup(tmp_path, monkeypatch, BODY.replace(b"\n", b"\r\n")) == 0


def test_content_change_is_drift(tmp_path, monkeypatch):
    assert _setup(tmp_path, monkeypatch, BODY.replace(b"X = 1", b"X = 2")) == 1


def test_content_change_with_crlf_is_still_drift(tmp_path, monkeypatch):
    assert _setup(tmp_path, monkeypatch, BODY.replace(b"X = 1", b"X = 2").replace(b"\n", b"\r\n")) == 1


def test_lone_cr_is_content(tmp_path, monkeypatch):
    """CRLF 짝만 뺀다 — 홀로 선 CR 은 내용이다."""
    assert _setup(tmp_path, monkeypatch, BODY.replace(b"X = 1", b"X =\r1")) == 1


def test_missing_vendor_is_unmeasured(tmp_path, monkeypatch):
    canon = tmp_path / "canon.py"
    canon.write_bytes(BODY)
    monkeypatch.setattr(V, "_ROOT", tmp_path)
    monkeypatch.setattr(V, "CANON", canon)
    monkeypatch.setattr(V, "VENDORS", (tmp_path / "missing.py",))
    assert V.check() == 2
