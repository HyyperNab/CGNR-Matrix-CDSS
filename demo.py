#!/usr/bin/env python3
"""
Quick demo of the CGNR Matrix CDSS pipeline and Gate 1 attenuation curve.

Run:  python demo.py
"""

import numpy as np

from logic import N_INTERVENTIONS, h_hormonal_attenuation, run_cgnr_pipeline


def main() -> None:
    # --- Gate 1: attenuation table ---
    print("=== Gate 1: CRP Sigmoid Attenuation ===")
    print("  threshold=50.0  midpoint=25.0  k=0.18")
    for crp in [0, 10, 20, 25, 30, 40, 45, 50, 55, 80]:
        h, status = h_hormonal_attenuation(crp)
        print(f"  CRP={crp:3d} mg/dL  ->  h={h:.4f}  [{status}]")

    # --- Pipeline demo ---
    print()
    print("=== Pipeline Validation ===")
    test_f = [1, 1, 1, 1, 1, 1, 0, 1, 1]  # intervention #7 refused
    test_scores = [0.85, 0.90, 0.45, 0.70, 0.82, 0.61, 0.95, 0.52, 0.77]

    result = run_cgnr_pipeline(
        patient_crp=12.0,
        corcondia=88.5,
        compliance_f=test_f,
        raw_scores=test_scores,
    )

    if result.ok and result.scores is not None:
        print(f"  Status: {result.flag}  h_hormonal={result.h_hormonal:.4f}")
        print(f"  Gated evidence scores (n={N_INTERVENTIONS}):")
        print(f"  {np.round(result.scores, 4)}")
    else:
        print(f"  Status: {result.flag}  incident: {result.incident}")


if __name__ == "__main__":
    main()
