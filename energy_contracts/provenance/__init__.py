"""AIRO 출력 계약 — 계보 봉투(정본).

소비 저장소는 **사본**을 두고 `verify_provenance_vendors.py` 가 해시로 대조한다.
"""
from .envelope import (ABSENCE_IN_DENOMINATOR, ABSENCE_KINDS, CONTRIBUTING,
                       DATA_SOURCE_LABELS, LINEAGE, NOT_MEASURED,
                       RESIDUAL_KINDS, Envelope, ProvenanceError,
                       assert_quotable, build_envelope, is_measured)

__all__ = ["ABSENCE_IN_DENOMINATOR", "ABSENCE_KINDS", "CONTRIBUTING",
           "DATA_SOURCE_LABELS", "LINEAGE", "NOT_MEASURED", "RESIDUAL_KINDS",
           "Envelope", "ProvenanceError", "assert_quotable", "build_envelope",
           "is_measured"]
