# CGNR Matrix — Gate Specification

## Overview

Each gate is a deterministic function that either passes (returns a value) or blocks (raises an exception). There are no probabilistic fallbacks, no "best effort" outputs, and no silent failures.

---

## Gate 1: Dynamic Floor

**SPOF resolved**: P0-1 (Attenuation-Floor Paradox / Sepsis Score Inflation)
**Module**: `logic/crp_sigmoid.py` → `logic/hil_gates.py`

### Mathematical specification

The hormonal attenuation coefficient:

```
h(CRP) = 1 / (1 + exp(k · (CRP - midpoint)))
```

| Parameter | Symbol | Default | Domain |
|-----------|--------|---------|--------|
| CRP value | CRP | — | [0, ∞) mg/dL |
| Steepness | k | 0.18 | (0, ∞) |
| Midpoint | mid | 25.0 | (0, threshold) mg/dL |
| Threshold | t | 50.0 | (0, ∞) mg/dL |

**Hard Stop**: if `CRP ≥ t`, then `h = 0.0` and gate status = `"HARD_STOP"`.

### Boundary behavior

- `CRP = 0` → `h ≈ 0.989` (near-full hormonal contribution, no inflammation)
- `CRP = 25` (midpoint) → `h = 0.500` (50% attenuation)
- `CRP = 49` → `h ≈ 0.013` (near-total attenuation)
- `CRP = 50` (threshold) → `h = 0.0`, **HardStop** raised

### Input validation

- CRP must be finite and ≥ 0
- Threshold must be finite and > 0
- Midpoint must be finite and in (0, threshold)
- k must be finite and > 0

### Design rationale

The sigmoid midpoint (25) is deliberately set below the hard-stop threshold (50). Placing the inflection on the threshold (the original v1.0 design) left `h ≈ 0.5` at CRP=50 — the curve never attenuated before the cliff. With the midpoint at half the threshold and `k=0.18`, h falls from ≈0.99 to ≈0.01 across the valid range: a genuine S-curve.

---

## Gate 2: 3σ Residual Norm

**SPOF resolved**: P0-2 (Rank Erasure / Logic Corruption)
**Module**: `logic/hil_gates.py`

### Mathematical specification

One-sided lower bound on CORCONDIA core consistency:

```
Accept if:  CORCONDIA ≥ μ - 3σ
Reject if:  CORCONDIA < μ - 3σ  →  RankFailure
```

| Parameter | Symbol | Default | Domain |
|-----------|--------|---------|--------|
| CORCONDIA | c | — | (-∞, ∞) % |
| Target mean | μ | 85.0 | (0, ∞) % |
| Std deviation | σ | 5.0 | (0, ∞) % |
| Acceptance floor | μ−3σ | 70.0 | — |

### Boundary behavior

- `CORCONDIA = 70.0` (floor) → PASS (boundary inclusive)
- `CORCONDIA = 69.9` → **RankFailure**
- `CORCONDIA = 85.0` (target) → PASS
- `CORCONDIA = 100.0` (excellent) → PASS (one-sided: higher is better)
- `CORCONDIA = 1000.0` → PASS

### Design rationale

CORCONDIA is a "higher is better" metric. The original v1.0 implementation used `abs((c-μ)/μ)*100 > 15` — a symmetric check that flagged a *better* fit (c=100) as corrupt. The one-sided lower bound ensures only actual degradation (c < floor) triggers failure.

### Input validation

- CORCONDIA must be finite
- μ must be finite and > 0
- σ must be finite and > 0

---

## Gate 3: Zero-Veto Compliance

**SPOF resolved**: P0-3 (Compliance Scalar Flaw / Patient Abandonment)
**Module**: `logic/hil_gates.py`

### Mathematical specification

Per-intervention evidence scaling:

```
E_gated = E(B) × f    (element-wise, n=9)
```

**Tier 3 escalation**: if `count(f ≤ 0) ≥ tier3_refusals`, raise **HardStop**.

| Parameter | Symbol | Default | Domain |
|-----------|--------|---------|--------|
| Compliance vector | f | — | [0,1]^9 |
| Evidence scores | E(B) | — | [0, ∞)^9 |
| Dimensionality | n | 9 | fixed |
| Tier 3 threshold | — | 4 | [1, n] |

### Boundary behavior

- `f = [1,1,1,1,1,1,0,1,1]` (1 refusal) → element 6 zeroed, others pass
- `f = [0,0,0,1,1,1,1,1,1]` (3 refusals) → 3 elements zeroed, others pass
- `f = [0,0,0,0,1,1,1,1,1]` (4 refusals) → **HardStop** (Tier 3)
- `f = [0]*9` (all refused) → **HardStop** (Tier 3)

### Design rationale

The original v1.0 design used a scalar compliance factor — one refusal (f=0) zeroed the entire protocol. The vector approach (f ∈ [0,1]^9) allows per-intervention veto: a patient refusing one intervention (e.g., MCT oil) still receives the other 8. Tier 3 escalation at ≥4 refusals ensures non-viable protocols are blocked.

### Input validation

- f and E(B) must have shape (9,)
- All elements must be finite (no NaN/Inf)
- f must be in [0, 1]
- E(B) must be ≥ 0

---

## Post-Gate Safeguards

**SPOFs resolved**: S-22 (normalisation breach), S-06 (geometric mean log(0))
**Module**: `logic/hil_gates.py :: apply_safeguards`

### Specification

```
1. v = CLIP(input, 0, 1)           # S-22: range invariant
2. v = WHERE(v == 0, ε, v)          # S-06: Laplace zero-guard
3. return CLIP(v, 0, 1)             # re-clip: preserve invariant
```

| Parameter | Default | Domain |
|-----------|---------|--------|
| Laplace ε | 1e-6 | (0, 1) |

### Design rationale

The original v1.0 implementation added ε to *all* elements after clipping, pushing values at 1.0 to 1.000001 — violating the S-22 invariant. The fix replaces only exact zeros with ε, then re-clips. The [0,1] bound is preserved by construction.

### Input validation

- Input must be finite (no NaN/Inf)
- ε must be finite and in (0, 1)

---

## Pipeline

The pipeline (`run_cgnr_pipeline`) executes gates sequentially:

```
Gate 1 → Gate 2 → Gate 3 → Safeguards → GREEN
```

Any gate failure catches the exception and returns a `PipelineResult` with:
- `flag = "RED"`
- `incident = Incident(gate_id, reason)`
- `scores = None`

On success:
- `flag = "GREEN"`
- `scores = np.ndarray` (safeguarded, in [0,1])
- `h_hormonal = float` (attenuation coefficient from Gate 1)
- `incident = None`
