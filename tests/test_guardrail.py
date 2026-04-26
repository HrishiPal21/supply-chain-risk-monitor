"""Unit tests for agents/nodes/guardrail.py — no network calls."""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
import unittest
from unittest.mock import MagicMock, patch

from agents.nodes.guardrail import (
    _grounding_context,
    _FALLBACK_REPORT,
    _MAX_GROUNDING_DOCS,
    _CHARS_PER_DOC,
)


class TestGroundingContext(unittest.TestCase):

    def test_empty_docs_returns_placeholder(self):
        result = _grounding_context([])
        self.assertIn("no source documents", result)

    def test_basic_doc_appears_in_output(self):
        docs = [{"source": "NewsAPI/Reuters", "text": "Supply chain disruption in Asia."}]
        result = _grounding_context(docs)
        self.assertIn("NewsAPI/Reuters", result)
        self.assertIn("Supply chain disruption", result)

    def test_edgar_docs_appear_first(self):
        docs = [
            {"source": "NewsAPI/Reuters", "text": "News article text."},
            {"source": "EDGAR/AAPL/10-K", "text": "Annual report text."},
        ]
        result = _grounding_context(docs)
        edgar_pos = result.index("EDGAR/AAPL/10-K")
        news_pos = result.index("NewsAPI/Reuters")
        self.assertLess(edgar_pos, news_pos, "EDGAR docs should appear before other sources")

    def test_multiple_edgar_all_prioritised(self):
        docs = [
            {"source": "RSS/FT", "text": "FT article."},
            {"source": "EDGAR/TSMC/10-K", "text": "TSMC filing."},
            {"source": "EDGAR/AAPL/10-K", "text": "Apple filing."},
        ]
        result = _grounding_context(docs)
        rss_pos = result.index("RSS/FT")
        tsmc_pos = result.index("EDGAR/TSMC")
        apple_pos = result.index("EDGAR/AAPL")
        self.assertLess(tsmc_pos, rss_pos)
        self.assertLess(apple_pos, rss_pos)

    def test_respects_max_doc_limit(self):
        docs = [{"source": f"src{i}", "text": f"text {i}"} for i in range(30)]
        result = _grounding_context(docs)
        # Only _MAX_GROUNDING_DOCS entries should appear
        count = result.count("[DOC ")
        self.assertLessEqual(count, _MAX_GROUNDING_DOCS)

    def test_text_truncated_to_chars_per_doc(self):
        long_text = "A" * (_CHARS_PER_DOC * 3)
        docs = [{"source": "web", "text": long_text}]
        result = _grounding_context(docs)
        # The snippet in the output must not exceed _CHARS_PER_DOC chars for that entry
        self.assertLessEqual(len(result.split("\n", 1)[1]), _CHARS_PER_DOC + 10)

    def test_skips_docs_with_empty_text(self):
        docs = [
            {"source": "A", "text": ""},
            {"source": "B", "text": "   "},
            {"source": "C", "text": "real text"},
        ]
        result = _grounding_context(docs)
        self.assertNotIn("[A]", result)
        self.assertIn("real text", result)

    def test_doc_index_labels_present(self):
        docs = [{"source": "s", "text": "content"}]
        result = _grounding_context(docs)
        self.assertIn("[DOC 1 |", result)

    def test_newlines_in_text_replaced(self):
        docs = [{"source": "s", "text": "line1\nline2\nline3"}]
        result = _grounding_context(docs)
        # After the header line, text should have no embedded newlines
        lines = result.split("\n")
        # Find the snippet line (not the header)
        snippet_lines = [l for l in lines if "line1" in l]
        self.assertTrue(len(snippet_lines) == 1, "Text should be collapsed to one line")
        self.assertIn("line2", snippet_lines[0])


class TestGuardrailNode(unittest.TestCase):
    """Test guardrail() with a mocked OpenAI client — no network."""

    def _make_state(self):
        return {
            "query": "test",
            "retrieved_docs": [{"source": "NewsAPI", "text": "Some news."}],
            "bear_analysis": "Bear says bad.",
            "bull_analysis": "Bull says good.",
            "geopolitical_analysis": "Geo says mixed.",
            "judge_verdict": "Moderate risk.",
            "guardrail_report": None,
        }

    def _mock_response(self, payload: dict):
        msg = MagicMock()
        msg.content = json.dumps(payload)
        choice = MagicMock()
        choice.message = msg
        resp = MagicMock()
        resp.choices = [choice]
        return resp

    def _valid_payload(self):
        return {
            "trust_scores": {"bear": 0.8, "bull": 0.7, "geopolitical": 0.6, "judge": 0.75},
            "flagged_claims": [],
            "confidence_band": {"low": 45, "high": 70},
            "overall_confidence": "Medium",
            "guardrail_notes": "Claims are mostly grounded.",
        }

    @patch("agents.nodes.guardrail.get_openai_client")
    @patch("agents.nodes.guardrail.chat_with_retry")
    def test_valid_json_stored_in_state(self, mock_chat, mock_client):
        mock_chat.return_value = self._mock_response(self._valid_payload())
        from agents.nodes.guardrail import guardrail
        result = guardrail(self._make_state())

        report = result["guardrail_report"]
        self.assertIsNotNone(report)
        self.assertAlmostEqual(report["trust_scores"]["bear"], 0.8)
        self.assertEqual(report["overall_confidence"], "Medium")
        self.assertEqual(report["flagged_claims"], [])

    @patch("agents.nodes.guardrail.get_openai_client")
    @patch("agents.nodes.guardrail.chat_with_retry")
    def test_malformed_json_uses_fallback(self, mock_chat, mock_client):
        msg = MagicMock()
        msg.content = "not json {"
        choice = MagicMock()
        choice.message = msg
        resp = MagicMock()
        resp.choices = [choice]
        mock_chat.return_value = resp

        from agents.nodes.guardrail import guardrail
        result = guardrail(self._make_state())

        report = result["guardrail_report"]
        self.assertEqual(report["overall_confidence"], _FALLBACK_REPORT["overall_confidence"])
        self.assertIn("JSON parse error", report["guardrail_notes"])

    @patch("agents.nodes.guardrail.get_openai_client")
    @patch("agents.nodes.guardrail.chat_with_retry")
    def test_flagged_claims_preserved(self, mock_chat, mock_client):
        payload = self._valid_payload()
        payload["flagged_claims"] = [
            {
                "agent": "bear",
                "claim": "inventory crashed 40%",
                "issue": "UNSUPPORTED",
                "detail": "no source document mentions inventory levels",
            }
        ]
        mock_chat.return_value = self._mock_response(payload)
        from agents.nodes.guardrail import guardrail
        result = guardrail(self._make_state())

        claims = result["guardrail_report"]["flagged_claims"]
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0]["issue"], "UNSUPPORTED")
        self.assertIn("detail", claims[0])

    @patch("agents.nodes.guardrail.get_openai_client")
    @patch("agents.nodes.guardrail.chat_with_retry")
    def test_state_keys_preserved(self, mock_chat, mock_client):
        mock_chat.return_value = self._mock_response(self._valid_payload())
        from agents.nodes.guardrail import guardrail
        state = self._make_state()
        result = guardrail(state)

        # Original state keys must still be present
        self.assertEqual(result["query"], state["query"])
        self.assertEqual(result["bear_analysis"], state["bear_analysis"])


if __name__ == "__main__":
    unittest.main()
