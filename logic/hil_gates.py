"""
CGNR Matrix — Human-in-the-Loop (HIL) Logic Gates
Version: 1.1.0 (ESPEN Submission Build)
Author: N. Ktari
License: MIT

This module implements the three deterministic validation gates and post-gate 
safeguards for the CGNR Matrix Clinical Decision Support System (CDSS).
These gates resolve critical SPOFs P0-1, P0-2, and P0-3.

Legal: Boundary violations trigger SOC-29 liability protection.
Dimensionality: n=9 (9 Priors / Interventions)
"""

import numpy as np

class HardStop(Exception):
    """Exception raised for clinical safety boundary violations (SOC-29)."""
    def __init__(self, gate_id, reason, message="Clinical output blocked"):
        self.gate_id = gate_id
        self.reason = reason
        super().__init__(f"[{gate_id}] {reason}: {message}")

class RankFailure(Exception):
    """Exception raised for statistical rank corruption (SPOF P0-2)."""
    pass

# ============================================================
# GATE 1: DYNAMIC FLOOR (SPOF P0-1)
# ============================================================
def gate_1_dynamic_floor(crp_value, h_hormonal):
    """
    Nullifies hormonal factors if CRP exceeds sepsis threshold (50 mg/dL).
    Resolves 60x evidence inflation during catabolic crisis.
    """
    CRP_THRESHOLD = 50.0  
    
    if crp_value > CRP_THRESHOLD:
        # Force collapse of hormonal attenuation
        h_hormonal = 0.0
        raise HardStop(
            gate_id="GATE_1", 
            reason=f"Sepsis detected (CRP {crp_value} > 50)"
        )
    return h_hormonal

# ============================================================
# GATE 2: 3σ RESIDUAL NORM CHECK (SPOF P0-2)
# ============================================================
def gate_2_residual_norm(corcondia_value):
    """
    Detects rank erasure by checking core consistency residual.
    Boundary limit: μ + 3σ (Target CORCONDIA >= 85%).
    """
    MU_CORCONDIA = 85.0
    BOUNDARY_3SIGMA = 15.0
    
    residual = abs((corcondia_value - MU_CORCONDIA) / MU_CORCONDIA) * 100.0
    
    if residual > BOUNDARY_3SIGMA:
        raise RankFailure(
            f"Residual {residual:.2f}% exceeds 3σ limit (SOC-29 applies)"
        )
    return True

# ============================================================
# GATE 3: ZERO-VETO COMPLIANCE (SPOF P0-3)
# ============================================================
def gate_3_zero_veto(f_vector, evidence_scores):
    """
    Enforces per-intervention veto for refused items (f=0).
    f_vector: 9-dimensional compliance vector f ∈ [0,1]^9
    """
    e_b = np.array(evidence_scores)
    f = np.array(f_vector)
    
    # Check for Tier 3 escalation (>= 4 refusals out of 9)
    veto_count = np.sum(f <= 0.0)
    if veto_count >= 4:
        raise HardStop(
            gate_id="GATE_3",
            reason=f"Protocol non-viable ({veto_count} interventions refused)"
        )
    
    # Enforce Zero-Veto and scale evidence
    # f=0 results in E(B)=0; f=1 results in 100% score
    adjusted_e_b = e_b * f
    
    return adjusted_e_b

# ============================================================
# POST-GATE SAFEGUARDS (S-22, S-06)
# ============================================================
def apply_safeguards(e_b_vector):
    """
    Applies CLIP normalization and Laplace smoothing to final output.
    """
    # S-22: Absolute Normalization CLIP[0,1]
    e_b_clipped = np.clip(e_b_vector, 0.0, 1.0)
    
    # S-06: Geometric Mean Zero-Guard (Laplace ε = 1e-6)
    if np.any(e_b_clipped == 0.0):
        e_b_clipped = e_b_clipped + 1e-6
        
    return e_b_clipped

# ============================================================
# FULL PIPELINE EXECUTION
# ============================================================
def run_cgnr_pipeline(patient_crp, corcondia, compliance_f, raw_scores):
    """
    Executes sequential validation. Returns final Evidence Scores and Status Flag.
    """
    try:
        # Stage 1: Dynamic Floor (Hormonal Modifier)
        _ = gate_1_dynamic_floor(patient_crp, h_hormonal=1.0)
        
        # Stage 2: Data Integrity (CORCONDIA Residual)
        gate_2_residual_norm(corcondia)
        
        # Stage 3: Compliance Veto (n=9 Vector)
        gated_scores = gate_3_zero_veto(compliance_f, raw_scores)
        
        # Final: Safeguards (Normalisation & Laplace)
        final_output = apply_safeguards(gated_scores)
        
        return final_output, "GREEN"

    except (HardStop, RankFailure) as e:
        # Log incident for SOC-29 liability audit
        print(f"PIPELINE BLOCKED: {e}")
        return None, "RED"

if __name__ == "__main__":
    # TEST CASE: Patient refusing Intervention #7 (e.g., Vegan refusing MCT)
    # n=9 interventions to match p1-p9 evidence priors
    test_f = [1, 1, 1, 1, 1, 1, 0, 1, 1] 
    test_scores = [0.85, 0.90, 0.45, 0.70, 0.82, 0.61, 0.95, 0.52, 0.77]
    
    print("--- Executing CGNR Matrix Pipeline Validation ---")
    output, flag = run_cgnr_pipeline(
        patient_crp=12.0, 
        corcondia=88.5, 
        compliance_f=test_f, 
        raw_scores=test_scores
    )
    
    if output is not None:
        print(f"Status: {flag}")
        print(f"Gated Evidence Scores (n=9): \n{np.round(output, 4)}")
    else:
        print(f"Status: {flag} - HARD STOP TRIGGERED")
