from typing import Dict, Callable, List, Any
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

ENABLED_PROVIDER_NAMES = ["local","web_wiki","web_arVix"]
#ENABLED_PROVIDER_NAMES = ["web_wiki"]
#ENABLED_PROVIDER_NAMES = ["local"]
#ENABLED_PROVIDER_NAMES = ["web_arVix"]

def get_enabled_providers() -> Dict[str, Callable[[str, int], List[Dict[str, Any]]]]:
    enabled_providers = {}
    for name in ENABLED_PROVIDER_NAMES:
        if name in AVAILABLE_PROVIDERS:
            enabled_providers[name] = AVAILABLE_PROVIDERS[name]
    return enabled_providers

def unified_search(q: str, limit: int = 10) -> List[Dict[str, Any]]:
    all_results = []
    providers = get_enabled_providers()

    q = translate_to_english(q)
    print(q);

    for name, search_func in providers.items():
        try:
            results = search_func(q, limit)
            if results and isinstance(results, list):
                all_results.extend(results)
        except Exception as e:
            print(f"Provider '{name}' failed: {e}")

    if not all_results:
        return []

    all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    return all_results[:limit]
