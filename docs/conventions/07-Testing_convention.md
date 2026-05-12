# Testing Conventions (Unit Test Focus) / Quy ước Kiểm thử (Trọng tâm Unit Test)

## 1. Purpose / Mục đích

### EN
This document defines the testing conventions for the project, with primary emphasis on unit tests.  
Its purpose is to ensure that business logic is isolated, testable, deterministic, and verified consistently before broader integration or system-level testing is added.

### VI
Tài liệu này định nghĩa các quy ước kiểm thử cho dự án, với trọng tâm chính là unit test.  
Mục tiêu là đảm bảo business logic được cô lập, có thể kiểm thử, có tính xác định, và được xác minh nhất quán trước khi bổ sung integration test hoặc kiểm thử ở mức hệ thống.

> [!TIP]
> **Tùy chọn tham khảo code mẫu tại:** [Example/unitest_example.py](Example/unitest_example.py)

## 2. Scope / Phạm vi

### EN
This document applies to:

- unit tests
- test configuration and test settings
- fixtures, mocks, stubs, and fakes
- test naming and structure
- separation between unit, integration, and performance tests
- test coverage expectations
- review and completion criteria for test quality

### VI
Tài liệu này áp dụng cho:

- unit test
- test configuration và test settings
- fixture, mock, stub, và fake
- quy tắc đặt tên và cấu trúc test
- cách tách unit test, integration test, và performance test
- kỳ vọng về test coverage
- tiêu chí review và hoàn thành chất lượng test

## 3. Core principles / Nguyên tắc cốt lõi

### 3.1 Unit tests come first / Unit test là lớp đầu tiên

#### EN
Unit tests are the default first layer of verification for business-relevant code.

#### VI
Unit test là lớp xác minh mặc định đầu tiên đối với code có ý nghĩa nghiệp vụ.

### 3.2 Unit tests must verify behavior in isolation / Unit test phải xác minh hành vi trong trạng thái cô lập

#### EN
Unit tests must be fast, deterministic, readable, and independent from external systems.

#### VI
Unit test phải nhanh, xác định được, dễ đọc, và không phụ thuộc vào hệ thống bên ngoài.

### 3.3 Testing must prioritize meaning over raw coverage numbers / Kiểm thử phải ưu tiên ý nghĩa hơn là con số coverage thô

#### EN
Coverage is useful, but the primary goal is to verify important behavior, edge cases, and expected failure paths.

#### VI
Coverage có ích, nhưng mục tiêu chính là xác minh hành vi quan trọng, edge case, và failure path được dự kiến.

## 4. Test strategy / Chiến lược kiểm thử

### 4.1 Unit tests are the default first layer / Unit test là lớp kiểm thử mặc định đầu tiên

#### EN
Every business-relevant module must be covered by unit tests before broader integration coverage is added.

#### VI
Mọi module có ý nghĩa nghiệp vụ phải được bao phủ bằng unit test trước khi bổ sung integration test ở mức rộng hơn.

### 4.2 Unit tests verify logic, not infrastructure / Unit test kiểm logic, không kiểm hạ tầng

#### EN
Unit tests should verify:

- decision logic
- branching behavior
- validation behavior
- transformations
- retry and fallback logic
- error handling and error translation
- use-case outcomes

They should not rely on:

- real databases
- real queues
- real external APIs
- real cloud services
- uncontrolled filesystem side effects

#### VI
Unit test nên kiểm:

- logic ra quyết định
- hành vi phân nhánh
- hành vi validation
- phép biến đổi dữ liệu
- logic retry và fallback
- xử lý lỗi và chuyển đổi lỗi
- kết quả của use case

Chúng không nên phụ thuộc vào:

- database thật
- queue thật
- external API thật
- cloud service thật
- side effect filesystem không được kiểm soát

### 4.3 Analyze scenarios before writing tests / Phân tích scenario trước khi viết test

#### EN
Before writing tests, identify:

- happy path
- expected failure paths
- edge cases
- state transitions
- invalid inputs
- branch conditions

#### VI
Trước khi viết test, cần xác định:

- happy path
- failure path dự kiến
- edge case
- chuyển trạng thái
- input không hợp lệ
- điều kiện phân nhánh

## 5. What unit tests must cover first / Những gì unit test phải ưu tiên bao phủ trước

### EN
Prioritize unit tests for:

- domain logic
- validation rules
- parsing and transformation rules
- branching logic
- retry logic
- fallback logic
- exception translation
- configuration validation logic
- helper functions with meaningful business or pipeline impact
- ML/data preprocessing rules
- feature engineering rules
- schema checks
- threshold or decision rules

### VI
Ưu tiên viết unit test trước cho:

- domain logic
- luật validation
- luật parse và transform
- branching logic
- retry logic
- fallback logic
- chuyển đổi exception
- logic validation của config
- helper function có ảnh hưởng nghiệp vụ hoặc pipeline rõ ràng
- luật tiền xử lý data/ML
- luật feature engineering
- kiểm tra schema
- luật threshold hoặc ra quyết định

## 6. Test configuration and test settings / Quy ước về test configuration và test settings

### 6.1 Test configuration is a valid test component / Test configuration là thành phần hợp lệ của test

#### EN
Tests may and should define dedicated test configuration when needed to isolate behavior from runtime configuration.

#### VI
Test có thể và nên định nghĩa test configuration riêng khi cần để cô lập hành vi khỏi runtime configuration.

### 6.2 Test configuration must be safe and local / Test configuration phải an toàn và cục bộ

#### EN
Test configuration must not depend on real production secrets or live runtime settings.

#### VI
Test configuration không được phụ thuộc vào secret production thật hoặc runtime setting đang chạy thật.

### 6.3 Prefer test-specific fixtures over ad hoc inline setup / Ưu tiên fixture dành riêng cho test hơn là setup tạm ngay trong test

#### EN
When multiple tests share the same configuration context, use a fixture rather than duplicating inline setup.

#### VI
Khi nhiều test dùng chung một context cấu hình, hãy dùng fixture thay vì lặp lại phần setup ngay trong từng test.

### 6.4 Test configuration must remain explicit / Test configuration phải giữ tính tường minh

#### EN
Test settings should remain simple, readable, and close to the behavior they support.

#### VI
Test setting phải đơn giản, dễ đọc, và gần với hành vi mà chúng phục vụ.

## 7. Fixtures, mocks, stubs, and fakes / Quy ước về fixture, mock, stub, và fake

### 7.1 Use pytest as the default framework / Dùng pytest làm framework mặc định

#### EN
pytest is the default testing framework for the project.

#### VI
pytest là framework kiểm thử mặc định của dự án.

### 7.2 Use fixtures to reduce repetition / Dùng fixture để giảm lặp

#### EN
Use pytest fixtures for reusable setup shared across multiple tests.

#### VI
Dùng fixture của pytest cho phần setup tái sử dụng giữa nhiều test.

### 7.3 Keep fixtures readable and shallow / Giữ fixture dễ đọc và không quá sâu

#### EN
Fixtures should remain small, explicit, and easy to understand.  
Avoid deeply layered fixture chains that hide test intent.

#### VI
Fixture phải nhỏ gọn, rõ ràng, và dễ hiểu.  
Tránh chuỗi fixture quá sâu làm che mất ý đồ của test.

### 7.4 Mock external dependencies, not the behavior under test / Mock dependency ngoài, không mock chính hành vi đang test

#### EN
Mock dependencies such as:

- repositories
- external APIs
- queues
- SDK calls
- file system boundaries
- loggers when needed

Do not mock away the main behavior being verified.

#### VI
Mock các dependency như:

- repository
- external API
- queue
- SDK call
- boundary của filesystem
- logger khi cần

Không được mock mất chính hành vi mà test đang cần xác minh.

### 7.5 Prefer fakes or lightweight fixtures when they improve clarity / Ưu tiên fake hoặc fixture nhẹ khi giúp rõ ràng hơn

#### EN
If a fake object is simpler and clearer than a complex mock chain, prefer the fake.

#### VI
Nếu fake object đơn giản và rõ ràng hơn một chuỗi mock phức tạp, hãy ưu tiên fake.

### 7.6 Patch at the correct lookup boundary / Patch tại đúng lookup boundary

#### EN
When patching is needed, patch the object where it is looked up by the unit under test.

#### VI
Khi cần patch, phải patch đúng chỗ mà unit under test thực sự lookup đối tượng đó.

### 7.7 Temporary resources must be isolated / Tài nguyên tạm phải được cô lập

#### EN
Use temporary directories, temporary files, or framework-provided temp utilities for filesystem-related unit tests.

#### VI
Dùng thư mục tạm, file tạm, hoặc utility temp của framework cho unit test liên quan tới filesystem.

## 8. Test naming / Quy ước đặt tên test

### 8.1 Test file names / Tên file test

#### EN
Test file names must use snake_case and start with test_.

#### VI
Tên file test phải dùng snake_case và bắt đầu bằng test_.

#### Examples / Ví dụ

- test_file_processor.py
- test_user_service.py
- test_feature_engineering.py

### 8.2 Test function names / Tên hàm test

#### EN
Test names must describe expected behavior clearly.

Preferred patterns:

- test_should_<expected_behavior>_when_<condition>
- test_<action>_<expected_result>
- test_<method>_<scenario>

#### VI
Tên test phải mô tả rõ hành vi mong đợi.

Mẫu ưu tiên:

- test_should_<expected_behavior>_when_<condition>
- test_<action>_<expected_result>
- test_<method>_<scenario>

### 8.3 Avoid vague test names / Tránh tên test mơ hồ

#### EN
Avoid names such as:

- test_case_1
- test_main
- test_basic
- test_works

#### VI
Tránh các tên như:

- test_case_1
- test_main
- test_basic
- test_works

## 9. Test structure / Cấu trúc test

### 9.1 Prefer Arrange–Act–Assert thinking / Ưu tiên tư duy Arrange–Act–Assert

#### EN
Tests should be structured around:

- Arrange
- Act
- Assert

#### VI
Test nên được tổ chức theo:

- Arrange
- Act
- Assert

### 9.2 One test should verify one primary behavior / Mỗi test nên xác minh một hành vi chính

#### EN
A single test should have one main reason to fail.

#### VI
Một test nên chỉ có một lý do chính để fail.

### 9.3 Group tests by unit responsibility / Nhóm test theo trách nhiệm của đơn vị được test

#### EN
Use test classes or file sections to group related tests by class, function, or responsibility.

#### VI
Dùng test class hoặc chia section trong file để nhóm các test liên quan theo class, function, hoặc trách nhiệm.

### 9.4 Keep test files focused / Giữ file test tập trung

#### EN
A unit test file should focus on one module, one class, or one closely related responsibility group.

#### VI
Một file unit test nên tập trung vào một module, một class, hoặc một nhóm trách nhiệm rất gần nhau.

## 10. Assertions and failure expectations / Quy ước về assert và kỳ vọng lỗi

### 10.1 Assertions must be specific / Assert phải cụ thể

#### EN
Assertions should verify meaningful outcomes and avoid vague truthiness checks when specific checks are possible.

#### VI
Assert phải kiểm kết quả có ý nghĩa và tránh kiểu kiểm mơ hồ khi có thể kiểm cụ thể hơn.

### 10.2 Expected failures must be tested explicitly / Failure dự kiến phải được test tường minh

#### EN
Use explicit exception assertions such as pytest.raises(...) for expected failure cases.

#### VI
Dùng assert exception tường minh như pytest.raises(...) cho các failure dự kiến.

### 10.3 Do not over-assert implementation trivia / Không assert quá mức vào chi tiết vụn vặt của implementation

#### EN
Prefer verifying stable behavior over fragile internal call patterns unless call behavior is itself part of the contract.

#### VI
Ưu tiên kiểm hành vi ổn định hơn là bám vào pattern gọi nội bộ dễ vỡ, trừ khi hành vi gọi đó chính là một phần của contract.

## 11. Separation of test types / Tách biệt các loại test

### 11.1 Unit tests must be separated from integration tests / Unit test phải tách khỏi integration test

#### EN
Unit tests, integration tests, and performance tests must not be mixed casually in the same file.

#### VI
Unit test, integration test, và performance test không được trộn lẫn tùy tiện trong cùng một file.

### 11.2 Use markers intentionally / Dùng marker có chủ đích

#### EN
Use markers such as integration, performance, or slow only when the test truly belongs to that category.

#### VI
Dùng marker như integration, performance, hoặc slow chỉ khi test thực sự thuộc loại đó.

### 11.3 Unit test files must not contain custom execution runners / File unit test không được chứa runner tự chế

#### EN
Do not place if __name__ == "__main__" test runners inside unit test files.  
Test execution must be handled by pytest, CI, or dedicated task runners.

#### VI
Không đặt runner kiểu if __name__ == "__main__" trong file unit test.  
Việc chạy test phải do pytest, CI, hoặc task runner chuyên dụng đảm nhiệm.

## 12. Coverage philosophy / Triết lý về coverage

### 12.1 Coverage is a signal, not the goal / Coverage là tín hiệu, không phải mục tiêu

#### EN
Coverage numbers are useful indicators, but they do not guarantee meaningful tests.

#### VI
Coverage là chỉ báo hữu ích, nhưng không đảm bảo test có ý nghĩa.

### 12.2 Prioritize behavior coverage over raw line coverage / Ưu tiên bao phủ hành vi hơn là bao phủ dòng lệnh thô

#### EN
When choosing what to test next, prioritize:

- important business behavior
- edge cases
- failure paths
- risky branches
- transformations with business impact

before chasing uncovered lines mechanically.

#### VI
Khi chọn viết test tiếp theo, hãy ưu tiên:

- hành vi nghiệp vụ quan trọng
- edge case
- failure path
- nhánh xử lý rủi ro
- phép biến đổi có ảnh hưởng nghiệp vụ

trước khi máy móc đuổi theo các dòng chưa được phủ.

### 12.3 Use coverage reports to find blind spots / Dùng coverage report để tìm vùng mù

#### EN
Coverage reports should be used to identify untested areas and guide better scenario selection.

#### VI
Coverage report nên được dùng để tìm vùng chưa được test và định hướng chọn scenario tốt hơn.

## 13. ML and data-specific unit testing / Unit test đặc thù cho ML và data

### 13.1 Unit tests must cover transformation logic / Unit test phải bao phủ logic biến đổi dữ liệu

#### EN
For data and ML systems, unit tests should verify transformation rules, feature generation, filtering logic, schema checks, and missing-value handling.

#### VI
Với hệ thống data và ML, unit test nên xác minh luật biến đổi dữ liệu, tạo feature, logic lọc, kiểm tra schema, và xử lý missing value.

### 13.2 Unit tests do not prove model quality / Unit test không chứng minh chất lượng mô hình

#### EN
Unit tests verify code correctness and pipeline behavior, not model performance quality in the statistical sense.

#### VI
Unit test xác minh tính đúng đắn của code và hành vi pipeline, không chứng minh chất lượng mô hình theo nghĩa thống kê.

### 13.3 Model-serving logic still needs unit tests / Logic phục vụ mô hình vẫn cần unit test

#### EN
Unit tests should still cover:

- model selection logic
- version routing
- threshold logic
- output schema
- fallback behavior
- error translation around inference

#### VI
Unit test vẫn nên bao phủ:

- logic chọn mô hình
- định tuyến theo version
- logic threshold
- schema đầu ra
- hành vi fallback
- chuyển đổi lỗi quanh bước inference

## 14. Contract Testing for Microservices / Contract Testing cho Microservices (Tier 2)

> ⚠️ Agent: Chỉ áp dụng section này sau khi user xác nhận kiến trúc Microservices.
> Xem `16-System_architecture_conventions.md` §3 để biết tiêu chí.

### 14.1 Consumer-Driven Contract Testing (CDC) is mandatory / CDC là bắt buộc

#### EN
🔴 **MUST**: In a microservice architecture (Tier 2), every public inter-service interface (REST, gRPC, or async Event) must be verified by Contract Tests, preferably using the Consumer-Driven Contract (CDC) approach (e.g., using Pact).
Unit tests alone cannot prevent a provider service from changing an API shape and breaking downstream consumers. End-to-end (E2E) tests are too slow and flaky. Contract testing solves this by verifying the interface implicitly.

#### VI
🔴 **MUST**: Trong kiến trúc microservices (Tier 2), mọi giao tiếp công cộng giữa các service (REST, gRPC, hoặc async Event) phải được xác minh bằng Contract Test, ưu tiên cách tiếp cận Consumer-Driven Contract (CDC) (ví dụ: dùng Pact).
Chỉ dùng unit test không thể ngăn provider service đổi hình dáng API và làm gãy các consumer ở downstream. Test End-to-end (E2E) quá chậm và thiếu ổn định. Contract testing giải quyết vấn đề này bằng cách xác minh interface một cách tường minh.

### 14.2 Consumer defines the expectations / Consumer định nghĩa kỳ vọng

#### EN
🔴 **MUST**: The consumer writes tests defining exactly what fields it expects from the provider. These expectations generate a "Contract" (e.g., a Pact file).
The provider must then verify its API against this generated Contract before deploying. A Provider must NEVER deploy if it breaks a Consumer's contract.

#### VI
🔴 **MUST**: Consumer viết test định nghĩa chính xác những field nào nó kỳ vọng từ provider. Những kỳ vọng này tạo ra một "Contract" (ví dụ: file Pact).
Provider sau đó phải xác minh API của mình với Contract này trước khi deploy. Provider KHÔNG BAO GIỜ được deploy nếu nó phá vỡ contract của Consumer.

### 14.3 Publish contracts to a Broker / Đẩy contract lên Broker

#### EN
🟡 **SHOULD**: Use a Contract Broker (like Pact Broker) to store and share contracts between services, rather than sharing them via Git or artifact repositories.
This enables the `can-i-deploy` check in CI/CD pipelines.

#### VI
🟡 **SHOULD**: Dùng Contract Broker (như Pact Broker) để lưu trữ và chia sẻ contract giữa các service, thay vì share qua Git hoặc artifact repository.
Điều này cho phép thực hiện bước check `can-i-deploy` trong CI/CD pipeline.

## 15. Anti-patterns / Mẫu xấu cần tránh

### EN
Avoid:

- mixing unit, integration, and performance tests in one file
- relying on real external systems in unit tests
- mocking away the very behavior being tested
- hidden fixture complexity
- vague test names
- unstable tests dependent on current time, execution order, or machine state
- asserting too much implementation detail without need
- using coverage as the only quality target
- embedding custom test runners inside test modules
- (Microservices) relying solely on E2E tests instead of Contract Tests for integration

### VI
Tránh:

- trộn unit, integration, và performance test trong một file
- phụ thuộc vào hệ thống ngoài thật trong unit test
- mock mất chính hành vi đang được test
- fixture phức tạp ẩn
- tên test mơ hồ
- test không ổn định do phụ thuộc thời gian hiện tại, thứ tự chạy, hoặc trạng thái máy
- assert quá nhiều vào implementation detail mà không cần thiết
- dùng coverage làm mục tiêu chất lượng duy nhất
- nhét custom test runner vào module test
- (Microservices) chỉ dựa vào E2E test thay vì Contract Test cho integration

## 16. Review checklist / Checklist review

### EN
When reviewing unit tests, check:

- Does the test verify one clear behavior?
- Is the test isolated from external systems?
- Are fixtures readable and justified?
- Are mocks used correctly and only where needed?
- Is the test name explicit?
- Are edge cases and failure paths covered?
- Is the test deterministic?
- Is the file focused on one responsibility?
- Is the test type correct for the scenario?
- Is coverage being used meaningfully rather than mechanically?
- (Microservices) Are Contract Tests defined for new API or event schemas?

### VI
Khi review unit test, cần kiểm tra:

- Test có xác minh một hành vi rõ ràng không?
- Test có được cô lập khỏi hệ thống ngoài không?
- Fixture có dễ đọc và có lý do rõ ràng không?
- Mock có được dùng đúng chỗ và chỉ khi cần không?
- Tên test có rõ ràng không?
- Edge case và failure path có được bao phủ không?
- Test có tính xác định không?
- File có tập trung vào một trách nhiệm không?
- Loại test có đúng với tình huống không?
- Coverage có đang được dùng có ý nghĩa thay vì máy móc không?
- (Microservices) Contract Test có được định nghĩa cho API hoặc event schema mới không?

## 17. Definition of done / Điều kiện hoàn thành

### EN
A module is testing-compliant only if:

- important business behavior is covered by unit tests
- expected edge cases and failure paths are tested
- tests are deterministic and isolated
- test names clearly describe behavior
- fixtures, mocks, and test configuration remain readable and intentional
- unit tests are separated from integration and performance tests
- coverage is reviewed as a signal, not treated as the sole success criterion
- (Microservices) public interfaces and events are covered by Contract Tests (CDC)

### VI
Một module chỉ được coi là tuân thủ testing convention khi:

- hành vi nghiệp vụ quan trọng được bao phủ bằng unit test
- edge case và failure path dự kiến đã được test
- test có tính xác định và được cô lập
- tên test mô tả rõ hành vi
- fixture, mock, và test configuration dễ đọc, có chủ đích
- unit test được tách khỏi integration test và performance test
- coverage được xem như tín hiệu hỗ trợ, không phải tiêu chí thành công duy nhất
- (Microservices) giao tiếp công cộng và event được bao phủ bởi Contract Test (CDC)
