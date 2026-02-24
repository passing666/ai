"""Simple offline reranker used by backend for improved document ordering.

This implementation uses a small IDF-weighted overlap: it scores documents
by summing term-frequency in the document for terms that appear in the
question, weighted by IDF computed across the candidate set.
"""
from __future__ import annotations

import math
import re
from typing import List, Dict


def _tokenize(text: str) -> List[str]:
    if not text:
        return []
    return [t for t in re.findall(r"\w+", text.lower())]


def rerank(question: str, docs: List[Dict], top_k: int = 4) -> List[Dict]:
    """Return docs re-ordered by a lightweight relevance score.

    Args:
        question: user question string
        docs: list of doc dicts with at least a `text` (or `title`) field
        top_k: number of top docs to return (preserves other metadata)

    Returns:
        list of docs sorted by descending score (length <= top_k)
    """
    q_tokens = set(_tokenize(question))
    if not docs:
        return []

    # build document term frequencies and document frequencies
    N = len(docs)
    dfs = {}
    doc_tfs = []
    for d in docs:
        text = (d.get("text") or "") + " " + (d.get("title") or "")
        tokens = _tokenize(text)
        tf = {}
        seen = set()
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
            if t not in seen:
                dfs[t] = dfs.get(t, 0) + 1
                seen.add(t)
        doc_tfs.append(tf)

    # idf smoothing
    idf = {t: math.log((1 + N) / (1 + df)) + 1.0 for t, df in dfs.items()}

    scores = []
    for tf, d in zip(doc_tfs, docs):
        score = 0.0
        for t in q_tokens:
            if t in tf:
                score += tf[t] * idf.get(t, 1.0)
        scores.append(score)

    ranked = sorted(zip(scores, docs), key=lambda x: x[0], reverse=True)
    selected = [d for s, d in ranked][:top_k]
    return selected
