# Agent Structure Conventions / Quy ước dựng cấu trúc cho Agent

## 1) Purpose / Mục đích

**EN**  
This document defines the structural conventions that the agent and developers must follow when creating a new project or extending an existing one.  
Its goal is to ensure that every project starts with a clear, scalable, and maintainable system structure before implementation details are added.

**VI**  
Tài liệu này định nghĩa các quy ước về cấu trúc mà agent và developer phải tuân theo khi tạo dự án mới hoặc mở rộng dự án hiện có.  
Mục tiêu là đảm bảo mọi dự án đều bắt đầu với một cấu trúc hệ thống rõ ràng, dễ mở rộng và dễ bảo trì trước khi đi sâu vào chi tiết triển khai.

---

## 2) Scope / Phạm vi

**EN**  
These conventions apply to project structure, architectural boundaries, system components, and scaffolding decisions.  
They do not yet define low-level coding style, implementation details, or domain-specific business rules.

**VI**  
Các quy ước này áp dụng cho cấu trúc dự án, ranh giới kiến trúc, các thành phần hệ thống, và quyết định dựng khung dự án.  
Chúng chưa đi vào coding style chi tiết, cách cài đặt cụ thể, hay luật nghiệp vụ theo từng domain.

---

## 3) Core principle / Nguyên tắc cốt lõi

**EN**  
The agent must generate projects based on architectural intent, not only by copying folders.  
Folder structure must reflect system responsibilities and future scalability.

**VI**  
Agent phải tạo dự án dựa trên ý đồ kiến trúc, không chỉ đơn thuần sao chép cây thư mục.  
Cấu trúc thư mục phải phản ánh trách nhiệm của hệ thống và khả năng mở rộng về sau.
Có thể tham khảo file System_structure.ini cùng mục
---

## 4) Structural defaults / Mặc định về cấu trúc

**EN**  
Every project must start from a modular and layered structure.  
At minimum, the structure must separate:
- business/domain logic
- application/use-case orchestration
- infrastructure and external integrations
- interfaces or entrypoints
- configuration
- tests
- documentation

**VI**  
Mọi dự án phải bắt đầu từ một cấu trúc phân lớp và chia module rõ ràng.  
Tối thiểu phải tách riêng:
- logic nghiệp vụ / domain
- orchestration / use-case / luồng xử lý
- hạ tầng và tích hợp ngoài
- interface hoặc entrypoint
- cấu hình
- kiểm thử
- tài liệu

---

## 5) Mandatory baseline layout / Cấu trúc nền tảng bắt buộc

**EN**  
Unless explicitly overridden, the agent must scaffold the following baseline structure:

project-root/
- src/
- tests/
- config/
- docs/
- scripts/
- infrastructure/
- README.md
- .env.example

**VI**  
Trừ khi có yêu cầu ghi đè rõ ràng, agent phải dựng cấu trúc nền tảng sau:

project-root/
- src/
- tests/
- config/
- docs/
- scripts/
- infrastructure/
- README.md
- .env.example

### 5.1 src / Mã nguồn chính

**EN**  
`src/` contains all production code.

**VI**  
`src/` chứa toàn bộ code chạy thực tế của hệ thống.

### 5.2 tests / Kiểm thử

**EN**  
`tests/` contains all test code and must be separated from production code.

**VI**  
`tests/` chứa toàn bộ code kiểm thử và phải tách biệt khỏi code production.

### 5.3 config / Cấu hình

**EN**  
`config/` contains shared settings and environment-specific overrides.

**VI**  
`config/` chứa cấu hình dùng chung và cấu hình riêng theo môi trường.

### 5.4 docs / Tài liệu

**EN**  
`docs/` contains architecture notes, setup instructions, and operational documents.

**VI**  
`docs/` chứa tài liệu kiến trúc, hướng dẫn cài đặt, và tài liệu vận hành.

### 5.5 scripts / Tập lệnh hỗ trợ

**EN**  
`scripts/` contains utility scripts and operational entrypoints, but must not contain core business logic.

**VI**  
`scripts/` chứa các script hỗ trợ hoặc entrypoint vận hành, nhưng không được chứa business logic cốt lõi.

### 5.6 infrastructure / Triển khai hạ tầng

**EN**  
`infrastructure/` contains deployment, containerization, and infrastructure-as-code assets.

**VI**  
`infrastructure/` chứa cấu hình triển khai, container hóa, và hạ tầng dưới dạng mã.

---

## 6) Layering rules / Luật phân lớp

### 6.1 Domain layer / Lớp domain

**EN**  
The domain layer contains core business concepts, rules, and validations.  
It must remain independent from frameworks and external services.

**VI**  
Lớp domain chứa các khái niệm nghiệp vụ cốt lõi, luật, và validation.  
Lớp này phải độc lập với framework và dịch vụ bên ngoài.

### 6.2 Application layer / Lớp application

**EN**  
The application layer orchestrates use cases and workflows.  
It coordinates domain logic and calls infrastructure through abstractions.

**VI**  
Lớp application điều phối các use case và workflow.  
Lớp này phối hợp domain logic và gọi hạ tầng thông qua abstraction rõ ràng.

### 6.3 Infrastructure layer / Lớp infrastructure

**EN**  
The infrastructure layer handles databases, files, APIs, queues, cloud services, and other technical integrations.

**VI**  
Lớp infrastructure xử lý database, file, API, queue, cloud service, và các tích hợp kỹ thuật khác.

### 6.4 Interface layer / Lớp giao tiếp

**EN**  
The interface layer contains HTTP routes, CLI commands, workers, schedulers, or event consumers.  
This layer must be thin and must delegate real logic to the application layer.

**VI**  
Lớp interface chứa HTTP route, CLI command, worker, scheduler, hoặc event consumer.  
Lớp này phải mỏng và phải chuyển phần logic chính xuống lớp application.

---

## 7) Architecture inference rules / Luật suy diễn kiến trúc

**EN**  
The agent must infer required modules from the system type instead of generating everything blindly.

**VI**  
Agent phải suy ra module cần thiết từ loại hệ thống thay vì sinh toàn bộ một cách máy móc.

### 7.1 If the project is an API service / Nếu dự án là API service

**EN**
Generate at minimum:
- `src/interfaces/http/` or `src/api/`
- `src/application/`
- `src/domain/`
- `src/infrastructure/`
- health check
- metrics entrypoint
- request/response schema location

**VI**
Phải tạo tối thiểu:
- `src/interfaces/http/` hoặc `src/api/`
- `src/application/`
- `src/domain/`
- `src/infrastructure/`
- health check
- metrics entrypoint
- nơi chứa request/response schema

### 7.2 If the project is a batch or scheduled system / Nếu dự án là hệ batch hoặc chạy định kỳ

**EN**
Generate at minimum:
- `src/jobs/` or `src/pipelines/`
- orchestration entrypoints
- workflow services in application layer
- operational scripts if needed

**VI**
Phải tạo tối thiểu:
- `src/jobs/` hoặc `src/pipelines/`
- các entrypoint điều phối
- workflow service ở lớp application
- script vận hành nếu cần

### 7.3 If the project is data or ML oriented / Nếu dự án thiên về data hoặc ML

**EN**
Generate at minimum:
- `src/data/ingestion/`
- `src/data/preprocessing/`
- `src/features/`
- `src/modeling/`
- `src/monitoring/`
- pipeline entrypoints
- evaluation structure

**VI**
Phải tạo tối thiểu:
- `src/data/ingestion/`
- `src/data/preprocessing/`
- `src/features/`
- `src/modeling/`
- `src/monitoring/`
- entrypoint cho pipeline
- cấu trúc dành cho evaluation

### 7.4 If the project integrates external systems / Nếu dự án tích hợp hệ ngoài

**EN**
Generate adapters under infrastructure and avoid mixing provider-specific logic into domain code.

**VI**
Phải tạo adapter dưới lớp infrastructure và không được trộn logic đặc thù nhà cung cấp vào domain code.

### 7.5 If the system is production-bound / Nếu hệ thống hướng production

**EN**
Also generate:
- environment-specific config
- logging bootstrap
- health checks
- metrics
- deployment assets
- rollback-aware operational structure

**VI**
Phải bổ sung thêm:
- config theo môi trường
- bootstrap logging
- health check
- metrics
- tài nguyên triển khai
- cấu trúc vận hành có tính đến rollback

---

## 8) Dependency direction / Hướng phụ thuộc giữa các lớp

**EN**  
Dependencies must flow inward toward business logic: `interfaces → application → domain`.  
Domain must not depend on framework or infrastructure.

For the complete dependency direction rules, layer-by-layer constraints, and review checklist, follow `04-Dependencies_import_conventions` §5.

**VI**  
Phụ thuộc phải đi từ ngoài vào trong, hướng về business logic: `interfaces → application → domain`.  
Domain không được phụ thuộc vào framework hoặc infrastructure.

Về quy tắc hướng dependency đầy đủ, ràng buộc theo từng layer, và checklist review, tuân theo `04-Dependencies_import_conventions` §5.

---

## 9) Component awareness rules / Luật nhận diện thành phần hệ thống

**EN**  
When creating a project, the agent must think in terms of system components, not only source files.  
It must identify whether the system needs:
- interfaces
- workflows
- storage
- external integrations
- monitoring
- deployment
- operations
- testing
- documentation

**VI**  
Khi tạo dự án, agent phải tư duy theo thành phần hệ thống, không chỉ theo file code.  
Agent phải xác định hệ thống có cần:
- interface
- workflow
- lưu trữ
- tích hợp ngoài
- giám sát
- triển khai
- vận hành
- kiểm thử
- tài liệu

---

## 10) Anti-patterns / Mẫu xấu cần tránh

**EN**
Do not generate:
- fat controllers
- business logic inside routes
- business logic inside DAG or scheduler files
- notebooks as production execution paths
- root-level chaos
- hard-coded environment values across files
- infrastructure code mixed with domain rules
- a project that has code but no testing or config structure

**VI**
Không được tạo:
- controller quá nặng
- business logic nằm trong route
- business logic nằm trong file DAG hoặc scheduler
- notebook trở thành đường chạy production
- thư mục gốc lộn xộn
- giá trị môi trường bị hard-code rải rác
- code hạ tầng trộn với luật nghiệp vụ
- dự án có code nhưng không có cấu trúc test hoặc config

---

## 11) Definition of scaffold completeness / Điều kiện để bộ khung được coi là hoàn chỉnh

**EN**  
A generated structure is considered complete only if:
- the main layers exist
- responsibilities are separated
- config is externalized
- tests have a place in the structure
- documentation has a place in the structure
- infrastructure has a place in the structure if deployment is expected
- system-specific components are included when relevant

**VI**  
Một cấu trúc sinh ra chỉ được coi là hoàn chỉnh khi:
- các lớp chính đã tồn tại
- trách nhiệm đã được tách rõ
- config đã được tách khỏi code
- test có vị trí rõ ràng trong cấu trúc
- tài liệu có vị trí rõ ràng trong cấu trúc
- hạ tầng có vị trí rõ ràng nếu có nhu cầu triển khai
- các thành phần đặc thù hệ thống đã được thêm vào khi cần

---

## 12) Deviation rule / Luật cho phép tối giản

**EN**  
The agent may simplify the structure only for prototypes, internal experiments, or explicitly short-lived tools.  
Even when simplified, the agent must still:
- keep production code under `src/`
- keep tests separate
- keep config separate
- avoid putting business logic in entrypoints

**VI**  
Agent chỉ được phép tối giản cấu trúc đối với prototype, thử nghiệm nội bộ, hoặc tool ngắn hạn có chỉ định rõ.  
Ngay cả khi tối giản, agent vẫn phải:
- để code production trong `src/`
- tách riêng test
- tách riêng config
- không đặt business logic trong entrypoint

---

## 13) Agent behavior / Hành vi bắt buộc của agent

**EN**  
Before scaffolding, the agent must:
1. identify the system type
2. identify required components
3. choose the minimal valid architecture
4. preserve separation of concerns
5. avoid generating unnecessary complexity

**VI**  
Trước khi dựng khung dự án, agent phải:
1. xác định loại hệ thống
2. xác định các thành phần cần có
3. chọn kiến trúc tối thiểu nhưng hợp lệ
4. giữ nguyên nguyên tắc tách trách nhiệm
5. tránh sinh ra độ phức tạp không cần thiết