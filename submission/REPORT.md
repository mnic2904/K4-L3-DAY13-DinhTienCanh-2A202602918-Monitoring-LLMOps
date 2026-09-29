# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Đinh Tiến Cảnh
- **MSSV:** 2A202602918
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/mnic2904/K4-L3-DAY13-DinhTienCanh-2A202602918-Monitoring-LLMOps
- **Commit SHA cuối:** `1a5a63911d6571ef213f15212e34bc8208b905cd`
- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-2A202602918`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | [01-pytest.png](evidence/01-pytest.png) |
| Log validator | [02-log-validator.png](evidence/02-log-validator.png) |
| Dashboard validator | [03-dashboard-validator.png](evidence/03-dashboard-validator.png) |
| Structured log | [04-structured-log.png](evidence/04-structured-log.png) |
| PII redaction | [05-pii-redaction.png](evidence/05-pii-redaction.png) |
| Trace list | [06-trace-list.png](evidence/06-trace-list.png) |
| Trace waterfall | [07-trace-waterfall.png](evidence/07-trace-waterfall.png) |
| Trace metadata | [08-trace-metadata.png](evidence/08-trace-metadata.png) |
| Prompt versions | [09-prompt-versions.png](evidence/09-prompt-versions.png) |
| Prompt rollback | [10-prompt-rollback.png](evidence/10-prompt-rollback.png) |
| Dashboard runtime | [11-dashboard-overview.png](evidence/11-dashboard-overview.png) |
| Incident metric | [12-incident-metric.png](evidence/12-incident-metric.png) |
| Incident log | [13-incident-log.png](evidence/13-incident-log.png) |
| Incident trace | [14-incident-trace.png](evidence/14-incident-trace.png) |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 | Đã truyền correlation ID, bind context và scrub PII trước khi ghi log. |
| `validate_dashboard.py` | HỢP LỆ: 6/6 panel | HỢP LỆ: 6/6 panel | Dashboard contract hợp lệ. |
| `pytest` | 22 passed in 1.97s | 24 passed | Bổ sung kiểm tra observability, PII và dashboard runtime. |
| Số traces hợp lệ | 0 xác nhận được | 10 | Root agent có child retrieval và generation trong project cá nhân. |
| Số PII leak | | 0 | Kiểm tra runtime với email, điện thoại, CCCD và thẻ thanh toán. |
| Latency P95 / TTFT P95 | | 3757 ms / 50 ms | Dashboard runtime, time range 60 phút. |
| Retrieval success rate | | 100% | Tính trên các event có `tool_success`. |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Middleware giữ `x-request-id` đúng dạng `req-<8-hex>`; nếu thiếu hoặc sai dạng thì sinh ID mới bằng UUID, bind vào context và trả lại qua response header.
- **Các metadata được ghi vào structured log:** `correlation_id`, `user_id_hash`, `session_id`, `feature`, `model` và `env`.
- **Cách bảo đảm PII được scrub trước khi ghi:** `scrub_event` xử lý đệ quy mọi chuỗi trong event và được đặt trước `JsonlFileProcessor`/JSON renderer.
- **Cách kiểm chứng kết quả:** Chạy workload sạch với email, số điện thoại, CCCD và thẻ; `validate_logs.py` đạt 100/100, không có PII leak; `pytest` đạt 24 tests.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Gửi 10 request bằng key của project cá nhân và xác minh lại qua Observations API v2; có 10 root observation mới.
- **Cấu trúc root/retrieval/generation observations:** `lab-agent-run` (agent) là root; `retrieval` (retriever) và `llm-generation` (generation) là hai child. Generation ghi model, managed prompt, input/output tokens, cost và TTFT.
- **Cách nối trace với log:** Metadata root chứa `correlation_id`; ví dụ trace production `2c2965841cfe275e33445e883a377420` khớp log `req-0000025a`.
- **Prompt name:** `day13-chat`.
- **Version/label baseline:** v1, labels `baseline` và `production` sau rollback.
- **Version/label candidate:** v2, label `candidate`.
- **Trace ID của mỗi version:** baseline v1 `270ef7000be903266d1988703683c984`; candidate v2 `83aaaca11fa729109989473c7aba83ce`; production sau rollback về v1 `2c2965841cfe275e33445e883a377420`.
- **Cách promote và rollback `production`:** Dùng Langfuse `update_prompt`: chuyển `production` sang v2, kiểm tra, rồi gắn lại `production` cho v1; trạng thái cuối v1=`baseline,production`, v2=`candidate,latest`.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** `/dashboard` đọc trực tiếp `data/logs.jsonl`, tự refresh 30 giây và hiển thị latency/TTFT, traffic, errors/retrieval, cost, tokens và quality; validator đạt 6/6.
- **SLO và lý do chọn:** 99.5% request trong 28 ngày phải có `response_sent` và latency không quá 3000 ms; ngưỡng này cảnh báo đúng đợt suy giảm hiện tại có P95 3757 ms.
- **Cách tính error budget:** 28 ngày = 40320 phút; `40320 × 0.5% = 201.6` phút không đạt SLO.
- **Ba alert và runbook tương ứng:** P95 latency > 3000 ms/5m, error rate > 2%/5m và quality < 0.75/15m; đều gửi Slack `#llmops-alerts` và có mitigation trong `docs/alerts.md`.

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1` (K4, incident `rag_slow`, feature `monitoring`).
- **Khoảng thời gian điều tra:** 2026-09-29 08:42:08–08:42:25 UTC (15:42:08–15:42:25 Asia/Ho_Chi_Minh).
- **Triệu chứng từ metrics:** 5/5 request HTTP 200 nhưng latency P50=2655 ms, P95/P99=3535 ms, vượt threshold 2000 ms; TTFT P95 chỉ 50 ms và error breakdown rỗng.
- **Log line và correlation ID liên quan:** `2026-09-29T08:42:13.841274Z response_sent correlation_id=req-c88da412 latency_ms=3535 feature=monitoring tool_success=true`.
- **Trace ID và span gây ảnh hưởng:** trace `b5bb6fdfb8b369e76016c4651ae09f1e`; root agent 3.54 s, child `RETRIEVER` 2.501 s, child `GENERATION` 0.158 s.
- **Root cause:** Incident `rag_slow` thêm độ trễ 2.5 giây trong `retrieve()`. Retrieval chiếm phần lớn latency; generation và TTFT bình thường nên LLM không phải nguyên nhân.
- **Fix action:** Tắt `rag_slow`/khôi phục retrieval backend. Chạy lại cùng workload cho kết quả 5 request có internal latency 152–154 ms.
- **Preventive measure:** Alert khi P95 > 3000 ms trong 5 phút; theo dõi riêng retrieval duration/success, đặt timeout và fallback khi vector store chậm.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Đặt correlation ID và request metadata trong `structlog.contextvars` ở middleware/đầu request để mọi log downstream tự nhận cùng context, tránh truyền tay và tránh lệch ID.
- **Một lỗi/blocker đã gặp:** Ban đầu Langfuse không có prompt `day13-chat`, nên request dùng local fallback và chưa chứng minh được prompt version/rollback.
- **Cách tìm nguyên nhân và xử lý:** Kiểm tra SDK/API cho thấy kết nối và key hợp lệ nhưng prompt trả 404; sau đó tạo v1/v2, gắn labels, gửi workload và xác minh lại bằng Observations API v2.
- **Cách hiểu luồng Metrics → Logs → Traces:** Metrics xác định P95 tăng và time range; log trong khoảng đó cung cấp `req-c88da412`; trace cùng correlation ID cho thấy retrieval 2.501 giây trong khi generation chỉ 0.158 giây, từ đó kết luận root cause.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** Version/label giúp truy vết và rollback thay đổi prompt; token/cost phát hiện chi phí bất thường; SLO/error budget định lượng mức suy giảm được chấp nhận và thời điểm cần phản ứng.
- **Điều quan trọng nhất đã học:** Một metric bất thường chưa đủ để kết luận; cần nối đúng request từ log sang waterfall trace rồi mới đưa ra fix.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** Không còn hạn chế kỹ thuật; chỉ còn push repository và nộp URL cùng commit SHA trên LMS/Codelabs.

## 9. Checklist trước khi nộp

- [x] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [x] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
