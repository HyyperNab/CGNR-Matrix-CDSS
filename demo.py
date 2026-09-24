#!/usr/bin/env python3
"""
CGNR Matrix CDSS — Demo script.

Shows three scenarios: GREEN (normal), RED-GATE-1 (sepsis),
and RED-GATE-3 (patient refusal escalation).

Run:  python demo.py
"""

import numpy as np

from logic import N_INTERVENTIONS, h_hormonal_attenuation, run_cgnr_pipeline


def print_header(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_result(result) -> None:
    if result.ok and result.scores is not None:
        print(f"  Flag:         {result.flag}")
        print(f"  h_hormonal:   {result.h_hormonal:.4f}")
        print(f"  Scores (n={N_INTERVENTIONS}):")
        print(f"  {np.round(result.scores, 4)}")
    else:
        inc = result.incident
        print(f"  Flag:         {result.flag}")
        print(f"  Gate:         {inc.gate_id}")
        print(f"  Reason:       {inc.reason}")


def main() -> None:
    # --- Gate 1: attenuation table ---
    print_header("Gate 1: CRP Sigmoid Attenuation")
    print("  threshold=50.0  midpoint=25.0  k=0.18")
    for crp in [0, 10, 20, 25, 30, 40, 45, 50, 55, 80]:
        h, status = h_hormonal_attenuation(crp)
        print(f"  CRP={crp:3d} mg/dL  ->  h={h:.4f}  [{status}]")

    # --- Scenario 1: GREEN (normal patient) ---
    print_header("Scenario 1: GREEN — Normal Patient")
    print("  CRP=12.0  CORCONDIA=88.5  1 refusal (intervention #7)")
    result = run_cgnr_pipeline(
        patient_crp=12.0,
        corcondia=88.5,
        compliance_f=[1, 1, 1, 1, 1, 1, 0, 1, 1],
        raw_scores=[0.85, 0.90, 0.45, 0.70, 0.82, 0.61, 0.95, 0.52, 0.77],
    )
    print_result(result)

    # --- Scenario 2: RED — Sepsis (Gate 1) ---
    print_header("Scenario 2: RED — Sepsis (Gate 1 Hard Stop)")
    print("  CRP=55.0  CORCONDIA=88.5  full compliance")
    result = run_cgnr_pipeline(
        patient_crp=55.0,
        corcondia=88.5,
        compliance_f=[1] * N_INTERVENTIONS,
        raw_scores=[0.85] * N_INTERVENTIONS,
    )
    print_result(result)

    # --- Scenario 3: RED — Rank corruption (Gate 2) ---
    print_header("Scenario 3: RED — Rank Corruption (Gate 2)")
    print("  CRP=12.0  CORCONDIA=45.0  full compliance")
    result = run_cgnr_pipeline(
        patient_crp=12.0,
        corcondia=45.0,
        compliance_f=[1] * N_INTERVENTIONS,
        raw_scores=[0.85] * N_INTERVENTIONS,
    )
    print_result(result)

    # --- Scenario 4: RED — Patient abandonment (Gate 3) ---
    print_header("Scenario 4: RED — Tier 3 Escalation (Gate 3)")
    print("  CRP=12.0  CORCONDIA=88.5  5/9 interventions refused")
    result = run_cgnr_pipeline(
        patient_crp=12.0,
        corcondia=88.5,
        compliance_f=[0, 0, 0, 0, 0, 1, 1, 1, 1],
        raw_scores=[0.85] * N_INTERVENTIONS,
    )
    print_result(result)

    print()


if __name__ == "__main__":
    main()
