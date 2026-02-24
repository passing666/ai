"""Providers package for data source adapters.

Each provider should implement a `search(q: str, limit: int)` function that
returns a list of dict-like Docs with keys like `id`, `title`, `text`, `score`, `source_url`, `metadata`.
"""

__all__ = [
    "local_provider",
]
