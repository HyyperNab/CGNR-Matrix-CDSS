<div align="center">

# 🧬 CGNR Matrix

### Constraint-Grounded Nutritional Recovery — Clinical Decision Support System

**From catabolic chaos → deterministic, evidence-grounded post-gastrectomy nutrition**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-v2.0.0-teal.svg)](https://github.com/HyyperNab/CGNR-Matrix-CDSS)
[![Status](https://img.shields.io/badge/status-logic%20locked-red.svg)](REPOSITORY_LOCK.md)
[![Tests](https://img.shields.io/badge/pytest-48%20passing-brightgreen.svg)](https://github.com/HyyperNab/CGNR-Matrix-CDSS/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen.svg)](https://github.com/HyyperNab/CGNR-Matrix-CDSS/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

</div>

---

> *Safety over throughput. Hard stops over soft fallbacks. Determinism over heuristics. Clinician accountability over algorithmic opacity. Every gate is a liability boundary.*

CGNR Matrix is a **3-mode tensor-based CDSS** for personalised post-gastrectomy nutrition. It computes evidence-weighted intervention scores through a pipeline guarded by three deterministic **Human-in-the-Loop (HIL) safety gates** — each resolving a critical Single Point of Failure (SPOF) identified in the 32-entry audit matrix.

📖 **[Read the SPOF analysis →](docs/SPOF_ANALYSIS.md)** — how 32 failure modes were identified, classified, and eliminated.

---

## 🎯 The Problem It Solves

Post-gastrectomy patients face catabolic crisis, hormonal disruption, and nutritional complexity. Existing CDSS approaches suffer from:

- **Sepsis score inflation** — CRP-driven hormonal factors inflate evidence up to 60× during catabolic crisis, producing dangerously aggressive recommendations
- **Rank erasure** — tensor decomposition silently degrades, producing statistically corrupt outputs that look valid
- **Compliance scalar flaws** — a single scalar compliance factor means one refusal can zero out the entire protocol, abandoning the patient

**Before**: A clinician receives a "GREEN" recommendation that is statistically corrupted, hormonally inflated, and ignores patient refusals.

**After**: Three deterministic gates intercept each failure mode. The pipeline either returns a clean, safeguarded evidence vector — or it Hard Stops with a structured SOC-29 incident record. No silent failures.

---

## 🚀 Quick Start

```bash
# Install (runtime + dev dependencies)
pip install -e ".[dev]"

# Run the test suite (48 tests, 90% coverage)
python -m pytest -v

# Demo: pipeline + attenuation curve
python demo.py
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

📖 **[Full quick start guide →](QUICK_START.md)**

---

## 🏗️ Architecture

```
Patient Input (CRP, CORCONDIA, compliance f∈[0,1]⁹, evidence scores)
    │
    ▼
┌──────────────────┐    ┌──────────────────────────────────────────┐
│   GATE 1         │    │ CRP Sigmoid Attenuation                  │
│   Dynamic Floor  │───▶│ h(CRP) = 1 / (1 + exp(k·(CRP - mid)))   │
│   (SPOF P0-1)    │    │ Hard Stop if CRP ≥ 50 mg/dL             │
└──────────────────┘    └──────────────────────────────────────────┘
    │ h_hormonal
    ▼
┌──────────────────┐    ┌──────────────────────────────────────────┐
│   GATE 2         │    │ One-sided 3σ Lower Bound                 │
│   Residual Norm  │───▶│ Accept if CORCONDIA ≥ μ - 3σ (= 70)     │
│   (SPOF P0-2)    │    │ RankFailure if below floor               │
└──────────────────┘    └──────────────────────────────────────────┘
    │
    ▼
┌──────────────────┐    ┌──────────────────────────────────────────┐
│   GATE 3         │    │ Per-Intervention Veto                    │
│   Zero-Veto      │───▶│ E(B) × f  (element-wise)                │
│   (SPOF P0-3)    │    │ Hard Stop if ≥4/9 refusals (Tier 3)     │
└──────────────────┘    └──────────────────────────────────────────┘
    │ gated scores
    ▼
┌──────────────────┐    ┌──────────────────────────────────────────┐
│   SAFEGUARDS     │    │ CLIP[0,1] (S-22) + Laplace ε=1e-6 (S-06)│
│   S-22 / S-06    │───▶│ Zero-guard preserves geometric mean     │
└──────────────────┘    └──────────────────────────────────────────┘
    │
    ▼
  GREEN → safeguarded evidence vector (n=9)
  RED   → structured Incident (SOC-29 audit trail)
```

**3 logic modules** · **9 interventions** · **32-entry SPOF matrix** · **3 deterministic gates** · **0 probabilistic fallbacks**

---

## 🛡️ Safety Gates

| Gate | Name | SPOF | Mechanism | Failure mode eliminated |
|------|------|------|-----------|------------------------|
| 1 | Dynamic Floor | P0-1 | CRP sigmoid → Hard Stop at sepsis threshold | 60× evidence inflation during catabolic crisis |
| 2 | 3σ Residual Norm | P0-2 | One-sided CORCONDIA lower bound (μ−3σ) | Rank erasure producing corrupt-but-valid-looking output |
| 3 | Zero-Veto | P0-3 | Per-intervention veto + Tier 3 escalation | Patient abandonment via scalar compliance collapse |

Post-gate safeguards: `CLIP[0,1]` normalisation (S-22) and Laplace zero-guard (S-06) protect the geometric-mean scoring pipeline from range violations and `log(0)` crashes.

📖 **[Gate specification →](docs/GATE_SPECIFICATION.md)**

---

## 🔒 Governance (Anti-Drift)

CGNR Matrix is **logic-locked** against drift. The safety gates, boundary constants, and safeguard ordering are frozen — changes require a written rationale and full regression testing.

| Principle | Enforcement |
|-----------|-------------|
| **Safety over throughput** | Hard Stops are non-negotiable. No fallback, no "best effort" output. |
| **Determinism** | Same input → identical output. No randomization, no heuristics. |
| **Clinician accountability** | Every blocked run produces a structured `Incident` (SOC-29 audit trail). |
| **NaN/Inf rejection** | All inputs validated for finiteness. No silent NaN propagation. |
| **Boundary conservatism** | Safety thresholds use `>=` (inclusive). The boundary itself is a Hard Stop. |
| **Invariant preservation** | `CLIP[0,1]` holds after every safeguard step, verified by 48 tests. |

See [`REPOSITORY_LOCK.md`](REPOSITORY_LOCK.md).

---

## 🛡️ Engineering Quality

| Guarantee | How |
|-----------|-----|
| **No silent failures** | All gate violations raise `HardStop` or `RankFailure` |
| **No NaN propagation** | `np.isfinite()` checks on every input path |
| **No CLIP violation** | Laplace zero-guard applied before final re-clip |
| **No dimension mismatch** | Vector shapes validated against `N_INTERVENTIONS=9` |
| **No dead code** | Gate 1 sigmoid is invoked by the pipeline (verified by tests) |
| **Full audit trail** | Every blocked run returns a structured `Incident` record |
| **Reproducible builds** | `pyproject.toml` pins Python ≥3.10, deps in `requirements.txt` |
| **CI-enforced** | ruff + mypy + pytest with 85% coverage gate on every push |

---

## ❌ Error Handling (No Silent Failures)

| Condition | Behavior |
|-----------|----------|
| CRP ≥ 50 mg/dL (sepsis threshold) | **HardStop** — Gate 1 blocks, h=0.0 |
| CORCONDIA < μ−3σ (rank corruption) | **RankFailure** — Gate 2 blocks |
| ≥4/9 interventions refused | **HardStop** — Gate 3 blocks (Tier 3 escalation) |
| NaN or Inf in any input | **ValueError** — rejected before gate execution |
| Compliance vector out of [0,1] | **ValueError** — rejected |
| Vector dimension ≠ 9 | **ValueError** — rejected |
| Laplace ε out of (0,1) | **ValueError** — rejected |
| CLIP[0,1] invariant violated | **Impossible** — re-clip after Laplace (test-verified) |

---

## 📊 Version History

| Version | Date | Change |
|---------|------|--------|
| v1.0.0 | 2026-01 | Initial ESPEN submission: logic + audit structure |
| **v2.0.0** | **2026-09** | **Engineering audit: math fixes, NaN guards, CI, 48 tests, governance lock** |

---

## 📦 Repository Layout

```
logic/
  __init__.py             Package exports, __version__
  crp_sigmoid.py          Gate 1 — CRP hormonal attenuation sigmoid
  hil_gates.py            Gates 1–3, safeguards, pipeline, incident records
audit/
  spof_matrix_29.csv      32-entry SPOF audit matrix (3 P0-* + 29 S-*)
docs/
  SPOF_ANALYSIS.md        Formal SPOF analysis & elimination plan
  GATE_SPECIFICATION.md   Mathematical specification of each gate
  MATH_VALIDATION.md      Numerical verification of all math claims
tests/
  test_cgnr_logic.py      48 tests, 90% coverage
.github/workflows/
  ci.yml                  CI pipeline (ruff → mypy → pytest, Python 3.10/3.11/3.12)
demo.py                   Pipeline demo + attenuation table
.gitignore
pyproject.toml            Packaging + tool config (ruff, mypy, pytest)
requirements.txt          Runtime dependencies
REPOSITORY_LOCK.md        Logic-lock governance document
QUICK_START.md            Quick start guide
AUDIT.md                  Engineering audit report
NOTES.md                  Deferred solver-layer items
LICENSE                   MIT
```

---

## ⚖️ Citation & Liability

This system implements the **SOC-29 (Safety Override Clause)** framework for algorithmic liability. Boundary violations trigger a `HardStop` and return a structured `Incident` record for the SOC-29 audit trail.

> ⚠️ **Research prototype.** Not a medical device. Hormonal-attenuation constants are theoretical baselines; clinical calibration is reserved for future work.

See the Main Paper for the full legal specification.

---

<div align="center">

**Logic locked. Gates verified. No silent failures.**

*Safety over throughput. Determinism over cleverness.*

</div>
