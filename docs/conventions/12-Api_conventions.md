# 12-API-Conventions / Quy ước thiết kế và xây dựng API

## 1. Purpose / Mục đích

### EN
This document defines the conventions for designing and implementing APIs so that they remain consistent, stable, scalable, and developer-friendly.

### VI
Tài liệu này định nghĩa các quy ước để thiết kế và xây dựng API sao cho nhất quán, ổn định, dễ mở rộng, và thân thiện với developer.

## 2. Scope / Phạm vi

### EN
This document applies to:

- public APIs
- internal service APIs
- REST-style resource APIs
- request and response semantics
- versioning
- pagination
- idempotency
- API consistency and usability

### VI
Tài liệu này áp dụng cho:

- public API
- API nội bộ giữa các service
- API kiểu resource/REST
- ngữ nghĩa request và response
- versioning
- pagination
- idempotency
- tính nhất quán và khả dụng của API

## 3. Core principles / Nguyên tắc cốt lõi

### 3.1 APIs must be resource-oriented / API phải xoay quanh tài nguyên

#### EN
APIs should be designed around resources and their relationships, not around arbitrary action names.

#### VI
API nên được thiết kế xoay quanh tài nguyên và quan hệ giữa các tài nguyên, không nên xoay quanh tên hành động tùy ý.

### 3.2 HTTP methods carry semantics / HTTP method mang ngữ nghĩa

#### EN
The meaning of an endpoint must come from the combination of resource path and HTTP method.

#### VI
Ý nghĩa của một endpoint phải đến từ sự kết hợp giữa resource path và HTTP method.

### 3.3 APIs must remain stable over time / API phải giữ được tính ổn định theo thời gian

#### EN
APIs must evolve without breaking existing consumers unexpectedly.

#### VI
API phải phát triển mà không làm gãy client đang dùng một cách bất ngờ.

### 3.4 APIs must be developer-friendly / API phải thân thiện với developer

#### EN
An API should be easy to understand, predictable to use, and consistent in naming, behavior, and error handling.

#### VI
API phải dễ hiểu, dễ đoán trong cách dùng, và nhất quán về tên gọi, hành vi, và xử lý lỗi.

## 4. Resource-oriented URL design / Quy ước thiết kế URL theo tài nguyên

### 4.1 Use nouns, not verbs, in paths / Dùng danh từ, không dùng động từ, trong path

#### EN
Paths should represent resources, not actions.

#### VI
Path phải biểu diễn tài nguyên, không biểu diễn hành động.

#### Preferred / Ưu tiên
- GET /v1/posts
- POST /v1/posts
- GET /v1/posts/{post_id}
- POST /v1/posts/{post_id}/comments

#### Avoid / Tránh
- /getPosts
- /createPost
- /doComment
- /executePostAction

### 4.2 Keep resources clearly separated / Tách tài nguyên rõ ràng

#### EN
Each resource should have a clear boundary and responsibility.

#### VI
Mỗi tài nguyên phải có ranh giới và trách nhiệm rõ ràng.

#### Examples / Ví dụ
- /posts
- /comments
- /users
- /feeds

#### VI
Không gom các concern không liên quan vào một endpoint chung chung.

### 4.3 Use nested resources only when the relationship is real / Chỉ dùng nested resource khi quan hệ thực sự rõ ràng

#### EN
Nested paths are appropriate when a child resource is naturally scoped by its parent.

#### VI
Nested path phù hợp khi tài nguyên con thực sự được định danh trong phạm vi của tài nguyên cha.

#### Preferred / Ưu tiên
- /posts/{post_id}/comments
- /users/{user_id}/feeds

#### Avoid / Tránh
- nested paths quá sâu hoặc không phản ánh quan hệ thật
- /system/{id}/operations/{op_id}/steps/{step_id}/details

## 5. HTTP method conventions / Quy ước về HTTP method

### 5.1 Use methods according to standard semantics / Dùng method theo đúng ngữ nghĩa chuẩn

#### EN
Use HTTP methods consistently:

- GET for retrieval
- POST for creation
- PUT for full replacement
- PATCH for partial update
- DELETE for removal

#### VI
Dùng HTTP method nhất quán:

- GET để lấy dữ liệu
- POST để tạo mới
- PUT để thay thế toàn bộ
- PATCH để cập nhật một phần
- DELETE để xóa

### 5.2 GET must be safe / GET phải an toàn

#### EN
GET endpoints must not change system state.

#### VI
Endpoint GET không được làm thay đổi trạng thái hệ thống.

#### Forbidden / Bị cấm
- GET /run-job
- GET /approve-payment
- GET /delete-user/{id}

### 5.3 Do not overload POST for everything / Không dùng POST cho mọi thứ

#### EN
Do not use POST as a generic replacement for all write operations when more precise semantics exist.

#### VI
Không dùng POST như một thay thế chung cho mọi thao tác ghi khi đã có semantics chính xác hơn.

## 6. Versioning conventions / Quy ước về versioning

### 6.1 Public APIs must be versioned / Public API phải có version

#### EN
Every public or externally consumed API must expose an explicit version.

#### VI
Mọi public API hoặc API được client ngoài sử dụng phải có version rõ ràng.

#### Preferred / Ưu tiên
- /v1/posts
- /v2/orders

### 6.2 Breaking changes require version strategy / Breaking change phải có chiến lược version

#### EN
Breaking changes must not be introduced silently into an existing stable version.

#### VI
Breaking change không được đưa ngầm vào một version ổn định đang tồn tại.

### 6.3 Backward compatibility must be intentional / Backward compatibility phải có chủ đích

#### EN
When changing API behavior, teams must evaluate whether the change is:

- backward compatible
- additive
- breaking
- version-worthy

#### VI
Khi thay đổi hành vi API, team phải đánh giá xem thay đổi đó là:

- tương thích ngược
- chỉ bổ sung thêm
- breaking
- cần version mới hay không

## 7. Pagination conventions / Quy ước về pagination

### 7.1 List endpoints must support pagination / Endpoint trả danh sách phải hỗ trợ pagination

#### EN
Endpoints returning potentially large collections must not return unbounded lists by default.

#### VI
Endpoint trả tập dữ liệu có thể lớn không được trả danh sách không giới hạn theo mặc định.

### 7.2 Use a consistent pagination scheme / Dùng một scheme pagination nhất quán

#### EN
The API must standardize one primary pagination style, such as:

- limit + offset
- page + page_size
- cursor-based pagination

#### VI
API phải chuẩn hóa một kiểu pagination chính, ví dụ:

- limit + offset
- page + page_size
- pagination kiểu cursor

### 7.3 Response metadata for pagination must be clear / Metadata của pagination trong response phải rõ

#### EN
Paginated responses should include the metadata needed for clients to navigate the result set safely.

#### VI
Response có phân trang nên chứa metadata cần thiết để client điều hướng tập kết quả an toàn.

#### Examples / Ví dụ
- current page or cursor
- page size or limit
- total count if appropriate
- next cursor or next page indicator

## 8. Filtering, sorting, and querying / Quy ước về filter, sort, và query

### 8.1 Use query parameters for filtering and slicing / Dùng query parameter cho filter và cắt lát dữ liệu

#### EN
Filtering, sorting, search, and pagination should normally be expressed through query parameters.

#### VI
Filtering, sorting, search, và pagination thường nên được biểu diễn qua query parameter.

#### Examples / Ví dụ
- /v1/posts?author_id=123
- /v1/posts?sort=created_at
- /v1/users/{id}/feed?limit=20

### 8.2 Keep query semantics consistent / Giữ semantics của query nhất quán

#### EN
If one collection endpoint uses limit, others should not randomly switch to size or count.

#### VI
Nếu một endpoint danh sách dùng limit, các endpoint khác không nên tùy tiện đổi sang size hoặc count.

## 9. Idempotency conventions / Quy ước về idempotency

### 9.1 Idempotency must be considered for write operations / Phải nghĩ tới idempotency với thao tác ghi

#### EN
Write operations that may be retried by clients, gateways, or networks must be designed with idempotency in mind.

#### VI
Các thao tác ghi có thể bị retry bởi client, gateway, hoặc network phải được thiết kế có tính đến idempotency.

### 9.2 Use idempotency keys where duplicates are costly / Dùng idempotency key khi duplicate gây tốn kém hoặc nguy hiểm

#### EN
Operations such as payment, order creation, or job triggering should support Idempotency-Key or an equivalent deduplication mechanism when duplicate execution is harmful.

#### VI
Các thao tác như thanh toán, tạo đơn hàng, hoặc kích hoạt job nên hỗ trợ Idempotency-Key hoặc cơ chế chống trùng tương đương khi việc thực thi trùng là nguy hiểm.

### 9.3 Idempotency behavior must be documented / Hành vi idempotency phải được tài liệu hóa

#### EN
Clients must be able to understand when repeated requests produce the same effect and how idempotency is enforced.

#### VI
Client phải hiểu được khi nào request lặp tạo cùng một hiệu ứng và idempotency được đảm bảo bằng cách nào.

## 10. Request and response consistency / Quy ước về tính nhất quán của request và response

### 10.1 Request and response shapes must be predictable / Hình dạng request và response phải dễ đoán

#### EN
APIs should use consistent naming, field structure, and response patterns across endpoints.

#### VI
API nên dùng cách đặt tên, cấu trúc field, và pattern response nhất quán giữa các endpoint.

### 10.2 Field naming must be standardized / Tên field phải được chuẩn hóa

#### EN
Choose one field naming style and apply it consistently across the API.

#### VI
Chọn một kiểu đặt tên field và áp dụng nhất quán trên toàn API.

### 10.3 Response contracts must remain stable / Contract của response phải ổn định

#### EN
Do not make silent structural changes to stable response payloads.

#### VI
Không được thay đổi cấu trúc response ổn định một cách âm thầm.

## 11. Error handling conventions for APIs / Quy ước xử lý lỗi cho API

### 11.1 API errors must be consistent / Lỗi API phải nhất quán

#### EN
The API must return errors in a consistent structure across endpoints.

#### VI
API phải trả lỗi theo một cấu trúc nhất quán giữa các endpoint.

### 11.2 Use HTTP status codes meaningfully / Dùng HTTP status code có ý nghĩa

#### EN
Status codes must reflect the real outcome category.

#### VI
Status code phải phản ánh đúng loại kết quả thực tế.

#### Examples / Ví dụ
- 200 OK for successful retrieval
- 201 Created for successful creation
- 400 Bad Request for invalid request shape
- 404 Not Found when the resource does not exist
- 409 Conflict for domain conflict
- 500 Internal Server Error for unexpected server failure

### 11.3 External errors must remain safe / Lỗi đưa ra ngoài phải an toàn

#### EN
Do not expose stack traces, raw SQL errors, or internal implementation details in API responses.

#### VI
Không được làm lộ stack trace, raw SQL error, hoặc chi tiết implementation nội bộ trong response API.

## 12. Developer-friendliness conventions / Quy ước về developer-friendliness

### 12.1 APIs must be easy to understand / API phải dễ hiểu

#### EN
The purpose of an endpoint should be inferable from its path, method, and resource naming.

#### VI
Mục đích của endpoint phải có thể suy ra từ path, method, và cách đặt tên resource.

### 12.2 APIs must be easy to consume correctly / API phải dễ dùng đúng

#### EN
APIs should reduce ambiguity and make correct usage straightforward.

#### VI
API nên giảm mơ hồ và giúp việc sử dụng đúng trở nên dễ dàng.

### 12.3 APIs must stay consistent across the system / API phải nhất quán trong toàn hệ thống

#### EN
Once a naming or semantic pattern is chosen, it should be reused across similar endpoints.

#### VI
Khi đã chọn một pattern về tên gọi hoặc semantics, phải tái sử dụng nó trên các endpoint tương tự.

## 13. Security and boundary basics / Cơ bản về security và boundary

### 13.1 APIs must validate external input / API phải validate input từ bên ngoài

#### EN
All incoming request data must be validated at the API boundary.

#### VI
Mọi dữ liệu request đi vào phải được validate tại boundary của API.

### 13.2 APIs must not leak internal details / API không được làm lộ chi tiết nội bộ

#### EN
Responses and errors must protect sensitive internal information.

#### VI
Response và error phải bảo vệ thông tin nội bộ nhạy cảm.

### 13.3 Authorization must not be inferred from path naming alone / Authorization không được suy diễn chỉ từ tên path

#### EN
Clear resource naming does not replace explicit authorization checks.

#### VI
Tên resource rõ ràng không thay thế cho kiểm tra phân quyền tường minh.

## 14. Anti-patterns / Mẫu xấu cần tránh

### EN
Avoid:

- action-style endpoints such as /getPosts or /createOrder
- using POST for every write operation
- returning unbounded list results by default
- introducing breaking changes silently
- inconsistent query parameter names across endpoints
- deeply nested URLs without a real resource hierarchy
- duplicate write effects caused by retries without idempotency strategy
- inconsistent error shapes
- endpoints that mix multiple unrelated responsibilities

### VI
Tránh:

- endpoint kiểu hành động như /getPosts hoặc /createOrder
- dùng POST cho mọi thao tác ghi
- trả danh sách không giới hạn theo mặc định
- đưa breaking change vào một cách âm thầm
- dùng tên query parameter không nhất quán giữa các endpoint
- URL nested quá sâu mà không có cấu trúc tài nguyên thật
- hiệu ứng ghi trùng do retry mà không có chiến lược idempotency
- cấu trúc lỗi không nhất quán
- endpoint trộn nhiều trách nhiệm không liên quan

## 15. Review checklist / Checklist review

### EN
When reviewing API design, check:

- Is the API resource-oriented?
- Does the path use nouns rather than verbs?
- Is the HTTP method correct for the intended operation?
- Is versioning present and appropriate?
- Does the list endpoint support pagination?
- Are filtering and query parameters consistent?
- Has idempotency been considered for write operations?
- Is the error behavior consistent and safe?
- Is the API easy for developers to understand and use correctly?
- Are resource boundaries clear and non-overlapping?

### VI
Khi review thiết kế API, cần kiểm tra:

- API có xoay quanh resource không?
- Path có dùng danh từ thay vì động từ không?
- HTTP method có đúng với thao tác mong muốn không?
- Versioning có hiện diện và phù hợp không?
- Endpoint danh sách có hỗ trợ pagination không?
- Filtering và query parameter có nhất quán không?
- Idempotency đã được cân nhắc cho thao tác ghi chưa?
- Hành vi lỗi có nhất quán và an toàn không?
- API có dễ để developer hiểu và dùng đúng không?
- Ranh giới giữa các resource có rõ ràng và không chồng chéo không?

## 16. Definition of done / Điều kiện hoàn thành

### EN
An API design is convention-compliant only if:

- it is resource-oriented
- it uses correct HTTP semantics
- it has an explicit versioning strategy where required
- list endpoints are paginated appropriately
- write operations consider idempotency where relevant
- request and response behavior is consistent
- error handling is safe and predictable
- the design is understandable and developer-friendly
- resource boundaries are clear and maintainable

### VI
Một thiết kế API chỉ được coi là tuân thủ convention khi:

- nó xoay quanh resource
- nó dùng đúng HTTP semantics
- nó có chiến lược versioning rõ ràng khi cần
- các endpoint danh sách được phân trang phù hợp
- các thao tác ghi có cân nhắc idempotency khi liên quan
- hành vi request và response nhất quán
- xử lý lỗi an toàn và dễ đoán
- thiết kế dễ hiểu và thân thiện với developer
- ranh giới resource rõ ràng và dễ bảo trì
