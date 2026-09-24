"""
CGNR Matrix — Human-in-the-Loop (HIL) Logic Gates
Version: 2.0.0
Author: N. Ktari
License: MIT

Deterministic validation gates and post-gate safeguards for the CGNR Matrix
Clinical Decision Support System (CDSS). These gates resolve the critical
Single Points of Failure P0-1, P0-2, and P0-3.

Legal:   Boundary violations trigger SOC-29 liability protection.
Dim:     n = 9 (9 priors / interventions)

Revision history
----------------
v2.0.0 — Engineering audit (see AUDIT.md):
  * Gate 1 now invokes the CRP sigmoid (previously dead code).
  * Gate 2 reimplemented as an honest one-sided 3sigma lower bound.
  * apply_safeguards Laplace step no longer breaks the CLIP[0,1] invariant.
  * Pipeline re-raises structured incidents instead of print/None.
  * Boundary comparisons use >= on safety thresholds.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from .crp_sigmoid import (
    CRP_MIDPOINT_DEFAULT,
    CRP_THRESHOLD_DEFAULT,
    K_DEFAULT,
    h_hormonal_attenuation,
)

N_INTERVENTIONS = 9


class HardStop(Exception):
    """Clinical safety boundary violation (SOC-29)."""

    def __init__(self, gate_id: str, reason: str,
                 message: str = "Clinical output blocked"):
        self.gate_id = gate_id
        self.reason = reason
        super().__init__(f"[{gate_id}] {reason}: {message}")


class RankFailure(Exception):
    """Statistical rank corruption (SPOF P0-2)."""


@dataclass
class Incident:
    """Structured record of a blocked pipeline run (SOC-29 audit trail)."""
    gate_id: str
    reason: str
    flag: str = "RED"


@dataclass
class PipelineResult:
    """Outcome of a pipeline run."""
    flag: str
    scores: np.ndarray | None = None
    h_hormonal: float | None = None
    incident: Incident | None = None

    @property
    def ok(self) -> bool:
        return self.flag == "GREEN"


# ============================================================
# GATE 1: DYNAMIC FLOOR (SPOF P0-1)
# ============================================================
def gate_1_dynamic_floor(
    crp_value: float,
    k: float = K_DEFAULT,
    crp_midpoint: float = CRP_MIDPOINT_DEFAULT,
    crp_threshold: float = CRP_THRESHOLD_DEFAULT,
) -> float:
    """
    Compute the CRP-dependent hormonal attenuation coefficient and enforce
    the dynamic floor.

    Resolves the 60x evidence-inflation failure during catabolic crisis by
    collapsing the hormonal factor to 0 when CRP reaches the sepsis
    threshold.

    Returns
    -------
    float
        Attenuation coefficient h in (0, 1] on PASS.

    Raises
    ------
    HardStop
        If ``crp_value >= crp_threshold``.
    ValueError
        On non-physical inputs (delegated to ``h_hormonal_attenuation``).
    """
    h, status = h_hormonal_attenuation(
        crp_value, k=k, crp_midpoint=crp_midpoint, crp_threshold=crp_threshold
    )
    if status == "HARD_STOP":
        raise HardStop(
            gate_id="GATE_1",
            reason=f"Sepsis detected (CRP {crp_value} >= {crp_threshold})",
        )
    return h


# ============================================================
# GATE 2: 3-sigma RESIDUAL NORM CHECK (SPOF P0-2)
# ============================================================
def gate_2_residual_norm(
    corcondia_value: float,
    mu_corcondia: float = 85.0,
    sigma: float = 5.0,
) -> bool:
    """
    Detect rank erasure via a one-sided 3-sigma lower bound on the
    CORCONDIA core-consistency diagnostic.

    CORCONDIA is a "higher is better" metric: a value above the target
    never indicates rank corruption, so the check is lower-bound only.

    Acceptance floor: ``mu_corcondia - 3 * sigma``  (default 85 - 15 = 70).

    Parameters
    ----------
    corcondia_value : float
        Observed CORCONDIA core consistency (percent).
    mu_corcondia : float
        Target / mean CORCONDIA (percent).
    sigma : float
        Assumed standard deviation of the CORCONDIA estimate (percent).

    Raises
    ------
    RankFailure
        If ``corcondia_value < mu_corcondia - 3 * sigma``.
    ValueError
        If parameters are non-physical.
    """
    if mu_corcondia <= 0 or sigma <= 0:
        raise ValueError("mu_corcondia and sigma must be > 0")
    lower_limit = mu_corcondia - 3.0 * sigma
    if corcondia_value < lower_limit:
        raise RankFailure(
            f"CORCONDIA {corcondia_value:.2f} below 3sigma floor "
            f"{lower_limit:.2f} (= {mu_corcondia} - 3*{sigma}); "
            f"rank corruption suspected (SOC-29 applies)"
        )
    return True


# ============================================================
# GATE 3: ZERO-VETO COMPLIANCE (SPOF P0-3)
# ============================================================
def gate_3_zero_veto(
    f_vector: Sequence[float],
    evidence_scores: Sequence[float],
    n: int = N_INTERVENTIONS,
    tier3_refusals: int = 4,
) -> np.ndarray:
    """
    Enforce per-intervention veto and scale evidence by graded compliance.

    Parameters
    ----------
    f_vector : sequence of float
        Compliance vector f in [0, 1]^n. f = 0 is a hard refusal (veto).
    evidence_scores : sequence of float
        Raw evidence priors E(B), length n.
    n : int
        Expected dimensionality (default 9).
    tier3_refusals : int
        Refusal count at which the protocol is non-viable (Tier 3).

    Returns
    -------
    numpy.ndarray
        Adjusted evidence ``E(B) * f`` (element-wise).

    Raises
    ------
    HardStop
        If refusals >= ``tier3_refusals`` (protocol non-viable).
    ValueError
        On dimensionality or range violations.
    """
    f = np.asarray(f_vector, dtype=float)
    e_b = np.asarray(evidence_scores, dtype=float)

    if f.shape != (n,) or e_b.shape != (n,):
        raise ValueError(
            f"expected length-{n} vectors; got f={f.shape}, e_b={e_b.shape}"
        )
    if np.any(f < 0.0) or np.any(f > 1.0):
        raise ValueError("compliance vector f must lie in [0, 1]")
    if np.any(e_b < 0.0):
        raise ValueError("evidence scores must be >= 0")

    veto_count = int(np.sum(f <= 0.0))
    if veto_count >= tier3_refusals:
        raise HardStop(
            gate_id="GATE_3",
            reason=f"Protocol non-viable ({veto_count}/{n} interventions refused)",
        )

    return e_b * f


# ============================================================
# POST-GATE SAFEGUARDS (S-22, S-06)
# ============================================================
def apply_safeguards(
    e_b_vector: np.ndarray | Sequence[float],
    laplace_eps: float = 1e-6,
) -> np.ndarray:
    """
    Apply CLIP[0, 1] normalisation (S-22) and Laplace zero-guard (S-06).

    The Laplace guard replaces exact zeros with ``laplace_eps`` (so the
    geometric mean log never sees log(0)) and is applied *before* a final
    clip, preserving the [0, 1] invariant.

    Parameters
    ----------
    e_b_vector : array-like
        Post-gate evidence vector.
    laplace_eps : float
        Replacement value for zero entries.

    Returns
    -------
    numpy.ndarray
        Safeguarded vector in [0, 1].
    """
    if laplace_eps <= 0 or laplace_eps >= 1:
        raise ValueError("laplace_eps must lie in (0, 1)")

    v = np.clip(np.asarray(e_b_vector, dtype=float), 0.0, 1.0)
    # Laplace zero-guard: replace zeros in-place, then re-clip so the
    # [0,1] invariant from S-22 is never violated.
    v = np.where(v == 0.0, laplace_eps, v)
    return np.clip(v, 0.0, 1.0)


# ============================================================
# FULL PIPELINE EXECUTION
# ============================================================
def run_cgnr_pipeline(
    patient_crp: float,
    corcondia: float,
    compliance_f: Sequence[float],
    raw_scores: Sequence[float],
    *,
    crp_midpoint: float = CRP_MIDPOINT_DEFAULT,
    crp_threshold: float = CRP_THRESHOLD_DEFAULT,
    mu_corcondia: float = 85.0,
    sigma: float = 5.0,
) -> PipelineResult:
    """
    Execute the sequential validation pipeline.

    Returns
    -------
    PipelineResult
        ``flag="GREEN"`` with ``scores`` and ``h_hormonal`` on success,
        or ``flag="RED"`` with an ``Incident`` on a blocked run.
    """
    try:
        # Stage 1 — Dynamic floor (real CRP sigmoid, no longer bypassed).
        h = gate_1_dynamic_floor(
            patient_crp,
            crp_midpoint=crp_midpoint,
            crp_threshold=crp_threshold,
        )

        # Stage 2 — Data integrity (one-sided 3sigma CORCONDIA).
        gate_2_residual_norm(corcondia, mu_corcondia=mu_corcondia, sigma=sigma)

        # Stage 3 — Compliance veto (n=9 vector).
        gated_scores = gate_3_zero_veto(compliance_f, raw_scores)

        # Final — CLIP + Laplace safeguards.
        final_output = apply_safeguards(gated_scores)

        return PipelineResult(flag="GREEN", scores=final_output,
                              h_hormonal=h)

    except (HardStop, RankFailure) as exc:
        gate = getattr(exc, "gate_id", "GATE_2")
        incident = Incident(gate_id=gate, reason=str(exc))
        return PipelineResult(flag="RED", incident=incident)


if __name__ == "__main__":
    # TEST: patient refusing intervention #7 (e.g. vegan refusing MCT).
    test_f = [1, 1, 1, 1, 1, 1, 0, 1, 1]
    test_scores = [0.85, 0.90, 0.45, 0.70, 0.82, 0.61, 0.95, 0.52, 0.77]

    print("--- CGNR Matrix Pipeline Validation ---")
    result = run_cgnr_pipeline(
        patient_crp=12.0,
        corcondia=88.5,
        compliance_f=test_f,
        raw_scores=test_scores,
    )

    if result.ok and result.scores is not None:
        print(f"Status: {result.flag}  h_hormonal={result.h_hormonal:.4f}")
        print(f"Gated evidence scores (n={N_INTERVENTIONS}):")
        print(np.round(result.scores, 4))
    else:
        print(f"Status: {result.flag}  incident: {result.incident}")
