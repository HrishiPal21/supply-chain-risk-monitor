"""Unit tests for agents/nodes/judge.py — no network calls."""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
import unittest
from unittest.mock import MagicMock, patch


# Import the private helpers directly — they have no network deps
from agents.nodes.judge import _label, _LABEL_FOR_SCORE, _ACTION_FOR_SCORE


class TestLabelMapping(unittest.TestCase):

    def test_boundaries(self):
        self.assertEqual(_label(0,   _LABEL_FOR_SCORE), "Very Low")
        self.assertEqual(_label(20,  _LABEL_FOR_SCORE), "Very Low")
        self.assertEqual(_label(21,  _LABEL_FOR_SCORE), "Low")
        self.assertEqual(_label(40,  _LABEL_FOR_SCORE), "Low")
        self.assertEqual(_label(41,  _LABEL_FOR_SCORE), "Moderate")
        self.assertEqual(_label(60,  _LABEL_FOR_SCORE), "Moderate")
        self.assertEqual(_label(61,  _LABEL_FOR_SCORE), "High")
        self.assertEqual(_label(80,  _LABEL_FOR_SCORE), "High")
        self.assertEqual(_label(81,  _LABEL_FOR_SCORE), "Critical")
        self.assertEqual(_label(100, _LABEL_FOR_SCORE), "Critical")

    def test_action_boundaries(self):
        self.assertEqual(_label(20,  _ACTION_FOR_SCORE), "Watch")
        self.assertEqual(_label(40,  _ACTION_FOR_SCORE), "Monitor")
        self.assertEqual(_label(60,  _ACTION_FOR_SCORE), "Monitor")
        self.assertEqual(_label(80,  _ACTION_FOR_SCORE), "Escalate")
        self.assertEqual(_label(100, _ACTION_FOR_SCORE), "Immediate Action")

    def test_above_max_returns_last(self):
        self.assertEqual(_label(999, _LABEL_FOR_SCORE), "Critical")


class TestJudgeNode(unittest.TestCase):
    """Test judge() with a mocked OpenAI client — no network."""

    def _make_state(self, multiplier=1.0):
        return {
            "query": "test query",
            "company": None,
            "region": None,
            "retrieved_docs": [],
            "exposure_level": "High",
            "exposure_multiplier": multiplier,
            "exposure_summary": "High exposure",
            "exposure_profile": None,
            "bear_analysis": "Bear output",
            "bull_analysis": "Bull output",
            "geopolitical_analysis": "Geo output",
            "judge_verdict": None,
            "risk_score": None,
            "raw_risk_score": None,
            "guardrail_report": None,
            "final_output": None,
            "partial_context": False,
            "failed_sources": [],
            "source_errors": {},
        }

    def _mock_response(self, payload: dict):
        msg = MagicMock()
        msg.content = json.dumps(payload)
        choice = MagicMock()
        choice.message = msg
        resp = MagicMock()
        resp.choices = [choice]
        return resp

    @patch("agents.nodes.judge.get_openai_client")
    @patch("agents.nodes.judge.chat_with_retry")
    def test_valid_json_scores_stored(self, mock_chat, mock_client):
        mock_chat.return_value = self._mock_response({
            "verdict": "Moderate risk.",
            "risk_score": 60,
            "risk_label": "Moderate",
            "consensus_points": ["point1"],
            "key_disagreements": [],
            "top_3_risks": ["r1"],
            "top_3_mitigants": ["m1"],
            "recommended_action": "Monitor",
        })
        from agents.nodes.judge import judge
        result = judge(self._make_state(multiplier=1.0))

        self.assertEqual(result["raw_risk_score"], 60.0)
        self.assertEqual(result["risk_score"], 60.0)
        fo = result["final_output"]
        self.assertEqual(fo["risk_score_raw"], 60.0)
        self.assertEqual(fo["risk_score_adjusted"], 60.0)
        self.assertEqual(fo["risk_score"], 60.0)

    @patch("agents.nodes.judge.get_openai_client")
    @patch("agents.nodes.judge.chat_with_retry")
    def test_exposure_multiplier_applied(self, mock_chat, mock_client):
        mock_chat.return_value = self._mock_response({
            "verdict": "High risk.",
            "risk_score": 80,
            "risk_label": "High",
            "consensus_points": [],
            "key_disagreements": [],
            "top_3_risks": [],
            "top_3_mitigants": [],
            "recommended_action": "Escalate",
        })
        from agents.nodes.judge import judge
        result = judge(self._make_state(multiplier=0.5))

        self.assertEqual(result["raw_risk_score"], 80.0)
        self.assertEqual(result["risk_score"], 40.0)  # 80 × 0.5
        fo = result["final_output"]
        self.assertEqual(fo["risk_score_raw"], 80.0)
        self.assertEqual(fo["risk_score_adjusted"], 40.0)
        # Label and action recalculated from adjusted score (40 → Low / Monitor)
        self.assertEqual(fo["risk_label"], "Low")
        self.assertEqual(fo["recommended_action"], "Monitor")

    @patch("agents.nodes.judge.get_openai_client")
    @patch("agents.nodes.judge.chat_with_retry")
    def test_malformed_json_uses_fallback(self, mock_chat, mock_client):
        msg = MagicMock()
        msg.content = "this is not json {"
        choice = MagicMock()
        choice.message = msg
        resp = MagicMock()
        resp.choices = [choice]
        mock_chat.return_value = resp

        from agents.nodes.judge import judge
        result = judge(self._make_state())

        # Fallback: risk_score default 50
        self.assertIsNotNone(result["final_output"])
        self.assertEqual(result["raw_risk_score"], 50.0)

    @patch("agents.nodes.judge.get_openai_client")
    @patch("agents.nodes.judge.chat_with_retry")
    def test_raw_score_not_overwritten_in_final_output(self, mock_chat, mock_client):
        """Regression: final_output must preserve risk_score_raw separately."""
        mock_chat.return_value = self._mock_response({
            "verdict": "v", "risk_score": 70, "risk_label": "High",
            "consensus_points": [], "key_disagreements": [],
            "top_3_risks": [], "top_3_mitigants": [],
            "recommended_action": "Escalate",
        })
        from agents.nodes.judge import judge
        result = judge(self._make_state(multiplier=0.25))

        fo = result["final_output"]
        # Raw must be the LLM value, adjusted must be different
        self.assertEqual(fo["risk_score_raw"], 70.0)
        self.assertAlmostEqual(fo["risk_score_adjusted"], 17.5)
        self.assertNotEqual(fo["risk_score_raw"], fo["risk_score_adjusted"])


if __name__ == "__main__":
    unittest.main()
