# Notes — deferred / out-of-scope items

The SPOF audit matrix (`audit/spof_matrix_29.csv`) documents resolutions
across the full CGNR stack. Several entries belong to the **solver layer**
(tensor decomposition backend), which is not shipped in this repository —
this repo contains only the `logic/` safety core and the `audit/` matrix.

The following audit resolutions are therefore **deferred** (claimed in the
matrix but not implemented here). They are tracked for completeness so the
repo does not overstate what it delivers:

| ID  | Claimed resolution            | Status    |
|-----|-------------------------------|-----------|
| S-07| AdvNS Solver (20 seeds)        | deferred  |
| S-08| Tikhonov Regularisation        | deferred  |
| S-11| Convergence tol 1e-8           | deferred  |
| S-13| Library pinning (Tensorly 0.8) | deferred  |
| S-05| Little & Rubin Imputation      | deferred  |

`requirements.txt` pins only the runtime dependencies the `logic/` core
uses (numpy, matplotlib). Development dependencies (pytest, ruff, mypy)
are declared in `pyproject.toml` under `[project.optional-dependencies] dev`
and installed via `pip install -e ".[dev]"`. When the solver layer lands,
its dependencies (e.g. `tensorly>=0.8`) should be added there.
