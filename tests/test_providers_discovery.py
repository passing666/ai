import importlib
from tools import aggregator_tool


def test_providers_discovered_and_callable():
    # This test ensures aggregator discovers providers in providers/ and calls them
    import asyncio

    docs, provider_times = asyncio.run(aggregator_tool.search('测试', limit=3))
    # Expect at least local_provider to be present
    assert 'local_provider' in provider_times
    # web_wiki may be discovered depending on import timing; if present, ensure it's callable
    if 'web_wiki' in provider_times:
        assert isinstance(provider_times['web_wiki'], int)
    # docs should be a list
    assert isinstance(docs, list)
