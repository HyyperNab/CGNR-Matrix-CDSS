# Engineering Audit — CGNR Matrix CDSS

Independent review of `logic/` and `audit/` for mathematical correctness,
internal consistency, and professional code hygiene. All findings below were
verified numerically before fixing.

## Status legend
- **FIXED** — corrected in this revision.
- **NOTED** — acknowledged limitation, documented in code rather than silently left.

---

## M1. Sigmoid attenuation is decorative  *(FIXED)*
**File:** `logic/crp_sigmoid.py`

With `k=0.1, crp_inflection=50`, across the clinically valid range
CRP ∈ [0, 50] the output only varies `0.993 → 0.500`. The inflection point
sits *on* the hard-stop boundary, so the curve never approaches 0 before the
cliff — "attenuation" does almost nothing.

```
crp= 0  h=0.993307
crp=20  h=0.952574
crp=45  h=0.622459
crp=50  h=0.500000   <- cliff to 0.0 above
```

**Fix:** decouple the sigmoid midpoint from the hard-stop threshold. The
inflection is now the *attenuation midpoint* (default 25 mg/dL, half the
sepsis threshold) and `k` is calibrated (default 0.18) so the curve falls
from ≈0.99 at CRP=0 to ≈0.01 as CRP approaches the threshold — a genuine
S-curve rather than a flat line truncated by a cliff.

## M2. Gate 2 "3σ" check is neither 3σ nor one-sided  *(FIXED)*
**File:** `logic/hil_gates.py`

Original code:
```python
residual = abs((corcondia_value - MU_CORCONDIA) / MU_CORCONDIA) * 100.0
if residual > BOUNDARY_3SIGMA:   # 15.0
```
This is a *symmetric percentage error*, not a 3σ residual — there is no
standard-deviation term. Because of `abs()`, a **higher** CORCONDIA (i.e. a
better model fit) triggers `RankFailure`:

```
corcondia=100.00  residual=17.65%  fail=True   <- perfect fit flagged as corrupt
corcondia= 72.25  residual=15.00%  fail=False
```

**Fix:** implement an honest one-sided lower-bound check. `sigma` is now an
explicit parameter (default 5.0); the acceptance floor is
`MU − 3σ = 85 − 15 = 70`. CORCONDIA above the mean never fails. The "3σ"
label is now truthful.

## M3. Safeguard order breaks the CLIP invariant  *(FIXED)*
**File:** `logic/hil_gates.py :: apply_safeguards`

```python
e_b_clipped = np.clip(e_b_vector, 0.0, 1.0)
if np.any(e_b_clipped == 0.0):
    e_b_clipped = e_b_clipped + 1e-6      # added to EVERY element
```
Adding ε to all elements *after* clipping pushes values that were exactly
1.0 to `1.000001`, violating the S-22 `CLIP[0,1]` invariant the line above
just established. Confirmed:
```
[0.0, 0.5, 1.0] -> [1e-6, 0.500001, 1.000001]   exceeds 1? True
```
Also, the conditional means Laplace smoothing is inconsistently applied
(present only when some element is zero).

**Fix:** replace exact zeros with ε (not additive to all), then re-clip.
Laplace ε is now applied deterministically and the [0,1] bound holds.

## L1. Two disconnected Gate 1 implementations  *(FIXED)*
`crp_sigmoid.h_hormonal_attenuation` returns a tuple `(h, status)`;
`hil_gates.gate_1_dynamic_floor` raises `HardStop`. The pipeline calls
`gate_1_dynamic_floor(..., h_hormonal=1.0)` and **never invokes the sigmoid**.
The README's "CRP-dependent hormonal attenuation" is absent from the actual
pipeline.

**Fix:** `gate_1_dynamic_floor` now computes `h` via
`h_hormonal_attenuation` internally, enforces the floor, and returns the
attenuated coefficient. The dead `h_hormonal` parameter is removed. The
pipeline passes through the real attenuated value.

## L2. `gate_1` parameter `h_hormonal` is dead code  *(FIXED)*
The parameter was reassigned locally and then an exception was raised, so it
could never influence output. Removed (folded into L1).

## L3. Safety boundary off-by-one  *(FIXED)*
`crp_value > 50` (strict) lets `CRP == 50.0` pass, yet 50 is defined as the
sepsis threshold. On a clinical safety boundary the conservative choice is
`>=`. Fixed to `>= crp_inflection` in both modules.

## L4. Dimensionality contradiction (n=9 vs n=8)  *(FIXED)*
Code, docstrings, and test vectors all use `n=9`, but the audit matrix
declared:
- S-17: `f in [0, 1]^8 graded adherence`
- S-18: `8-field structured log`

**Fix:** S-17 and S-18 corrected to `n=9` / `9-field` for consistency with
the tensor dimensionality declared in the header and `S-29`.

## L5. Pipeline swallows safety exceptions and `print()`s  *(FIXED)*
`run_cgnr_pipeline` caught `HardStop`/`RankFailure`, printed to stdout, and
returned `(None, "RED")`. A clinical safety module must not bury boundary
violations in stdout.

**Fix:** pipeline now catches exceptions and returns a structured
`PipelineResult` with an `Incident` record (gate id, reason). Callers
decide how to surface it. No bare `print`.

## L6. Audit matrix claims unimplemented resolutions  *(NOTED)*
S-07 (AdvNS solver, 20 seeds), S-08 (Tikhonov regularisation),
S-11 (convergence tol 1e-8), S-13 (Tensorly 0.8 pinning) are asserted as
resolved but have no corresponding code in this repository. These belong to
the solver layer, which is out of scope for this logic/audit core.

**Action:** `requirements.txt` now pins the runtime deps that *are* used
(numpy, matplotlib). A `NOTES.md` entry marks the solver-layer items as
deferred so the audit no longer overstates what the repo delivers.

## H1. LibreOffice lock file committed to git  *(FIXED)*
`audit/.~lock.spof_matrix_29.csv#` was tracked. Removed from the index;
`.gitignore` now excludes lock files.

## H2. No .gitignore / requirements.txt / tests / package marker  *(FIXED)*
Added `.gitignore`, `requirements.txt`, `logic/__init__.py`,
`tests/test_cgnr_logic.py`, and a `pytest`-compatible test suite covering
the sigmoid curve, each gate, the safeguard invariant, and the pipeline.
