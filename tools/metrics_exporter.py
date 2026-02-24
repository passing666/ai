"""Simple metrics exporter: write provider_times to a Prometheus text file
and optionally serve it over HTTP (static file server).

Usage examples:
  # write metrics to file
  from tools.metrics_exporter import write_metrics_file
  write_metrics_file({"local": 12.0}, "./metrics.txt")

  # run a simple HTTP server to serve the directory containing metrics file
  python tools/metrics_exporter.py --metrics-file ./metrics.txt --port 8001
"""
from __future__ import annotations

import argparse
import http.server
import os
import socketserver
from typing import Dict

from .metrics import provider_times_to_metrics_lines


def write_metrics_file(provider_times: Dict[str, float], path: str) -> None:
    """Write provider_times in Prometheus text format to `path`."""
    lines = provider_times_to_metrics_lines(provider_times)
    # ensure directory exists
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(lines)


def run_http_server(metrics_file: str, port: int = 8000) -> None:
    """Serve the directory containing `metrics_file` on given port.

    This uses Python's builtin SimpleHTTPRequestHandler.
    """
    directory = os.path.abspath(os.path.dirname(metrics_file))
    os.chdir(directory)
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), Handler) as httpd:
        print(f"Serving metrics at http://127.0.0.1:{port}/{os.path.basename(metrics_file)}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Shutting down metrics server")


def _main():
    parser = argparse.ArgumentParser(description="Serve provider_times as Prometheus metrics")
    parser.add_argument("--metrics-file", required=True, help="Path to metrics file to write/serve")
    parser.add_argument("--provider-times-json", help="Optional JSON file with provider_times to write before serving")
    parser.add_argument("--port", type=int, default=8000, help="Port to serve metrics on")

    args = parser.parse_args()

    if args.provider_times_json:
        import json

        with open(args.provider_times_json, "r", encoding="utf-8") as f:
            provider_times = json.load(f)
        write_metrics_file(provider_times, args.metrics_file)

    run_http_server(args.metrics_file, port=args.port)


if __name__ == "__main__":
    _main()
