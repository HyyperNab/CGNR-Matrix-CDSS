# Engineering Audit — CGNR Matrix CDSS

Independent review of `logic/` and `audit/` for mathematical correctness,
internal consistency, and professional code hygiene. All findings below were
verified numerically before fixing.

**Full SPOF analysis**: [`docs/SPOF_ANALYSIS.md`](docs/SPOF_ANALYSIS.md)
**Math verification**: [`docs/MATH_VALIDATION.md`](docs/MATH_VALIDATION.md)
**Gate specification**: [`docs/GATE_SPECIFICATION.md`](docs/GATE_SPECIFICATION.md)

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

**Fix:** decouple the sigmoid midpoint from the hard-stop threshold. The
inflection is now the *attenuation midpoint* (default 25 mg/dL, half the
sepsis threshold) and `k` is calibrated (default 0.18) so the curve falls
from ≈0.99 at CRP=0 to ≈0.01 as CRP approaches the threshold — a genuine
S-curve rather than a flat line truncated by a cliff.

## M2. Gate 2 "3σ" check is neither 3σ nor one-sided  *(FIXED)*
**File:** `logic/hil_gates.py`

Original code used a symmetric percentage error with `abs()` — a *higher*
CORCONDIA (better fit) triggered `RankFailure` (corcondia=100 failed).

**Fix:** honest one-sided lower bound. `sigma` is an explicit parameter
(default 5.0); acceptance floor is `μ − 3σ = 70`. CORCONDIA above the mean
never fails.

## M3. Safeguard order breaks the CLIP invariant  *(FIXED)*
**File:** `logic/hil_gates.py :: apply_safeguards`

Adding ε to all elements after clipping pushed 1.0 → 1.000001, violating S-22.

**Fix:** replace exact zeros with ε (not additive to all), then re-clip.

## L1. Two disconnected Gate 1 implementations  *(FIXED)*
The pipeline called `gate_1_dynamic_floor(h_hormonal=1.0)` and never invoked
the sigmoid. Fixed: gate_1 now computes h via `h_hormonal_attenuation`.

## L2. `gate_1` parameter `h_hormonal` is dead code  *(FIXED)*
Removed (folded into L1).

## L3. Safety boundary off-by-one  *(FIXED)*
`crp_value > 50` (strict) let CRP=50.0 pass. Fixed to `>=`.

## L4. Dimensionality contradiction (n=9 vs n=8)  *(FIXED)*
CSV S-17/S-18 corrected from n=8 to n=9.

## L5. Pipeline swallows safety exceptions and `print()`s  *(FIXED)*
Pipeline now catches exceptions and returns a structured `PipelineResult`
with an `Incident` record. No bare `print`.

## L6. Audit matrix claims unimplemented resolutions  *(NOTED)*
Solver-layer items (S-07, S-08, S-11, S-13, S-05) documented as deferred
in `NOTES.md`.

## S1. NaN/Inf inputs not guarded  *(FIXED)*
All gate inputs now reject NaN/Inf with `ValueError`. 8 tests added.

## H1. LibreOffice lock file committed to git  *(FIXED)*
Removed; `.gitignore` excludes lock files.

## H2. No .gitignore / requirements.txt / tests / package marker  *(FIXED)*
Added all infrastructure: `.gitignore`, `pyproject.toml`, `requirements.txt`,
`logic/__init__.py`, test suite, CI, `REPOSITORY_LOCK.md`, docs.
