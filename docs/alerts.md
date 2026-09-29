# Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## High request latency

- Tên: High request latency
- Severity: warning
- Duration: 5m
- Kênh thông báo: Slack `#llmops-alerts`
- SLI/SLO liên quan: P95 latency và SLO request thành công trong 3000 ms.
- Điều kiện và thời gian duy trì: `latency_p95_ms > 3000` liên tục 5 phút.
- Ảnh hưởng tới người dùng: Phản hồi chậm, có nguy cơ timeout.
- Ba bước kiểm tra đầu tiên: Xác định time range trên dashboard; lấy correlation ID chậm trong log; mở trace và so sánh retrieval với generation.
- Mitigation tạm thời: Giảm concurrency hoặc bỏ qua retrieval khi upstream chậm.
- Owner: llm-platform

## High request error rate

- Tên: High request error rate
- Severity: critical
- Duration: 5m
- Kênh thông báo: Slack `#llmops-alerts`
- SLI/SLO liên quan: Error rate guardrail tối đa 2%.
- Điều kiện và thời gian duy trì: `error_rate_pct > 2` liên tục 5 phút.
- Ảnh hưởng tới người dùng: Request thất bại hoặc không có câu trả lời.
- Ba bước kiểm tra đầu tiên: Xem error breakdown; lọc `request_failed` và correlation ID; mở trace để tìm observation lỗi.
- Mitigation tạm thời: Bật fallback và cô lập dependency lỗi.
- Owner: llm-platform

## Low response quality

- Tên: Low response quality
- Severity: warning
- Duration: 15m
- Kênh thông báo: Slack `#llmops-alerts`
- SLI/SLO liên quan: Quality proxy trung bình tối thiểu 0.75.
- Điều kiện và thời gian duy trì: `quality_score_avg < 0.75` liên tục 15 phút.
- Ảnh hưởng tới người dùng: Câu trả lời kém liên quan hoặc thiếu căn cứ.
- Ba bước kiểm tra đầu tiên: So sánh quality theo feature; kiểm tra retrieval success; đối chiếu prompt version trên trace.
- Mitigation tạm thời: Rollback label `production` về prompt baseline gần nhất.
- Owner: ai-quality
