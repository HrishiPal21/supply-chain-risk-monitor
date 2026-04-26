"""Unit tests for tools/pinecone_client.py — no network calls."""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import unittest
from unittest.mock import MagicMock, patch


class TestUpsertDocsDedupe(unittest.TestCase):
    """Test dedup, empty-text filtering, and batching in upsert_docs()."""

    def _make_docs(self, texts: list[str]) -> list[dict]:
        return [{"id": f"doc-{i}", "source": "test", "text": t} for i, t in enumerate(texts)]

    @patch("tools.pinecone_client._get_index")
    @patch("tools.pinecone_client.embed_batch_with_retry")
    @patch("tools.pinecone_client.get_openai_client")
    def test_duplicate_texts_upserted_once(self, mock_client, mock_embed, mock_index):
        mock_embed.return_value = [[0.1] * 3]
        index = MagicMock()
        mock_index.return_value = index

        from tools.pinecone_client import upsert_docs
        docs = self._make_docs(["same text", "same text", "same text"])
        upsert_docs(docs)

        # embed_batch_with_retry called with only 1 unique text
        call_args = mock_embed.call_args
        self.assertEqual(len(call_args.kwargs["inputs"]), 1)
        # upsert called with 1 vector
        index.upsert.assert_called_once()
        vectors = index.upsert.call_args.kwargs["vectors"]
        self.assertEqual(len(vectors), 1)

    @patch("tools.pinecone_client._get_index")
    @patch("tools.pinecone_client.embed_batch_with_retry")
    @patch("tools.pinecone_client.get_openai_client")
    def test_empty_text_skipped(self, mock_client, mock_embed, mock_index):
        mock_embed.return_value = [[0.1] * 3]
        index = MagicMock()
        mock_index.return_value = index

        from tools.pinecone_client import upsert_docs
        docs = [
            {"id": "a", "source": "s", "text": ""},
            {"id": "b", "source": "s", "text": "   "},
            {"id": "c", "source": "s", "text": "real content"},
        ]
        upsert_docs(docs)

        inputs = mock_embed.call_args.kwargs["inputs"]
        self.assertEqual(inputs, ["real content"])

    @patch("tools.pinecone_client._get_index")
    @patch("tools.pinecone_client.embed_batch_with_retry")
    @patch("tools.pinecone_client.get_openai_client")
    def test_empty_doc_list_returns_early(self, mock_client, mock_embed, mock_index):
        from tools.pinecone_client import upsert_docs
        upsert_docs([])
        mock_embed.assert_not_called()
        mock_index.assert_not_called()

    @patch("tools.pinecone_client._get_index")
    @patch("tools.pinecone_client.embed_batch_with_retry")
    @patch("tools.pinecone_client.get_openai_client")
    def test_all_empty_texts_returns_early(self, mock_client, mock_embed, mock_index):
        from tools.pinecone_client import upsert_docs
        upsert_docs([{"id": "x", "source": "s", "text": ""}])
        mock_embed.assert_not_called()

    @patch("tools.pinecone_client._get_index")
    @patch("tools.pinecone_client.embed_batch_with_retry")
    @patch("tools.pinecone_client.get_openai_client")
    def test_unique_texts_all_upserted(self, mock_client, mock_embed, mock_index):
        n = 5
        mock_embed.return_value = [[float(i)] * 3 for i in range(n)]
        index = MagicMock()
        mock_index.return_value = index

        from tools.pinecone_client import upsert_docs
        docs = self._make_docs([f"unique text {i}" for i in range(n)])
        upsert_docs(docs)

        inputs = mock_embed.call_args.kwargs["inputs"]
        self.assertEqual(len(inputs), n)
        vectors = index.upsert.call_args.kwargs["vectors"]
        self.assertEqual(len(vectors), n)

    @patch("tools.pinecone_client._get_index")
    @patch("tools.pinecone_client.embed_batch_with_retry")
    @patch("tools.pinecone_client.get_openai_client")
    def test_metadata_text_truncated_to_500(self, mock_client, mock_embed, mock_index):
        mock_embed.return_value = [[0.0] * 3]
        index = MagicMock()
        mock_index.return_value = index

        from tools.pinecone_client import upsert_docs
        long_text = "X" * 2000
        upsert_docs([{"id": "long", "source": "s", "text": long_text}])

        vectors = index.upsert.call_args.kwargs["vectors"]
        self.assertEqual(len(vectors[0]["metadata"]["text"]), 500)

    @patch("tools.pinecone_client._get_index")
    @patch("tools.pinecone_client.embed_batch_with_retry")
    @patch("tools.pinecone_client.get_openai_client")
    def test_source_preserved_in_metadata(self, mock_client, mock_embed, mock_index):
        mock_embed.return_value = [[0.1] * 3]
        index = MagicMock()
        mock_index.return_value = index

        from tools.pinecone_client import upsert_docs
        upsert_docs([{"id": "d1", "source": "EDGAR/AAPL/10-K", "text": "filing text"}])

        vectors = index.upsert.call_args.kwargs["vectors"]
        self.assertEqual(vectors[0]["metadata"]["source"], "EDGAR/AAPL/10-K")

    @patch("tools.pinecone_client._get_index")
    @patch("tools.pinecone_client.embed_batch_with_retry")
    @patch("tools.pinecone_client.get_openai_client")
    def test_large_batch_calls_embed_multiple_times(self, mock_client, mock_embed, mock_index):
        """With _EMBED_BATCH=100, 150 unique docs should trigger 2 embed calls."""
        from tools.pinecone_client import _EMBED_BATCH
        n = _EMBED_BATCH + 50
        mock_embed.side_effect = lambda *a, **kw: [[0.1] * 3 for _ in kw["inputs"]]
        index = MagicMock()
        mock_index.return_value = index

        from tools.pinecone_client import upsert_docs
        docs = self._make_docs([f"doc text {i}" for i in range(n)])
        upsert_docs(docs)

        self.assertEqual(mock_embed.call_count, 2)


if __name__ == "__main__":
    unittest.main()
