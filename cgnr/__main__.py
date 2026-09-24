"""
CGNR Matrix CDSS — Command-line interface.

Usage::

    python -m cgnr evaluate --crp 12 --corcondia 88.5 \
        --scores 0.85 0.90 0.45 0.70 0.82 0.61 0.95 0.52 0.77 \
        --compliance 1 1 1 1 1 1 0 1 1
    python -m cgnr gate1 --crp 30
    python -m cgnr gate2 --corcondia 72
    python -m cgnr curve
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections.abc import Sequence

from logic import (
    N_INTERVENTIONS,
    gate_1_dynamic_floor,
    gate_2_residual_norm,
    h_hormonal_attenuation,
    run_cgnr_pipeline,
)

logger = logging.getLogger("cgnr")


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _parse_floats(values: Sequence[str]) -> list[float]:
    return [float(v) for v in values]


def cmd_evaluate(args: argparse.Namespace) -> int:
    """Run the full pipeline and print a JSON result."""
    _setup_logging(args.verbose)

    scores = _parse_floats(args.scores)
    compliance = _parse_floats(args.compliance)

    if len(scores) != N_INTERVENTIONS:
        logger.error("expected %d scores, got %d", N_INTERVENTIONS, len(scores))
        return 2
    if len(compliance) != N_INTERVENTIONS:
        logger.error(
            "expected %d compliance values, got %d", N_INTERVENTIONS, len(compliance)
        )
        return 2

    logger.info(
        "CRP=%.1f  CORCONDIA=%.1f  n=%d",
        args.crp,
        args.corcondia,
        N_INTERVENTIONS,
    )
    result = run_cgnr_pipeline(
        patient_crp=args.crp,
        corcondia=args.corcondia,
        compliance_f=compliance,
        raw_scores=scores,
    )

    if result.ok and result.scores is not None:
        output = {
            "flag": result.flag,
            "h_hormonal": round(result.h_hormonal, 6),
            "scores": [round(float(s), 6) for s in result.scores],
            "incident": None,
        }
        logger.info("Pipeline: GREEN")
    else:
        output = {
            "flag": result.flag,
            "h_hormonal": None,
            "scores": None,
            "incident": {
                "gate_id": result.incident.gate_id if result.incident else "UNKNOWN",
                "reason": result.incident.reason if result.incident else "Unknown",
            },
        }
        logger.warning("Pipeline: RED (%s)", output["incident"]["gate_id"])

    print(json.dumps(output, indent=2))
    return 0 if result.ok else 1


def cmd_gate1(args: argparse.Namespace) -> int:
    """Evaluate Gate 1 only."""
    _setup_logging(args.verbose)
    try:
        h = gate_1_dynamic_floor(args.crp)
        print(f"PASS  h_hormonal={h:.6f}")
        return 0
    except Exception as exc:
        print(f"BLOCKED  {exc}")
        return 1


def cmd_gate2(args: argparse.Namespace) -> int:
    """Evaluate Gate 2 only."""
    _setup_logging(args.verbose)
    try:
        gate_2_residual_norm(args.corcondia)
        print(f"PASS  CORCONDIA={args.corcondia} >= floor (mu-3sigma=70)")
        return 0
    except Exception as exc:
        print(f"BLOCKED  {exc}")
        return 1


def cmd_curve(args: argparse.Namespace) -> int:
    """Print the Gate 1 attenuation table."""
    _setup_logging(args.verbose)
    print("threshold=50.0  midpoint=25.0  k=0.18")
    for crp in [0, 10, 20, 25, 30, 40, 45, 50, 55, 80]:
        h, status = h_hormonal_attenuation(crp)
        print(f"CRP={crp:3d} mg/dL  ->  h={h:.4f}  [{status}]")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cgnr",
        description="CGNR Matrix CDSS — Clinical Decision Support System",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="enable debug logging"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # evaluate
    p_eval = sub.add_parser("evaluate", help="run the full pipeline")
    p_eval.add_argument("--crp", type=float, required=True, help="serum CRP in mg/dL")
    p_eval.add_argument(
        "--corcondia", type=float, required=True, help="CORCONDIA core consistency (%%)"
    )
    p_eval.add_argument(
        "--scores", nargs="+", required=True, help=f"{N_INTERVENTIONS} evidence scores"
    )
    p_eval.add_argument(
        "--compliance",
        nargs="+",
        required=True,
        help=f"{N_INTERVENTIONS} compliance values [0-1]",
    )
    p_eval.set_defaults(func=cmd_evaluate)

    # gate1
    p_g1 = sub.add_parser("gate1", help="evaluate Gate 1 only")
    p_g1.add_argument("--crp", type=float, required=True)
    p_g1.set_defaults(func=cmd_gate1)

    # gate2
    p_g2 = sub.add_parser("gate2", help="evaluate Gate 2 only")
    p_g2.add_argument("--corcondia", type=float, required=True)
    p_g2.set_defaults(func=cmd_gate2)

    # curve
    p_curve = sub.add_parser("curve", help="print the Gate 1 attenuation table")
    p_curve.set_defaults(func=cmd_curve)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
