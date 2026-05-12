# 00-Index and Glossary / Bản đồ quy ước và thuật ngữ chung

## 1. Purpose / Mục đích

### EN
This file is the entry point for the entire coding conventions system.  
It provides a map of all convention files, their responsibilities, and cross-reference relationships, as well as a shared glossary of terms used across the conventions.

**For agents**: Always read this file first to understand which convention files are relevant to the current task before generating or reviewing code.

### VI
File này là điểm vào cho toàn bộ hệ thống coding conventions.  
Nó cung cấp bản đồ của tất cả file convention, trách nhiệm của chúng, và mối quan hệ tham chiếu chéo, cũng như bảng thuật ngữ chung được dùng xuyên suốt các quy ước.

**Cho agent**: Luôn đọc file này trước để hiểu file convention nào liên quan đến task hiện tại trước khi gen hoặc review code.

---

## 2. Convention file index / Danh mục file quy ước

| # | File | Phạm vi / Scope | Khi nào đọc / When to read |
|---|------|-----------------|----------------------------|
| 01 | `01-Structure_conventions` | Cấu trúc dự án, phân lớp, baseline layout | Khi tạo dự án mới hoặc thêm module |
| 02 | `02-Config_conventions` | Config code, type safety, validation, env | Khi viết hoặc thay đổi config |
| 03 | `03-Naming_style_conventions` | Naming rules, coding style, formatter | Khi đặt tên bất kỳ thành phần code nào |
| 04 | `04-Dependencies_import_conventions` | Import rules, dependency direction, layer rules | Khi thêm import hoặc tạo dependency mới |
| 05 | `05-Error_handling_convention` | Error classification, handling by layer | Khi viết error handling hoặc exception |
| 06 | `06-Logging_observability_convention` | Logging, metrics, health checks, alerting | Khi thêm log, metric, hoặc health check |
| 07 | `07-Testing_convention` | Unit test, integration test, fixtures, mocks | Khi viết hoặc review test |
| 08 | `08-Security_secrets_conventions` | Secrets, data safety, least privilege | Khi xử lý secret, credential, hoặc dữ liệu nhạy cảm |
| 09 | `09-Git_pr_release_convention` | Branch, commit, PR, review, merge, release | Khi tạo branch, commit, PR, hoặc release |
| 10 | `10-Code_design_principles` | SOLID, function design, complexity, refactoring | Khi thiết kế class, function, hoặc refactor |
| 11 | `11-Definition_of_done` | DoD for code, feature, PR, release | Khi kiểm tra work item đã hoàn thành chưa |
| 12 | `12-Api_conventions` | REST, versioning, pagination, idempotency | Khi thiết kế hoặc thay đổi API |
| 13 | `13-data_ml_conventions` | Data pipeline, feature eng, model, experiment, ML testing | Khi làm việc với data hoặc ML code |
| 14 | `14-infrastructure_deployment` | Docker, compose, Terraform, K8s, CI/CD, rollback | Khi viết Dockerfile, IaC, hoặc pipeline |
| 15 | `15-Documentation_conventions` | Docstring, type hints, comment, README, CHANGELOG, ADR | Khi viết tài liệu hoặc docstring |
| 16 | `16-System_architecture_conventions`| Module boundary, data ownership, DDD, EDA, Saga, Resilience | Khi thiết kế kiến trúc, tách service, giao tiếp hệ thống |
| 17 | `17-Feature_flags_convention`     | Release flags, operational flags, cleanup process | Khi dùng kỹ thuật phát hành lũy tiến, tắt bật tính năng |
| 18 | `18-Observability_orchestration_conventions` | Prometheus, Grafana, K8s advanced, Terraform advanced, Airflow on K8s, log aggregation | Khi triển khai monitoring stack, Airflow trên K8s, hoặc Terraform/K8s nâng cao |

---

## 3. Cross-reference map / Bản đồ tham chiếu chéo

Bảng dưới cho biết khi đọc file A, nên tham chiếu thêm file nào.

### EN
The table below shows canonical ownership: when a topic appears in multiple files, the **Canonical file** owns the full detail, and other files cross-reference to it.

### VI
Bảng dưới thể hiện quyền sở hữu canonical: khi một chủ đề xuất hiện ở nhiều file, **file Canonical** chứa chi tiết đầy đủ, các file khác tham chiếu tới nó.

| Chủ đề / Topic | Canonical file | Tham chiếu từ / Referenced by |
|----------------|---------------|-------------------------------|
| Dependency direction / Hướng phụ thuộc | `04-Dependencies` §5.3 | `01-Structure` §8, `10-Code_design` §8.4 |
| Layer rules (domain, app, infra) | `04-Dependencies` §5.4 | `01-Structure` §6, `10-Code_design` §8.1 |
| Import grouping order | `04-Dependencies` §4 | `03-Naming` §5.3 |
| Test naming conventions | `07-Testing` §8 | `03-Naming` §3.12 |
| No secrets in logs | `08-Security` §7 | `05-Error_handling` §9.2, `06-Logging` §4.6 |
| Log once at boundary | `06-Logging` §4.7 | `05-Error_handling` §9.1 |
| Safe config defaults | `08-Security` §6 | `02-Config` §8.2 |
| Line length limit | `03-Naming` §5.2 | `10-Code_design` §6.3 |
| Health check endpoints | `14-Infrastructure` §11 | `06-Logging` §7.2 |
| CI/CD pipeline structure | `14-Infrastructure` §10 | `09-Git` §12.1 |
| Type hints (ML-specific) | `13-Data_ML` §13.1 | `15-Documentation` §5.1 |
| Definition of Done (general) | `11-Definition_of_done` | `13-Data_ML` §16, `14-Infrastructure` §15 |
| Folder structure for modules | `01-Structure` §5-6 | `16-System_architecture` §4.3 |
| Error retry and classification | `05-Error_handling` | `16-System_architecture` §12.4, §13.2 |
| Correlation ID propagation | `06-Logging` §8 | `16-System_architecture` §6.2, §10.5 |
| Contract Testing (CDC) | `07-Testing` §14 | `16-System_architecture` §10.3 |
| API Idempotency Implementation | `12-Api_conventions` | `16-System_architecture` §10.4 |
| Feature flag evaluation at boundary | `17-Feature_flags` §4.3 | `10-Code_design` §8 |
| Notebook conventions | `13-Data_ML` §10 | `08-Security` §11 |
| CHANGELOG format | `15-Documentation` §8 | `09-Git_PR` §9.4 |
| Docker production-grade (HEALTHCHECK, tagging, scanning) | `18-Observability_orchestration` §4 | `14-Infrastructure` §5 |
| Terraform advanced (module structure, naming, version pin) | `18-Observability_orchestration` §5 | `14-Infrastructure` §7 |
| K8s basic conventions (limits, probes, secrets, namespaces) | `14-Infrastructure` §8 | `18-Observability_orchestration` §6 |
| Prometheus metric naming | `18-Observability_orchestration` §7.3 | `06-Logging` §6.3 |
| Alert rule format (PrometheusRule CRD) | `18-Observability_orchestration` §7.6 | `06-Logging` §9 |
| Grafana dashboard as code | `18-Observability_orchestration` §11 | `14-Infrastructure` §4 |
| Log aggregation (infra level) | `18-Observability_orchestration` §12 | `06-Logging` §4-5 |
| Airflow deployment (K8s) | `18-Observability_orchestration` §8 | `14-Infrastructure` §6.3 |
| Secrets flow across stack | `18-Observability_orchestration` §9.3 | `08-Security` §7 |

---

## 4. File reading guide by task type / Hướng dẫn đọc file theo loại task

### EN

| Task type | Files to read (in order) |
|-----------|---------------------------|
| **Create a new project** | 01 → 03 → 04 → 10 → 02 → 08 → 14 |
| **Write a new feature** | 10 → 03 → 04 → 05 → 07 → 11 |
| **Write/review API** | 12 → 10 → 05 → 06 → 03 → 08 |
| **Write/review ML code** | 13 → 10 → 03 → 07 → 06 → 02 |
| **Write infrastructure** | 14 → 18 → 10 → 08 → 02 → 09 |
| **Write tests** | 07 → 10 → 03 → 13 (if ML) |
| **Create a PR** | 09 → 11 → 15 |
| **Review code** | 10 → 04 → 03 → 11 + domain-specific file |
| **Write documentation** | 15 → 03 |
| **Handle secrets/config** | 08 → 02 → 14 |
| **Design architecture/modules** | 16 → 01 → 05 → 06 → 12 |
| **Implement new feature** | 10 → 03 → 04 → 05 → 07 → 17 (if needed) → 11 |
| **Deploy monitoring stack** | 18 → 14 → 06 → 08 |
| **Deploy Airflow on K8s** | 18 → 14 → 13 → 08 |

### VI

| Loại task | File cần đọc (theo thứ tự) |
|-----------|-----------------------------|
| **Tạo dự án mới** | 16 → 01 → 03 → 04 → 10 → 02 → 08 → 14 |
| **Viết tính năng mới** | 10 → 03 → 04 → 05 → 07 → 17 (nếu cần flag) → 11 |
| **Viết/review API** | 12 → 10 → 05 → 06 → 03 → 08 |
| **Viết/review ML code** | 13 → 10 → 03 → 07 → 06 → 02 |
| **Viết infrastructure** | 14 → 18 → 10 → 08 → 02 → 09 |
| **Viết test** | 07 → 10 → 03 → 13 (nếu ML) |
| **Tạo PR** | 09 → 11 → 15 |
| **Review code** | 10 → 04 → 03 → 11 + file chuyên biệt |
| **Viết tài liệu** | 15 → 03 |
| **Xử lý secret/config** | 08 → 02 → 14 |
| **Thiết kế kiến trúc/module** | 16 → 01 → 05 → 06 → 12 |
| **Deploy monitoring stack** | 18 → 14 → 06 → 08 |
| **Deploy Airflow trên K8s** | 18 → 14 → 13 → 08 |

---

## 5. Glossary / Bảng thuật ngữ

Các thuật ngữ dưới đây được dùng nhất quán trong toàn bộ bộ quy ước. Khi đọc bất kỳ file nào, thuật ngữ luôn mang ý nghĩa này.

| Thuật ngữ / Term | Định nghĩa / Definition |
|-------------------|------------------------|
| **Domain layer** | Lớp chứa business rules, entities, value objects. Không phụ thuộc framework hoặc infrastructure. / Layer containing business rules, entities, value objects. No framework or infrastructure dependency. |
| **Application layer** | Lớp điều phối use cases, workflows, và tương tác giữa domain với boundary. / Layer orchestrating use cases, workflows, and interactions between domain and boundaries. |
| **Infrastructure layer** | Lớp triển khai chi tiết kỹ thuật: database, SDK, messaging, file system. / Layer implementing technical detail: database, SDK, messaging, file system. |
| **Interface layer** | Lớp xử lý transport và entrypoint: HTTP route, CLI, scheduler. / Layer handling transport and entrypoints: HTTP routes, CLI, schedulers. |
| **Boundary** | Điểm mà hệ thống giao tiếp với bên ngoài (API endpoint, queue consumer, CLI entrypoint). / Point where the system communicates with the outside (API endpoint, queue consumer, CLI entrypoint). |
| **Contract** | Giao diện trừu tượng (interface, abstract class, protocol) định nghĩa hành vi mà không chỉ định implementation. / Abstract interface defining behavior without specifying implementation. |
| **Adapter** | Implementation cụ thể của contract, nằm ở infrastructure layer. / Concrete implementation of a contract, located in infrastructure layer. |
| **Secret** | Bất kỳ giá trị nhạy cảm nào: password, API key, token, signing key, connection string có credential. / Any sensitive value: password, API key, token, signing key, connection string with credentials. |
| **Config** | Giá trị cấu hình được load từ environment hoặc file, có kiểu dữ liệu rõ ràng và được validate khi khởi động. / Configuration value loaded from environment or file, with explicit type and validated at startup. |
| **DoD (Definition of Done)** | Tập hợp điều kiện phải thỏa mãn trước khi code được coi là hoàn thành. / Set of conditions that must be met before code is considered complete. |
| **Canonical** | File hoặc section sở hữu chi tiết đầy đủ của một quy tắc. Các file khác tham chiếu tới nó thay vì lặp lại. / File or section that owns the full detail of a rule. Other files reference it instead of repeating. |
| **Cross-reference** | Tham chiếu tới canonical file thay vì lặp lại nội dung. Format: `follow [filename] §X`. / Reference to canonical file instead of repeating content. |
| **Feature function** | Hàm biến đổi raw data thành feature cho model ML. Phải stateless, typed, testable. / Function transforming raw data into ML model features. Must be stateless, typed, testable. |
| **Pipeline step** | Một bước trong data/ML pipeline. Phải idempotent và có input/output schema rõ ràng. / A step in a data/ML pipeline. Must be idempotent with clear input/output schema. |
| **IaC (Infrastructure as Code)** | Quản lý infrastructure bằng code (Terraform, Pulumi...) thay vì thao tác thủ công. / Managing infrastructure through code instead of manual operations. |
| **Liveness probe** | Kiểm tra process có còn sống không. Nếu fail → restart container. / Check if process is alive. Failure → restart container. |
| **Readiness probe** | Kiểm tra service có sẵn sàng nhận traffic không. Nếu fail → ngừng route traffic tới. / Check if service is ready for traffic. Failure → stop routing traffic to it. |
| **ADR (Architecture Decision Record)** | Tài liệu ghi nhận quyết định kiến trúc quan trọng: context, decision, consequences. / Document recording important architectural decisions: context, decision, consequences. |
| **Idempotent** | Thực hiện nhiều lần cho cùng kết quả như thực hiện một lần. / Executing multiple times produces the same result as executing once. |
| **Bounded Context** | (DDD) Ranh giới ngữ nghĩa mà bên trong đó domain model được áp dụng hợp lệ. / (DDD) Semantic boundary within which a domain model is valid. |
| **Saga Pattern** | Chuỗi các local transaction phân tán, dùng compensating action (undo) nếu có lỗi. / Sequence of distributed local transactions, using compensating actions to undo failures. |
| **Circuit Breaker** | Mẫu bảo vệ hệ thống: ngừng gửi request tới service đang chết chờ nó hồi phục. / Pattern to stop sending requests to a failing service until it recovers. |
| **Transactional Outbox** | Mẫu đảm bảo nhất quán dữ liệu: lưu vào DB và đẩy message vào Outbox cùng một transaction. / Pattern to ensure atomic DB save and message publish. |
| **Entity Service Trap** | Anti-pattern: Service chỉ thực hiện CRUD cho một entity duy nhất (VD: ProductService) → tạo coupling. / Anti-pattern: Service only doing CRUD for one entity. |
| **Feature Flag** | Biến cấu hình để ẩn/hiện tính năng tại runtime mà không cần deploy lại code. / Config toggle to enable/disable features at runtime without deploying code. |
| **ServiceMonitor** | (K8s) CRD khai báo cho Prometheus Operator biết service nào cần scrape. / (K8s) CRD declaring which services Prometheus should scrape. |
| **PrometheusRule** | (K8s) CRD định nghĩa recording rules và alert rules cho Prometheus. / (K8s) CRD defining recording rules and alert rules for Prometheus. |
| **PodDisruptionBudget** | (K8s) Đảm bảo số lượng pod tối thiểu vẫn chạy khi bảo trì node. / (K8s) Ensures minimum pod count during node maintenance. |
| **Recording Rule** | PromQL pre-computed, lưu kết quả aggregate để tối ưu query. / Pre-computed PromQL saving aggregated results for query optimization. |
| **StatsD Exporter** | Bridge chuyển metric từ StatsD format sang Prometheus format. / Bridge converting metrics from StatsD format to Prometheus format. |
| **git-sync** | Sidecar container tự động pull DAG file từ Git repo vào Airflow pod. / Sidecar container that auto-pulls DAG files from a Git repo into Airflow pods. |

---

## 6. Versioning / Phiên bản

| Phiên bản | Ngày | Thay đổi |
|-----------|------|----------|
| v1.0 | 2026-03-19 | Tạo bộ quy ước ban đầu gồm 15 file (01–15) |
| v1.1 | 2026-03-19 | Bổ sung file 16 (System Architecture), 17 (Feature Flags), CDC Pact (07), OTEL (06), Resilience (05) |
| v1.2 | 2026-03-30 | Bổ sung file 18 (Observability & Orchestration): Prometheus, Grafana, K8s advanced, Terraform advanced, Airflow on K8s, Log aggregation. Cập nhật cross-reference map, reading guide, glossary |

---

## 7. How to maintain this index / Cách duy trì bản đồ này

### EN
When adding a new convention file:
1. Add a row to the **Convention file index** (§2)
2. Add any new cross-references to the **Cross-reference map** (§3)
3. Update the **File reading guide** (§4) if the new file is relevant to existing task types
4. Add new terms to the **Glossary** (§5) if introduced
5. Update the **Versioning** table (§6)

### VI
Khi thêm file convention mới:
1. Thêm dòng vào **Danh mục file** (§2)
2. Thêm cross-reference mới vào **Bản đồ tham chiếu** (§3)
3. Cập nhật **Hướng dẫn đọc file** (§4) nếu file mới liên quan đến loại task hiện có
4. Thêm thuật ngữ mới vào **Bảng thuật ngữ** (§5) nếu xuất hiện
5. Cập nhật bảng **Phiên bản** (§6)

---

## 8. Agent conventions reading flow / Luồng đọc quy ước của Agent

**Cho AI/Agents:** Khi bắt đầu một task liên quan tới code của dự án, agent PHẢI tuân thủ luồng quyết định sau:

1. Đọc yêu cầu của User.
2. Từ yêu cầu, phân loại task (ví dụ: tạo file mới, sửa API, hay design kiến trúc).
3. Tra cứu **§4. File reading guide by task type** trong file này để lấy danh sách file convention cần đọc.
4. Ưu tiên đọc `16-System_architecture_conventions.md` (nếu liên quan đến module/service boundary).
   - **BƯỚC QUYẾT ĐỊNH (CRITICAL):**
     - Đọc §3 của `16-System_architecture_conventions.md`.
     - Agent PHẢI chủ động hỏi User: *"Dự án của bạn áp dụng kiến trúc nào: Monolith, Modular Monolith, hay Microservices?"*
5. Đọc các file convention còn lại trong danh sách từ §4 trước khi bắt đầu gen/review code.
6. **THAM KHẢO (TÙY CHỌN):** Có thể xem các file mẫu trong thư mục `Example/` (ví dụ `Example/unitest_example.py` khi viết test, hoặc `Example/naming_style_example.md` khi xem xét style code) để tham khảo và dễ hình dung hơn về pattern triển khai nếu cần thiết.
