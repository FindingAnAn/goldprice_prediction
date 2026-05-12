# 06-Logging-Observability / Quy ước Logging và Observability

## 1. Purpose / Mục đích

### EN
This document defines how logging, metrics, health checks, tracing, and alerts must be designed and implemented across the system.  
Its purpose is to make system behavior observable, diagnosable, and operable in both development and production environments.

### VI
Tài liệu này định nghĩa cách thiết kế và triển khai logging, metrics, health checks, tracing, và alert trong toàn hệ thống.  
Mục tiêu là giúp hành vi hệ thống có thể được quan sát, chẩn đoán, và vận hành tốt trong cả môi trường phát triển lẫn production.

## 2. Scope / Phạm vi

### EN
This document applies to:

- application logs
- infrastructure and integration logs
- health and readiness checks
- runtime metrics
- request and job observability
- tracing and correlation
- alerting and operational signals

### VI
Tài liệu này áp dụng cho:

- log của application
- log của infrastructure và integration
- health check và readiness check
- metric runtime
- khả năng quan sát request và job
- tracing và correlation
- alert và tín hiệu vận hành

## 3. Core Principles / Nguyên tắc cốt lõi

### 3.1 Observability is a first-class system capability / Observability là năng lực hạng nhất của hệ thống

#### EN
Observability must be designed as part of the system, not added only after production issues occur.

#### VI
Observability phải được thiết kế như một phần của hệ thống, không phải chỉ thêm vào sau khi production gặp sự cố.

### 3.2 Logs are for events, metrics are for trends, traces are for flow / Log để ghi sự kiện, metric để theo dõi xu hướng, trace để theo dõi luồng

#### EN
Use logs, metrics, and traces for their intended purposes.  
Do not overload one signal type to replace another.

#### VI
Dùng logs, metrics, và traces đúng mục đích của chúng.  
Không dùng một loại tín hiệu để thay thế máy móc cho loại khác.

### 3.3 Operational visibility must not leak sensitive data / Khả năng quan sát vận hành không được làm lộ dữ liệu nhạy cảm

#### EN
Observability must help diagnosis without exposing secrets, credentials, tokens, or sensitive user data.

#### VI
Observability phải hỗ trợ chẩn đoán mà không làm lộ secret, credential, token, hoặc dữ liệu người dùng nhạy cảm.

## 4. Logging conventions / Quy ước về logging

### 4.1 Logging must be initialized centrally / Logging phải được khởi tạo tập trung

#### EN
Logging configuration must be defined in one central place and reused across the application.

#### VI
Cấu hình logging phải được định nghĩa ở một nơi tập trung và tái sử dụng trong toàn bộ ứng dụng.

#### Rules / Luật

##### EN
- do not configure logging independently in many modules
- use a shared logger configuration entrypoint
- keep logger behavior consistent across environments

##### VI
Không được:

- tự cấu hình logging rải rác ở nhiều module
- mỗi file tự dựng logger format riêng
- làm hành vi logger khác nhau một cách ngẫu nhiên giữa các môi trường

### 4.2 Log levels must have clear meaning / Log level phải có ý nghĩa rõ ràng

#### EN
Each log level must be used consistently.

#### VI
Mỗi log level phải được dùng nhất quán.

#### Recommended usage / Cách dùng khuyến nghị

##### EN
- **DEBUG**: internal diagnostic detail useful during development or deep investigation
- **INFO**: important state transitions and successful operational milestones
- **WARNING**: abnormal but recoverable conditions
- **ERROR**: failed operations requiring attention
- **CRITICAL**: severe failures affecting system availability or correctness

##### VI
- **DEBUG**: chi tiết chẩn đoán nội bộ, hữu ích khi phát triển hoặc điều tra sâu
- **INFO**: chuyển trạng thái quan trọng và mốc vận hành thành công
- **WARNING**: tình huống bất thường nhưng còn phục hồi được
- **ERROR**: thao tác thất bại cần được chú ý
- **CRITICAL**: lỗi nghiêm trọng ảnh hưởng đến tính sẵn sàng hoặc tính đúng đắn của hệ thống

### 4.3 Logs must capture meaningful events / Log phải ghi lại sự kiện có ý nghĩa

#### EN
Logs should capture meaningful state transitions, failures, retries, and external interactions.

#### VI
Log nên ghi lại các chuyển trạng thái có ý nghĩa, failure, retry, và tương tác với hệ thống ngoài.

#### Examples / Ví dụ
- request started / request completed
- job started / job completed / job failed
- external API called / failed / timed out
- model inference started / completed / failed
- retraining triggered
- fallback path activated

### 4.4 Prefer structured logging / Ưu tiên structured logging

#### EN
Prefer structured logs with explicit fields over free-form strings whenever practical.

#### VI
Ưu tiên structured logging với field rõ ràng thay vì chuỗi tự do nếu có thể.

#### Preferred / Ưu tiên
```python
logger.info(
    "Invoice processed",
    extra={"invoice_id": invoice_id, "customer_id": customer_id}
)
```

#### Avoid / Tránh
```python
logger.info(f"Invoice {invoice_id} processed for customer {customer_id}")
```

#### Why / Vì sao

##### EN
Structured logs are easier to search, filter, aggregate, and analyze.

##### VI
Structured log dễ tìm kiếm, lọc, tổng hợp, và phân tích hơn.

### 4.5 Log context, not noise / Log ngữ cảnh, không log nhiễu

#### EN
Log messages must be concise and useful.  
Avoid excessive logging that adds no diagnostic or operational value.

#### VI
Thông điệp log phải ngắn gọn và hữu ích.  
Tránh log quá nhiều nhưng không tạo thêm giá trị chẩn đoán hoặc vận hành.

#### Avoid / Tránh
- logging every trivial assignment
- logging repetitive success messages in tight loops
- dumping entire payloads by default
- logging giant stack traces where no action is possible

### 4.6 Do not log secrets or sensitive data / Không log secret hoặc dữ liệu nhạy cảm

#### EN
Never log passwords, API keys, access tokens, private credentials, or full sensitive payloads.
For the complete list of prohibited data and redaction rules, follow `08-Security_secrets_conventions` §7.

#### VI
Không bao giờ log mật khẩu, API key, access token, credential riêng tư, hoặc toàn bộ payload nhạy cảm.
Về danh sách đầy đủ dữ liệu bị cấm và quy tắc redaction, tuân theo `08-Security_secrets_conventions` §7.

### 4.7 Log once at the correct operational boundary / Log một lần tại đúng boundary vận hành

#### EN
A failure should usually be logged once at the boundary where it becomes operationally meaningful.

#### VI
Một failure thường chỉ nên được log một lần tại boundary nơi nó trở nên có ý nghĩa vận hành.

#### Preferred / Ưu tiên
- infrastructure may add debug context during translation
- application may add workflow context if needed
- interface or top-level runner emits the main operational log

#### Avoid / Tránh
- the same exception logged at infrastructure, application, interface, and scheduler levels without additional value

## 5. Log content rules / Quy tắc về nội dung log

### 5.1 Every important log entry should answer at least one useful question / Mỗi log quan trọng nên trả lời ít nhất một câu hỏi hữu ích

#### EN
A useful log entry should help answer:

- what happened?
- where did it happen?
- which entity or request was involved?
- what was the result?
- what should be investigated next?

#### VI
Một log hữu ích nên giúp trả lời:

- chuyện gì đã xảy ra?
- nó xảy ra ở đâu?
- entity hoặc request nào liên quan?
- kết quả là gì?
- bước điều tra tiếp theo nên là gì?

### 5.2 Use stable identifiers in logs / Dùng identifier ổn định trong log

#### EN
Prefer stable identifiers such as:

- request_id
- job_id
- user_id
- invoice_id
- model_version
- trace_id

#### VI
Ưu tiên dùng identifier ổn định như:

- request_id
- job_id
- user_id
- invoice_id
- model_version
- trace_id

### 5.3 Log messages should reflect intent, not implementation trivia / Log nên phản ánh ý đồ, không phải chi tiết vụn vặt của implementation

#### EN
Prefer messages such as:

- Failed to process invoice
- Model inference timed out
- Retrying partner request

Avoid messages such as:

- Entered function
- Variable x changed
- Line 42 reached

#### VI
Ưu tiên các message như:

- Failed to process invoice
- Model inference timed out
- Retrying partner request

Tránh các message như:

- Entered function
- Variable x changed
- Line 42 reached

## 6. Metrics conventions / Quy ước về metrics

### 6.1 Metrics are required for production-capable systems / Metrics là bắt buộc với hệ thống hướng production

#### EN
Production-capable systems must emit metrics for operational visibility.

#### VI
Hệ thống hướng production phải phát ra metrics để quan sát vận hành.

### 6.2 Metrics must be chosen intentionally / Metric phải được chọn có chủ đích

#### EN
Track metrics that reflect:

- throughput
- latency
- error rates
- resource usage
- dependency health
- domain-specific success indicators

#### VI
Theo dõi các metric phản ánh:

- throughput
- latency
- tỷ lệ lỗi
- mức sử dụng tài nguyên
- sức khỏe của dependency
- chỉ số thành công đặc thù domain

#### Examples / Ví dụ
- request count
- request latency
- job duration
- retry count
- failed external calls
- queue lag
- model inference latency
- prediction success rate
- drift alert count

### 6.3 Metrics must use stable names and clear labels / Metric phải có tên ổn định và nhãn rõ ràng

> **Cross-reference / Tham chiếu chéo**: Chuẩn đặt tên metric cụ thể cho Prometheus (format `<namespace>_<subsystem>_<name>_<unit>`, label naming) được định nghĩa trong `18-Observability_orchestration_conventions` §7.3.

#### EN
Metric names should be stable, descriptive, and consistent.  
Labels should be chosen carefully to avoid uncontrolled cardinality.

#### VI
Tên metric nên ổn định, dễ hiểu, và nhất quán.  
Label phải được chọn cẩn thận để tránh cardinality tăng mất kiểm soát.

#### Avoid / Tránh
- labels with raw user input
- labels with unbounded IDs
- dynamically generated metric names

### 6.4 Logs are not a substitute for metrics / Log không thay thế metric

#### EN
Do not rely only on logs to infer latency, throughput, or failure trends when metrics should exist explicitly.

#### VI
Không được chỉ dựa vào log để suy ra latency, throughput, hoặc xu hướng lỗi khi đáng ra metric phải tồn tại rõ ràng.

## 7. Health check conventions / Quy ước về health check

### 7.1 Health checks must reflect service state meaningfully / Health check phải phản ánh trạng thái service có ý nghĩa

#### EN
Health checks should indicate whether the system can respond, operate, and serve traffic safely.

#### VI
Health check nên phản ánh liệu hệ thống có thể phản hồi, vận hành, và phục vụ traffic an toàn hay không.

### 7.2 Separate liveness and readiness when relevant / Tách liveness và readiness khi cần

#### EN
When the deployment platform supports it, distinguish liveness, readiness, and startup probes.
For endpoint naming, implementation detail, and Kubernetes/docker-compose health check rules, follow `14-infrastructure_deployment` §11.

#### VI
Khi nền tảng triển khai hỗ trợ, cần phân biệt liveness, readiness, và startup probe.
Về tên endpoint, chi tiết triển khai, và quy tắc health check cho Kubernetes/docker-compose, tuân theo `14-infrastructure_deployment` §11.

### 7.3 Health checks must avoid deep accidental side effects / Health check không được gây side effect sâu ngoài ý muốn

#### EN
Health checks should be lightweight and safe.  
They must not mutate data or trigger unnecessary heavy operations.

#### VI
Health check phải nhẹ và an toàn.  
Không được làm thay đổi dữ liệu hoặc kích hoạt các thao tác nặng không cần thiết.

### 7.4 Dependency-aware health checks should be explicit / Health check phụ thuộc hệ ngoài phải rõ ràng

#### EN
If readiness depends on a database, queue, model registry, or external dependency, that dependency should be reflected explicitly and safely.

#### VI
Nếu readiness phụ thuộc vào database, queue, model registry, hoặc hệ ngoài, các phụ thuộc đó phải được phản ánh rõ ràng và an toàn.

## 8. Tracing and correlation / Tracing và correlation

### 8.1 Requests and jobs should be traceable end to end / Request và job nên theo dõi được từ đầu đến cuối

#### EN
Where practical, each request, job, or workflow should carry a correlation identifier across boundaries.

#### VI
Khi khả thi, mỗi request, job, hoặc workflow nên mang một correlation identifier xuyên qua các boundary.

#### Common fields / Field thường dùng
- request_id
- trace_id
- correlation_id
- job_id
- workflow_id

### 8.2 Propagate correlation context across layers / Lan truyền correlation context qua các layer

#### EN
Correlation identifiers should be propagated through:

- API requests
- async jobs
- queue messages
- background workers
- external service calls where supported

#### VI
Correlation identifier nên được lan truyền qua:

- API request
- async job
- queue message
- background worker
- external service call nếu được hỗ trợ

### 8.3 Tracing complements logs and metrics / Tracing bổ sung cho log và metric

#### EN
Use traces to understand flow, timing, and dependency relationships across multiple services or steps.

#### VI
Dùng trace để hiểu luồng, thời gian, và quan hệ phụ thuộc giữa nhiều service hoặc nhiều bước xử lý.

## 9. Alerting conventions / Quy ước về alert

> **Cross-reference / Tham chiếu chéo**: Format cụ thể cho Prometheus alert rule (PrometheusRule CRD, bắt buộc severity/summary/description/runbook_url) được định nghĩa trong `18-Observability_orchestration_conventions` §7.6.

### 9.1 Alerts must be actionable / Alert phải có thể hành động được

#### EN
Every alert should correspond to a condition that operators can understand and act on.

#### VI
Mỗi alert phải tương ứng với một điều kiện mà người vận hành có thể hiểu và hành động được.

#### Avoid / Tránh
- alerts with no clear owner
- alerts with no runbook or expected action
- alerts based on noisy, low-signal events

### 9.2 Alert on symptoms that matter / Alert theo triệu chứng có ý nghĩa

#### EN
Prefer alerting on:

- sustained high error rate
- elevated latency
- failing readiness
- backlog growth
- model drift
- repeated job failures
- dependency outages

#### VI
Ưu tiên alert theo:

- tỷ lệ lỗi cao kéo dài
- latency tăng bất thường
- readiness fail
- backlog tăng
- model drift
- job fail lặp lại
- dependency outage

### 9.3 Avoid alert fatigue / Tránh mệt mỏi vì alert

#### EN
Do not create alerts for every warning-level event.  
Alert thresholds should be chosen to reduce noise while preserving useful signal.

#### VI
Không tạo alert cho mọi sự kiện mức warning.  
Ngưỡng alert phải được chọn để giảm nhiễu nhưng vẫn giữ tín hiệu hữu ích.

## 10. Environment behavior / Hành vi theo môi trường

### 10.1 Development and production may differ in verbosity / Dev và production có thể khác nhau về độ chi tiết

#### EN
Development may allow more verbose logs.  
Production must prioritize signal quality, stability, and safety.

#### VI
Môi trường development có thể cho phép log chi tiết hơn.  
Production phải ưu tiên chất lượng tín hiệu, tính ổn định, và tính an toàn.

### 10.2 Debug logging must be controllable / Debug logging phải điều khiển được

#### EN
Debug-level logging must be configurable and must not be permanently enabled in production by default.

#### VI
Debug-level logging phải có thể cấu hình và không được bật mặc định vĩnh viễn trên production.

## 11. ML and data-specific observability / Observability đặc thù cho ML và data

### 11.1 Data and ML systems require domain-specific observability / Hệ thống data và ML cần observability đặc thù domain

#### EN
Data and ML systems must observe not only technical health but also data and model quality.

#### VI
Hệ thống data và ML không chỉ phải quan sát sức khỏe kỹ thuật mà còn phải quan sát chất lượng dữ liệu và mô hình.

#### Examples / Ví dụ
- data freshness
- schema validation failures
- missing feature rates
- model version currently serving
- inference latency
- prediction error distribution
- drift indicators
- retraining trigger counts

### 11.2 Model behavior must be observable after deployment / Hành vi mô hình phải quan sát được sau triển khai

#### EN
Model monitoring should include enough signals to detect degradation, drift, and abnormal serving behavior.

#### VI
Theo dõi mô hình phải có đủ tín hiệu để phát hiện suy giảm, drift, và hành vi phục vụ bất thường.

## 12. Distributed Tracing (Tier 2 - Microservices) / Distributed Tracing cho Microservices

> ⚠️ Agent: Chỉ áp dụng section này sau khi user xác nhận kiến trúc Microservices.
> Xem `16-System_architecture_conventions.md` §3 để biết tiêu chí.

### 12.1 OpenTelemetry is the standard / OpenTelemetry là tiêu chuẩn bắt buộc

#### EN
🔴 **MUST**: Distributed tracing in microservices must be implemented using OpenTelemetry (OTEL) standard SDKs.
Do not use vendor-specific tracing libraries (e.g., Datadog APM SDK directly) inside business code.
Export traces using OTLP (OpenTelemetry Protocol) to an OpenTelemetry Collector.

#### VI
🔴 **MUST**: Distributed tracing trong microservices phải được implement bằng OpenTelemetry (OTEL) standard SDK.
Không dùng thư viện tracing đặc thù của vendor (ví dụ Datadog APM SDK trực tiếp) bên trong business code.
Export trace qua OTLP (OpenTelemetry Protocol) tới OpenTelemetry Collector.

### 12.2 W3C TraceContext propagation / Lan truyền W3C TraceContext

#### EN
🔴 **MUST**: Context propagation across service boundaries must use the W3C TraceContext HTTP headers formats (`traceparent` and `tracestate`).
This ensures traces are not broken when passing through different languages, frameworks, or service meshes.

#### VI
🔴 **MUST**: Việc lan truyền context xuyên ranh giới service phải dùng định dạng W3C TraceContext HTTP header (`traceparent` và `tracestate`).
Điều này đảm bảo trace không bị ngắt quãng khi đi qua các ngôn ngữ, framework, hay service mesh khác nhau.

### 12.3 OTEL Baggage for business context / OTEL Baggage cho ngữ cảnh nghiệp vụ

#### EN
🟡 **SHOULD**: Use OTEL Baggage to propagate business context (e.g., `tenant_id`, `user_tier`) across service hops without putting them in every API signature.
However, do NOT put sensitive user data or large payloads in Baggage.

#### VI
🟡 **SHOULD**: Dùng OTEL Baggage để truyền business context (ví dụ `tenant_id`, `user_tier`) qua nhiều service hop mà không cần đưa vào tham số của mọi API.
Tuy nhiên, KHÔNG đưa dữ liệu user nhạy cảm hoặc payload lớn vào Baggage.

### 12.4 SLO-based Alerting / Cảnh báo dựa trên SLO

#### EN
🔴 **MUST** (for production services): Alerts must be based on Service Level Objectives (SLOs) and Error Budgets, not just static thresholds.
- Do NOT alert when CPU > 80% (cause-based alert)
- DO alert when the P99 Latency > 500ms for 5 minutes (symptom-based alert, impacts user)

#### VI
🔴 **MUST** (cho service production): Alert phải dựa trên Service Level Objectives (SLOs) và Error Budget, không chỉ là threshold tĩnh.
- KHÔNG alert khi CPU > 80% (alert theo nguyên nhân)
- CÓ alert khi P99 Latency > 500ms trong 5 phút (alert theo triệu chứng, ảnh hưởng user)

---

## 13. Anti-patterns / Mẫu xấu cần tránh

### EN
Avoid:

- logging secrets or sensitive payloads
- logging the same error repeatedly across many layers
- using logs as the only source of operational visibility
- relying on free-form logs when structured logs are practical
- creating health checks that mutate state
- using metrics with unstable names or unbounded labels
- creating alerts that are noisy but not actionable
- enabling verbose debug logs permanently in production
- treating observability as optional post-release work
- (Microservices) vendor lock-in with proprietary tracing SDKs inside domain code

### VI
Tránh:

- log secret hoặc payload nhạy cảm
- log lặp cùng một lỗi ở nhiều layer
- dùng log làm nguồn quan sát vận hành duy nhất
- chỉ dùng log tự do khi structured log là khả thi
- tạo health check làm thay đổi trạng thái hệ thống
- dùng metric có tên không ổn định hoặc label không giới hạn
- tạo alert nhiều nhiễu nhưng không hành động được
- bật debug log quá chi tiết vĩnh viễn ở production
- xem observability như phần việc tùy chọn sau khi release
- (Microservices) bị khóa vào vendor (lock-in) vì dùng tracing SDK độc quyền bên trong domain code

## 14. Review checklist / Checklist review

### EN
When reviewing logging and observability, check:

- Is logging initialized centrally?
- Are log levels used consistently?
- Do important flows emit meaningful logs?
- Is sensitive data protected?
- Are stable identifiers included where needed?
- Are metrics present for throughput, latency, and failures?
- Do health checks reflect real operational readiness?
- Are correlation IDs propagated?
- Are alerts actionable and not noisy?
- For ML/data systems, are data and model quality signals present?
- (Microservices) Is OpenTelemetry standardized and W3C TraceContext propagated correctly?

### VI
Khi review logging và observability, cần kiểm tra:

- Logging đã được khởi tạo tập trung chưa?
- Log level có được dùng nhất quán không?
- Các luồng quan trọng có phát ra log có ý nghĩa không?
- Dữ liệu nhạy cảm có được bảo vệ không?
- Có stable identifier khi cần không?
- Có metric cho throughput, latency, và failure không?
- Health check có phản ánh đúng readiness vận hành không?
- Correlation ID có được lan truyền không?
- Alert có hành động được và không quá nhiễu không?
- Với hệ data/ML, có tín hiệu về chất lượng dữ liệu và mô hình không?
- (Microservices) OpenTelemetry có được chuẩn hóa và W3C TraceContext được lan truyền đúng không?

## 15. Definition of done / Điều kiện hoàn thành

### EN
A module or service is observability-compliant only if:

- logging is configured consistently
- meaningful operational logs exist
- sensitive information is protected
- metrics exist for key operational behavior
- health checks are present where applicable
- tracing or correlation exists for important flows
- alerts are defined for important failure conditions (preferably SLO-based)
- observability covers both technical health and domain-relevant signals
- (Microservices) traces are exported via OTLP without proprietary SDKs

### VI
Một module hoặc service chỉ được coi là tuân thủ observability khi:

- logging được cấu hình nhất quán
- tồn tại các log vận hành có ý nghĩa
- thông tin nhạy cảm được bảo vệ
- có metric cho các hành vi vận hành quan trọng
- có health check khi phù hợp
- có tracing hoặc correlation cho các luồng quan trọng
- có alert cho các điều kiện failure quan trọng (ưu tiên dựa trên SLO)
- observability bao phủ cả sức khỏe kỹ thuật lẫn tín hiệu liên quan tới domain
- (Microservices) trace được export qua OTLP mà không dùng SDK độc quyền
