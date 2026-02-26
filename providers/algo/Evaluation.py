import math
import re
from collections import Counter

STOP_WORDS = {"what", "is", "are", "the", "a", "an", "of", "in", "for", "to", "and"}


def tokenize(text: str):
    tokens = re.findall(r"\w+", text.lower())
    return [t for t in tokens if t not in STOP_WORDS]


def calculate_normalized_scores(query: str, texts: list[str]) -> list[float]:
    if not texts or not query:
        return [0.0] * len(texts)

    query_tokens = tokenize(query)
    query_vec = Counter(query_tokens)

    results = []
    for text in texts:
        doc_tokens = tokenize(text)
        doc_vec = Counter(doc_tokens)

        common_terms = set(query_vec.keys()) & set(doc_vec.keys())
        dot_product = sum(query_vec[t] * doc_vec[t] for t in common_terms)

        mag_query = math.sqrt(sum(v**2 for v in query_vec.values()))
        mag_doc = math.sqrt(sum(v**2 for v in doc_vec.values()))

        similarity = (
            dot_product / (mag_query * mag_doc) if (mag_query * mag_doc) > 0 else 0
        )
        results.append(round(similarity, 2))

    return results
