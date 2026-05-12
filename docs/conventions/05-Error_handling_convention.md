# 05-Error-Handling / Quy ước xử lý lỗi

## 1. Purpose / Mục đích

**EN**  
This document defines how errors must be classified, raised, propagated, translated, logged, and exposed across the system.

**VI**  
Tài liệu này định nghĩa cách lỗi phải được phân loại, phát sinh, lan truyền, chuyển đổi, ghi log, và đưa ra ngoài trong toàn hệ thống.

---

## 2. Scope / Phạm vi

**EN**  
This document applies to:
- validation errors
- domain and business-rule errors
- application and workflow errors
- infrastructure and integration errors
- unexpected system failures
- error propagation across layers
- error logging and external error exposure

**VI**  
Tài liệu này áp dụng cho:
- lỗi validation
- lỗi domain và business rule
- lỗi application và workflow
- lỗi infrastructure và integration
- lỗi hệ thống không mong muốn
- việc lan truyền lỗi giữa các layer
- việc log lỗi và đưa lỗi ra ngoài

---

## 3. Core principle / Nguyên tắc cốt lõi

**EN**  
Errors must be handled clearly, consistently, and at the correct architectural boundary.  
The system must fail loudly for unexpected problems and fail predictably for expected business and validation conditions.

**VI**  
Lỗi phải được xử lý rõ ràng, nhất quán, và tại đúng ranh giới kiến trúc.  
Hệ thống phải fail rõ ràng với lỗi không mong muốn và fail có thể dự đoán được với các trường hợp validation hoặc business rule đã biết trước.

---

## 4. Error categories / Phân loại lỗi

### 4.1 Validation errors / Lỗi validation

**EN**  
Validation errors occur when input data, config, or payloads do not satisfy required structure or format.

**VI**  
Lỗi validation xảy ra khi dữ liệu đầu vào, config, hoặc payload không thỏa mãn cấu trúc hoặc định dạng yêu cầu.

**Examples / Ví dụ**
- missing required field
- invalid email format
- invalid config value
- malformed request body

---

### 4.2 Domain errors / Lỗi domain

**EN**  
Domain errors occur when business rules or invariants are violated.

**VI**  
Lỗi domain xảy ra khi luật nghiệp vụ hoặc invariant bị vi phạm.

**Examples / Ví dụ**
- insufficient balance
- invalid order state transition
- user is not allowed to perform an action

---

### 4.3 Application errors / Lỗi application

**EN**  
Application errors occur when a use case or workflow cannot be completed correctly.

**VI**  
Lỗi application xảy ra khi một use case hoặc workflow không thể hoàn thành đúng cách.

**Examples / Ví dụ**
- workflow dependency missing
- required resource not found during orchestration
- use case cannot proceed in the current state

---

### 4.4 Infrastructure errors / Lỗi hạ tầng

**EN**  
Infrastructure errors occur in technical integrations such as databases, APIs, queues, filesystems, and external services.

**VI**  
Lỗi hạ tầng xảy ra ở các tích hợp kỹ thuật như database, API, queue, filesystem, và dịch vụ bên ngoài.

**Examples / Ví dụ**
- database timeout
- external API unavailable
- permission denied on filesystem
- queue publish failure

---

### 4.5 Unexpected errors / Lỗi không mong muốn

**EN**  
Unexpected errors represent bugs, unhandled states, or failures that were not part of the expected control flow.

**VI**  
Lỗi không mong muốn là bug, trạng thái chưa được xử lý, hoặc failure không nằm trong luồng điều khiển dự kiến.

**Examples / Ví dụ**
- `NoneType` errors caused by a defect
- unhandled branch in logic
- programming errors
- invalid assumptions in code

---

## 5. Layer responsibilities / Trách nhiệm theo layer

### 5.1 Domain layer / Lớp domain

**EN**  
The domain layer may raise business-rule and invariant-related errors only.  
It must not raise framework-specific, transport-specific, or infrastructure-specific exceptions.

**VI**  
Lớp domain chỉ được raise lỗi liên quan đến luật nghiệp vụ và invariant.  
Không được raise exception đặc thù framework, transport, hoặc hạ tầng.

**Allowed / Được phép**
- `InsufficientBalanceError`
- `InvalidOrderStateError`
- `PolicyViolationError`

**Forbidden / Bị cấm**
- `HTTPException`
- raw database exceptions
- transport-layer response errors

---

### 5.2 Application layer / Lớp application

**EN**  
The application layer coordinates workflows and may catch domain and infrastructure errors to translate them into use-case-level meaning.

**VI**  
Lớp application điều phối workflow và có thể catch lỗi từ domain và infrastructure để chuyển thành ngữ nghĩa phù hợp với use case.

**Responsibilities / Trách nhiệm**
- orchestrate use cases
- add use-case context to failures
- decide whether to propagate, translate, or stop execution

---

### 5.3 Interface layer / Lớp interface

**EN**  
The interface layer is responsible for mapping internal errors to external responses such as HTTP responses, CLI exit codes, or job status outcomes.

**VI**  
Lớp interface chịu trách nhiệm map lỗi nội bộ sang response bên ngoài như HTTP response, CLI exit code, hoặc job status outcome.

**Responsibilities / Trách nhiệm**
- map error to user-facing response
- decide status code or exit code
- keep external error payloads safe and stable

---

### 5.4 Infrastructure layer / Lớp infrastructure

**EN**  
The infrastructure layer may catch vendor- or library-specific exceptions and translate them into infrastructure-level errors meaningful to the rest of the system.

**VI**  
Lớp infrastructure có thể catch exception đặc thù thư viện hoặc nhà cung cấp và chuyển chúng thành lỗi hạ tầng có ý nghĩa với phần còn lại của hệ thống.

**Responsibilities / Trách nhiệm**
- isolate vendor-specific errors
- translate technical failures
- avoid leaking raw implementation details upward unless necessary

---

## 6. Exception design rules / Luật thiết kế exception

### 6.1 Use custom exceptions where semantics matter / Dùng custom exception khi ngữ nghĩa quan trọng

**EN**  
Use explicit custom exception types when the caller must distinguish one failure class from another.

**VI**  
Dùng custom exception rõ ràng khi caller cần phân biệt loại thất bại này với loại khác.

---

### 6.2 Exception names must be explicit / Tên exception phải rõ nghĩa

**EN**  
Exception class names must use `PascalCase` and end with `Error`.

**VI**  
Tên class exception phải dùng `PascalCase` và kết thúc bằng `Error`.

**Examples / Ví dụ**
- `ConfigError`
- `ValidationError`
- `ExternalServiceTimeoutError`
- `UserCreationError`

---

### 6.3 Avoid vague exception names / Tránh tên exception mơ hồ

**EN**  
Avoid generic names such as `AppError`, `GeneralError`, or `SomethingWrongError` unless they are intentionally used as abstract base types.

**VI**  
Tránh các tên chung chung như `AppError`, `GeneralError`, hoặc `SomethingWrongError`, trừ khi chúng được dùng có chủ đích như abstract base type.

---

### 6.4 Use exception hierarchy intentionally / Dùng cây phân cấp exception có chủ đích

**EN**  
Use base exception types only when they help grouping related failures meaningfully.

**VI**  
Chỉ dùng base exception type khi nó thực sự giúp gom các lỗi liên quan theo cách có ý nghĩa.

**Example / Ví dụ**
```python
class DomainError(Exception):
    pass

class InsufficientBalanceError(DomainError):
    pass

class InvalidOrderStateError(DomainError):
    pass
```

---

## 7. Catching and propagation rules / Luật bắt và lan truyền lỗi

### 7.1 Catch only when you can act meaningfully / Chỉ catch khi có thể xử lý có ý nghĩa

**EN**  
Do not catch exceptions unless you can:
- recover safely
- translate them at a boundary
- add necessary context
- clean up resources

**VI**  
Không catch exception nếu không thể:
- phục hồi an toàn
- chuyển đổi lỗi tại một boundary
- thêm ngữ cảnh cần thiết
- dọn dẹp tài nguyên

---

### 7.2 Do not swallow exceptions silently / Không được nuốt lỗi âm thầm

**EN**  
Silent exception swallowing is forbidden.

**VI**  
Cấm nuốt lỗi âm thầm.

**Forbidden / Bị cấm**
```python
try:
    do_work()
except Exception:
    pass
```

---

### 7.3 Avoid broad exception handling unless required at boundaries / Tránh catch quá rộng trừ khi ở boundary

**EN**  
`except Exception` should be avoided except at explicit outer boundaries such as top-level job runners, request middleware, or process supervisors.

**VI**  
`except Exception` nên tránh, trừ khi ở boundary ngoài cùng như job runner cấp cao nhất, request middleware, hoặc process supervisor.

---

### 7.4 Re-raise with context, not noise / Raise lại với ngữ cảnh, không tạo nhiễu

**EN**  
When re-raising, add meaningful context or translate to a more appropriate exception type.

**VI**  
Khi raise lại, phải thêm ngữ cảnh có ý nghĩa hoặc chuyển sang loại exception phù hợp hơn.

**Preferred / Ưu tiên**
```python
try:
    repository.save(user)
except TimeoutError as exc:
    raise UserPersistenceError(
        "Failed to save user due to repository timeout"
    ) from exc
```

**Avoid / Tránh**
```python
try:
    repository.save(user)
except Exception:
    raise Exception("Something failed")
```

---

### 7.5 Preserve root cause when translating errors / Giữ lại nguyên nhân gốc khi chuyển lỗi

**EN**  
When translating one exception into another, preserve the original exception using chaining.

**VI**  
Khi chuyển một exception sang exception khác, phải giữ lại nguyên nhân gốc bằng cơ chế chaining.

**Preferred / Ưu tiên**
```python
try:
    partner_client.send(payload)
except TimeoutError as exc:
    raise ExternalServiceTimeoutError("Partner request timed out") from exc
```

---

## 8. Translation rules / Luật chuyển đổi lỗi

### 8.1 Translate technical exceptions at the technical boundary / Chuyển lỗi kỹ thuật tại boundary kỹ thuật

**EN**  
Infrastructure-specific exceptions should be translated inside infrastructure or application boundaries before being exposed upward.

**VI**  
Các lỗi đặc thù kỹ thuật phải được chuyển đổi ngay tại boundary của infrastructure hoặc application trước khi đi lên trên.

**Example / Ví dụ**
```python
try:
    response = requests.get(url, timeout=5)
except requests.Timeout as exc:
    raise ExternalServiceTimeoutError("Partner API request timed out") from exc
```

---

### 8.2 Map internal errors to safe external responses / Map lỗi nội bộ sang response ngoài an toàn

**EN**  
External responses must not expose sensitive internals such as raw SQL errors, stack traces, secret values, or vendor-specific details.

**VI**  
Response đưa ra ngoài không được làm lộ nội bộ nhạy cảm như raw SQL error, stack trace, secret value, hoặc chi tiết đặc thù nhà cung cấp.

**Preferred / Ưu tiên**
- return stable error codes
- return safe human-readable messages
- keep detailed diagnostics in internal logs only

**Ưu tiên**
- trả về error code ổn định
- trả về message an toàn, dễ hiểu
- giữ chi tiết chẩn đoán trong log nội bộ

---

### 8.3 Do not leak infrastructure semantics into domain language / Không làm rò ngữ nghĩa hạ tầng vào domain

**EN**  
Database, queue, SDK, or HTTP-client specifics must not become part of domain exception language.

**VI**  
Chi tiết database, queue, SDK, hoặc HTTP client không được trở thành một phần của ngôn ngữ exception ở domain.

**Avoid / Tránh**
- `DatabaseBalanceError`
- `SqlAlchemyOrderStateError`

---

## 9. Logging rules for errors / Luật log khi có lỗi

### 9.1 Log errors once at the right boundary / Log lỗi một lần tại đúng boundary

**EN**  
Prefer logging errors at the boundary where they are handled or emitted externally.  
Do not log the same error redundantly at every layer.

For the complete boundary-logging rules and examples, follow `06-Logging_observability_convention` §4.7.

**VI**  
Ưu tiên log lỗi tại boundary nơi lỗi được xử lý hoặc đưa ra ngoài.  
Không log trùng cùng một lỗi ở mọi layer.

Về quy tắc log tại boundary đầy đủ và ví dụ, tuân theo `06-Logging_observability_convention` §4.7.

---

### 9.2 Log context, not secrets / Log ngữ cảnh, không log secret

**EN**  
Error logs should include actionable context (e.g. entity IDs, operation names) but must never expose secrets.  
For the full list of prohibited data in logs, follow `08-Security_secrets_conventions` §7.

**VI**  
Log lỗi nên chứa ngữ cảnh hữu ích (ví dụ entity ID, tên thao tác) nhưng tuyệt đối không được lộ secret.  
Về danh sách đầy đủ dữ liệu bị cấm trong log, tuân theo `08-Security_secrets_conventions` §7.

---

### 9.3 Unexpected errors must remain observable / Lỗi không mong muốn phải còn khả năng quan sát

**EN**  
Unexpected errors must be logged with enough context for diagnosis and must not disappear behind generic return values.

**VI**  
Lỗi không mong muốn phải được log với đủ ngữ cảnh để chẩn đoán và không được biến mất sau các giá trị trả về chung chung.

---

## 10. External exposure rules / Luật đưa lỗi ra ngoài

### 10.1 External clients must receive stable error semantics / Client bên ngoài phải nhận ngữ nghĩa lỗi ổn định

**EN**  
External consumers should receive stable error codes, categories, and messages rather than raw internal exceptions.

**VI**  
Client bên ngoài nên nhận error code, category, và message ổn định thay vì raw internal exception.

---

### 10.2 Human-readable does not mean over-detailed / Dễ hiểu không có nghĩa là quá chi tiết

**EN**  
User-facing error messages should be understandable but must not reveal internals unnecessary for the caller.

**VI**  
Message lỗi hướng người dùng phải dễ hiểu nhưng không được để lộ chi tiết nội bộ không cần thiết cho caller.

---

### 10.3 Different audiences may require different error detail levels / Mỗi đối tượng cần mức chi tiết lỗi khác nhau

**EN**  
Internal logs, operational dashboards, and external client responses may carry different levels of detail.

**VI**  
Log nội bộ, dashboard vận hành, và response ra ngoài có thể mang các mức chi tiết lỗi khác nhau.

---

## 11. Resilience Patterns (Microservices Tier 2) / Mẫu chống chịu lỗi (Tier 2)

> ⚠️ Agent: Chỉ áp dụng section này sau khi user xác nhận kiến trúc Microservices.
> Xem `16-System_architecture_conventions.md` §3 để biết tiêu chí.

### 11.1 Retry for transient errors only / Chỉ retry cho lỗi tạm thời

**EN**  
`Transient` errors (network timeouts, 503s) SHOULD be retried using Exponential Backoff and Jitter.  
`Non-transient` errors (400 validation, 404 not found) MUST NOT be retried.  
For microservices, see `16-System_architecture_conventions.md` §13 for full resilience rules.

**VI**  
Lỗi `Transient` (network timeout, 503) NÊN được retry dùng Exponential Backoff và Jitter.  
Lỗi `Non-transient` (400 validation, 404 not found) KHÔNG ĐƯỢC retry.  
Với microservices, xem `16-System_architecture_conventions.md` §13 để có quy tắc resilience đầy đủ.

---

### 11.2 Circuit Breaker for cascading failure prevention / Circuit Breaker chống lỗi dây chuyền

**EN**  
External service calls in distributed systems MUST use a Circuit Breaker pattern to fail fast when downstream is degraded, protecting local resources.

**VI**  
Gọi hàm ra dịch vụ ngoài trong hệ thống phân tán PHẢI dùng mẫu Circuit Breaker để fail fast khi downstream bị suy giảm, nhằm bảo vệ tài nguyên local.

---

## 12. Anti-patterns / Mẫu xấu cần tránh

**EN**  
Avoid:
- `except Exception: pass`
- `except Exception: return False` without context
- raising framework-specific exceptions in domain logic
- leaking raw infrastructure errors to external clients
- using exceptions for normal control flow when a clear non-exception path exists
- logging the same failure multiple times across layers
- converting every failure into the same generic exception
- hiding defects behind business-style return values

**VI**  
Tránh:
- `except Exception: pass`
- `except Exception: return False` mà không có ngữ cảnh
- raise exception đặc thù framework trong domain logic
- làm lộ raw infrastructure error ra client
- dùng exception cho luồng điều khiển bình thường khi đã có cách rõ ràng hơn
- log lặp cùng một failure ở nhiều layer
- chuyển mọi failure thành cùng một generic exception
- che bug bằng các giá trị trả về kiểu business outcome

---

## 12. Review checklist / Checklist review

**EN**  
When reviewing error handling, check:
- Is the error category clear?
- Is the error handled at the right layer?
- Is the exception type explicit enough?
- Is any exception being swallowed?
- Is any sensitive internal detail leaked outward?
- Is logging done once and with enough context?
- Is root cause preserved when errors are translated?
- Are framework exceptions kept out of domain logic?

**VI**  
Khi review phần xử lý lỗi, cần kiểm tra:
- Loại lỗi có rõ không?
- Lỗi có được xử lý ở đúng layer không?
- Loại exception có đủ rõ nghĩa không?
- Có exception nào đang bị nuốt không?
- Có chi tiết nội bộ nhạy cảm nào bị lộ ra ngoài không?
- Việc log có đúng một lần và đủ ngữ cảnh không?
- Nguyên nhân gốc có được giữ lại khi translate lỗi không?
- Exception của framework có bị lẫn vào domain logic không?

---

## 13. Definition of done / Điều kiện hoàn thành

**EN**  
A module is error-handling compliant only if:
- expected failures are classified clearly
- exceptions are raised at the right layer
- exceptions are caught only when meaningful action is possible
- no silent swallowing exists
- internal errors are translated safely at boundaries
- logs provide context without leaking sensitive information
- root causes are preserved where translation occurs
- external consumers receive stable and safe error semantics

**VI**  
Một module chỉ được coi là tuân thủ quy ước xử lý lỗi khi:
- các failure dự kiến được phân loại rõ
- exception được raise ở đúng layer
- exception chỉ bị catch khi có thể xử lý có ý nghĩa
- không có nuốt lỗi âm thầm
- lỗi nội bộ được chuyển đổi an toàn tại các boundary
- log có đủ ngữ cảnh mà không làm lộ thông tin nhạy cảm
- nguyên nhân gốc được giữ lại ở nơi có chuyển đổi lỗi
- phía ngoài nhận được ngữ nghĩa lỗi ổn định và an toàn
