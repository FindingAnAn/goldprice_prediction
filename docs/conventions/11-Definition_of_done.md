# 11-Definition-of-Done / Quy ước về Definition of Done

## 1. Purpose / Mục đích

### EN
This document defines what “done” means for a code change, module, feature, or delivery unit.  
Its purpose is to ensure that work is not considered complete merely because code exists, but only when the change is correct, reviewable, testable, operable, and safe to hand over.

### VI
Tài liệu này định nghĩa “done” nghĩa là gì đối với một thay đổi code, module, feature, hoặc đơn vị bàn giao.  
Mục tiêu là đảm bảo một công việc không được coi là hoàn thành chỉ vì đã có code, mà chỉ khi thay đổi đó đúng, có thể review, có thể kiểm thử, có thể vận hành, và an toàn để bàn giao.

## 2. Scope / Phạm vi

### EN
This document applies to:

- code changes
- modules and services
- features and use cases
- pull requests
- release candidates
- agent-generated changes
- manual development work submitted for review

### VI
Tài liệu này áp dụng cho:

- thay đổi code
- module và service
- feature và use case
- pull request
- release candidate
- thay đổi do agent sinh ra
- công việc phát triển thủ công được đưa vào review

## 3. Core principles / Nguyên tắc cốt lõi

### 3.1 Done means usable, not merely written / Done nghĩa là dùng được, không chỉ là đã viết xong

#### EN
Work is not done just because implementation exists.  
It is done only when the intended outcome is working and verifiable.

#### VI
Một công việc không được coi là done chỉ vì đã có implementation.  
Nó chỉ được coi là done khi kết quả mong muốn thực sự hoạt động và có thể xác minh được.

### 3.2 Done must be evidence-based / Done phải dựa trên bằng chứng

#### EN
A claim that work is complete must be supported by observable evidence such as tests, review context, logs, screenshots, examples, or validation results.

#### VI
Việc khẳng định một công việc đã hoàn thành phải được hỗ trợ bằng bằng chứng có thể quan sát được như test, ngữ cảnh review, log, screenshot, ví dụ, hoặc kết quả xác minh.

### 3.3 Done includes quality, safety, and operability / Done bao gồm chất lượng, an toàn, và khả năng vận hành

#### EN
A change is not done if it works functionally but is unsafe, untestable, unreviewable, or operationally blind.

#### VI
Một thay đổi chưa được coi là done nếu nó chỉ chạy đúng về mặt chức năng nhưng lại không an toàn, không thể kiểm thử, khó review, hoặc không thể quan sát khi vận hành.

### 3.4 Partial completion must be named explicitly / Hoàn thành một phần phải được gọi tên rõ ràng

#### EN
If a task is only partially complete, it must be described as partial, draft, prototype, or WIP.  
It must not be presented as done.

#### VI
Nếu một tác vụ mới chỉ hoàn thành một phần, nó phải được mô tả rõ là partial, draft, prototype, hoặc WIP.  
Không được trình bày nó như thể đã done.

## 4. Unit of completion / Đơn vị được đánh giá là hoàn thành

### 4.1 A code unit may be done / Một đơn vị code có thể được coi là done

#### EN
A function, class, module, or component may be considered done if it satisfies the conventions relevant to its scope.

#### VI
Một function, class, module, hoặc component có thể được coi là done nếu nó thỏa các convention phù hợp với phạm vi của nó.

### 4.2 A feature may be done / Một feature có thể được coi là done

#### EN
A feature is done when its user-visible or workflow-visible behavior is complete, validated, and integrated with the necessary boundaries.

#### VI
Một feature được coi là done khi hành vi nhìn thấy được từ phía người dùng hoặc luồng nghiệp vụ đã hoàn chỉnh, được xác minh, và tích hợp với các boundary cần thiết.

### 4.3 A pull request may be done / Một pull request có thể được coi là done

#### EN
A pull request is done when the change is review-ready, traceable, tested appropriately, and safe to merge.

#### VI
Một pull request được coi là done khi thay đổi bên trong nó sẵn sàng để review, truy vết được, được test phù hợp, và an toàn để merge.

### 4.4 A release unit may be done / Một đơn vị release có thể được coi là done

#### EN
A release candidate is done only when deployment, rollback, compatibility, and operational expectations have been considered.

#### VI
Một release candidate chỉ được coi là done khi các kỳ vọng về triển khai, rollback, tương thích, và vận hành đã được cân nhắc.

## 5. Functional completeness / Hoàn chỉnh về chức năng

### 5.1 Intended behavior must be implemented / Hành vi mục tiêu phải được triển khai

#### EN
The required business or technical behavior must exist and match the accepted intent of the change.

#### VI
Hành vi nghiệp vụ hoặc kỹ thuật được yêu cầu phải tồn tại và khớp với ý đồ đã được chấp nhận của thay đổi.

### 5.2 Expected success and failure paths must be handled / Luồng thành công và thất bại dự kiến phải được xử lý

#### EN
A change is not complete if only the happy path is implemented while expected failure paths remain undefined.

#### VI
Một thay đổi chưa hoàn chỉnh nếu mới chỉ xử lý happy path còn các failure path dự kiến vẫn chưa được định nghĩa hoặc xử lý.

### 5.3 Edge cases must be handled or explicitly constrained / Edge case phải được xử lý hoặc giới hạn rõ ràng

#### EN
Relevant edge cases must either be supported, rejected intentionally, or documented as out of scope.

#### VI
Các edge case liên quan phải được hỗ trợ, bị từ chối có chủ đích, hoặc được tài liệu hóa là ngoài phạm vi.

## 6. Design and code quality completeness / Hoàn chỉnh về thiết kế và chất lượng code

### 6.1 Structure and boundaries must remain consistent / Cấu trúc và boundary phải nhất quán

#### EN
The change must respect the intended architecture, module boundaries, and dependency direction.

#### VI
Thay đổi phải tôn trọng kiến trúc dự kiến, ranh giới module, và hướng phụ thuộc.

### 6.2 Code conventions must be respected / Các coding convention phải được tuân thủ

#### EN
Relevant conventions for naming, imports, dependencies, configuration, and API design must be followed where applicable.

#### VI
Các convention liên quan tới naming, import, dependency, cấu hình, và thiết kế API phải được tuân thủ khi phù hợp.

### 6.3 Temporary artifacts must be removed / Các dấu vết tạm thời phải được dọn sạch

#### EN
Debug leftovers, commented-out experiments, dead code, and misleading placeholders must not remain in a done change.

#### VI
Các phần dư như debug tạm, code bị comment bỏ, dead code, và placeholder gây hiểu nhầm không được tồn tại trong một thay đổi đã done.

## 7. Configuration and environment readiness / Mức sẵn sàng về cấu hình và môi trường

### 7.1 Runtime behavior must not depend on hidden local assumptions / Hành vi runtime không được phụ thuộc vào giả định local ẩn

#### EN
A change must not require undocumented local machine behavior to work correctly.

#### VI
Một thay đổi không được phụ thuộc vào các hành vi riêng của máy local mà không được tài liệu hóa.

### 7.2 Required configuration must be explicit and validated / Cấu hình bắt buộc phải rõ ràng và được kiểm tra hợp lệ

#### EN
New configuration, environment variables, and runtime requirements must be defined clearly and validated where appropriate.

#### VI
Các cấu hình mới, biến môi trường, và yêu cầu runtime phải được nêu rõ và được kiểm tra hợp lệ khi phù hợp.

### 7.3 Environment-specific impact must be understood / Ảnh hưởng theo môi trường phải được hiểu rõ

#### EN
The change must account for development, test, staging, and production implications when those environments matter.

#### VI
Thay đổi phải tính đến tác động trên môi trường development, test, staging, và production khi các môi trường này có ý nghĩa.

## 8. Error handling and operational readiness / Mức sẵn sàng về xử lý lỗi và vận hành

### 8.1 Expected errors must be handled intentionally / Lỗi dự kiến phải được xử lý có chủ đích

#### EN
Expected validation, business, and technical failure modes must be handled at the appropriate boundary.

#### VI
Các failure mode dự kiến về validation, nghiệp vụ, và kỹ thuật phải được xử lý tại boundary phù hợp.

### 8.2 Operational visibility must exist where relevant / Phải có khả năng quan sát vận hành khi phù hợp

#### EN
If the change affects runtime behavior, it should include the necessary logs, metrics, health checks, alerts, or traces for safe operation.

#### VI
Nếu thay đổi ảnh hưởng tới hành vi runtime, nó nên có log, metric, health check, alert, hoặc trace cần thiết để vận hành an toàn.

### 8.3 Recovery behavior must not be accidental / Hành vi phục hồi không được mang tính ngẫu nhiên

#### EN
Retries, fallback, rollback, or failure communication must be intentional where they are relevant to the change.

#### VI
Retry, fallback, rollback, hoặc cách thông báo failure phải có chủ đích ở những nơi chúng liên quan tới thay đổi.

## 9. Testing completeness / Hoàn chỉnh về kiểm thử

### 9.1 Important behavior must be verified / Hành vi quan trọng phải được xác minh

#### EN
Important business or system behavior must be covered by appropriate tests or equivalent validation.

#### VI
Các hành vi quan trọng của nghiệp vụ hoặc hệ thống phải được bao phủ bằng test phù hợp hoặc hình thức xác minh tương đương.

### 9.2 Test depth must match risk / Độ sâu kiểm thử phải tương xứng với rủi ro

#### EN
Critical or risky changes require stronger verification than trivial edits.

#### VI
Các thay đổi quan trọng hoặc có rủi ro cao cần mức xác minh mạnh hơn so với các chỉnh sửa nhỏ.

### 9.3 Non-automated verification must be explicit / Xác minh không tự động phải được nêu rõ

#### EN
If manual testing, exploratory validation, or temporary review steps are used, they must be described explicitly.

#### VI
Nếu có dùng test thủ công, xác minh khám phá, hoặc bước review tạm thời, chúng phải được mô tả rõ ràng.

## 10. Security and data safety completeness / Hoàn chỉnh về bảo mật và an toàn dữ liệu

### 10.1 No unsafe secret handling may remain / Không được còn cách xử lý secret không an toàn

#### EN
No real credential, token, or secret may be committed, hard-coded, or exposed through outputs.

#### VI
Không được có credential, token, hoặc secret thật bị commit, hard-code, hoặc làm lộ qua output.

### 10.2 External input and output must be treated safely / Input và output từ bên ngoài phải được xử lý an toàn

#### EN
Validation, sanitization, redaction, and safe error exposure must be applied where the change crosses external boundaries.

#### VI
Validation, sanitization, che dữ liệu, và đưa lỗi ra ngoài an toàn phải được áp dụng ở các boundary giao tiếp với bên ngoài.

### 10.3 Permissions and access assumptions must be intentional / Giả định về quyền và truy cập phải có chủ đích

#### EN
A change must not silently broaden access, bypass authorization, or weaken safety assumptions.

#### VI
Một thay đổi không được âm thầm mở rộng quyền truy cập, bỏ qua authorization, hoặc làm yếu đi các giả định an toàn.

## 11. Documentation completeness / Hoàn chỉnh về tài liệu

### 11.1 Necessary usage or maintenance documentation must be updated / Tài liệu sử dụng hoặc bảo trì cần thiết phải được cập nhật

#### EN
Relevant README, setup steps, operational notes, or developer guidance must be updated when behavior changes.

#### VI
README, bước cài đặt, ghi chú vận hành, hoặc hướng dẫn cho developer liên quan phải được cập nhật khi hành vi thay đổi.

### 11.2 Interface changes must be documented / Thay đổi interface phải được tài liệu hóa

#### EN
Changes to APIs, events, configs, schemas, commands, or operational procedures must be documented where consumers depend on them.

#### VI
Các thay đổi tới API, event, config, schema, command, hoặc quy trình vận hành phải được tài liệu hóa khi có bên sử dụng phụ thuộc vào chúng.

### 11.3 Limitations and deferred work must be visible / Giới hạn và phần hoãn lại phải hiển thị rõ

#### EN
Known limitations, trade-offs, and deferred follow-up work must be stated clearly instead of being hidden.

#### VI
Các giới hạn đã biết, trade-off, và phần việc follow-up bị hoãn phải được nêu rõ thay vì bị che đi.

## 12. Review and merge readiness / Mức sẵn sàng để review và merge

### 12.1 A done change must be reviewable / Một thay đổi done phải review được

#### EN
A reviewer must be able to understand what changed, why it changed, and how it was validated.

#### VI
Reviewer phải có khả năng hiểu thay đổi gì, vì sao thay đổi, và nó đã được xác minh như thế nào.

### 12.2 Required checks must pass / Các check bắt buộc phải pass

#### EN
Linting, tests, build checks, type checks, or other project-required validations must pass before a change is treated as done.

#### VI
Linting, test, build check, type check, hoặc các bước xác minh bắt buộc khác của dự án phải pass trước khi một thay đổi được coi là done.

### 12.3 The delivery unit must be safe to hand over / Đơn vị bàn giao phải an toàn để chuyển giao

#### EN
A done change must be understandable and usable by another developer, reviewer, operator, or future maintainer.

#### VI
Một thay đổi done phải đủ dễ hiểu và sử dụng được đối với developer khác, reviewer, operator, hoặc người bảo trì trong tương lai.

## 13. Exceptions and non-done states / Ngoại lệ và trạng thái chưa done

### 13.1 WIP is not done / WIP không phải là done

#### EN
Work in progress may be shareable, but it must not be labeled as complete.

#### VI
Công việc đang làm dở có thể được chia sẻ, nhưng không được gắn nhãn là đã hoàn thành.

### 13.2 Deferred work must be explicit and bounded / Phần việc hoãn lại phải rõ ràng và có ranh giới

#### EN
If something is intentionally deferred, it must be recorded clearly with scope and reason.

#### VI
Nếu có phần việc được cố ý hoãn lại, nó phải được ghi rõ cùng với phạm vi và lý do.

### 13.3 Emergency exceptions require explicit acknowledgement / Ngoại lệ khẩn cấp cần được ghi nhận rõ ràng

#### EN
Emergency changes may use a reduced process, but the deviation must be explicit, reviewable afterward, and followed by remediation if needed.

#### VI
Các thay đổi khẩn cấp có thể đi theo quy trình rút gọn, nhưng phần sai lệch phải được nêu rõ, có thể review lại sau, và có bước khắc phục nếu cần.

## 14. Anti-patterns / Mẫu xấu cần tránh

### EN
Avoid the following:

- claiming “done” when only the happy path works
- calling something done without tests or equivalent validation
- merging work that still depends on hidden local setup
- leaving TODOs that are actually blockers
- hiding known risks in PR descriptions or handover notes
- treating review comments as optional after declaring completion
- calling a change done while observability, rollback, or documentation is still missing where clearly needed

### VI
Tránh các tình huống sau:

- nói là “done” khi mới chỉ chạy được happy path
- gọi một thay đổi là done khi chưa có test hoặc xác minh tương đương
- merge công việc vẫn còn phụ thuộc vào setup local ẩn
- để TODO nhưng thực chất là blocker
- che các rủi ro đã biết trong mô tả PR hoặc ghi chú bàn giao
- coi comment review là tùy chọn sau khi đã tuyên bố hoàn thành
- gọi một thay đổi là done trong khi observability, rollback, hoặc tài liệu còn thiếu rõ ràng ở nơi cần có

## 15. Review checklist / Checklist review

### EN
Before accepting a task, feature, or PR as done, check:

- does it satisfy the intended behavior?
- are expected failure paths handled?
- does it follow the relevant conventions?
- is configuration explicit and safe?
- is it tested or otherwise verified appropriately?
- does it avoid secret leakage and unsafe assumptions?
- is operational visibility sufficient?
- is documentation or handover context updated?
- is the change safe to review, merge, and maintain?

### VI
Trước khi chấp nhận một tác vụ, feature, hoặc PR là done, hãy kiểm tra:

- nó đã đáp ứng đúng hành vi mục tiêu chưa?
- các failure path dự kiến đã được xử lý chưa?
- nó có tuân thủ các convention liên quan không?
- cấu hình đã rõ ràng và an toàn chưa?
- nó đã được test hoặc xác minh phù hợp chưa?
- nó có tránh làm lộ secret và các giả định không an toàn không?
- khả năng quan sát khi vận hành đã đủ chưa?
- tài liệu hoặc ngữ cảnh bàn giao đã được cập nhật chưa?
- thay đổi này đã an toàn để review, merge, và bảo trì chưa?

## 16. Definition of done / Điều kiện hoàn thành

### EN
A task, module, feature, PR, or release unit is considered done only if:

- the intended behavior is implemented and verified
- relevant success paths, failure paths, and edge cases are handled or explicitly constrained
- applicable architecture and coding conventions are respected
- configuration and environment requirements are explicit
- testing or equivalent validation provides real evidence
- security, secret handling, and data safety expectations are satisfied
- operational concerns such as logging, observability, and recovery are addressed where relevant
- documentation, review context, and handover information are sufficient
- no material blocker is hidden behind the word “done”

### VI
Một tác vụ, module, feature, PR, hoặc đơn vị release chỉ được coi là done khi:

- hành vi mục tiêu đã được triển khai và xác minh
- các success path, failure path, và edge case liên quan đã được xử lý hoặc giới hạn rõ ràng
- các convention kiến trúc và coding liên quan được tuân thủ
- yêu cầu về cấu hình và môi trường được nêu rõ
- test hoặc hình thức xác minh tương đương cung cấp bằng chứng thực sự
- các kỳ vọng về bảo mật, xử lý secret, và an toàn dữ liệu được đáp ứng
- các khía cạnh vận hành như logging, observability, và recovery được xử lý ở nơi cần thiết
- tài liệu, ngữ cảnh review, và thông tin bàn giao là đủ
- không có blocker quan trọng nào bị che giấu phía sau từ “done”
