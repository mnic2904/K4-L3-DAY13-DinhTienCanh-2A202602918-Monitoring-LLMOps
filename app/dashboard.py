from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from .metrics import percentile

router = APIRouter()


def dashboard_snapshot(path: Path | None = None, minutes: int = 60) -> dict:
    if path is None:
        from .logging_config import LOG_PATH

        path = LOG_PATH
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=minutes)
    records = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                record = json.loads(line)
                timestamp = datetime.fromisoformat(record["ts"].replace("Z", "+00:00"))
                if timestamp >= cutoff:
                    record["_dashboard_ts"] = timestamp
                    records.append(record)
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

    requests = [record for record in records if record.get("event") == "request_received"]
    responses = [record for record in records if record.get("event") == "response_sent"]
    errors = [record for record in records if record.get("event") == "request_failed"]
    tools = [record for record in records if record.get("tool_success") is not None]
    latencies = [record["latency_ms"] for record in responses if "latency_ms" in record]
    ttfts = [record["ttft_ms"] for record in responses if "ttft_ms" in record]

    return {
        "time_range_minutes": minutes,
        "updated_at": now.isoformat(),
        "latency": {
            "p50": percentile(latencies, 50),
            "p95": percentile(latencies, 95),
            "p99": percentile(latencies, 99),
            "ttft_p95": percentile(ttfts, 95),
        },
        "traffic": {
            "requests": len(requests),
            "per_minute": sum(record["_dashboard_ts"] >= now - timedelta(minutes=1) for record in requests),
        },
        "errors": {
            "error_rate_pct": round(len(errors) / len(requests) * 100, 2) if requests else 0,
            "retrieval_success_pct": round(
                sum(record.get("tool_success") is True for record in tools) / len(tools) * 100, 2
            ) if tools else 0,
        },
        "cost": {"total_usd": round(sum(record.get("cost_usd", 0) for record in responses), 4)},
        "tokens": {
            "input": sum(record.get("tokens_in", 0) for record in responses),
            "output": sum(record.get("tokens_out", 0) for record in responses),
        },
        "quality": {
            "average": round(mean(record.get("quality_score", 0) for record in responses), 3)
            if responses else 0
        },
    }


@router.get("/dashboard/data")
async def dashboard_data() -> dict:
    return dashboard_snapshot()


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard() -> str:
    return """<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>K4-L3A Monitoring Dashboard</title><style>
body{margin:0;background:#09111f;color:#e8eef8;font:15px system-ui;padding:28px}header{display:flex;justify-content:space-between;align-items:end;margin-bottom:22px}h1{margin:0;font-size:25px}.meta{color:#8fa3bf}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.card{background:#111d30;border:1px solid #243650;border-radius:12px;padding:18px}.card h2{font-size:15px;color:#9fb5d1;margin:0 0 15px}.value{font-size:27px;font-weight:700}.row{display:flex;justify-content:space-between;margin-top:10px}.ok{color:#42d392}.bad{color:#ff6b6b}.threshold{border-top:1px solid #293b55;margin-top:15px;padding-top:10px;color:#91a6c1;font-size:13px}@media(max-width:850px){.grid{grid-template-columns:1fr}}
</style></head><body><header><div><h1>K4-L3A · Monitoring & LLMOps</h1><div class="meta">Source: data/logs.jsonl · Auto-refresh: 30s</div></div><div class="meta" id="updated"></div></header><main class="grid" id="grid"></main>
<script>
const card=(title,body,threshold)=>`<section class="card"><h2>${title}</h2>${body}<div class="threshold">Threshold: ${threshold}</div></section>`;
async function refresh(){const d=await fetch('/dashboard/data').then(r=>r.json()); document.querySelector('#updated').textContent=`Last ${d.time_range_minutes} min · ${new Date(d.updated_at).toLocaleTimeString()}`;
const status=(good)=>good?'ok':'bad'; document.querySelector('#grid').innerHTML=
card('Latency percentiles & TTFT',`<div class="value ${status(d.latency.p95<=3000)}">P95 ${d.latency.p95} ms</div><div class="row"><span>P50 ${d.latency.p50} ms</span><span>P99 ${d.latency.p99} ms</span></div><div class="row"><span>TTFT P95</span><span>${d.latency.ttft_p95} ms</span></div>`,'P95 ≤ 3000 ms')+
card('Request traffic',`<div class="value">${d.traffic.requests} requests</div><div class="row"><span>Average rate</span><span>${d.traffic.per_minute} req/min</span></div>`,'rate ≥ 1 req/min')+
card('Errors & retrieval',`<div class="value ${status(d.errors.error_rate_pct<=2)}">${d.errors.error_rate_pct}% errors</div><div class="row"><span>Retrieval success</span><span class="${status(d.errors.retrieval_success_pct>=90)}">${d.errors.retrieval_success_pct}%</span></div>`,'errors ≤ 2%; retrieval ≥ 90%')+
card('Cost over time',`<div class="value ${status(d.cost.total_usd<=2.5)}">$${d.cost.total_usd}</div><div class="row"><span>Total in selected range</span><span>USD</span></div>`,'total ≤ $2.50')+
card('Input & output tokens',`<div class="value">${d.tokens.input+d.tokens.output}</div><div class="row"><span>Input ${d.tokens.input}</span><span>Output ${d.tokens.output}</span></div>`,'total ≤ 50,000 tokens')+
card('Quality proxy',`<div class="value ${status(d.quality.average>=.75)}">${d.quality.average}</div><div class="row"><span>Mean score</span><span>0–1</span></div>`,'mean ≥ 0.75');}
refresh(); setInterval(refresh,30000);
</script></body></html>"""
