"""Combiner package split: candidate vs precompute vs diagnostics."""

from __future__ import annotations

import src.combiner.diagnostics as diagnostics
import src.combiner.precompute as precompute
from src.combiner import candidate


def test_precompute_and_diagnostics_import_cleanly() -> None:
    assert precompute.precompute_candidate_signal_matrices is not None
    assert precompute.CandidateSignalMatrix is not None
    assert diagnostics.write_candidate_diagnostics is not None


def test_candidate_reexports_precompute_public_api() -> None:
    assert candidate.precompute_candidate_signal_matrices is precompute.precompute_candidate_signal_matrices
    assert candidate.CandidateSignalMatrix is precompute.CandidateSignalMatrix
    assert candidate.build_candidate_signal_arrays is precompute.build_candidate_signal_arrays
    assert candidate.build_context_cache_key is precompute.build_context_cache_key
    assert candidate.write_precompute_profile_summary is precompute.write_precompute_profile_summary


def test_candidate_reexports_diagnostics() -> None:
    assert candidate.write_candidate_diagnostics is diagnostics.write_candidate_diagnostics
