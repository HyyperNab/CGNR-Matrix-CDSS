"""CGNR Matrix CDSS — logic package."""

from .crp_sigmoid import h_hormonal_attenuation
from .hil_gates import (
    N_INTERVENTIONS,
    HardStop,
    Incident,
    PipelineResult,
    RankFailure,
    apply_safeguards,
    gate_1_dynamic_floor,
    gate_2_residual_norm,
    gate_3_zero_veto,
    run_cgnr_pipeline,
)

__all__ = [
    "N_INTERVENTIONS",
    "HardStop",
    "Incident",
    "PipelineResult",
    "RankFailure",
    "apply_safeguards",
    "gate_1_dynamic_floor",
    "gate_2_residual_norm",
    "gate_3_zero_veto",
    "h_hormonal_attenuation",
    "run_cgnr_pipeline",
]

__version__ = "2.0.0"
