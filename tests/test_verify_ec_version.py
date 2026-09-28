"""A broken import must not masquerade as an optional missing dependency."""
import builtins
import importlib.metadata
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "verify_ec_version_hunter", Path(__file__).resolve().parents[1] / "tools/verify_ec_version.py")
verifier = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(verifier)


@pytest.mark.parametrize("failure,expected", [
    (ModuleNotFoundError("absent", name="energy_contracts"), 0),
    (ModuleNotFoundError("missing dependency", name="required_dependency"), 2),
    (RuntimeError("broken installation"), 2),
])
def test_import_absence_and_failure_are_distinct(monkeypatch, failure, expected):
    original = builtins.__import__
    def import_package(name, *args, **kwargs):
        if name == "energy_contracts":
            raise failure
        return original(name, *args, **kwargs)
    def no_metadata(name):
        raise importlib.metadata.PackageNotFoundError(name)
    monkeypatch.setattr(importlib.metadata, "version", no_metadata)
    monkeypatch.setattr(builtins, "__import__", import_package)
    assert verifier.main(["--quiet"]) == expected


@pytest.mark.parametrize("version,expected", [("test-version", 0), ("old-version", 1), (None, 1)])
def test_loaded_code_version_contract(monkeypatch, version, expected):
    monkeypatch.setattr(verifier, "repo_version", lambda: "test-version")
    monkeypatch.setattr(verifier, "installed", lambda: (version, "/package/__init__.py", None))
    assert verifier.main(["--quiet"]) == expected
