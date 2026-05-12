# 16-System-Architecture-Conventions / Quy ước kiến trúc hệ thống

## 1. Purpose / Mục đích

### EN
This document defines architectural conventions for how modules and services are designed, communicate, own data, and handle failure across the system.
It applies to **all** architecture types — from monolith to microservices — using a tiered approach.

### VI
Tài liệu này định nghĩa các quy ước kiến trúc về cách module và service được thiết kế, giao tiếp, sở hữu dữ liệu, và xử lý lỗi trong toàn hệ thống.
Áp dụng cho **mọi** kiểu kiến trúc — từ monolith đến microservices — theo cách tiếp cận phân tầng.

> [!TIP]
> **Tùy chọn tham khảo cấu trúc kiến trúc mẫu tại:** [Example/system_structure_example.ini](Example/system_structure_example.ini)

> **For agents**: Read §3 (Context Declaration) first. Do NOT apply Tier 2 rules without confirming architecture type with the user.

---

## 2. Scope / Phạm vi

### EN
This document covers:
- module and service boundary design
- data ownership between modules
- inter-module and inter-service communication patterns
- event-driven architecture
- distributed transaction management (Saga)
- resilience and fault tolerance patterns
- service mesh infrastructure

It does NOT cover:
- physical folder layout → follow `01-Structure_conventions`
- API design details → follow `12-Api_conventions`
- deployment and CI/CD → follow `14-infrastructure_deployment`

### VI
Tài liệu này bao gồm:
- thiết kế ranh giới module và service
- quyền sở hữu dữ liệu giữa các module
- mẫu giao tiếp giữa module và giữa service
- kiến trúc hướng sự kiện
- quản lý giao dịch phân tán (Saga)
- mẫu chống chịu lỗi và dung lỗi
- hạ tầng service mesh

KHÔNG bao gồm:
- cấu trúc thư mục vật lý → tuân theo `01-Structure_conventions`
- chi tiết thiết kế API → tuân theo `12-Api_conventions`
- triển khai và CI/CD → tuân theo `14-infrastructure_deployment`

---

## 3. Context declaration / Khai báo ngữ cảnh (BẮT BUỘC)

### 3.1 Architecture type must be declared before applying this file / Phải khai báo kiểu kiến trúc trước khi áp dụng file này

#### EN
Before applying any rule in this file, the architecture type must be identified:

| Type | Apply |
|------|-------|
| **Monolith** | Tier 1 only |
| **Modular Monolith** | Tier 1 only |
| **Microservices** | Tier 1 + Tier 2 |

#### VI
Trước khi áp dụng bất kỳ quy tắc nào trong file này, phải xác định kiểu kiến trúc:

| Kiểu | Áp dụng |
|------|---------|
| **Monolith** | Chỉ Tier 1 |
| **Modular Monolith** | Chỉ Tier 1 |
| **Microservices** | Tier 1 + Tier 2 |

### 3.2 Agent rules / Luật cho agent

#### EN
- Agent MUST ask the user about architecture type before generating architecture-related code
- If unknown → default to Tier 1 only
- NEVER auto-apply Tier 2 without explicit confirmation

#### VI
- Agent PHẢI hỏi user về kiểu kiến trúc trước khi gen code liên quan đến kiến trúc
- Nếu chưa rõ → mặc định chỉ áp dụng Tier 1
- KHÔNG BAO GIỜ tự áp dụng Tier 2 mà không có xác nhận rõ ràng

---

# ════════════════════════════════════════════════════
# TIER 1: LUÔN ÁP DỤNG — Modular Foundation
# (Mọi dự án, bất kể kiến trúc)
# ════════════════════════════════════════════════════

## 4. Module boundary conventions / Quy ước ranh giới module (Tier 1 — luôn áp dụng)

### 4.1 Code must be organized by business capability / Code phải tổ chức theo năng lực nghiệp vụ

#### EN
Modules must represent business capabilities (e.g., `catalog`, `payment`, `notification`), not technical layers or database tables.
This ensures that when a business requirement changes, the change is contained within one module.

#### VI
Module phải đại diện cho năng lực nghiệp vụ (ví dụ: `catalog`, `payment`, `notification`), không phải tầng kỹ thuật hay bảng database.
Điều này đảm bảo khi yêu cầu nghiệp vụ thay đổi, thay đổi được chứa gọn trong một module.

#### Preferred / Ưu tiên
```
src/
  catalog/       ← business capability
  payment/       ← business capability
  notification/  ← business capability
```

#### Avoid / Tránh
```
src/
  models/        ← technical grouping
  controllers/
  services/
```

### 4.2 Modules must communicate through interfaces / Module phải giao tiếp qua interface

#### EN
A module must not import another module's internal classes, functions, or models directly.
Instead, modules interact through public interfaces (abstract class, protocol, or exported contract).
This keeps modules decoupled so they can be modified or extracted independently.

#### VI
Module không được import trực tiếp class, function, hoặc model nội bộ của module khác.
Thay vào đó, module tương tác qua interface công cộng (abstract class, protocol, hoặc contract được export).
Điều này giữ module tách rời để có thể sửa đổi hoặc tách ra độc lập.

#### Preferred / Ưu tiên
```python
# payment/contracts.py — public interface
class PaymentGateway(Protocol):
    async def charge(self, amount: Decimal, customer_id: str) -> PaymentResult: ...

# catalog/application/order_service.py — uses interface
class OrderService:
    def __init__(self, payment: PaymentGateway):
        self.payment = payment
```

#### Forbidden / Cấm
```python
# catalog/application/order_service.py — imports internal directly
from payment.infrastructure.stripe_client import StripeClient  # ❌ tight coupling
```

### 4.3 Namespace and package structure must reflect module boundary / Namespace và package phải phản ánh ranh giới module

#### EN
Each module should have its own package or namespace. For physical folder structure rules, follow `01-Structure_conventions` §5–§6.

#### VI
Mỗi module phải có package hoặc namespace riêng. Về quy tắc cấu trúc thư mục vật lý, tuân theo `01-Structure_conventions` §5–§6.

### 4.4 Anti-pattern: God module / Mẫu xấu: module ôm đồm

#### EN
A module that handles unrelated responsibilities (e.g., a `common` or `utils` module that grows unbounded) is a god module.
If a module has logic belonging to multiple business domains, it must be split.

#### VI
Module xử lý những trách nhiệm không liên quan nhau (ví dụ module `common` hoặc `utils` phình to không kiểm soát) là god module.
Nếu module chứa logic thuộc nhiều domain nghiệp vụ khác nhau, nó phải được tách ra.

---

## 5. Data ownership conventions / Quy ước sở hữu dữ liệu (Tier 1 — luôn áp dụng)

### 5.1 Each module owns its data / Mỗi module sở hữu dữ liệu riêng

#### EN
Each module must own and manage its own data (tables, schemas, collections).
This prevents changes in one module's schema from cascading failures across other modules — the most common cause of "distributed monolith" even in a single-codebase project.

#### VI
Mỗi module phải sở hữu và quản lý dữ liệu riêng (tables, schemas, collections).
Điều này ngăn việc thay đổi schema của một module gây lỗi domino sang module khác — nguyên nhân phổ biến nhất của "distributed monolith" ngay cả trong dự án một codebase.

### 5.2 No cross-module direct data access / Không truy cập dữ liệu chéo module trực tiếp

#### EN
One module must NOT directly query, join, or modify another module's data.
Data exchange must go through the owning module's public interface.

#### VI
Module này KHÔNG ĐƯỢC trực tiếp query, join, hoặc sửa dữ liệu của module khác.
Việc trao đổi dữ liệu phải đi qua interface công cộng của module sở hữu dữ liệu.

#### Preferred / Ưu tiên
```python
# Need customer info from customer module
customer = await customer_service.get_by_id(customer_id)
```

#### Forbidden / Cấm
```python
# Direct query to another module's table
customer = await db.execute("SELECT * FROM customers WHERE id = ?", customer_id)
```

### 5.3 Data sharing through public interface / Chia sẻ dữ liệu qua interface công cộng

#### EN
In a monolith, data sharing is done through function calls via contracts.
The module that owns the data exposes a service or repository contract; consuming modules call that contract.

#### VI
Trong monolith, chia sẻ dữ liệu thông qua lời gọi hàm qua contract.
Module sở hữu dữ liệu expose service hoặc repository contract; module sử dụng gọi contract đó.

### 5.4 Data ownership must be documented / Quyền sở hữu dữ liệu phải được ghi nhận

#### EN
Each table or collection must have a clear owner module. This can be documented through:
- naming convention: table prefix matches module name (e.g., `payment_transactions`)
- schema comments
- a data ownership map in `docs/`

#### VI
Mỗi bảng hoặc collection phải có module sở hữu rõ ràng. Có thể ghi nhận qua:
- quy ước đặt tên: prefix bảng khớp với tên module (ví dụ: `payment_transactions`)
- comment trong schema
- bảng đồ sở hữu dữ liệu trong `docs/`

---

## 6. Module communication conventions / Quy ước giao tiếp module (Tier 1 — luôn áp dụng)

### 6.1 Modules call each other through abstraction / Module gọi nhau qua abstraction

#### EN
All inter-module calls must go through abstractions (interface, protocol, contract).
This makes modules independently testable and replaceable.

#### VI
Mọi lời gọi giữa module phải qua abstraction (interface, protocol, contract).
Điều này giúp module có thể test độc lập và thay thế được.

### 6.2 Correlation ID must exist from entry point / Correlation ID phải có từ entry point

#### EN
Every request, job, or workflow must carry a correlation identifier from the entry point through all layers.
This is essential for debugging and tracing, even in a monolith.
For full correlation ID propagation and log format rules, follow `06-Logging_observability_convention` §8.

#### VI
Mọi request, job, hoặc workflow phải mang một correlation identifier từ entry point xuyên qua mọi layer.
Điều này cần thiết cho debugging và tracing, ngay cả trong monolith.
Về quy tắc đầy đủ về lan truyền correlation ID và format log, tuân theo `06-Logging_observability_convention` §8.

### 6.3 Heavy tasks must be async-ready from day 1 / Task nặng phải sẵn sàng async từ ngày 1

#### EN
Tasks that are slow, unreliable, or resource-intensive should be designed for asynchronous execution from the beginning.
Even in a monolith, use background workers or task queues instead of blocking the main request.

#### VI
Task chậm, không ổn định, hoặc tốn tài nguyên phải được thiết kế cho async execution ngay từ đầu.
Ngay cả trong monolith, hãy dùng background worker hoặc task queue thay vì block request chính.

#### Preferred / Ưu tiên
```python
# Async-ready: send email via background task
await task_queue.enqueue(send_welcome_email, user_id=user.id)
```

#### Avoid / Tránh
```python
# Blocking: send email in request handler
await send_welcome_email(user.id)  # blocks response for 2-5 seconds
return {"status": "created"}
```

### 6.4 Decision criteria for splitting a module into a service / Tiêu chí quyết định tách module thành service riêng

#### EN
Consider extracting a module into a separate service when:
- the module needs independent scaling (different load profile)
- the module has a different deployment cadence
- the module requires a different technology stack
- the module's failure should be isolated from the main system
- the team responsible for the module is separate

Do NOT split just because "microservices are better."

#### VI
Cân nhắc tách module thành service riêng khi:
- module cần scale độc lập (load profile khác biệt)
- module có nhịp deploy khác biệt
- module cần technology stack khác
- failure của module cần được cô lập khỏi hệ thống chính
- team chịu trách nhiệm module là team riêng

KHÔNG tách chỉ vì "microservices tốt hơn."

---

## 7. Scalability foundations / Nền tảng mở rộng (Tier 1 — luôn áp dụng)

### 7.1 Stateless design / Thiết kế không trạng thái

#### EN
Application processes must not store user session or request state in process memory.
Use external state stores (database, Redis, distributed cache) so that any process instance can handle any request.

#### VI
Process ứng dụng không được lưu session hoặc trạng thái request trong bộ nhớ process.
Dùng state store bên ngoài (database, Redis, distributed cache) để bất kỳ instance nào cũng xử lý được bất kỳ request nào.

### 7.2 Config externalization / Tách cấu hình ra ngoài

#### EN
All configuration must be externalized. For complete config conventions, follow `02-Config_conventions`.

#### VI
Mọi cấu hình phải được tách khỏi code. Về quy ước config đầy đủ, tuân theo `02-Config_conventions`.

### 7.3 Caching principles / Nguyên tắc caching

#### EN
- Cache only data that is read-heavy and changes infrequently
- Always define TTL (Time to Live) — no indefinite cache
- Design cache invalidation strategy before implementing cache
- Consider cache stampede prevention (lock, probabilistic early expiration)

#### VI
- Chỉ cache dữ liệu đọc nhiều và ít thay đổi
- Luôn định nghĩa TTL (Time to Live) — không cache vô thời hạn
- Thiết kế chiến lược cache invalidation trước khi implement cache
- Cân nhắc ngăn chặn cache stampede (lock, probabilistic early expiration)

### 7.4 Connection pooling / Quản lý pool kết nối

#### EN
Database clients, HTTP clients, and message broker connections must use connection pooling.
Configure pool size limits and idle timeouts appropriate to the deployment environment.

#### VI
Database client, HTTP client, và message broker connection phải dùng connection pooling.
Cấu hình giới hạn pool size và idle timeout phù hợp với môi trường triển khai.

---

# ════════════════════════════════════════════════════
# TIER 2: CHỈ KHI MICROSERVICES
# (Agent phải hỏi user trước khi áp dụng)
# ════════════════════════════════════════════════════

## 8. Service boundary & DDD conventions / Quy ước ranh giới service & DDD (Tier 2 — microservice only)

### 8.1 Service boundary must align with Bounded Context / Ranh giới service phải khớp với Bounded Context

#### EN
Each microservice must map to exactly one Bounded Context in Domain-Driven Design.
A Bounded Context defines the boundary within which a particular domain model applies.
Do NOT draw service boundaries based on database tables or UI screens.

#### VI
Mỗi microservice phải tương ứng với đúng một Bounded Context trong Domain-Driven Design.
Bounded Context định nghĩa ranh giới mà trong đó một domain model cụ thể được áp dụng.
KHÔNG vẽ ranh giới service dựa trên bảng database hoặc màn hình UI.

### 8.2 Service must be named after business capability / Service phải được đặt tên theo năng lực nghiệp vụ

#### EN
Services must be named after what they DO (capability), not what they STORE (entity).

#### VI
Service phải được đặt tên theo khả năng nghiệp vụ mà chúng THỰC HIỆN, không phải thứ mà chúng LƯU TRỮ.

#### Preferred / Ưu tiên
- `order-fulfillment-service` — kể câu chuyện nghiệp vụ đầy đủ
- `payment-processing-service`
- `catalog-management-service`

#### Avoid / Tránh
- `product-service` — chỉ là CRUD wrapper cho bảng product → Entity Service Trap
- `user-service` — quá chung, không rõ capability

### 8.3 Context Map must be documented / Context Map phải được ghi nhận

#### EN
Relationships between Bounded Contexts must be documented using Context Map patterns:

| Pattern | When to use |
|---------|-------------|
| **Partnership** | Two teams co-evolve their models together |
| **Customer-Supplier** | Upstream supplies, downstream consumes, priorities negotiated |
| **Anti-Corruption Layer (ACL)** | Downstream translates upstream model to protect its own domain |
| **Conformist** | Downstream accepts upstream model as-is (simple but coupled) |

#### VI
Mối quan hệ giữa các Bounded Context phải được ghi nhận bằng Context Map pattern:

| Pattern | Khi nào dùng |
|---------|-------------|
| **Partnership** | Hai team cùng phát triển model |
| **Customer-Supplier** | Upstream cung cấp, downstream tiêu thụ, thương lượng ưu tiên |
| **Anti-Corruption Layer (ACL)** | Downstream dịch model upstream để bảo vệ domain riêng |
| **Conformist** | Downstream chấp nhận model upstream nguyên trạng (đơn giản nhưng coupled) |

### 8.4 Anti-pattern: Entity Service Trap / Mẫu xấu: bẫy Entity Service

#### EN
A service that only wraps CRUD operations for a single entity (e.g., `ProductService` that only does Create/Read/Update/Delete on products) is an Entity Service.
This is an anti-pattern because it scatters business logic across callers and creates coupling.
A proper service encapsulates a complete business capability.

#### VI
Service chỉ bọc thao tác CRUD cho một entity duy nhất (ví dụ: `ProductService` chỉ Create/Read/Update/Delete sản phẩm) là Entity Service.
Đây là anti-pattern vì nó phân tán business logic sang các caller và tạo coupling.
Service đúng phải đóng gói một năng lực nghiệp vụ hoàn chỉnh.

### 8.5 Boundary quality KPI / KPI chất lượng ranh giới

#### EN
- **Change Cohesion ≥ 80%**: at least 80% of changes should only affect 1 service
- **Blast Radius**: a failure in one service must NOT cascade to unrelated services

#### VI
- **Change Cohesion ≥ 80%**: ít nhất 80% các thay đổi chỉ ảnh hưởng 1 service
- **Blast Radius**: failure ở một service KHÔNG ĐƯỢC lan sang service không liên quan

---

## 9. Database per Service conventions / Quy ước Database per Service (Tier 2 — microservice only)

### 9.1 Each service must have its own database / Mỗi service PHẢI có database riêng

#### EN
Each microservice must own and exclusively access its own database instance or schema.
Shared databases create schema coupling: one small schema change can break multiple services and destroy independent deployability — the most common root cause of "distributed monolith."

#### VI
Mỗi microservice phải sở hữu và chỉ truy cập database instance hoặc schema riêng của nó.
Shared database tạo schema coupling: một thay đổi schema nhỏ có thể phá hỏng nhiều service và phá vỡ khả năng deploy độc lập — nguyên nhân gốc phổ biến nhất của "distributed monolith."

### 9.2 Cross-service JOIN and direct DB query are forbidden / Cấm JOIN chéo service và query DB trực tiếp

#### EN
🔴 **MUST**: No service may directly query, join, or write to another service's database.
All data access across service boundaries must go through the owning service's API.

#### VI
🔴 **MUST**: Không service nào được trực tiếp query, join, hoặc ghi vào database của service khác.
Mọi truy cập dữ liệu xuyên ranh giới service phải đi qua API của service sở hữu.

### 9.3 Safe data sharing: Read Model via events / Chia sẻ dữ liệu an toàn: Read Model qua event

#### EN
When a service needs another service's data for queries (not writes), use a Read Model:
1. The owning service publishes domain events when data changes
2. The consuming service subscribes and maintains a local read-only copy
3. The read model is eventually consistent — acceptable for most query use cases

#### VI
Khi service cần dữ liệu của service khác để query (không phải write), dùng Read Model:
1. Service sở hữu publish domain event khi dữ liệu thay đổi
2. Service sử dụng subscribe và duy trì bản sao chỉ đọc local
3. Read model là eventually consistent — chấp nhận được cho hầu hết use case query

### 9.4 Advanced patterns: Event Sourcing and CQRS / Pattern nâng cao: Event Sourcing và CQRS

#### EN
- **Event Sourcing**: store state as a sequence of events instead of current state. Use ONLY when audit trail is a core business requirement. Complexity is very high.
- **CQRS**: separate read and write models. Use when read patterns differ significantly from write patterns (read >> write).

🔵 **MAY**: These patterns are optional. Do NOT adopt them "just because microservices."

#### VI
- **Event Sourcing**: lưu trạng thái dưới dạng chuỗi event thay vì trạng thái hiện tại. Chỉ dùng khi audit trail là yêu cầu nghiệp vụ cốt lõi. Độ phức tạp rất cao.
- **CQRS**: tách read model và write model. Dùng khi pattern đọc khác biệt đáng kể so với pattern ghi (read >> write).

🔵 **MAY**: Các pattern này là tùy chọn. KHÔNG áp dụng chỉ vì "đang dùng microservices."

### 9.5 4-phase database separation from monolith / Quy trình 4 giai đoạn tách DB từ monolith

> Áp dụng chỉ khi có kế hoạch migrate từ monolith sang microservices.
> Dự án monolith không có plan migrate không cần đọc section này.

#### EN
When migrating from monolith to microservices, separate the database in phases:

1. **Phase 1**: Extract business logic into a service module, still sharing the database
2. **Phase 2**: Split schema by domain boundary (separate tables/schemas per module)
3. **Phase 3**: Establish Outbox event sync between modules
4. **Phase 4**: Fully separate databases — each service has its own DB instance

#### VI
Khi chuyển từ monolith sang microservices, tách database theo từng phase:

1. **Phase 1**: Tách business logic vào module service, vẫn dùng chung DB
2. **Phase 2**: Chia schema theo domain boundary (bảng/schema riêng mỗi module)
3. **Phase 3**: Thiết lập Outbox event sync giữa các module
4. **Phase 4**: Tách DB hoàn toàn — mỗi service có DB instance riêng

---

## 10. Inter-service communication conventions / Quy ước giao tiếp giữa service (Tier 2 — microservice only)

### 10.1 Choose protocol by context / Chọn protocol theo ngữ cảnh

#### EN

| Protocol | When to use | Characteristics |
|----------|-------------|-----------------|
| **REST** | Public API, external clients | Universal, easy to debug, well-tooled |
| **gRPC** | Internal service-to-service | High performance, strict contract (protobuf), streaming |
| **GraphQL** | Client needs flexible queries | Avoids over-fetching, higher complexity |
| **Message Broker (Kafka, RabbitMQ)** | Async, decoupled workflows | At-least-once delivery, requires idempotency |

🟡 **SHOULD**: Prefer gRPC for internal service-to-service communication for better performance and type safety.

#### VI

| Protocol | Khi nào dùng | Đặc điểm |
|----------|-------------|-----------|
| **REST** | API công cộng, client bên ngoài | Phổ biến, dễ debug, nhiều công cụ |
| **gRPC** | Nội bộ service-to-service | Hiệu năng cao, contract chặt (protobuf), streaming |
| **GraphQL** | Client cần linh hoạt query | Tránh over-fetching, phức tạp hơn |
| **Message Broker (Kafka, RabbitMQ)** | Async, workflow tách rời | At-least-once delivery, cần idempotency |

🟡 **SHOULD**: Ưu tiên gRPC cho giao tiếp nội bộ service-to-service để hiệu năng tốt hơn và type safety.

### 10.2 Backward compatibility is mandatory / Backward compatibility là bắt buộc

#### EN
🔴 **MUST**: Any change to a service's public API must be backward compatible.
V1 consumers must still work when V2 is deployed. Use API versioning when breaking changes are unavoidable.
For API versioning rules, follow `12-Api_conventions`.

#### VI
🔴 **MUST**: Mọi thay đổi API công cộng của service phải backward compatible.
Consumer V1 vẫn phải hoạt động khi V2 được deploy. Dùng API versioning khi breaking change không tránh được.
Về quy tắc versioning API, tuân theo `12-Api_conventions`.

### 10.3 Contract Testing is mandatory for public interfaces / Contract Test bắt buộc cho interface công cộng

#### EN
🔴 **MUST**: Every inter-service API and event schema must have a contract test.
For CDC/Pact implementation details and CI integration, follow `07-Testing_convention` §Contract Testing.

#### VI
🔴 **MUST**: Mọi inter-service API và event schema phải có contract test.
Về chi tiết implement CDC/Pact và tích hợp CI, tuân theo `07-Testing_convention` §Contract Testing.

### 10.4 Idempotency key is required for all write operations / Idempotency key bắt buộc cho mọi write operation

#### EN
🔴 **MUST**: Every write operation that crosses service boundaries must support idempotency.
The caller provides an idempotency key; the receiver deduplicates using that key.
For idempotency implementation, follow `12-Api_conventions`.

#### VI
🔴 **MUST**: Mọi write operation xuyên ranh giới service phải hỗ trợ idempotency.
Caller cung cấp idempotency key; receiver deduplicate bằng key đó.
Về implement idempotency, tuân theo `12-Api_conventions`.

### 10.5 Correlation ID must be propagated across all service calls / Correlation ID phải được forward qua mọi service call

#### EN
🔴 **MUST**: Correlation ID (trace_id, request_id) must be forwarded through every outbound service call — HTTP headers, gRPC metadata, Kafka message headers.
For correlation ID rules, follow `06-Logging_observability_convention` §8.

#### VI
🔴 **MUST**: Correlation ID (trace_id, request_id) phải được forward qua mọi outbound service call — HTTP header, gRPC metadata, Kafka message header.
Về quy tắc correlation ID, tuân theo `06-Logging_observability_convention` §8.

---

## 11. Event-Driven Architecture conventions / Quy ước kiến trúc hướng sự kiện (Tier 2 — microservice only)

### 11.1 Choreography vs Orchestration / Choreography vs Orchestration

#### EN
Choose the coordination pattern based on workflow complexity:

| Pattern | When to use | Trade-offs |
|---------|-------------|------------|
| **Choreography** | Simple flows (2-3 services), each reacts to events independently | Easy to start, hard to trace, can become event spaghetti |
| **Orchestration** | Complex flows, clear sequence, need visibility | Central orchestrator, easier to monitor, single point of logic |

#### VI
Chọn mẫu phối hợp dựa trên độ phức tạp workflow:

| Pattern | Khi nào dùng | Trade-off |
|---------|-------------|-----------|
| **Choreography** | Luồng đơn giản (2-3 service), mỗi service tự phản ứng theo event | Dễ bắt đầu, khó trace, có thể thành event spaghetti |
| **Orchestration** | Luồng phức tạp, trình tự rõ ràng, cần visibility | Orchestrator tập trung, dễ monitor hơn, logic tập trung |

### 11.2 Transactional Outbox Pattern is mandatory for event publishing / Transactional Outbox Pattern bắt buộc khi publish event

#### EN
🔴 **MUST**: When a service saves data to its database AND publishes an event, both must happen atomically.
The Transactional Outbox Pattern solves this:
1. Save the domain data AND the event into the same database transaction (event → `outbox` table)
2. A separate worker reads the `outbox` table and publishes events to the message broker
3. Mark events as published after successful delivery

Without this pattern: if the service crashes after DB save but before event publish, data and events are inconsistent.

#### VI
🔴 **MUST**: Khi service lưu dữ liệu vào DB VÀ publish event, cả hai phải xảy ra nguyên tử.
Transactional Outbox Pattern giải quyết vấn đề này:
1. Lưu domain data VÀ event vào cùng một database transaction (event → bảng `outbox`)
2. Worker riêng đọc bảng `outbox` và publish event lên message broker
3. Đánh dấu event đã published sau khi gửi thành công

Nếu không có pattern này: service crash sau khi lưu DB nhưng trước khi publish event → dữ liệu và event không nhất quán.

```python
# Preferred: Transactional Outbox
async with transaction():
    await order_repo.save(order)
    await outbox_repo.save(OutboxEvent(
        aggregate_id=order.id,
        event_type="order.placed",
        payload=order.to_event_payload()
    ))
# Worker (separate process) polls outbox and publishes to Kafka
```

### 11.3 Every event consumer must be idempotent / Mọi event consumer phải idempotent

#### EN
🔴 **MUST**: Exactly-once delivery is practically impossible in distributed systems.
The realistic guarantee is: **at-least-once delivery + idempotent consumer = effectively-once processing**.
Every consumer must check if it has already processed an event before processing it again.

#### VI
🔴 **MUST**: Exactly-once delivery thực tế không thể đạt được trong hệ phân tán.
Guarantee thực tế là: **at-least-once delivery + idempotent consumer = effectively-once processing**.
Mọi consumer phải kiểm tra xem event đã được xử lý chưa trước khi xử lý lại.

```python
# Preferred: idempotent consumer
async def handle_payment_event(event: PaymentEvent) -> None:
    if await processed_events.exists(event.event_id):
        return  # skip duplicate
    async with transaction():
        await process_payment(event)
        await processed_events.mark(event.event_id)

# Forbidden: no idempotency check
async def handle_payment_event(event: PaymentEvent) -> None:
    await process_payment(event)  # will charge money multiple times if duplicate
```

### 11.4 Event naming convention / Quy ước đặt tên event

#### EN
Events must use past tense + domain format:
- `order.placed`
- `payment.refunded`
- `inventory.reserved`
- `user.registered`

Events represent facts that have already happened.

#### VI
Event phải dùng thì quá khứ + format domain:
- `order.placed`
- `payment.refunded`
- `inventory.reserved`
- `user.registered`

Event đại diện cho sự kiện đã xảy ra.

### 11.5 Event schema must be backward compatible / Schema event phải backward compatible

#### EN
🔴 **MUST**: Event schema changes must be backward compatible.
- Adding new fields: OK (consumer ignores unknown fields)
- Removing or renaming fields: FORBIDDEN (breaks existing consumers)
- Changing field types: FORBIDDEN

Include schema version in the event metadata.

#### VI
🔴 **MUST**: Thay đổi schema event phải backward compatible.
- Thêm field mới: OK (consumer bỏ qua field không biết)
- Xóa hoặc đổi tên field: CẤM (phá hỏng consumer hiện có)
- Thay đổi kiểu field: CẤM

Đưa schema version vào metadata của event.

---

## 12. Saga Pattern conventions / Quy ước Saga Pattern (Tier 2 — microservice only)

### 12.1 When to use Saga / Khi nào dùng Saga

#### EN
Use Saga when a business transaction spans multiple services and requires all-or-nothing semantics.
In monolith: `BEGIN → ... → COMMIT/ROLLBACK` (single transaction).
In microservices: no global transaction → Saga = chain of local transactions + compensating actions.

Example — Order placement:
```
Order → Payment → Inventory → Shipping
If Inventory fails:
  → Payment: refund (compensating action)
  → Order: mark as cancelled (compensating action)
```

#### VI
Dùng Saga khi transaction nghiệp vụ trải qua nhiều service và cần ngữ nghĩa all-or-nothing.
Trong monolith: `BEGIN → ... → COMMIT/ROLLBACK` (một transaction).
Trong microservices: không có global transaction → Saga = chuỗi local transaction + compensating action.

### 12.2 Compensating actions must be defined before implementing the main action / Compensating action phải được định nghĩa trước khi implement action chính

#### EN
🔴 **MUST**: Before implementing any Saga step, the compensating (undo) action must be designed and documented.
A Saga step without a compensating action is a time bomb.

| Step | Action | Compensating Action |
|------|--------|-------------------|
| 1 | Create Order | Cancel Order |
| 2 | Reserve Payment | Refund Payment |
| 3 | Reserve Inventory | Release Inventory |
| 4 | Schedule Shipping | Cancel Shipment |

#### VI
🔴 **MUST**: Trước khi implement bất kỳ bước Saga nào, compensating (undo) action phải được thiết kế và ghi nhận.
Bước Saga không có compensating action là quả bom hẹn giờ.

### 12.3 Choreography Saga vs Orchestration Saga / Choreography Saga vs Orchestration Saga

#### EN

| Type | How it works | When to use |
|------|-------------|-------------|
| **Choreography Saga** | Each service listens for events and publishes next event | Simple flows (2-3 steps), loose coupling |
| **Orchestration Saga** | Central orchestrator tells each service what to do | Complex flows (4+ steps), need visibility and control |

🟡 **SHOULD**: Prefer Orchestration Saga for flows with more than 3 steps — choreography becomes very hard to trace and debug.

#### VI

| Loại | Cách hoạt động | Khi nào dùng |
|------|----------------|-------------|
| **Choreography Saga** | Mỗi service lắng nghe event và publish event tiếp | Luồng đơn giản (2-3 bước), loose coupling |
| **Orchestration Saga** | Orchestrator trung tâm chỉ đạo mỗi service làm gì | Luồng phức tạp (4+ bước), cần visibility và kiểm soát |

🟡 **SHOULD**: Ưu tiên Orchestration Saga cho luồng hơn 3 bước — choreography rất khó trace và debug ở quy mô lớn.

### 12.4 Retry strategy: Exponential Backoff + Jitter / Chiến lược retry: Exponential Backoff + Jitter

#### EN
🔴 **MUST**: Retries in Saga steps must use Exponential Backoff with Jitter.
- Exponential Backoff: wait time doubles each retry (0.5s → 1s → 2s → 4s)
- Jitter: add random delay to prevent retry storms (many services retrying at the same moment)

For detailed retry and error classification rules, follow `05-Error_handling_convention`.

#### VI
🔴 **MUST**: Retry trong bước Saga phải dùng Exponential Backoff với Jitter.
- Exponential Backoff: thời gian chờ tăng gấp đôi mỗi lần retry (0.5s → 1s → 2s → 4s)
- Jitter: thêm delay ngẫu nhiên để tránh retry storm (nhiều service retry cùng lúc)

Về quy tắc retry và phân loại lỗi chi tiết, tuân theo `05-Error_handling_convention`.

```python
# Preferred: Exponential Backoff + Jitter
retry_config = RetryPolicy(
    initial_delay=0.5,
    multiplier=2,
    max_attempts=3,
    jitter=True  # adds random 0-50% to each delay
)

# Forbidden: fixed retry without backoff
for i in range(3):
    result = await call_service()  # all retries hit service at same intervals
```

---

## 13. Resilience Pattern conventions / Quy ước mẫu chống chịu lỗi (Tier 2 — microservice only)

### 13.1 Circuit Breaker is mandatory for all external service calls / Circuit Breaker bắt buộc cho mọi external service call

#### EN
🔴 **MUST**: Every outbound call to an external service must be wrapped in a Circuit Breaker.
A Circuit Breaker prevents cascading failures by stopping calls to a failing service:

```
Closed (normal) → failure threshold exceeded → Open (all calls fail fast)
  → timeout expires → Half-Open (allow one test call)
    → success → Closed  |  failure → Open again
```

#### VI
🔴 **MUST**: Mọi outbound call tới external service phải được bọc trong Circuit Breaker.
Circuit Breaker ngăn lỗi lan rộng bằng cách dừng gọi service đang lỗi:

```python
# Preferred: Circuit Breaker wraps external call
with circuit_breaker("payment-service", failure_threshold=5, timeout=30):
    result = await payment_client.charge(amount)

# Forbidden: no protection
result = await payment_client.charge(amount)  # if payment-service is down, this hangs/crashes repeatedly
```

### 13.2 Retry only for transient errors / Chỉ retry cho lỗi tạm thời

#### EN
🔴 **MUST**: Retries are only for transient (temporary) errors.
- **Transient** (RETRY): network timeout, connection refused, 503 Service Unavailable
- **Non-transient** (DO NOT RETRY): 400 Bad Request, 404 Not Found, validation error, business rule violation

For error classification details, follow `05-Error_handling_convention`.

#### VI
🔴 **MUST**: Retry chỉ dành cho lỗi tạm thời (transient).
- **Transient** (RETRY): network timeout, connection refused, 503 Service Unavailable
- **Non-transient** (KHÔNG RETRY): 400 Bad Request, 404 Not Found, lỗi validation, vi phạm business rule

Về chi tiết phân loại lỗi, tuân theo `05-Error_handling_convention`.

### 13.3 Bulkhead: resource isolation / Bulkhead: cô lập tài nguyên

#### EN
🟡 **SHOULD**: Use the Bulkhead pattern to isolate resources for high-risk or high-load service calls.
Each external service call should have its own thread pool or connection pool so that one slow service does not exhaust resources needed by others.

#### VI
🟡 **SHOULD**: Dùng Bulkhead pattern để cô lập tài nguyên cho các service call rủi ro cao hoặc tải nặng.
Mỗi external service call nên có thread pool hoặc connection pool riêng để một service chậm không chiếm hết tài nguyên cần cho service khác.

### 13.4 Graceful degradation and fallback / Degradation và fallback thông minh

#### EN
🟡 **SHOULD**: Services must have defined fallback behavior when a dependency is unavailable:
- Return cached data when the upstream service is down
- Return a reduced-functionality response instead of a full error
- Queue the operation for later processing

#### VI
🟡 **SHOULD**: Service phải có hành vi fallback khi dependency không khả dụng:
- Trả về dữ liệu từ cache khi upstream service bị down
- Trả về response chức năng giảm thay vì lỗi hoàn toàn
- Đưa thao tác vào hàng đợi để xử lý sau

### 13.5 Chaos Testing / Kiểm thử hỗn loạn

#### EN
🟡 **SHOULD**: Periodically inject controlled failures in staging environments to verify resilience:
- Simulate network latency between services
- Kill service instances randomly
- Inject disk I/O failures
- Introduce message broker delays

Requirements:
- Chaos Testing must NEVER run in production without explicit approval
- Results must be logged and tracked as part of the resilience report
- Tests must not require human intervention to run

#### VI
🟡 **SHOULD**: Định kỳ inject lỗi có kiểm soát trong môi trường staging để xác minh resilience:
- Mô phỏng network latency giữa các service
- Kill service instance ngẫu nhiên
- Inject lỗi disk I/O
- Tạo delay trên message broker

Yêu cầu:
- Chaos Testing KHÔNG BAO GIỜ chạy trên production mà không có approval rõ ràng
- Kết quả phải được log và theo dõi trong resilience report
- Test không được cần human intervention để chạy

---

## 14. Service Mesh conventions / Quy ước Service Mesh (Tier 2 — microservice only)

### 14.1 When to adopt a Service Mesh / Khi nào áp dụng Service Mesh

#### EN
🔵 **MAY**: Consider adopting a Service Mesh when:
- The system has ≥10 services
- Zero-trust security is required (mTLS everywhere)
- Uniform traffic management is needed (retry, timeout, circuit breaker at infra level)
- The team wants to remove cross-cutting concerns from application code

Do NOT adopt a Service Mesh for a small number of services — the operational overhead outweighs the benefits.

#### VI
🔵 **MAY**: Cân nhắc áp dụng Service Mesh khi:
- Hệ thống có ≥10 service
- Yêu cầu zero-trust security (mTLS mọi nơi)
- Cần quản lý traffic đồng nhất (retry, timeout, circuit breaker ở tầng infra)
- Team muốn loại bỏ cross-cutting concerns khỏi application code

KHÔNG áp dụng Service Mesh cho số lượng service nhỏ — overhead vận hành lớn hơn lợi ích.

### 14.2 Mutual TLS (mTLS) in production / Mutual TLS (mTLS) trong production

#### EN
🔴 **MUST** (when using Service Mesh): All service-to-service communication in production must use mTLS.
mTLS ensures both caller and receiver authenticate each other — no impersonation possible.

Without Service Mesh: use application-level mTLS or a shared certificate authority.

#### VI
🔴 **MUST** (khi dùng Service Mesh): Mọi giao tiếp service-to-service trong production phải dùng mTLS.
mTLS đảm bảo cả caller và receiver xác thực lẫn nhau — không thể giả mạo.

Khi không dùng Service Mesh: dùng mTLS ở tầng application hoặc shared certificate authority.

### 14.3 Do not duplicate Mesh capabilities in application code / Không lặp lại khả năng Mesh trong code ứng dụng

#### EN
🔴 **MUST** (when using Service Mesh): If the Service Mesh already handles retry, timeout, and circuit breaker, do NOT implement them again in application code.
Duplication causes:
- Double retries (exponential explosion)
- Conflicting timeout values
- Harder debugging

Document clearly which resilience features are handled by the Mesh vs by application code.

#### VI
🔴 **MUST** (khi dùng Service Mesh): Nếu Service Mesh đã xử lý retry, timeout, và circuit breaker, KHÔNG implement lại trong application code.
Lặp lại gây ra:
- Double retry (bùng nổ exponential)
- Timeout value xung đột
- Debug khó hơn

Ghi nhận rõ ràng tính năng resilience nào do Mesh xử lý vs do application code xử lý.

### 14.4 Service Mesh technology guide / Hướng dẫn chọn công nghệ Service Mesh

#### EN

| Technology | Strengths | When to choose |
|------------|-----------|----------------|
| **Istio** | Feature-rich, mature ecosystem, advanced traffic management | Large-scale systems, need fine-grained traffic control, already on Kubernetes |
| **Linkerd** | Lightweight, simpler operations, lower resource footprint | Teams prioritizing simplicity, smaller clusters, fast adoption needed |
| **Consul Connect** | Multi-platform (K8s + VM), service discovery built-in | Hybrid environments, HashiCorp ecosystem |

#### VI

| Công nghệ | Thế mạnh | Khi nào chọn |
|-----------|----------|-------------|
| **Istio** | Nhiều tính năng, hệ sinh thái trưởng thành, quản lý traffic nâng cao | Hệ thống quy mô lớn, cần kiểm soát traffic chi tiết, đã dùng Kubernetes |
| **Linkerd** | Nhẹ, vận hành đơn giản hơn, tốn ít tài nguyên hơn | Team ưu tiên đơn giản, cluster nhỏ hơn, cần áp dụng nhanh |
| **Consul Connect** | Đa nền tảng (K8s + VM), service discovery tích hợp | Môi trường hybrid, hệ sinh thái HashiCorp |

### 14.5 Observability integration with Service Mesh / Tích hợp Observability với Service Mesh

#### EN
🟡 **SHOULD**: Service Mesh provides automatic telemetry (latency, error rate, request volume per service).
Integrate Mesh telemetry with the centralized observability stack.
For observability conventions, follow `06-Logging_observability_convention`.

#### VI
🟡 **SHOULD**: Service Mesh cung cấp telemetry tự động (latency, error rate, request volume mỗi service).
Tích hợp telemetry của Mesh vào stack observability tập trung.
Về quy ước observability, tuân theo `06-Logging_observability_convention`.

---

## 15. Anti-patterns / Mẫu xấu cần tránh

### EN

| Anti-pattern | Consequence | How to detect |
|-------------|-------------|---------------|
| **Shared database** | Schema coupling → one change breaks many services | Multiple services have connection strings to the same DB |
| **Synchronous chain call > 3 hops** | Latency explosion, fragile chain | Trace shows Service A → B → C → D → E synchronously |
| **Distributed monolith** | Services are small but tightly coupled, must deploy together | Cannot deploy one service without coordinating with others |
| **Entity Service Trap** | Business logic scattered across callers | Service only does CRUD, callers contain all logic |
| **Saga without compensating actions** | Inconsistent state after partial failure | Saga step has no documented undo operation |
| **Event spaghetti** | Untrackable event chains, no one knows the full flow | >5 services in a choreography chain with no diagram |
| **God module** | One module handles unrelated responsibilities | `common/` or `utils/` grows without limit |
| **Cross-module direct DB query** | Breaking data ownership | SQL joins across module tables |

### VI

| Anti-pattern | Hậu quả | Cách nhận ra |
|-------------|---------|-------------|
| **Shared database** | Schema coupling → một thay đổi phá nhiều service | Nhiều service có connection string đến cùng DB |
| **Chuỗi gọi sync > 3 hops** | Latency bùng nổ, chuỗi dễ gãy | Trace cho thấy Service A → B → C → D → E đồng bộ |
| **Distributed monolith** | Service nhỏ nhưng tightly coupled, phải deploy cùng nhau | Không thể deploy một service mà không phối hợp với service khác |
| **Entity Service Trap** | Business logic phân tán sang các caller | Service chỉ làm CRUD, caller chứa mọi logic |
| **Saga thiếu compensating action** | State không nhất quán sau lỗi một phần | Bước Saga không có thao tác undo được ghi nhận |
| **Event spaghetti** | Chuỗi event không theo dõi được | >5 service trong choreography chain mà không có diagram |
| **God module** | Một module ôm nhiều trách nhiệm không liên quan | `common/` hoặc `utils/` phình to không giới hạn |
| **Query DB chéo module** | Phá vỡ data ownership | SQL join giữa bảng của các module khác nhau |

---

## 16. Review checklist / Checklist review

### EN
When reviewing architecture or service design, check:

**Tier 1 (all projects):**
- [ ] Is each module organized around a business capability (not technical layer)?
- [ ] Do modules communicate only through interfaces/contracts?
- [ ] Does each module own its own data exclusively?
- [ ] Is there no cross-module direct data access?
- [ ] Is correlation ID generated at entry point and propagated through all layers?
- [ ] Are heavy/slow tasks designed for async execution?
- [ ] Is the application stateless (no in-process session state)?

**Tier 2 (microservices only):**
- [ ] Does each service align with one Bounded Context?
- [ ] Is the service named after a capability (not an entity)?
- [ ] Does each service have its own database?
- [ ] Is there no cross-service JOIN or direct DB query?
- [ ] Do all external service calls have a Circuit Breaker?
- [ ] Is every event consumer idempotent?
- [ ] Is Transactional Outbox used when DB write + event publish must be atomic?
- [ ] Are compensating actions defined for every Saga step?
- [ ] Are contract tests written for every public inter-service interface?
- [ ] Is correlation ID forwarded through all outbound service calls?
- [ ] Are event schemas backward compatible?

### VI
Khi review kiến trúc hoặc thiết kế service, cần kiểm tra:

**Tier 1 (mọi dự án):**
- [ ] Mỗi module có tổ chức theo năng lực nghiệp vụ không (không phải tầng kỹ thuật)?
- [ ] Module có chỉ giao tiếp qua interface/contract không?
- [ ] Mỗi module có sở hữu dữ liệu riêng không?
- [ ] Có truy cập dữ liệu chéo module trực tiếp không?
- [ ] Correlation ID có được tạo từ entry point và truyền qua mọi layer không?
- [ ] Task nặng/chậm có được thiết kế cho async execution không?
- [ ] Ứng dụng có stateless không (không lưu session state trong process)?

**Tier 2 (chỉ microservices):**
- [ ] Mỗi service có khớp với một Bounded Context không?
- [ ] Service có được đặt tên theo capability (không phải entity) không?
- [ ] Mỗi service có database riêng không?
- [ ] Có JOIN chéo service hoặc query DB trực tiếp không?
- [ ] Mọi external service call có Circuit Breaker không?
- [ ] Mọi event consumer có idempotent không?
- [ ] Transactional Outbox có được dùng khi DB write + event publish phải atomic không?
- [ ] Compensating action có được định nghĩa cho mọi bước Saga không?
- [ ] Contract test có được viết cho mọi inter-service interface công cộng không?
- [ ] Correlation ID có được forward qua mọi outbound service call không?
- [ ] Event schema có backward compatible không?

---

## 17. Definition of done / Điều kiện hoàn thành

### EN
A service or module is architecture-compliant only if:

**Tier 1:**
- modules are organized by business capability
- modules communicate through interfaces
- data ownership is clear and enforced
- correlation ID is propagated
- heavy tasks use async execution
- application is stateless
- caching has TTL and invalidation strategy
- connection pooling is configured

**Tier 2 (microservices only):**
- service boundary aligns with Bounded Context
- database is owned exclusively by one service
- no cross-service direct DB access exists
- Circuit Breaker wraps all external calls
- event consumers are idempotent
- Transactional Outbox is used for atomic DB + event operations
- compensating actions are defined for all Saga steps
- contract tests exist for public interfaces
- event schemas are backward compatible
- mTLS is enabled in production (when Service Mesh is used)

### VI
Một service hoặc module chỉ được coi là tuân thủ quy ước kiến trúc khi:

**Tier 1:**
- module được tổ chức theo năng lực nghiệp vụ
- module giao tiếp qua interface
- quyền sở hữu dữ liệu rõ ràng và được thực thi
- correlation ID được lan truyền
- task nặng dùng async execution
- ứng dụng là stateless
- caching có TTL và chiến lược invalidation
- connection pooling được cấu hình

**Tier 2 (chỉ microservices):**
- ranh giới service khớp với Bounded Context
- database được sở hữu độc quyền bởi một service
- không có truy cập DB chéo service trực tiếp
- Circuit Breaker bọc mọi external call
- event consumer là idempotent
- Transactional Outbox được dùng cho thao tác atomic DB + event
- compensating action được định nghĩa cho mọi bước Saga
- contract test có cho mọi interface công cộng
- event schema backward compatible
- mTLS được bật trong production (khi dùng Service Mesh)
