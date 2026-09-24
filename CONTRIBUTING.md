# Contributing to CGNR Matrix CDSS

Thank you for your interest in contributing. This is a **safety-critical**
clinical decision support system — contributions are held to a higher
standard than typical open-source projects.

## ⚠️ Read this first

This repository is **logic-locked** (see [`REPOSITORY_LOCK.md`](REPOSITORY_LOCK.md)).
Changes to safety-critical constants, gate logic, or safeguard ordering
require a formal amendment. If your change touches any of these, open an
issue for discussion **before** writing code.

## Development setup

```bash
git clone https://github.com/HyyperNab/CGNR-Matrix-CDSS.git
cd CGNR-Matrix-CDSS
pip install -e ".[dev]"
```

## Pre-commit checklist

Before submitting a PR, all of these must pass:

```bash
ruff check logic/ tests/ demo.py cgnr/    # lint
ruff format --check logic/ tests/ demo.py cgnr/  # format
mypy logic/ --ignore-missing-imports      # type-check
pytest --cov=logic --cov-fail-under=90    # tests + coverage
```

CI runs the same checks on Python 3.10, 3.11, and 3.12.

## What you can contribute

### Allowed without amendment
- **Bug fixes** that don't change gate behavior (e.g., better error messages)
- **New tests** (more coverage is always welcome)
- **Documentation** improvements
- **Dependency updates** (within semver)
- **Performance** optimizations that produce identical output

### Requires amendment (see REPOSITORY_LOCK.md)
- Changing any locked constant (CRP threshold, k, μ, σ, n, tier3, ε)
- Modifying gate logic or ordering
- Reordering safeguard steps
- Changing the public API

### Forbidden
- Removing NaN/Inf guards
- Adding fallback logic to any gate
- Making Hard Stops non-blocking
- Removing the re-clip after Laplace

## Pull request process

1. **Open an issue** describing the change (especially for safety-critical changes)
2. **Branch** from `main`: `git checkout -b your-name/description`
3. **Write tests** for your change
4. **Run the full checklist** above
5. **Update `CHANGELOG.md`** under `[Unreleased]`
6. **Reference the issue** in your PR description

## Code style

- **Python ≥3.10** — use `match/case`, `|` union types, `from __future__ import annotations`
- **Type annotations** on all public functions
- **Docstrings** in NumPy style
- **Line length** 88 chars (enforced by ruff)
- **Imports** sorted by ruff (isort-compatible)

## Test guidelines

- Every public function needs at least one test
- Edge cases (NaN, Inf, boundary values, dimension mismatch) must be tested
- Math claims need numerical verification (see `docs/MATH_VALIDATION.md`)
- Coverage must stay ≥90%
