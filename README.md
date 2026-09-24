# CGNR Matrix — Clinical Decision Support System

[![CI](https://github.com/HyyperNab/CGNR-Matrix-CDSS/actions/workflows/ci.yml/badge.svg)](https://github.com/HyyperNab/CGNR-Matrix-CDSS/actions/workflows/ci.yml)
[![python](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![license](https://img.shields.io/badge/license-MIT-green)]()

Mathematical core and safety-validation framework for the **Constraint-Grounded
Nutritional Recovery (CGNR) Matrix**, a 3-mode tensor-based CDSS for
personalised post-gastrectomy nutrition. It operates behind three deterministic
**Human-in-the-Loop (HIL)** safety gates.

> ⚠️ **Research prototype.** Not a medical device. The hormonal-attenuation
> constants are theoretical baselines; clinical calibration is reserved for
> future work. See the `Citation & Liability` section.

## 🛡️ Safety gates

| Gate | Name | SPOF resolved | What it does |
|------|------|---------------|--------------|
| 1 | Dynamic Floor | P0-1 | CRP-dependent hormonal attenuation; Hard Stop at the sepsis threshold |
| 2 | 3σ Residual Norm | P0-2 | One-sided CORCONDIA lower bound (`μ − 3σ`); detects rank erasure |
| 3 | Zero-Veto | P0-3 | Per-intervention compliance veto on `f = 0`; Tier 3 escalation at ≥4 refusals |

Post-gate safeguards: `CLIP[0,1]` normalisation (S-22) and Laplace zero-guard
(S-06) protect the geometric-mean scoring.

## 📦 Repository layout

```
logic/
  __init__.py        package exports
  crp_sigmoid.py     Gate 1 — hormonal attenuation sigmoid
  hil_gates.py       Gates 1–3, safeguards, pipeline
audit/
  spof_matrix_29.csv 32-entry SPOF audit matrix (3 critical P0-* + 29 systematic S-*)
tests/
  test_cgnr_logic.py pytest suite (48 tests, 90% coverage)
.github/workflows/
  ci.yml              CI pipeline (ruff → mypy → pytest)
demo.py                  demo script (pipeline + attenuation table)
.gitignore
pyproject.toml           packaging + tool config
requirements.txt         runtime dependencies
AUDIT.md                 engineering audit (findings + fixes)
NOTES.md                 deferred solver-layer items
LICENSE                  MIT
```

## 🚀 Quick start

```bash
pip install -e ".[dev]"          # runtime + dev dependencies
python -m pytest -v              # run the test suite (48 tests)
python demo.py                   # demo: pipeline run + attenuation table
```

### Example

```python
from logic import run_cgnr_pipeline

result = run_cgnr_pipeline(
    patient_crp=12.0,
    corcondia=88.5,
    compliance_f=[1, 1, 1, 1, 1, 1, 0, 1, 1],   # intervention #7 refused
    raw_scores=[0.85, 0.90, 0.45, 0.70, 0.82, 0.61, 0.95, 0.52, 0.77],
)

if result.ok:
    print(result.scores)        # gated, safeguarded evidence vector
    print(result.h_hormonal)    # attenuation coefficient applied
else:
    print(result.incident)      # structured SOC-29 record
```

## 🔍 Engineering audit

`AUDIT.md` documents the independent review of math correctness, internal
consistency, and code hygiene. Every finding was verified numerically before
fixing. Headline fixes:

- Gate 1 sigmoid now genuinely attenuates (was a near-flat curve truncated by a cliff) and is actually invoked by the pipeline.
- Gate 2 is an honest one-sided 3σ lower bound (a better CORCONDIA no longer fails).
- Safeguard Laplace step no longer breaks the `CLIP[0,1]` invariant.
- Dimensionality contradiction (`n=9` vs `n=8` in the audit matrix) resolved.
- Boundary comparisons use `>=` on safety thresholds.
- NaN/Inf inputs rejected across all gates and safeguards.
- LibreOffice lock file removed from version control.

## ⚖️ Citation & liability

This system implements the **SOC-29 (Safety Override Clause)** framework for
algorithmic liability. Boundary violations trigger a `HardStop` and return a
structured `Incident` record for the SOC-29 audit trail. See the Main Paper for
the full legal specification.
