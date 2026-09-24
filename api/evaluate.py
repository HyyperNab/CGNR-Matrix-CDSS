"""Vercel serverless function: CGNR Matrix pipeline evaluation."""

from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler

# Make logic importable in Vercel serverless environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic import N_INTERVENTIONS, run_cgnr_pipeline


def _cors_headers() -> dict[str, str]:
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }


def _json_response(handler: BaseHTTPRequestHandler, status: int, body: dict) -> None:
    payload = json.dumps(body, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(payload)))
    for k, v in _cors_headers().items():
        handler.send_header(k, v)
    handler.end_headers()
    handler.wfile.write(payload)


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:
        self.send_response(204)
        for k, v in _cors_headers().items():
            self.send_header(k, v)
        self.end_headers()

    def do_POST(self) -> None:
        content_length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(content_length) if content_length else b"{}"

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            _json_response(self, 400, {"error": "Invalid JSON body"})
            return

        # Parse inputs
        crp = float(data.get("crp", 0))
        corcondia = float(data.get("corcondia", 0))
        scores = data.get("scores", [])
        compliance = data.get("compliance", [])

        # Validate
        if not isinstance(scores, list) or not isinstance(compliance, list):
            _json_response(
                self,
                400,
                {
                    "error": "scores and compliance must be arrays",
                },
            )
            return

        if len(scores) != N_INTERVENTIONS or len(compliance) != N_INTERVENTIONS:
            _json_response(
                self,
                400,
                {
                    "error": f"expected {N_INTERVENTIONS} scores and {N_INTERVENTIONS}"
                    f" compliance values",
                },
            )
            return

        try:
            scores = [float(s) for s in scores]
            compliance = [float(c) for c in compliance]
        except (TypeError, ValueError):
            _json_response(
                self,
                400,
                {
                    "error": "scores and compliance must be numeric",
                },
            )
            return

        result = run_cgnr_pipeline(
            patient_crp=crp,
            corcondia=corcondia,
            compliance_f=compliance,
            raw_scores=scores,
        )

        if result.ok and result.scores is not None:
            _json_response(
                self,
                200,
                {
                    "flag": result.flag,
                    "h_hormonal": round(result.h_hormonal, 6),
                    "scores": [round(float(s), 6) for s in result.scores],
                    "incident": None,
                },
            )
        else:
            incident = result.incident
            _json_response(
                self,
                200,
                {
                    "flag": result.flag,
                    "h_hormonal": None,
                    "scores": None,
                    "incident": {
                        "gate_id": incident.gate_id if incident else "UNKNOWN",
                        "reason": incident.reason if incident else "Unknown",
                    },
                },
            )

    def do_GET(self) -> None:
        _json_response(
            self,
            200,
            {
                "endpoint": "CGNR Matrix CDSS Pipeline",
                "method": "POST",
                "params": {
                    "crp": "float (mg/dL)",
                    "corcondia": "float (%)",
                    "scores": f"array of {N_INTERVENTIONS} floats",
                    "compliance": f"array of {N_INTERVENTIONS} floats [0-1]",
                },
                "n_interventions": N_INTERVENTIONS,
            },
        )

    def log_message(self, *args) -> None:
        pass  # suppress serverless logging
