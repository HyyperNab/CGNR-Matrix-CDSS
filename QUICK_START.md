# CGNR Matrix v2.0.0 — Quick Start

## Install

```bash
# Clone
git clone https://github.com/HyyperNab/CGNR-Matrix-CDSS.git
cd CGNR-Matrix-CDSS

# Install (runtime + dev dependencies)
pip install -e ".[dev]"
```

## Run

```bash
# Test suite (57 tests, 100% coverage)
python -m pytest -v

# Demo: 4 scenarios (GREEN + 3 RED paths)
python demo.py

# CLI: structured JSON output
python -m cgnr evaluate --crp 12 --corcondia 88.5 \
    --scores 0.85 0.90 0.45 0.70 0.82 0.61 0.95 0.52 0.77 \
    --compliance 1 1 1 1 1 1 0 1 1

# Lint + format + type-check
ruff check logic/ tests/ demo.py cgnr/
ruff format --check logic/ tests/ demo.py cgnr/
mypy logic/ --ignore-missing-imports
```

## What You Get

- **3 deterministic safety gates** (CRP floor, CORCONDIA 3σ, compliance veto)
- **9-intervention evidence vector** with per-item compliance scaling
- **CLIP[0,1] + Laplace zero-guard** safeguards
- **Structured Incident records** on every blocked run (SOC-29 audit trail)
- **NaN/Inf rejection** on all input paths
- **CLI** with JSON output and structured logging (`python -m cgnr`)
- **57-test regression suite** with 100% coverage

## API

```python
from logic import run_cgnr_pipeline, PipelineResult

result: PipelineResult = run_cgnr_pipeline(
    patient_crp=12.0,          # mg/dL
    corcondia=88.5,            # core consistency %
    compliance_f=[1]*9,        # f ∈ [0,1]^9
    raw_scores=[0.85]*9,       # E(B) priors
)

# GREEN path
result.ok             # True
result.flag           # "GREEN"
result.scores         # np.ndarray, shape (9,), in [0,1]
result.h_hormonal     # float, attenuation coefficient

# RED path
result.incident       # Incident(gate_id="GATE_1", reason="...", flag="RED")
```

### Individual gates

```python
from logic import (
    h_hormonal_attenuation,   # Gate 1 sigmoid
    gate_1_dynamic_floor,     # Gate 1 (returns h or raises HardStop)
    gate_2_residual_norm,     # Gate 2 (returns True or raises RankFailure)
    gate_3_zero_veto,         # Gate 3 (returns ndarray or raises HardStop)
    apply_safeguards,         # CLIP + Laplace
)
```

## Gate Boundaries (Locked)

See [`REPOSITORY_LOCK.md`](REPOSITORY_LOCK.md) for the full lock specification.

| Constant | Value | Meaning |
|----------|-------|---------|
| CRP threshold | 50.0 mg/dL | Sepsis Hard Stop boundary |
| CRP midpoint | 25.0 mg/dL | Sigmoid inflection point |
| k | 0.18 | Sigmoid steepness |
| μ (CORCONDIA) | 85.0% | Target core consistency |
| σ | 5.0% | CORCONDIA standard deviation |
| 3σ floor | 70.0% | Minimum acceptable CORCONDIA |
| n | 9 | Intervention count |
| Tier 3 | ≥4 refusals | Protocol non-viable threshold |
