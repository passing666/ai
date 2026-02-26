import os
import json
import tempfile

from tools.metrics_exporter import write_metrics_file


def test_write_metrics_file_creates_file_and_content(tmp_path):
    metrics = {"local": 12.0, "remote": 34}
    path = tmp_path / "out" / "metrics.txt"
    write_metrics_file(metrics, str(path))
    assert path.exists()
    txt = path.read_text(encoding="utf-8")
    assert "provider_local_ms" in txt
    assert "provider_remote_ms" in txt
