"""
CGNR Matrix — CRP Sigmoid Attenuation Model
Gate 1: Dynamic Floor (resolves SPOF P0-1: Sepsis Overestimation)

Reference: Main Paper Eq. 3; CDSS Manual §2.2

The hormonal attenuation coefficient h(CRP) ∈ (0, 1] scales the hormonal
contribution to the evidence tensor. It is near 1 at low inflammation
(no attenuation) and collapses toward 0 as CRP approaches the sepsis
threshold, at which point Gate 1 issues a Hard Stop.

Design notes
------------
The sigmoid *midpoint* (`crp_midpoint`) is deliberately set below the
hard-stop threshold (`crp_threshold`). Placing the inflection on the
threshold (the original design) left h ≈ 0.5 at CRP=50 — i.e. the curve
never attenuated before the cliff. With the midpoint at half the threshold
and k calibrated accordingly, h falls from ≈0.99 (CRP=0) to ≈0.01 just
below the threshold: a genuine S-curve rather than a flat line truncated
by a cliff.
"""

from __future__ import annotations

import numpy as np

# Sepsis threshold (mg/dL). Reference: McClave 2016 [12], Singer 2019 [13].
CRP_THRESHOLD_DEFAULT = 50.0
# Midpoint of the attenuation curve (mg/dL). Half the threshold by default.
CRP_MIDPOINT_DEFAULT = CRP_THRESHOLD_DEFAULT / 2.0
# Steepness calibrated so h approaches 0.01 as CRP nears the threshold.
# h(t) = 1/(1+exp(k*(t-m))) ≈ 0.01  =>  k*(t-m) ≈ ln(99) ≈ 4.595
# k ≈ 4.595 / (50 - 25) ≈ 0.184, rounded to 0.18
K_DEFAULT = 0.18


def h_hormonal_attenuation(
    crp_value: float,
    k: float = K_DEFAULT,
    crp_midpoint: float = CRP_MIDPOINT_DEFAULT,
    crp_threshold: float = CRP_THRESHOLD_DEFAULT,
) -> tuple[float, str]:
    """
    Compute the hormonal attenuation coefficient.

    Parameters
    ----------
    crp_value : float
        Serum CRP in mg/dL. Must be >= 0.
    k : float, optional
        Sigmoid steepness (theoretical baseline; clinical calibration
        reserved for future work).
    crp_midpoint : float, optional
        CRP at which attenuation is 50 % (the sigmoid inflection). Kept
        below ``crp_threshold`` so the curve fully attenuates before the
        Hard Stop.
    crp_threshold : float, optional
        CRP sepsis threshold (mg/dL). At or above this value a Hard Stop
        is issued.

    Returns
    -------
    tuple[float, str]
        ``(h_value, gate_status)`` where ``h_value`` is 0.0 on a Hard Stop
        and otherwise the sigmoid output in (0, 1), and ``gate_status`` is
        ``"HARD_STOP"`` or ``"PASS"``.

    Raises
    ------
    ValueError
        If inputs are non-physical (negative CRP, non-positive threshold,
        midpoint not in (0, threshold), k <= 0).
    """
    if not np.isfinite(crp_value):
        raise ValueError(f"crp_value must be finite (got {crp_value})")
    if crp_value < 0:
        raise ValueError(f"crp_value must be >= 0 (got {crp_value})")
    if not np.isfinite(crp_threshold) or crp_threshold <= 0:
        raise ValueError(
            f"crp_threshold must be a positive finite number "
            f"(got {crp_threshold})"
        )
    if not np.isfinite(crp_midpoint) or not 0 < crp_midpoint < crp_threshold:
        raise ValueError(
            f"crp_midpoint must be a finite value in (0, crp_threshold); got "
            f"midpoint={crp_midpoint}, threshold={crp_threshold}"
        )
    if not np.isfinite(k) or k <= 0:
        raise ValueError(f"k must be a positive finite number (got {k})")

    # Hard Stop at the boundary (>=, conservative on a safety threshold).
    if crp_value >= crp_threshold:
        return 0.0, "HARD_STOP"

    h_val = 1.0 / (1.0 + np.exp(k * (crp_value - crp_midpoint)))
    # Numerical guard: sigmoid is asymptotic, never exactly 0 or 1.
    h_val = float(np.clip(h_val, 1e-12, 1.0))
    return h_val, "PASS"


# === VISUALISATION (optional) ===
def plot_attenuation_curve(
    k: float = K_DEFAULT,
    crp_midpoint: float = CRP_MIDPOINT_DEFAULT,
    crp_threshold: float = CRP_THRESHOLD_DEFAULT,
    savepath: str | None = None,
) -> None:
    """Plot the Gate 1 attenuation curve. Requires matplotlib."""
    import matplotlib.pyplot as plt

    crp_range = np.linspace(0, crp_threshold * 2, 400)
    h_values = [h_hormonal_attenuation(c, k, crp_midpoint, crp_threshold)[0]
                for c in crp_range]

    plt.figure(figsize=(10, 5))
    plt.plot(crp_range, h_values, "b-", linewidth=2, label="h_hormonal")
    plt.axvline(x=crp_threshold, color="red", linestyle="--", alpha=0.7,
                label=f"CRP = {crp_threshold:.0f} (Hard Stop)")
    plt.axvline(x=crp_midpoint, color="orange", linestyle=":", alpha=0.6,
                label=f"midpoint = {crp_midpoint:.0f}")
    plt.fill_between(crp_range, 0, 1, where=(crp_range >= crp_threshold),
                     color="red", alpha=0.1, label="Hard Stop zone")
    plt.xlabel("Serum CRP (mg/dL)")
    plt.ylabel("h_hormonal")
    plt.title("Gate 1: CRP-Dependent Hormonal Attenuation")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    if savepath:
        plt.savefig(savepath, dpi=150)
    plt.show()


if __name__ == "__main__":
    print(
        f"threshold={CRP_THRESHOLD_DEFAULT}"
        f"  midpoint={CRP_MIDPOINT_DEFAULT}"
        f"  k={K_DEFAULT}"
    )
    for crp in [0, 10, 20, 25, 30, 40, 45, 50, 55, 80]:
        h, status = h_hormonal_attenuation(crp)
        print(f"CRP={crp:3d} mg/dL  ->  h={h:.4f}  [{status}]")
