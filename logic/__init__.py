"""CGNR Matrix CDSS — logic package."""

from .crp_sigmoid import h_hormonal_attenuation
from .hil_gates import (
    HardStop,
    Incident,
    N_INTERVENTIONS,
    PipelineResult,
    RankFailure,
    apply_safeguards,
    gate_1_dynamic_floor,
    gate_2_residual_norm,
    gate_3_zero_veto,
    run_cgnr_pipeline,
)

__all__ = [
    "h_hormonal_attenuation",
    "gate_1_dynamic_floor",
    "gate_2_residual_norm",
    "gate_3_zero_veto",
    "apply_safeguards",
    "run_cgnr_pipeline",
    "HardStop",
    "RankFailure",
    "Incident",
    "PipelineResult",
    "N_INTERVENTIONS",
]

__version__ = "2.0.0"
