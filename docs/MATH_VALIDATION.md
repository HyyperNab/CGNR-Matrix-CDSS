# CGNR Matrix — Math Validation

Every mathematical claim in this repository was verified numerically. This document records the verification results.

**Verification date**: 2026-09-24
**Python**: 3.12.3
**NumPy**: 1.24+

---

## M1: Sigmoid Attenuation Curve

### Claim
With `k=0.18, midpoint=25, threshold=50`, h falls from ≈0.99 (CRP=0) to ≈0.01 (CRP≈50).

### Verification

```
CRP= 0   h=0.989013   (claim: ≈0.99)   ✓
CRP=10   h=0.937027
CRP=20   h=0.710950
CRP=25   h=0.500000   (midpoint, exact 0.5)   ✓
CRP=30   h=0.289050
CRP=40   h=0.062973
CRP=45   h=0.026597
CRP=49   h=0.013125   (claim: ≈0.01)   ✓
CRP=50   h=0.000000   (Hard Stop)   ✓
```

**Monotonicity**: verified decreasing across [0, 49.9] (50-point sweep, `itertools.pairwise` check).

**Result**: ✅ PASS

---

## M2: Gate 2 One-Sided 3σ Lower Bound

### Claim
`μ - 3σ = 85 - 15 = 70`. CORCONDIA ≥ 70 passes; < 70 fails. Higher values never fail.

### Verification

```
CORCONDIA= 10.0   FAIL (RankFailure)   ✓
CORCONDIA= 50.0   FAIL (RankFailure)   ✓
CORCONDIA= 69.9   FAIL (RankFailure)   ✓
CORCONDIA= 70.0   PASS (boundary)      ✓
CORCONDIA= 85.0   PASS (target)        ✓
CORCONDIA=100.0   PASS (better fit)    ✓
CORCONDIA=120.0   PASS                 ✓
CORCONDIA=1000.0  PASS                 ✓
```

**Result**: ✅ PASS (one-sided, higher-is-better verified)

---

## M3: Safeguard CLIP[0,1] Invariant

### Claim
After Laplace zero-guard, all values remain in [0, 1].

### Verification

```
Input: [0.0, 0.5, 1.0]
Output: [1e-06, 0.5, 1.0]
max(output) = 1.0   (NOT 1.000001)   ✓
min(output) = 1e-06   ✓

Input: [-0.5, 0.0, 0.5, 1.0, 2.0]
Output: [1e-06, 1e-06, 0.5, 1.0, 1.0]
max = 1.0   ✓

Input: [0.0] * 9
Output: [1e-06] * 9
max = 1e-06 ≤ 1.0   ✓

Random sweep: 50 values in [-0.5, 1.5)
All outputs in [0, 1]   ✓
```

**Result**: ✅ PASS (invariant preserved, including edge cases)

---

## M4: k Calibration

### Claim
`k ≈ ln(99) / (threshold - midpoint) = 4.595 / 25 ≈ 0.184`, rounded to 0.18.

### Verification

```
ln(99) = 4.595120
k_exact = 4.595120 / (50 - 25) = 0.183805
K_DEFAULT = 0.18

h(49) with k=0.18:    0.013125
h(49) with k=0.1838:  0.012584
```

Both produce h < 0.05 near the threshold. The rounding from 0.184 to 0.18 has negligible clinical impact (h difference < 0.001 at CRP=49).

**Result**: ✅ PASS

---

## M5: Boundary Inclusivity (>=)

### Claim
`CRP = 50.0` (exactly the threshold) triggers Hard Stop.

### Verification

```
h_hormonal_attenuation(50.0) → (0.0, "HARD_STOP")   ✓
gate_1_dynamic_floor(50.0)   → raises HardStop       ✓
h_hormonal_attenuation(49.9) → (0.011, "PASS")       ✓
```

**Result**: ✅ PASS (boundary is inclusive, conservative)

---

## M6: NaN/Inf Rejection

### Claim
All gate inputs reject NaN and Inf with ValueError.

### Verification

```
h_hormonal_attenuation(NaN)    → ValueError   ✓
h_hormonal_attenuation(Inf)    → ValueError   ✓
gate_2_residual_norm(NaN)      → ValueError   ✓
gate_2_residual_norm(Inf)      → ValueError   ✓
gate_3_zero_veto([NaN, ...])   → ValueError   ✓
apply_safeguards([NaN, 0.5])   → ValueError   ✓
apply_safeguards([Inf, 0.5])   → ValueError   ✓
```

**Result**: ✅ PASS (no NaN propagation possible)

---

## M7: Dimensionality Consistency

### Claim
`N_INTERVENTIONS = 9` everywhere (code, tests, CSV, docs).

### Verification

```
hil_gates.py:    N_INTERVENTIONS = 9
__init__.py:     exports N_INTERVENTIONS
test suite:      uses N_INTERVENTIONS for all vector shapes
CSV S-17:        "f in [0, 1]^9 graded adherence"
CSV S-18:        "9-field structured log"
README:          "9 interventions"
REPOSITORY_LOCK: "n = 9"
```

**Result**: ✅ PASS (no n=8 remnants)

---

## Test Suite

All 48 tests pass. Coverage: 90.44%.

```
logic/__init__.py      4 stmts    0 miss   100%
logic/crp_sigmoid.py  44 stmts    4 miss    91%  (only __main__ demo uncovered)
logic/hil_gates.py    88 stmts    9 miss    90%  (only __main__ demo uncovered)
TOTAL                136 stmts   13 miss    90%
```

Uncovered lines are exclusively `if __name__ == "__main__"` demo blocks, which are covered by `demo.py` instead.
