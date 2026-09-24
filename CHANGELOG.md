# Changelog

All notable changes to CGNR Matrix CDSS are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [v2.1.0] — 2026-09-24

### Professional upgrade: CLI, 100% coverage, governance

#### Added
- **CLI**: `python -m cgnr evaluate|gate1|gate2|curve` with JSON output
  and structured logging.
- **100% test coverage**: removed `__main__` demo blocks from logic
  modules (replaced by `demo.py`). Coverage 90% → 100%.
- **9 CLI tests**: evaluate (GREEN + 3 RED paths), gate1, gate2, curve.
- **`demo.py` upgraded**: now shows 4 scenarios (GREEN + 3 RED paths:
  sepsis, rank corruption, Tier 3 escalation).
- **`CHANGELOG.md`**: Keep a Changelog format.
- **`CONTRIBUTING.md`**: contribution guide for safety-critical changes.
- **ruff format** enforcement in CI (format check alongside lint).
- **`cgnr/` package**: CLI entry point module.

#### Changed
- CI coverage gate raised from 85% to 90%.
- 57 tests total (was 48).

#### Removed
- `__main__` demo blocks from `crp_sigmoid.py` and `hil_gates.py`
  (replaced by `demo.py` and `python -m cgnr curve`).

---

## [v2.0.0] — 2026-09-24

### Engineering audit: math, logic, and hygiene corrections

#### Fixed — Math (verified numerically)
- **Gate 1 sigmoid**: midpoint decoupled from hard-stop threshold. Curve now
  attenuates 0.99→0.01 across [0,50] instead of a flat 0.99→0.50 truncated
  by a cliff. `k` recalibrated (0.18), boundary uses `>=`.
- **Gate 2 "3σ"**: reimplemented as honest one-sided lower bound
  (`μ − 3σ = 70`). A higher CORCONDIA (better fit) no longer triggers
  `RankFailure`.
- **Safeguard CLIP invariant**: Laplace zero-guard now replaces zeros
  in-place then re-clips. `1.000001` violation eliminated.

#### Fixed — Logic
- Gate 1 now invokes `h_hormonal_attenuation` (was dead code; pipeline
  passed `h_hormonal=1.0` and never called the sigmoid).
- Removed dead `h_hormonal` parameter from `gate_1_dynamic_floor`.
- Pipeline returns structured `PipelineResult`/`Incident` instead of
  `(None, "RED")` + `print()`.
- Dimensionality contradiction fixed: S-17/S-18 corrected from n=8 to n=9.
- Boundary comparisons use `>=` on safety thresholds.
- NaN/Inf inputs rejected across all gates and safeguards.

#### Added
- GitHub Actions CI (ruff → mypy → pytest, Python 3.10/3.11/3.12).
- `pyproject.toml` with setuptools backend, dev extras, tool config.
- `pytest` suite: 48 tests, 90% coverage.
- CLI: `python -m cgnr evaluate|gate1|gate2|curve`.
- `REPOSITORY_LOCK.md`: governance document with frozen constants.
- `QUICK_START.md`: standalone quick start with API reference.
- `docs/SPOF_ANALYSIS.md`: formal 32-entry SPOF analysis.
- `docs/GATE_SPECIFICATION.md`: mathematical specification of each gate.
- `docs/MATH_VALIDATION.md`: numerical verification of all math claims.
- `CHANGELOG.md`, `CONTRIBUTING.md`.
- `.gitignore`, `requirements.txt`, `logic/__init__.py`, `demo.py`.

#### Removed
- LibreOffice lock file (`audit/.~lock.spof_matrix_29.csv#`) from git.
- `__main__` demo blocks from logic modules (replaced by `demo.py`).

---

## [v1.0.0] — 2026-01

### Initial ESPEN submission

- CRP sigmoid attenuation model (`crp_sigmoid.py`).
- HIL gate pseudocode (`hil_gates.py`).
- 29-point SPOF audit matrix (`audit/spof_matrix_29.csv`).
