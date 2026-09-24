# CGNR Matrix v2.0.0 — REPOSITORY LOCK

**Date**: 2026-09-24
**Version**: v2.0.0
**Status**: HARD LOCKED
**Codename**: AUDIT-LOCK
**Amendment**: Engineering audit (v1.0.0 → v2.0.0)

---

## LOCK STATUS: ✅ ACTIVE

This repository is **HARD LOCKED** against drift.

**Changes require**:
1. Version bump
2. Written rationale
3. Full regression testing (48 tests must pass)
4. SPOF matrix update (if new failure modes discovered)
5. Math validation re-run (see `docs/MATH_VALIDATION.md`)

---

## WHAT IS LOCKED

### 1. Gate Boundaries (Safety-Critical)

| Constant | Value | Location | Lock reason |
|----------|-------|----------|-------------|
| `CRP_THRESHOLD_DEFAULT` | 50.0 mg/dL | `crp_sigmoid.py` | Sepsis threshold (McClave 2016, Singer 2019) |
| `CRP_MIDPOINT_DEFAULT` | 25.0 mg/dL | `crp_sigmoid.py` | Sigmoid inflection (half threshold by design) |
| `K_DEFAULT` | 0.18 | `crp_sigmoid.py` | Sigmoid steepness (calibrated: h→0.01 near threshold) |
| `MU_CORCONDIA` | 85.0 | `hil_gates.py` | Target CORCONDIA core consistency |
| `SIGMA` | 5.0 | `hil_gates.py` | CORCONDIA standard deviation (floor = 70) |
| `N_INTERVENTIONS` | 9 | `hil_gates.py` | Tensor dimensionality (3-mode, 9 priors) |
| `TIER3_REFUSALS` | 4 | `hil_gates.py` | Tier 3 escalation threshold (≥4/9 refusals) |
| `LAPLACE_EPS` | 1e-6 | `hil_gates.py` | Geometric mean zero-guard |

**Frozen**. Changing these without clinical re-validation = safety violation.

### 2. Gate Logic (Immutable)

```
Gate 1: h(CRP) = 1/(1+exp(k·(CRP-mid)))  →  Hard Stop if CRP ≥ threshold
Gate 2: Accept if CORCONDIA ≥ μ - 3σ      →  RankFailure if below
Gate 3: E(B) × f  (element-wise)          →  Hard Stop if refusals ≥ tier3
```

**Frozen**. The gate ordering (1→2→3) is a safety invariant.

### 3. Safeguard Ordering (S-22 → S-06)

```
1. CLIP[0,1]          (S-22: range invariant)
2. Replace 0 → ε      (S-06: Laplace zero-guard)
3. Re-CLIP[0,1]       (preserve invariant)
```

**Frozen**. The re-clip after Laplace is the fix for audit finding M3.

### 4. Core Principles

```
1. safety_over_throughput
2. hard_stops_over_soft_fallbacks
3. determinism_over_heuristics
4. clinician_accountability_over_algorithmic_opacity
5. every_gate_is_a_liability_boundary
```

---

## WHAT IS NOT LOCKED

| Item | Status | Notes |
|------|--------|-------|
| Solver layer (S-07, S-08, S-11, S-13) | Deferred | See `NOTES.md` |
| Plot styling | Open | Cosmetic only |
| Demo data | Open | Example only |
| Test additions | Encouraged | More coverage welcome |

---

## CHANGE POLICY

### Allowed without amendment
- Adding tests
- Updating docs
- Cosmetic changes (formatting, comments)
- Dependency version bumps (within semver)

### Requires amendment (version bump + rationale + regression)
- Changing any locked constant
- Modifying gate logic
- Reordering safeguard steps
- Changing `N_INTERVENTIONS`
- Removing or renaming public API

### Forbidden
- Removing NaN/Inf guards
- Removing the re-clip after Laplace
- Adding fallback logic to any gate
- Making Hard Stops non-blocking
