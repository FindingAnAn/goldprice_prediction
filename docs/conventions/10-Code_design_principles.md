# 10-Code-design-principles / Quy ước nguyên tắc thiết kế code

## 1. Purpose / Mục đích

### EN
This document defines the design principles for writing code that is readable, modular, testable, change-friendly, and operationally safe.  
Its purpose is to guide how functions, classes, modules, and boundaries must be designed so that the codebase remains maintainable as the system grows.

### VI
Tài liệu này định nghĩa các nguyên tắc thiết kế để viết code dễ đọc, có tính module, dễ kiểm thử, dễ thay đổi, và an toàn khi vận hành.  
Mục tiêu là hướng dẫn cách thiết kế hàm, class, module, và boundary để codebase vẫn dễ bảo trì khi hệ thống phát triển.

## 2. Scope / Phạm vi

### EN
This document applies to:

- business logic modules
- domain and application services
- reusable components and libraries
- integration boundaries
- function, class, and module design
- dependency direction and abstraction use
- complexity and readability expectations
- trade-offs and exceptions when applying SOLID and clean code principles

### VI
Tài liệu này áp dụng cho:

- module nghiệp vụ
- domain service và application service
- component và thư viện có thể tái sử dụng
- boundary tích hợp với hệ thống ngoài
- thiết kế hàm, class, và module
- hướng phụ thuộc và cách dùng abstraction
- kỳ vọng về độ phức tạp và khả năng đọc hiểu
- đánh đổi và ngoại lệ khi áp dụng SOLID và clean code

## 3. Core principles / Nguyên tắc cốt lõi

### 3.1 Readability and maintainability come before cleverness / Khả năng đọc hiểu và bảo trì quan trọng hơn sự “thông minh” phô diễn

#### EN
Code must be optimized first for correctness, clarity, and maintainability.  
Do not introduce clever structures, dense tricks, or excessive abstraction when a simpler design communicates intent better.

#### VI
Code phải được tối ưu trước hết cho tính đúng đắn, rõ ràng, và khả năng bảo trì.  
Không đưa vào các cấu trúc “khéo quá mức”, mẹo dày đặc, hoặc abstraction quá tay khi thiết kế đơn giản hơn truyền đạt ý đồ tốt hơn.

### 3.2 SOLID is a design discipline, not a ritual / SOLID là kỷ luật thiết kế, không phải nghi thức hình thức

#### EN
SOLID principles must improve separation of concerns, testability, and extension safety.  
They must not be applied mechanically in ways that fragment the code without delivering practical value.

#### VI
Các nguyên lý SOLID phải giúp tăng tách biệt trách nhiệm, khả năng kiểm thử, và độ an toàn khi mở rộng.  
Không được áp dụng máy móc theo cách làm code bị phân mảnh nhưng không tạo ra giá trị thực tế.

### 3.3 Metrics are review signals, not goals by themselves / Chỉ số là tín hiệu review, không phải mục tiêu tự thân

#### EN
Line counts, nesting depth, parameter counts, and complexity scores are warning signals.  
They help identify possible design problems, but they do not replace human judgment.

#### VI
Số dòng, độ sâu lồng, số lượng tham số, và điểm complexity là tín hiệu cảnh báo.  
Chúng giúp phát hiện vấn đề thiết kế tiềm năng, nhưng không thay thế được đánh giá của con người.

### 3.4 Design must fit the lifetime and risk of the code / Thiết kế phải phù hợp với vòng đời và rủi ro của code

#### EN
Long-lived business logic, shared modules, and boundary components require stronger design discipline than one-off scripts, throwaway prototypes, or generated code.

#### VI
Business logic sống lâu, module dùng chung, và component ở boundary cần kỷ luật thiết kế chặt hơn so với script dùng một lần, prototype ngắn hạn, hoặc code sinh tự động.

## 4. Function design rules / Quy ước thiết kế hàm

### 4.1 A function should do one coherent thing / Một hàm nên thực hiện một việc mạch lạc

#### EN
A function should have one primary intent that can be described clearly in one phrase.  
If a function mixes unrelated concerns such as validation, orchestration, persistence, notification, and formatting, it should be refactored.

#### VI
Một hàm nên có một ý định chính có thể mô tả rõ ràng bằng một cụm ngắn.  
Nếu một hàm trộn các concern không liên quan như validation, điều phối, lưu trữ, gửi thông báo, và formatting, nó nên được refactor.

#### Signs of violation / Dấu hiệu vi phạm

##### EN
- the function name needs "and", "then", or many clauses
- the function both decides and performs unrelated side effects
- the function is hard to summarize without describing multiple responsibilities

##### VI
- tên hàm cần dùng "and", "then", hoặc nhiều vế
- hàm vừa ra quyết định vừa làm nhiều side effect không liên quan
- khó tóm tắt hàm nếu không phải mô tả nhiều trách nhiệm

### 4.2 Function names must reveal intent / Tên hàm phải bộc lộ ý đồ

#### EN
Function names must use verbs or verb phrases and must describe what the function does from the caller's perspective.

#### VI
Tên hàm phải dùng động từ hoặc cụm động từ và phải mô tả hàm làm gì từ góc nhìn của caller.

#### Preferred / Ưu tiên
- `calculate_invoice_total`
- `load_user_profile`
- `send_password_reset_email`

#### Avoid / Tránh
- `handle_data`
- `process_stuff`
- `do_it`

### 4.3 Functions should stay short enough to understand quickly / Hàm nên đủ ngắn để hiểu nhanh

#### EN
A function should usually remain small enough to read in one screen and understand without excessive scrolling.

#### VI
Một hàm thường nên đủ nhỏ để đọc trong một màn hình và hiểu được mà không phải cuộn quá nhiều.

#### Review threshold / Ngưỡng review

##### EN
- up to around 30 logical lines is normally acceptable
- above that, the function should be reviewed for extractable responsibilities
- above around 50 logical lines requires explicit justification or refactoring

##### VI
- khoảng tới 30 dòng logic thường là chấp nhận được
- vượt mức đó, hàm nên được review xem có trách nhiệm nào có thể tách ra không
- vượt khoảng 50 dòng logic thì phải có giải thích rõ hoặc refactor

### 4.4 Parameter count must remain intentional / Số lượng tham số phải có chủ đích

#### EN
A function should prefer a small parameter surface.  
Too many parameters often indicate mixed responsibilities, a missing value object, or a weak boundary design.

#### VI
Một hàm nên ưu tiên bề mặt tham số nhỏ.  
Quá nhiều tham số thường là dấu hiệu của trách nhiệm bị trộn, thiếu value object, hoặc thiết kế boundary còn yếu.

#### Review threshold / Ngưỡng review

##### EN
- 0 to 3 parameters is preferred
- 4 to 5 parameters requires review
- more than 5 parameters should be redesigned unless the boundary contract clearly requires it

##### VI
- 0 đến 3 tham số là mức ưu tiên
- 4 đến 5 tham số cần review
- hơn 5 tham số nên được thiết kế lại trừ khi contract ở boundary thực sự yêu cầu

### 4.5 Control flow should remain shallow and explicit / Luồng điều khiển nên nông và rõ ràng

#### EN
Deep nesting increases cognitive load and hides decision structure.  
Prefer guard clauses, small helpers, and explicit branch separation to reduce nesting.

#### VI
Lồng quá sâu làm tăng tải nhận thức và che khuất cấu trúc quyết định.  
Ưu tiên guard clause, helper nhỏ, và tách nhánh rõ ràng để giảm nesting.

#### Review threshold / Ngưỡng review

##### EN
- nesting deeper than 3 levels is a warning sign
- nesting deeper than 4 levels should normally be refactored

##### VI
- nesting sâu hơn 3 cấp là tín hiệu cảnh báo
- nesting sâu hơn 4 cấp thông thường nên được refactor

### 4.6 Prefer explicit constants over magic values / Ưu tiên hằng số rõ nghĩa thay cho giá trị ma thuật

#### EN
Magic numbers, unexplained literals, and hidden thresholds reduce readability and make changes error-prone.

#### VI
Magic number, literal khó hiểu, và ngưỡng ẩn làm giảm khả năng đọc hiểu và khiến việc thay đổi dễ gây lỗi.

#### Preferred / Ưu tiên
```python
MAX_RETRY_ATTEMPTS = 3
if retry_count >= MAX_RETRY_ATTEMPTS:
    raise RetryLimitExceededError()
```

#### Avoid / Tránh
```python
if retry_count >= 3:
    raise RetryLimitExceededError()
```

## 5. SOLID principles / Nguyên lý SOLID

### 5.1 Single Responsibility Principle / Nguyên lý Trách nhiệm Duy nhất

#### EN
A class, module, or function should have one main reason to change.  
Do not create god objects or multipurpose modules that mix business rules, persistence, transport, formatting, and notification logic.

#### VI
Một class, module, hoặc hàm nên chỉ có một lý do chính để thay đổi.  
Không tạo god object hoặc module đa dụng trộn business rule, persistence, transport, formatting, và logic thông báo.

#### Expected behavior / Hành vi mong đợi

##### EN
- separate persistence from business rules
- separate orchestration from infrastructure details
- separate calculation from presentation formatting

##### VI
- tách persistence khỏi business rule
- tách orchestration khỏi chi tiết hạ tầng
- tách calculation khỏi formatting hiển thị

### 5.2 Open/Closed Principle / Nguyên lý Đóng để sửa, Mở để mở rộng

#### EN
Code should be open to extension but not require repeated modification of stable logic whenever a new variation appears.  
When behavior is expected to vary over time, prefer a design that adds a new implementation rather than patching a growing conditional chain.

#### VI
Code nên mở để mở rộng nhưng không đòi hỏi phải liên tục sửa logic ổn định mỗi khi xuất hiện một biến thể mới.  
Khi hành vi được dự đoán sẽ biến đổi theo thời gian, ưu tiên thiết kế cho phép thêm implementation mới thay vì vá vào chuỗi điều kiện ngày càng dài.

#### Guidance / Hướng dẫn

##### EN
- short, local `if` statements are not forbidden by themselves
- repeated branching over type, provider, or strategy usually signals an extension point
- use polymorphism, strategy objects, or handler registration when variation is expected to grow

##### VI
- `if` ngắn, cục bộ tự nó không bị cấm
- branch lặp đi lặp lại theo type, provider, hoặc strategy thường là dấu hiệu của extension point
- dùng polymorphism, strategy object, hoặc handler registry khi biến thể được dự đoán sẽ tăng

### 5.3 Liskov Substitution Principle / Nguyên lý Thay thế Liskov

#### EN
Any implementation of an abstraction must preserve the expected contract of that abstraction.  
A subtype must not silently weaken guarantees, reject valid input that the parent accepts, or replace supported behavior with a runtime surprise.

#### VI
Mọi implementation của một abstraction phải giữ nguyên contract kỳ vọng của abstraction đó.  
Một lớp con không được âm thầm làm yếu cam kết, từ chối input hợp lệ mà lớp cha chấp nhận, hoặc thay hành vi được hỗ trợ bằng bất ngờ khi runtime.

#### Forbidden / Bị cấm

##### EN
- overriding a supported method only to raise `NotSupportedError` or equivalent
- changing the semantic meaning of a returned value while keeping the same signature
- requiring stricter preconditions than the abstraction promises

##### VI
- override một method được hỗ trợ chỉ để ném `NotSupportedError` hoặc tương đương
- đổi nghĩa ngữ nghĩa của giá trị trả về nhưng giữ nguyên signature
- yêu cầu precondition ngặt hơn so với abstraction đã hứa

### 5.4 Interface Segregation Principle / Nguyên lý Phân tách Interface

#### EN
Clients must not be forced to depend on methods they do not need.  
Interfaces should describe focused capabilities rather than broad collections of unrelated actions.

#### VI
Client không được bị ép phụ thuộc vào các method mà chúng không cần.  
Interface nên mô tả capability có trọng tâm thay vì gom nhiều hành động không liên quan vào cùng một chỗ.

#### Preferred / Ưu tiên
- `InvoiceReader`
- `InvoiceWriter`
- `NotificationSender`

#### Avoid / Tránh
- `SystemManager`
- `DataHandler`
- interfaces that mix read, write, retry, export, and notification concerns

### 5.5 Dependency Inversion Principle / Nguyên lý Đảo ngược phụ thuộc

#### EN
High-level policy must not depend directly on low-level technical detail.  
Business logic should depend on abstractions or ports, while infrastructure provides concrete implementations.

#### VI
Chính sách ở mức cao không được phụ thuộc trực tiếp vào chi tiết kỹ thuật mức thấp.  
Business logic nên phụ thuộc vào abstraction hoặc port, còn hạ tầng cung cấp implementation cụ thể.

#### Preferred / Ưu tiên
- inject collaborators through constructor or explicit composition
- define ports at the boundary of the business need
- keep external SDKs, database clients, and framework objects outside the domain core

#### Avoid / Tránh
- creating database clients directly inside business rules
- importing framework-specific types into domain models
- hiding hard dependencies behind static globals

## 6. Complexity and size thresholds / Ngưỡng về độ phức tạp và kích thước

### 6.1 Cyclomatic complexity must stay reviewable / Độ phức tạp cyclomatic phải còn review được

#### EN
Cyclomatic complexity should remain low enough that the function can be reasoned about and tested with confidence.

#### VI
Cyclomatic complexity nên được giữ ở mức đủ thấp để hàm còn có thể được suy luận và kiểm thử một cách tự tin.

#### Review threshold / Ngưỡng review

##### EN
- 1 to 10 is normally healthy
- above 10 requires review
- above 15 usually requires refactoring or explicit justification
- above 20 is high risk and should be treated as an exception case

##### VI
- 1 đến 10 thường là mức khỏe mạnh
- trên 10 cần review
- trên 15 thường cần refactor hoặc giải thích rõ
- trên 20 là rủi ro cao và nên được xem là trường hợp ngoại lệ

### 6.2 Class and module size should remain comprehensible / Kích thước class và module nên còn dễ hiểu

#### EN
Large classes and modules often hide poor separation of concerns.  
The goal is not to minimize file size mechanically, but to preserve a coherent mental model.

#### VI
Class và module lớn thường che giấu việc tách trách nhiệm chưa tốt.  
Mục tiêu không phải là giảm kích thước file một cách máy móc, mà là giữ được mô hình nhận thức mạch lạc.

#### Review threshold / Ngưỡng review

##### EN
- classes larger than roughly 300 to 500 lines require review for mixed responsibilities
- large modules should be split when they contain multiple unrelated change reasons

##### VI
- class lớn hơn khoảng 300 đến 500 dòng cần được review xem có trộn trách nhiệm hay không
- module lớn nên được tách khi chứa nhiều lý do thay đổi không liên quan

### 6.3 Line length should support readability / Độ dài dòng phải phục vụ khả năng đọc

#### EN
Code lines should remain within the style limit of the language or formatter in use.  
The specific line length limit is defined in `03-Naming_style_conventions` §5.2.

#### VI
Dòng code nên nằm trong giới hạn style của ngôn ngữ hoặc formatter đang dùng.  
Giới hạn độ dài dòng cụ thể được định nghĩa trong `03-Naming_style_conventions` §5.2.

## 7. Dependency and abstraction rules / Quy tắc về phụ thuộc và abstraction

### 7.1 Every new abstraction must earn its existence / Mỗi abstraction mới phải xứng đáng được tạo ra

#### EN
Do not introduce interfaces, base classes, wrappers, or indirection layers without a clear design reason.

#### VI
Không tạo interface, base class, wrapper, hoặc lớp gián tiếp nếu không có lý do thiết kế rõ ràng.

#### Valid reasons / Lý do hợp lệ

##### EN
- protecting a business boundary from infrastructure detail
- enabling substitution of external providers
- making important business logic testable in isolation
- defining a stable extension point that is expected to grow

##### VI
- bảo vệ business boundary khỏi chi tiết hạ tầng
- cho phép thay thế external provider
- làm cho business logic quan trọng có thể test trong trạng thái cô lập
- định nghĩa extension point ổn định được dự đoán sẽ mở rộng

### 7.2 Do not create interface-for-one without value / Không tạo interface-một-đối-tượng nếu không tạo giá trị

#### EN
A single implementation is not automatically a problem.  
Do not create an interface only to satisfy a pattern name if the abstraction does not improve testability, replaceability, or boundary clarity.

#### VI
Việc chỉ có một implementation tự nó không phải vấn đề.  
Không tạo interface chỉ để thỏa một tên pattern nếu abstraction đó không cải thiện testability, replaceability, hoặc độ rõ của boundary.

### 7.3 Composition is preferred over hidden coupling / Ưu tiên composition hơn coupling ẩn

#### EN
Dependencies should be explicit in the object graph and visible at composition time.

#### VI
Phụ thuộc nên được biểu diễn rõ trong object graph và hiển thị tại thời điểm composition.

#### Avoid / Tránh
- hidden singletons
- service locators as default dependency mechanism
- global mutable state used as implicit dependency

## 8. Architectural placement rules / Quy tắc về vị trí kiến trúc

### 8.1 Domain code must stay pure from framework and infrastructure / Domain phải giữ sạch khỏi framework và hạ tầng

#### EN
Domain code should contain business entities, value objects, invariants, and core business rules.  
It must not depend directly on transport frameworks, ORMs, HTTP clients, queue SDKs, or UI concerns.

For the detailed list of allowed and forbidden dependencies per layer, follow `04-Dependencies_import_conventions` §5.4.

#### VI
Code ở Domain nên chứa business entity, value object, invariant, và business rule cốt lõi.  
Nó không được phụ thuộc trực tiếp vào framework transport, ORM, HTTP client, queue SDK, hoặc concern giao diện.

Về danh sách chi tiết allowed/forbidden dependency theo từng layer, tuân theo `04-Dependencies_import_conventions` §5.4.

### 8.2 Application code orchestrates use cases / Application điều phối use case

#### EN
Application code coordinates workflows, permissions, transactions, policy execution, and interactions between domain behavior and boundary ports.

#### VI
Code ở Application điều phối workflow, quyền hạn, transaction, thực thi policy, và tương tác giữa hành vi domain với các port ở boundary.

### 8.3 Infrastructure implements technical detail / Infrastructure triển khai chi tiết kỹ thuật

#### EN
Infrastructure code contains adapters, gateways, repositories, SDK wrappers, transport clients, and persistence implementations.

#### VI
Code ở Infrastructure chứa adapter, gateway, repository, SDK wrapper, transport client, và implementation liên quan tới persistence.

### 8.4 Dependencies must point inward / Hướng phụ thuộc phải đi vào trong

#### EN
Source-code dependencies must point toward the more stable business core.  
For the canonical dependency direction rules and layer-by-layer breakdown, follow `04-Dependencies_import_conventions` §5.3.

#### VI
Phụ thuộc ở mức source code phải hướng về lõi nghiệp vụ ổn định hơn.  
Về quy tắc hướng dependency canonical và chi tiết theo từng layer, tuân theo `04-Dependencies_import_conventions` §5.3.

## 9. Readability and naming rules / Quy tắc về khả năng đọc và đặt tên

### 9.1 Names must communicate domain meaning / Tên phải truyền tải ý nghĩa nghiệp vụ

#### EN
Names must describe what the thing is, what it does, or what it represents in the business context.  
Do not hide meaning behind vague technical labels.

#### VI
Tên phải mô tả thứ đó là gì, làm gì, hoặc đại diện cho điều gì trong ngữ cảnh nghiệp vụ.  
Không che giấu ý nghĩa bằng các nhãn kỹ thuật mơ hồ.

### 9.2 Boolean names should read like propositions / Tên boolean nên đọc như mệnh đề đúng/sai

#### EN
Boolean variables and methods should read naturally as true/false statements.

#### VI
Biến và method kiểu boolean nên đọc tự nhiên như một mệnh đề đúng/sai.

#### Preferred / Ưu tiên
- `is_active`
- `has_access`
- `can_retry`

#### Avoid / Tránh
- `flag1`
- `status_value`
- `retry_check`

### 9.3 Formatting must support reviewability / Trình bày phải hỗ trợ khả năng review

#### EN
Whitespace, grouping, ordering, and structure should help a reviewer understand intent quickly.  
Formatting must serve comprehension, not personal preference.

#### VI
Khoảng trắng, cách nhóm, thứ tự, và cấu trúc nên giúp reviewer hiểu ý đồ nhanh.  
Trình bày phải phục vụ việc hiểu code, không phải sở thích cá nhân.

#### Note / Ghi chú

##### EN
Language-specific style rules remain governed by the dedicated naming and style convention document.

##### VI
Các quy tắc style riêng theo ngôn ngữ vẫn do tài liệu naming và style chuyên biệt chi phối.

## 10. Defensive design and failure awareness / Thiết kế phòng vệ và nhận thức về failure

### 10.1 Design must make invalid states harder to represent / Thiết kế phải làm cho trạng thái không hợp lệ khó xuất hiện hơn

#### EN
Prefer designs that encode invariants, constrain invalid input early, and make misuse visible rather than silently tolerated.

#### VI
Ưu tiên các thiết kế mã hóa được invariant, giới hạn input không hợp lệ sớm, và làm cho việc dùng sai trở nên hiển thị thay vì âm thầm được chấp nhận.

### 10.2 Validate at the correct boundary / Validate ở đúng boundary

#### EN
External input should be validated at the entry boundary, while core invariants should be preserved inside the domain model.

#### VI
Input từ bên ngoài nên được validate tại boundary đi vào, còn invariant cốt lõi phải được bảo toàn trong domain model.

### 10.3 Failure semantics must be explicit / Ngữ nghĩa failure phải rõ ràng

#### EN
When a function or component can fail in meaningful ways, that possibility should be visible through its contract, return model, or exception behavior.

#### VI
Khi một hàm hoặc component có thể thất bại theo các cách có ý nghĩa, khả năng đó phải được thể hiện rõ qua contract, mô hình trả về, hoặc hành vi exception.

## 11. Trade-offs and controlled exceptions / Đánh đổi và ngoại lệ có kiểm soát

### 11.1 Not every piece of code requires the same design weight / Không phải mọi đoạn code đều cần cùng một mức thiết kế

#### EN
The stricter parts of this document apply most strongly to long-lived, business-relevant, shared, or high-risk code.

#### VI
Những phần chặt chẽ nhất của tài liệu này áp dụng mạnh nhất cho code sống lâu, liên quan nghiệp vụ, dùng chung, hoặc rủi ro cao.

#### Typically strict / Thường áp dụng chặt

##### EN
- domain logic
- application services
- integration boundaries
- shared libraries
- security-sensitive flows

##### VI
- domain logic
- application service
- integration boundary
- thư viện dùng chung
- luồng nhạy cảm về bảo mật

#### Typically flexible / Thường linh hoạt hơn

##### EN
- short-lived scripts
- migration utilities
- experiments and prototypes
- test fixtures
- generated code

##### VI
- script ngắn hạn
- utility migration
- thử nghiệm và prototype
- test fixture
- code sinh tự động

### 11.2 Exceptions must be intentional and visible / Ngoại lệ phải có chủ đích và hiển thị rõ

#### EN
A threshold may be exceeded when keeping the code as-is is the clearer or safer design choice, but the reason should be visible in review context.

#### VI
Một ngưỡng có thể được vượt khi giữ nguyên code lại là lựa chọn rõ ràng hoặc an toàn hơn về thiết kế, nhưng lý do phải hiển thị rõ trong ngữ cảnh review.

#### Examples / Ví dụ
- a parsing routine with naturally dense branching
- a performance-critical hot path that avoids extra allocations
- a framework-mandated callback signature
- a carefully isolated algorithm that is complex by nature

### 11.3 Avoid metric gaming / Tránh “chơi chỉ số”

#### EN
Do not split functions, invent wrapper objects, or add interfaces only to satisfy thresholds while making the real design worse.

#### VI
Không tách hàm, bịa thêm wrapper object, hoặc thêm interface chỉ để vượt ngưỡng chỉ số trong khi thiết kế thực tế lại tệ đi.

## 12. Refactoring triggers / Tín hiệu cần refactor

### 12.1 Repeated change pain is a refactoring signal / Khó khăn lặp lại khi thay đổi là tín hiệu cần refactor

#### EN
Refactor when the same area repeatedly becomes fragile, confusing, duplicated, or expensive to test.

#### VI
Hãy refactor khi cùng một vùng code liên tục trở nên mong manh, khó hiểu, lặp lại, hoặc tốn kém để kiểm thử.

### 12.2 Duplication must be judged carefully / Sự lặp lại phải được đánh giá cẩn trọng

#### EN
Not all duplication is equally harmful.  
Duplicate code should be removed when it represents repeated knowledge that is likely to drift, not when removing it would force premature abstraction.

#### VI
Không phải mọi sự lặp lại đều gây hại như nhau.  
Code trùng lặp nên được loại bỏ khi nó đại diện cho tri thức bị lặp và có khả năng lệch dần theo thời gian, không phải khi việc loại bỏ nó sẽ ép abstraction quá sớm.

### 12.3 Refactoring must improve a real quality attribute / Refactor phải cải thiện một thuộc tính chất lượng thực sự

#### EN
A refactor should improve at least one of the following:

- readability
- testability
- boundary clarity
- replaceability
- correctness confidence
- operational safety

#### VI
Một refactor nên cải thiện ít nhất một trong các yếu tố sau:

- khả năng đọc hiểu
- khả năng kiểm thử
- độ rõ của boundary
- khả năng thay thế implementation
- độ tự tin về tính đúng
- độ an toàn vận hành

## 13. Agent and automation rules / Quy ước cho agent và tự động hóa

### 13.1 Agents must prefer the simplest design that satisfies the need / Agent phải ưu tiên thiết kế đơn giản nhất nhưng vẫn đáp ứng nhu cầu

#### EN
Agents must not introduce additional indirection unless it solves a concrete design problem.

#### VI
Agent không được đưa thêm lớp gián tiếp nếu nó không giải quyết một vấn đề thiết kế cụ thể.

### 13.2 Agents must keep reasoning visible in the structure / Agent phải làm cho lập luận thiết kế hiện ra qua cấu trúc code

#### EN
Generated code should make responsibilities, dependencies, and boundaries easy to infer from naming and structure.

#### VI
Code do agent sinh ra phải làm cho trách nhiệm, phụ thuộc, và boundary dễ suy ra từ tên gọi và cấu trúc.

### 13.3 Agents must not hide complexity behind superficial cleanliness / Agent không được che giấu độ phức tạp bằng sự “sạch” bề ngoài

#### EN
A design is not acceptable if it only appears clean by distributing complexity across too many thin wrappers or pass-through layers.

#### VI
Một thiết kế không được coi là chấp nhận được nếu nó chỉ trông sạch vì đã dàn độ phức tạp ra quá nhiều wrapper mỏng hoặc lớp chuyển tiếp thụ động.

## 14. Anti-patterns / Mẫu xấu cần tránh

### EN
Avoid these anti-patterns:

- god classes or god services handling too many concerns
- long functions that mix orchestration, validation, persistence, and side effects
- conditional trees that keep growing with each new provider or behavior type
- interfaces created only for ritualistic dependency injection
- domain code importing ORM, HTTP, or framework-specific primitives
- wrapper layers that only forward calls without adding boundary value
- metric gaming that reduces quality while pretending to improve cleanliness
- abstractions that hide the real execution path and make debugging harder without compensating value

### VI
Tránh các mẫu xấu sau:

- god class hoặc god service ôm quá nhiều concern
- hàm dài trộn orchestration, validation, persistence, và side effect
- cây điều kiện cứ phình ra mỗi khi có provider hoặc kiểu hành vi mới
- interface được tạo ra chỉ để làm màu cho dependency injection
- domain code import trực tiếp ORM, HTTP, hoặc primitive riêng của framework
- lớp wrapper chỉ chuyển tiếp lời gọi mà không tạo thêm giá trị boundary
- “chơi chỉ số” làm giảm chất lượng nhưng giả vờ tăng độ sạch
- abstraction che khuất luồng thực thi thật và làm debug khó hơn mà không bù lại giá trị tương xứng

## 15. Review checklist / Checklist review

### EN
Before considering a design acceptable, confirm that:

- the function, class, or module has a clear primary responsibility
- names reveal intent and business meaning
- complexity remains reviewable and testable
- parameter count and nesting are justified
- dependencies are explicit and point in the correct direction
- abstractions exist for a real reason
- domain logic is not contaminated by infrastructure detail
- readability improved or at least did not regress
- thresholds were used as signals, not gamed as targets
- any exception to the guideline is visible and justified

### VI
Trước khi coi thiết kế là chấp nhận được, hãy xác nhận rằng:

- hàm, class, hoặc module có trách nhiệm chính rõ ràng
- tên gọi bộc lộ ý đồ và ý nghĩa nghiệp vụ
- độ phức tạp vẫn còn review và test được
- số lượng tham số và mức nesting có giải thích hợp lý
- phụ thuộc là rõ ràng và đi đúng hướng
- abstraction tồn tại vì một lý do thực sự
- domain logic không bị nhiễm chi tiết hạ tầng
- khả năng đọc hiểu đã tốt hơn hoặc ít nhất không tệ đi
- các ngưỡng chỉ được dùng như tín hiệu, không bị “chơi” như mục tiêu
- mọi ngoại lệ với guideline đều được hiển thị và giải thích

## 16. Definition of compliance / Điều kiện được coi là tuân thủ

### EN
Code is considered compliant with this document when:

- its responsibilities and boundaries are easy to understand
- its design follows SOLID principles where they add practical value
- its functions and modules remain readable, reviewable, and testable
- its abstractions are justified rather than ritualistic
- its dependency direction protects the business core from technical leakage
- its exceptions are explicit, limited, and defensible
- it reduces future change risk instead of merely looking tidy in the present

### VI
Code được coi là tuân thủ tài liệu này khi:

- trách nhiệm và boundary của nó dễ hiểu
- thiết kế của nó tuân theo SOLID ở những nơi điều đó tạo ra giá trị thực tế
- hàm và module của nó vẫn dễ đọc, dễ review, và dễ kiểm thử
- abstraction của nó có lý do tồn tại rõ ràng thay vì mang tính nghi thức
- hướng phụ thuộc của nó bảo vệ được lõi nghiệp vụ khỏi rò rỉ kỹ thuật
- các ngoại lệ của nó là rõ ràng, có giới hạn, và có thể bảo vệ được về mặt lý do
- nó làm giảm rủi ro thay đổi trong tương lai thay vì chỉ trông gọn gàng ở hiện tại
