# 09-Git-PR-Release / Quy ước về Git, PR, và Release

## 1. Purpose / Mục đích

### EN
This document defines the conventions for source control, pull requests, code review, merging, and releasing software changes.  
Its purpose is to keep code changes traceable, reviewable, safe to merge, and safe to release.

### VI
Tài liệu này định nghĩa các quy ước về quản lý mã nguồn, pull request, code review, merge, và release thay đổi phần mềm.  
Mục tiêu là giữ cho mọi thay đổi code có thể truy vết, dễ review, an toàn để merge, và an toàn để release.

## 2. Scope / Phạm vi

### EN
This document applies to:

- branch creation and naming
- commit history and commit messages
- pull request structure
- code review expectations
- merge rules
- release preparation
- tagging and versioning
- rollback expectations

### VI
Tài liệu này áp dụng cho:

- tạo branch và đặt tên branch
- lịch sử commit và commit message
- cấu trúc pull request
- kỳ vọng khi code review
- luật merge
- chuẩn bị release
- tagging và versioning
- kỳ vọng về rollback

## 3. Core principles / Nguyên tắc cốt lõi

### 3.1 Every change must be traceable / Mọi thay đổi phải truy vết được

#### EN
Every meaningful code change must be attributable, reviewable, and understandable after the fact.

#### VI
Mọi thay đổi code có ý nghĩa phải truy vết được, review được, và hiểu lại được về sau.

### 3.2 Small, clear changes are preferred / Ưu tiên thay đổi nhỏ, rõ ràng

#### EN
Smaller and focused changes are preferred over large mixed changes.

#### VI
Ưu tiên thay đổi nhỏ và tập trung hơn là những thay đổi lớn, trộn nhiều mục đích.

### 3.3 No change is complete without validation / Không thay đổi nào được coi là hoàn tất nếu chưa được xác minh

#### EN
A change must be tested, reviewed, and explained before it is considered ready to merge or release.

#### VI
Một thay đổi phải được test, review, và giải thích rõ trước khi được coi là sẵn sàng để merge hoặc release.

## 4. Branching conventions / Quy ước về branch

### 4.1 Mainline branches must be protected / Branch chính phải được bảo vệ

#### EN
Primary branches such as main or master must be protected and must not be used for direct unreviewed commits.

#### VI
Các branch chính như main hoặc master phải được bảo vệ và không được dùng cho commit trực tiếp chưa review.

### 4.2 Create a dedicated branch for each focused change / Tạo branch riêng cho mỗi thay đổi có trọng tâm

#### EN
Each feature, fix, or maintenance task should be developed in its own branch.

#### VI
Mỗi feature, bug fix, hoặc tác vụ bảo trì nên được thực hiện trên branch riêng.

### 4.3 Branch names must be descriptive / Tên branch phải có ý nghĩa rõ ràng

#### EN
Branch names should use a short, descriptive prefix and a meaningful subject.

#### VI
Tên branch nên dùng prefix ngắn gọn và phần mô tả có ý nghĩa.

#### Preferred patterns / Mẫu ưu tiên
- feature/user-auth
- fix/payment-timeout
- chore/update-lint-rules
- test/add-file-processor-tests
- docs/update-architecture-rules

### 4.4 Avoid vague branch names / Tránh tên branch mơ hồ

#### EN
Avoid names such as:

- update
- new-branch
- fix-stuff
- temp
- misc

#### VI
Tránh các tên như:

- update
- new-branch
- fix-stuff
- temp
- misc
-...


## 5. Commit conventions / Quy ước về commit

### 5.1 Every commit must have a clear purpose / Mỗi commit phải có mục đích rõ ràng

#### EN
A commit should represent one logical step or one coherent unit of change.

#### VI
Một commit nên đại diện cho một bước logic hoặc một đơn vị thay đổi nhất quán.

### 5.2 Commit messages must be explicit / Commit message phải rõ ràng

#### EN
Commit messages must state what changed, using concise and readable language.

#### VI
Commit message phải nêu rõ thay đổi là gì, dùng ngôn ngữ ngắn gọn và dễ đọc.

### 5.3 Prefer conventional prefixes / Ưu tiên prefix theo loại thay đổi

#### EN
Use consistent prefixes such as:

- feat:
- fix:
- refactor:
- test:
- docs:
- chore:

#### VI
Dùng prefix nhất quán như:

- feat:
- fix:
- refactor:
- test:
- docs:
- chore:

#### Examples / Ví dụ
- feat: add retry logic for zip ingestion
- fix: handle missing config value in file processor
- test: add unit tests for feature transformer
- docs: update dependency conventions

### 5.4 Avoid mixed-purpose commits / Tránh commit trộn nhiều mục đích

#### EN
Do not mix unrelated refactors, bug fixes, formatting, and new features in the same commit without a strong reason.

#### VI
Không trộn refactor, bug fix, formatting, và feature mới không liên quan trong cùng một commit nếu không có lý do rất rõ.

### 5.5 Keep history reviewable / Giữ lịch sử commit dễ review

#### EN
Prefer a commit history that helps reviewers understand the progression of the change.

#### VI
Ưu tiên lịch sử commit giúp reviewer hiểu tiến trình thay đổi.

## 6. Pull request conventions / Quy ước về pull request

### 6.1 Every meaningful change must go through a PR / Mọi thay đổi có ý nghĩa phải đi qua PR

#### EN
Changes that affect shared codebases must be reviewed through a pull request unless an emergency procedure explicitly allows otherwise.

#### VI
Các thay đổi ảnh hưởng tới codebase dùng chung phải được review qua pull request, trừ khi có quy trình khẩn cấp cho phép ngoại lệ.

### 6.2 PR titles must be clear / Tiêu đề PR phải rõ ràng

#### EN
The PR title should summarize the main change in one line.

#### VI
Tiêu đề PR phải tóm tắt thay đổi chính trong một dòng.

### 6.3 PR descriptions must explain intent / Mô tả PR phải giải thích được ý đồ

#### EN
Each PR should include:

- what changed
- why it changed
- affected components
- how it was tested
- risks or limitations
- breaking changes if any

#### VI
Mỗi PR nên bao gồm:

- thay đổi gì
- vì sao thay đổi
- thành phần nào bị ảnh hưởng
- đã test như thế nào
- rủi ro hoặc giới hạn
- breaking change nếu có

### 6.4 Prefer small and focused PRs / Ưu tiên PR nhỏ và tập trung

#### EN
PRs should be small enough to review effectively.  
If a change becomes too large, split it into smaller, coherent PRs.

#### VI
PR nên đủ nhỏ để review hiệu quả.  
Nếu thay đổi trở nên quá lớn, hãy tách thành các PR nhỏ hơn nhưng vẫn nhất quán.

### 6.5 PRs must not hide unrelated work / PR không được giấu thay đổi không liên quan

#### EN
A PR must not include unrelated refactors, formatting sweeps, or opportunistic cleanup unless clearly stated and justified.

#### VI
PR không được chứa refactor không liên quan, format hàng loạt, hoặc cleanup tiện tay nếu chưa được nêu rõ và giải thích hợp lý.

## 7. Code review conventions / Quy ước về code review

### 7.1 Review checks correctness first / Review ưu tiên tính đúng trước

#### EN
Review must first verify that the change is correct, safe, and understandable.

#### VI
Review trước hết phải xác minh rằng thay đổi là đúng, an toàn, và dễ hiểu.

### 7.2 Review must consider conventions and architecture / Review phải xét cả convention và kiến trúc

#### EN
Reviewers should check:

- structure and layer boundaries
- naming and style
- dependency direction
- config and secret handling
- test coverage and test quality
- logging and error handling
- backward compatibility where relevant

#### VI
Reviewer nên kiểm tra:

- cấu trúc và ranh giới layer
- naming và style
- chiều dependency
- xử lý config và secret
- test coverage và chất lượng test
- logging và error handling
- backward compatibility khi phù hợp

### 7.3 Feedback must be actionable / Feedback phải hành động được

#### EN
Review feedback should be specific, concrete, and tied to a clear concern.

#### VI
Feedback khi review phải cụ thể, rõ ràng, và gắn với một concern xác định.

### 7.4 Approval means merge-ready, not “looks fine enough” / Approval nghĩa là sẵn sàng merge, không phải “có vẻ ổn”

#### EN
A reviewer should approve only when the change is genuinely ready to merge under the project’s standards.

#### VI
Reviewer chỉ nên approve khi thay đổi thực sự sẵn sàng để merge theo chuẩn của dự án.

## 8. Merge rules / Luật merge

### 8.1 Do not merge with failing checks / Không merge khi check đang fail

#### EN
A PR must not be merged when required CI checks are failing.

#### VI
PR không được merge khi các CI check bắt buộc đang fail.

### 8.2 Do not merge without required review / Không merge nếu chưa đủ review bắt buộc

#### EN
A PR must not be merged without the required approvals defined by the team.

#### VI
PR không được merge nếu chưa đủ approval bắt buộc theo quy định của team.

### 8.3 Merge method must be consistent / Cách merge phải nhất quán

#### EN
The repository should standardize one preferred merge method such as:

- squash merge
- rebase merge
- merge commit

#### VI
Repository nên chuẩn hóa một cách merge ưu tiên như:

- squash merge
- rebase merge
- merge commit

### 8.4 Prefer a clean mainline history / Ưu tiên lịch sử branch chính sạch

#### EN
Choose a merge approach that preserves clarity and keeps mainline history understandable.

#### VI
Chọn cách merge giữ được sự rõ ràng và làm cho lịch sử branch chính dễ hiểu.

## 9. Release conventions / Quy ước về release

### 9.1 Release must be intentional / Release phải có chủ đích

#### EN
A release is a controlled event, not merely any merge to the main branch.

#### VI
Release là một sự kiện có kiểm soát, không chỉ đơn giản là bất kỳ merge nào vào branch chính.

### 9.2 Every release must identify what is being released / Mỗi release phải xác định rõ cái gì đang được phát hành

#### EN
A release should clearly identify:

- version or tag
- included changes
- affected services or modules
- known risks or limitations

#### VI
Mỗi release nên xác định rõ:

- version hoặc tag
- các thay đổi được đưa vào
- service hoặc module bị ảnh hưởng
- rủi ro hoặc giới hạn đã biết

### 9.3 Versioning must be consistent / Versioning phải nhất quán

#### EN
Use a consistent release versioning strategy, such as semantic versioning or an agreed internal version scheme.

#### VI
Dùng một chiến lược versioning nhất quán, như semantic versioning hoặc scheme nội bộ đã thống nhất.

### 9.4 Release notes must be meaningful / Release note phải có ý nghĩa

#### EN
Release notes should summarize what matters operationally and functionally, not just repeat raw commit messages.

#### VI
Release note nên tóm tắt những gì có ý nghĩa về vận hành và chức năng, không chỉ lặp lại raw commit message.

## 10. Tagging and version markers / Quy ước về tag và mốc version

### 10.1 Tags must be explicit and stable / Tag phải rõ ràng và ổn định

#### EN
Release tags should follow a consistent naming format.

#### VI
Tag release phải theo một format nhất quán.

#### Examples / Ví dụ
- v1.2.0
- v2.0.1
- release-2026-03-17

### 10.2 Do not create ambiguous release markers / Không tạo mốc release mơ hồ

#### EN
Avoid vague tags such as:

- latest
- final
- new
- release2

#### VI
Tránh các tag mơ hồ như:

- latest
- final
- new
- release2

## 11. Rollback and recovery expectations / Kỳ vọng về rollback và recovery

### 11.1 Every release should consider rollback / Mọi release nên tính đến rollback

#### EN
Changes should be released in a way that allows safe rollback or recovery when possible.

#### VI
Thay đổi nên được release theo cách cho phép rollback hoặc recovery an toàn khi có thể.

### 11.2 Breaking changes must be explicit / Breaking change phải được nêu rõ

#### EN
Breaking changes must be identified before merge or release.

#### VI
Breaking change phải được nhận diện rõ trước khi merge hoặc release.

### 11.3 Migrations and irreversible changes require extra care / Migration và thay đổi không đảo ngược cần cẩn trọng hơn

#### EN
Schema changes, data migrations, and destructive changes must include a rollback or mitigation plan.

#### VI
Schema change, data migration, và thay đổi mang tính phá hủy phải có kế hoạch rollback hoặc giảm thiểu rủi ro.

## 12. CI/CD expectations / Kỳ vọng với CI/CD

### 12.1 CI must validate merge readiness / CI phải xác minh trạng thái sẵn sàng merge

#### EN
CI should check the quality gates relevant to the repository, such as tests, linting, formatting, type checks, security checks, and packaging or build checks.

For detailed CI/CD pipeline structure, job scoping, secret handling, and deployment rules, follow `14-infrastructure_deployment` §10.

#### VI
CI nên kiểm tra các quality gate phù hợp với repository, như tests, linting, formatting, type checks, security checks, và packaging hoặc build checks.

Về cấu trúc CI/CD pipeline chi tiết, phạm vi job, xử lý secret, và quy tắc deployment, tuân theo `14-infrastructure_deployment` §10.

### 12.2 Release pipelines must be controlled / Pipeline release phải được kiểm soát

#### EN
Release pipelines should be explicit, repeatable, and auditable.

#### VI
Pipeline release phải rõ ràng, lặp lại được, và có thể kiểm toán.

## 13. Agent and automation rules / Quy ước cho agent và tự động hóa

### 13.1 Agents must keep changes focused / Agent phải giữ thay đổi có trọng tâm

#### EN
Coding agents should avoid generating oversized, mixed-purpose changes when the task can be split more cleanly.

#### VI
Coding agent phải tránh sinh ra thay đổi quá lớn, trộn nhiều mục đích khi nhiệm vụ có thể tách nhỏ rõ ràng hơn.

### 13.2 Agents must describe what changed / Agent phải mô tả được đã thay đổi gì

#### EN
Generated PR summaries or change notes must explain:

- what changed
- why it changed
- what was tested
- what remains risky or incomplete

#### VI
PR summary hoặc ghi chú thay đổi do agent sinh ra phải giải thích:

- thay đổi gì
- vì sao thay đổi
- đã test gì
- còn rủi ro hoặc phần chưa hoàn tất nào

### 13.3 Agents must not bypass review discipline / Agent không được phá vỡ kỷ luật review

#### EN
Automated changes must still respect repository review and merge rules.

#### VI
Thay đổi tự động vẫn phải tôn trọng quy tắc review và merge của repository.

## 14. Anti-patterns / Mẫu xấu cần tránh

### EN
Avoid:

- direct unreviewed commits to protected branches
- vague branch names
- meaningless commit messages
- giant mixed-purpose PRs
- merging with failing CI
- releasing without notes or clear version markers
- hiding breaking changes in unrelated PRs
- using “temporary” fixes as normal merge practice
- treating review as a rubber stamp

### VI
Tránh:

- commit trực tiếp chưa review vào branch được bảo vệ
- tên branch mơ hồ
- commit message vô nghĩa
- PR khổng lồ trộn nhiều mục đích
- merge khi CI đang fail
- release mà không có note hoặc version marker rõ ràng
- giấu breaking change trong PR không liên quan
- biến fix “tạm” thành thực hành merge bình thường
- xem review như thủ tục đóng dấu cho xong

## 15. Review checklist / Checklist review

### EN
When reviewing Git/PR/release discipline, check:

- Is the branch name clear?
- Are commits focused and readable?
- Does the PR explain what and why?
- Is the change small enough to review well?
- Have tests and required checks passed?
- Are risks and breaking changes clearly stated?
- Is the merge method consistent with repository policy?
- Is the release or rollback impact understood?

### VI
Khi review kỷ luật Git/PR/release, cần kiểm tra:

- Tên branch có rõ ràng không?
- Commit có tập trung và dễ đọc không?
- PR có giải thích được thay đổi gì và vì sao không?
- Thay đổi có đủ nhỏ để review tốt không?
- Test và các check bắt buộc đã pass chưa?
- Rủi ro và breaking change có được nêu rõ không?
- Cách merge có nhất quán với policy của repository không?
- Ảnh hưởng tới release hoặc rollback đã được hiểu rõ chưa?

## 16. Definition of done / Điều kiện hoàn thành

### EN
A change is Git/PR/release compliant only if:

- it is developed in a properly named branch
- its commits are focused and understandable
- it goes through a clear pull request
- it is reviewed against project standards
- required checks pass before merge
- release-relevant changes are versioned and documented clearly
- rollback or recovery implications are considered where relevant

### VI
Một thay đổi chỉ được coi là tuân thủ Git/PR/release convention khi:

- nó được phát triển trên branch đặt tên đúng
- commit của nó có trọng tâm và dễ hiểu
- nó đi qua một pull request rõ ràng
- nó được review theo chuẩn của dự án
- các check bắt buộc pass trước khi merge
- các thay đổi liên quan tới release được version hóa và tài liệu hóa rõ ràng
- ảnh hưởng tới rollback hoặc recovery được cân nhắc khi phù hợp
