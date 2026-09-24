"""
Tests for the CGNR Matrix CLI.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cgnr.__main__ import main


def _scores(val: float = 0.5) -> list[str]:
    return [str(val)] * 9


def _compliance(val: int = 1) -> list[str]:
    return [str(val)] * 9


class TestCLI:
    def test_evaluate_green(self, capsys):
        rc = main(
            [
                "evaluate",
                "--crp",
                "12",
                "--corcondia",
                "88.5",
                "--scores",
                "0.85",
                "0.90",
                "0.45",
                "0.70",
                "0.82",
                "0.61",
                "0.95",
                "0.52",
                "0.77",
                "--compliance",
                "1",
                "1",
                "1",
                "1",
                "1",
                "1",
                "0",
                "1",
                "1",
            ]
        )
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert out["flag"] == "GREEN"
        assert out["h_hormonal"] is not None
        assert len(out["scores"]) == 9

    def test_evaluate_red_sepsis(self, capsys):
        rc = main(
            [
                "evaluate",
                "--crp",
                "55",
                "--corcondia",
                "88.5",
                "--scores",
                *_scores(),
                "--compliance",
                *_compliance(),
            ]
        )
        assert rc == 1
        out = json.loads(capsys.readouterr().out)
        assert out["flag"] == "RED"
        assert out["incident"]["gate_id"] == "GATE_1"

    def test_evaluate_red_rank(self, capsys):
        rc = main(
            [
                "evaluate",
                "--crp",
                "12",
                "--corcondia",
                "10",
                "--scores",
                *_scores(),
                "--compliance",
                *_compliance(),
            ]
        )
        assert rc == 1
        out = json.loads(capsys.readouterr().out)
        assert out["flag"] == "RED"
        assert out["incident"]["gate_id"] == "GATE_2"

    def test_evaluate_wrong_score_count(self, capsys):
        rc = main(
            [
                "evaluate",
                "--crp",
                "12",
                "--corcondia",
                "88.5",
                "--scores",
                "0.5",
                "0.5",
                "0.5",
                "--compliance",
                *_compliance(),
            ]
        )
        assert rc == 2

    def test_gate1_pass(self, capsys):
        rc = main(["gate1", "--crp", "30"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "PASS" in out

    def test_gate1_blocked(self, capsys):
        rc = main(["gate1", "--crp", "55"])
        assert rc == 1
        out = capsys.readouterr().out
        assert "BLOCKED" in out

    def test_gate2_pass(self, capsys):
        rc = main(["gate2", "--corcondia", "88"])
        assert rc == 0

    def test_gate2_blocked(self, capsys):
        rc = main(["gate2", "--corcondia", "10"])
        assert rc == 1

    def test_curve(self, capsys):
        rc = main(["curve"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "CRP=" in out
        assert "HARD_STOP" in out
