import json
from datetime import datetime, timezone

from app.dashboard import dashboard_snapshot
from app.metrics import percentile


def test_percentile_basic() -> None:
    assert percentile([100, 200, 300, 400], 50) >= 100


def test_dashboard_snapshot_reads_structured_logs(tmp_path) -> None:
    path = tmp_path / "logs.jsonl"
    ts = datetime.now(timezone.utc).isoformat()
    records = [
        {"ts": ts, "event": "request_received"},
        {"ts": ts, "event": "response_sent", "latency_ms": 200, "ttft_ms": 50,
         "cost_usd": 0.01, "tokens_in": 10, "tokens_out": 20,
         "quality_score": 0.9, "tool_success": True},
    ]
    path.write_text("\n".join(json.dumps(record) for record in records), encoding="utf-8")

    snapshot = dashboard_snapshot(path)

    assert snapshot["latency"]["p95"] == 200
    assert snapshot["errors"]["retrieval_success_pct"] == 100
    assert snapshot["tokens"] == {"input": 10, "output": 20}
