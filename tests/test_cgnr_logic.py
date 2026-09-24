"""
Test suite for the CGNR Matrix logic gates.

Run with:  python -m pytest -v     (after: pip install -r requirements.txt)
Fallback:  python tests/test_cgnr_logic.py
"""

import os
import sys

import numpy as np
import pytest

# Make `logic` importable when running the file directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.crp_sigmoid import (
    CRP_MIDPOINT_DEFAULT,
    CRP_THRESHOLD_DEFAULT,
    K_DEFAULT,
    h_hormonal_attenuation,
)
from logic.hil_gates import (
    N_INTERVENTIONS,
    HardStop,
    RankFailure,
    apply_safeguards,
    gate_1_dynamic_floor,
    gate_2_residual_norm,
    gate_3_zero_veto,
    run_cgnr_pipeline,
)

THRESH = CRP_THRESHOLD_DEFAULT
MID = CRP_MIDPOINT_DEFAULT


# ------------------------------------------------------------------
# Sigmoid (Gate 1 core)
# ------------------------------------------------------------------
class TestSigmoid:
    def test_low_crp_near_one(self):
        h, s = h_hormonal_attenuation(0.0)
        assert s == "PASS"
        assert h > 0.98  # near full contribution at no inflammation

    def test_at_threshold_hard_stop(self):
        h, s = h_hormonal_attenuation(THRESH)
        assert s == "HARD_STOP"
        assert h == 0.0

    def test_above_threshold_hard_stop(self):
        h, s = h_hormonal_attenuation(THRESH + 1)
        assert s == "HARD_STOP" and h == 0.0

    def test_monotonic_decreasing(self):
        crps = np.linspace(0, THRESH - 0.1, 50)
        hs = [h_hormonal_attenuation(c)[0] for c in crps]
        assert all(b <= a + 1e-12 for a, b in zip(hs, hs[1:]))

    def test_attenuates_meaningfully(self):
        # The audit fix: h must drop well below 0.5 before the threshold.
        h_at_near = h_hormonal_attenuation(THRESH - 1.0)[0]
        assert h_at_near < 0.05

    def test_negative_crp_raises(self):
        with pytest.raises(ValueError):
            h_hormonal_attenuation(-1.0)

    def test_midpoint_validation(self):
        with pytest.raises(ValueError):
            h_hormonal_attenuation(10.0, crp_midpoint=THRESH)


# ------------------------------------------------------------------
# Gate 1
# ------------------------------------------------------------------
class TestGate1:
    def test_pass_returns_coefficient(self):
        h = gate_1_dynamic_floor(12.0)
        assert 0.0 < h <= 1.0

    def test_sepsis_raises(self):
        with pytest.raises(HardStop) as exc:
            gate_1_dynamic_floor(THRESH)
        assert exc.value.gate_id == "GATE_1"

    def test_boundary_inclusive(self):
        # CRP == threshold must Hard Stop (audit L3).
        with pytest.raises(HardStop):
            gate_1_dynamic_floor(THRESH)


# ------------------------------------------------------------------
# Gate 2
# ------------------------------------------------------------------
class TestGate2:
    def test_good_corcondia_passes(self):
        assert gate_2_residual_norm(88.5) is True

    def test_perfect_corcondia_passes(self):
        # Audit M2: a too-high (better) fit must NOT fail.
        assert gate_2_residual_norm(100.0) is True
        assert gate_2_residual_norm(120.0) is True

    def test_below_floor_fails(self):
        with pytest.raises(RankFailure):
            gate_2_residual_norm(60.0)

    def test_floor_is_mu_minus_3sigma(self):
        # default: 85 - 15 = 70
        with pytest.raises(RankFailure):
            gate_2_residual_norm(69.9)
        assert gate_2_residual_norm(70.0) is True

    def test_custom_sigma(self):
        assert gate_2_residual_norm(80.0, mu_corcondia=85.0, sigma=2.0) is True
        with pytest.raises(RankFailure):
            gate_2_residual_norm(78.0, mu_corcondia=85.0, sigma=2.0)


# ------------------------------------------------------------------
# Gate 3
# ------------------------------------------------------------------
class TestGate3:
    def test_single_veto_zeros_score(self):
        f = [1] * N_INTERVENTIONS
        f[6] = 0
        scores = [0.5] * N_INTERVENTIONS
        out = gate_3_zero_veto(f, scores)
        assert out[6] == 0.0
        assert np.all(out[:6] == 0.5)

    def test_too_many_refusals_blocks(self):
        f = [0, 0, 0, 0, 1, 1, 1, 1, 1]
        with pytest.raises(HardStop) as exc:
            gate_3_zero_veto(f, [0.5] * N_INTERVENTIONS)
        assert exc.value.gate_id == "GATE_3"

    def test_dimension_mismatch_raises(self):
        with pytest.raises(ValueError):
            gate_3_zero_veto([1, 0, 1], [0.5, 0.5, 0.5])

    def test_out_of_range_compliance_raises(self):
        with pytest.raises(ValueError):
            gate_3_zero_veto([1.5] + [1] * (N_INTERVENTIONS - 1),
                             [0.5] * N_INTERVENTIONS)


# ------------------------------------------------------------------
# Safeguards (audit M3)
# ------------------------------------------------------------------
class TestSafeguards:
    def test_clip_upper_bound_holds(self):
        # The audit fix: adding Laplace eps must never push past 1.0.
        out = apply_safeguards([0.0, 0.5, 1.0])
        assert np.max(out) <= 1.0
        assert out[0] > 0.0  # zero replaced
        assert out[2] == 1.0  # untouched

    def test_no_zeros_unchanged(self):
        out = apply_safeguards([0.3, 0.7, 0.9])
        np.testing.assert_allclose(out, [0.3, 0.7, 0.9])

    def test_range_invariant(self):
        rng = np.random.default_rng(0)
        v = rng.random(50) * 2 - 0.5  # spans [-0.5, 1.5)
        out = apply_safeguards(v)
        assert np.min(out) >= 0.0
        assert np.max(out) <= 1.0


# ------------------------------------------------------------------
# Pipeline
# ------------------------------------------------------------------
class TestPipeline:
    def test_green_path(self):
        f = [1] * N_INTERVENTIONS
        f[6] = 0
        r = run_cgnr_pipeline(12.0, 88.5, f, [0.85] * N_INTERVENTIONS)
        assert r.ok
        assert r.scores is not None
        # intervention #7 refused -> gated to 0, then Laplace replaces 0 with eps
        assert r.scores[6] == pytest.approx(1e-6)
        assert r.h_hormonal is not None

    def test_sepsis_blocks(self):
        r = run_cgnr_pipeline(55.0, 88.5, [1] * N_INTERVENTIONS,
                              [0.5] * N_INTERVENTIONS)
        assert not r.ok
        assert r.incident is not None
        assert r.incident.gate_id == "GATE_1"

    def test_rank_failure_blocks(self):
        r = run_cgnr_pipeline(12.0, 50.0, [1] * N_INTERVENTIONS,
                              [0.5] * N_INTERVENTIONS)
        assert not r.ok
        assert r.incident.gate_id == "GATE_2"

    def test_too_many_refusals_blocks(self):
        f = [0, 0, 0, 0, 1, 1, 1, 1, 1]
        r = run_cgnr_pipeline(12.0, 88.5, f, [0.5] * N_INTERVENTIONS)
        assert not r.ok
        assert r.incident.gate_id == "GATE_3"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
