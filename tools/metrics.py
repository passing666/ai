"""Small helpers to format provider timing into exportable metrics.

Provides a simple Prometheus-like lines formatter and a JSON-friendly
conversion function for `provider_times` produced by aggregator.
"""

from __future__ import annotations

from typing import Dict, Any


def provider_times_to_metrics_lines(provider_times: Dict[str, float]) -> str:
    """Return newline-separated Prometheus-style metric lines.

    Example output:
        provider_local_provider_ms 12
        provider_other_ms 34
    """
    lines = []
    for name, ms in provider_times.items():
        metric_name = f"provider_{name}_ms"
        # sanitize metric name: replace non-alnum with underscore
        metric_name = "".join(
            c if c.isalnum() or c == "_" else "_" for c in metric_name
        )
        lines.append(f"{metric_name} {float(ms)}")
    return "\n".join(lines)


def provider_times_to_json(provider_times: Dict[str, float]) -> Dict[str, Any]:
    """Return a JSON-friendly mapping for embedding into debug payloads.

    Keeps original values but ensures floats.
    """
    return {k: float(v) for k, v in provider_times.items()}
