"""Providers package for data source adapters.

Each provider should implement a `search(q: str, limit: int)` function that
returns a list of dict-like Docs with keys like `id`, `title`, `text`, `score`, `source_url`, `metadata`.
"""

from typing import Dict, Callable, List, Any

try:
    from .sources import local_providers
    from .sources import wiki_providers
    from .sources import arVix_providers
    from .algo.Translation import translate_to_english
except ImportError:
    from sources import local_providers
    from sources import wiki_providers
    from sources import arVix_providers
    from algo.Translation import translate_to_english

AVAILABLE_PROVIDERS: Dict[str, Callable[[str, int], List[Dict[str, Any]]]] = {
    "local": local_providers.search,
    "web_wiki": wiki_providers.search,
    "web_arVix": arVix_providers.search,
}

# Enabled providers (order matters for deterministic results)
ENABLED_PROVIDER_NAMES = ["local", "web_wiki", "web_arVix"]


def get_enabled_providers() -> Dict[str, Callable[[str, int], List[Dict[str, Any]]]]:
    enabled_providers: Dict[str, Callable[[str, int], List[Dict[str, Any]]]] = {}
    for name in ENABLED_PROVIDER_NAMES:
        if name in AVAILABLE_PROVIDERS:
            enabled_providers[name] = AVAILABLE_PROVIDERS[name]
    return enabled_providers


def unified_search(q: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Run enabled providers' `search` and return merged, scored results.

    The query is translated to English (via `translate_to_english`) to make
    provider queries more consistent. Results are sorted by `score` descending
    and truncated to `limit`.
    """
    all_results: List[Dict[str, Any]] = []
    providers = get_enabled_providers()

    q_en = translate_to_english(q)
    for name, search_func in providers.items():
        try:
            results = search_func(q_en, limit)
            if results and isinstance(results, list):
                all_results.extend(results)
        except Exception as e:
            # Keep going if a provider fails; do not raise here.
            print(f"Provider '{name}' failed: {e}")

    if not all_results:
        return []

    all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return all_results[:limit]


__all__ = [
    "AVAILABLE_PROVIDERS",
    "ENABLED_PROVIDER_NAMES",
    "get_enabled_providers",
    "unified_search",
]
