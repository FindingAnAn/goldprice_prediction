# 08-Security-Secrets / Quy ước về Security và Secrets

## 1. Purpose / Mục đích

### EN
This document defines the minimum security and secret-handling conventions that all code, configuration, and operational workflows must follow.  
Its purpose is to prevent avoidable security mistakes, reduce accidental data exposure, and ensure that sensitive information is handled safely by both developers and coding agents.

### VI
Tài liệu này định nghĩa các quy ước tối thiểu về bảo mật và xử lý secrets mà mọi code, cấu hình, và quy trình vận hành phải tuân theo.  
Mục tiêu là ngăn các sai sót bảo mật có thể tránh được, giảm nguy cơ lộ dữ liệu ngoài ý muốn, và đảm bảo thông tin nhạy cảm được xử lý an toàn bởi cả developer lẫn coding agent.

## 2. Scope / Phạm vi

### EN
This document applies to:

- source code
- configuration files
- environment variables
- secrets and credentials
- logs and error output
- test data and test settings
- CI/CD pipelines
- deployment and runtime settings

### VI
Tài liệu này áp dụng cho:

- source code
- file cấu hình
- biến môi trường
- secrets và credentials
- log và output lỗi
- test data và test settings
- CI/CD pipeline
- cấu hình triển khai và runtime

## 3. Core principles / Nguyên tắc cốt lõi

### 3.1 Secure by default / An toàn theo mặc định

#### EN
Code and configuration must default to safe behavior.  
Unsafe shortcuts must never become the default project pattern.

#### VI
Code và cấu hình phải mặc định theo hướng an toàn.  
Các lối tắt không an toàn không bao giờ được trở thành pattern mặc định của dự án.

### 3.2 Secrets must never live in source code / Secret không bao giờ được nằm trong source code

#### EN
Secrets must not be hard-coded, committed, or embedded directly in code, notebooks, configuration files, or scripts.

#### VI
Secret không được hard-code, commit, hoặc nhúng trực tiếp trong code, notebook, file cấu hình, hoặc script.

### 3.3 Least privilege must guide access / Quyền tối thiểu là nguyên tắc định hướng truy cập

#### EN
Every credential, token, account, and service identity should have only the minimum permissions needed.

#### VI
Mọi credential, token, account, và service identity chỉ nên có đúng mức quyền tối thiểu cần thiết.

### 3.4 Sensitive data must not leak through diagnostics / Dữ liệu nhạy cảm không được rò qua chẩn đoán hệ thống

#### EN
Logs, traces, exceptions, and debug output must never expose secrets or sensitive personal data.

#### VI
Log, trace, exception, và debug output không được làm lộ secret hoặc dữ liệu cá nhân nhạy cảm.

## 4. What counts as a secret / Những gì được coi là secret

### EN
Secrets include, but are not limited to:

- passwords
- API keys
- access tokens
- refresh tokens
- private keys
- connection strings with credentials
- signing secrets
- encryption keys
- cloud credentials
- webhook secrets

### VI
Secret bao gồm nhưng không giới hạn ở:

- mật khẩu
- API key
- access token
- refresh token
- private key
- connection string có chứa credential
- signing secret
- khóa mã hóa
- cloud credential
- webhook secret

## 5. Secret storage rules / Luật lưu trữ secret

### 5.1 Secrets must come from approved runtime sources / Secret phải đến từ nguồn runtime được phê duyệt

#### EN
Secrets must be loaded from approved secure sources such as:

- environment variables
- secret managers
- vault systems
- CI/CD secret stores
- deployment platform secret injection

#### VI
Secret phải được nạp từ các nguồn an toàn được phê duyệt như:

- biến môi trường
- secret manager
- hệ vault
- kho secret của CI/CD
- cơ chế inject secret của nền tảng triển khai

### 5.2 Do not store real secrets in repository files / Không lưu secret thật trong file của repository

#### EN
Real secrets must not appear in:

- source files
- .env.example
- config templates
- notebooks
- committed shell scripts
- documentation examples

#### VI
Secret thật không được xuất hiện trong:

- file source
- .env.example
- config template
- notebook
- shell script đã commit
- ví dụ trong tài liệu

### 5.3 Example files may contain placeholders only / File ví dụ chỉ được chứa placeholder

#### EN
Example files may contain placeholders such as:

- YOUR_API_KEY_HERE
- CHANGE_ME
- example.local
- postgres://user:password@host:5432/db only if clearly fake

#### VI
File ví dụ chỉ được chứa placeholder như:

- YOUR_API_KEY_HERE
- CHANGE_ME
- example.local
- postgres://user:password@host:5432/db chỉ khi rõ ràng là giả

## 6. Configuration and environment safety / An toàn cấu hình và môi trường

### 6.1 Configuration must separate secret and non-secret values / Cấu hình phải tách giá trị secret và không-secret

#### EN
Configuration should clearly distinguish:

- non-sensitive settings
- runtime-sensitive secrets

#### VI
Cấu hình phải phân biệt rõ:

- setting không nhạy cảm
- secret nhạy cảm theo runtime

### 6.2 Safe defaults are allowed only for non-sensitive values / Chỉ cho phép default an toàn với giá trị không nhạy cảm

#### EN
Defaults may be used for:

- localhost
- non-production ports
- local directories
- debug flags

Defaults must not be used for:

- real passwords
- production tokens
- signing keys
- sensitive endpoints requiring trust

#### VI
Chỉ cho phép default cho:

- localhost
- port không phải production
- thư mục local
- debug flag

Không được dùng default cho:

- mật khẩu thật
- token production
- signing key
- endpoint nhạy cảm đòi hỏi độ tin cậy

### 6.3 Environment-specific files must stay safe / File theo môi trường phải giữ an toàn

#### EN
Environment-specific configuration files must not contain real credentials unless they are generated, injected, or stored securely outside version control.

#### VI
File cấu hình theo môi trường không được chứa credential thật, trừ khi chúng được sinh ra, inject, hoặc lưu an toàn ngoài version control.

## 7. Logging, errors, and output safety / An toàn cho log, lỗi, và output

### 7.1 Never log secrets / Không bao giờ log secret

#### EN
Never log:

- passwords
- tokens
- raw authorization headers
- private keys
- full credentials
- unredacted connection strings

#### VI
Không bao giờ log:

- mật khẩu
- token
- raw authorization header
- private key
- full credential
- connection string chưa che giấu

### 7.2 Redact sensitive data before output / Che dữ liệu nhạy cảm trước khi output

#### EN
If sensitive values must be referenced for diagnostics, use redacted or masked forms.

#### VI
Nếu cần nhắc tới giá trị nhạy cảm để chẩn đoán, phải dùng dạng đã che hoặc mask.

#### Preferred / Ưu tiên
- token=***
- password=[REDACTED]
- api_key_prefix=sk-abc...

### 7.3 External error responses must stay safe / Response lỗi ra ngoài phải an toàn

#### EN
External responses must not reveal:

- stack traces
- SQL details
- internal hostnames
- raw vendor exceptions
- credential hints

#### VI
Response lỗi đưa ra ngoài không được làm lộ:

- stack trace
- chi tiết SQL
- hostname nội bộ
- raw exception của vendor
- gợi ý về credential

## 8. Input and data handling rules / Quy tắc xử lý input và dữ liệu

### 8.1 Never trust raw external input / Không tin tưởng raw input từ bên ngoài

#### EN
All external input must be validated at the proper boundary.

#### VI
Mọi input từ bên ngoài phải được validate tại boundary phù hợp.

### 8.2 Sensitive personal data must be minimized / Dữ liệu cá nhân nhạy cảm phải được tối thiểu hóa

#### EN
Only collect, process, log, and persist sensitive data when it is necessary for the system’s intended purpose.

#### VI
Chỉ thu thập, xử lý, log, và lưu trữ dữ liệu nhạy cảm khi thật sự cần cho mục đích của hệ thống.

### 8.3 Test data must not use real secrets or private production data / Test data không được dùng secret thật hoặc dữ liệu production riêng tư

#### EN
Use fake, synthetic, or safely anonymized test data.

#### VI
Dùng dữ liệu giả, dữ liệu tổng hợp, hoặc dữ liệu đã được ẩn danh an toàn cho test.

## 9. Access control and least privilege / Kiểm soát truy cập và quyền tối thiểu

### 9.1 Use the minimum permissions required / Dùng đúng mức quyền tối thiểu cần thiết

#### EN
Credentials and service accounts must have only the permissions needed for the intended job.

#### VI
Credential và service account chỉ được cấp đúng mức quyền cần cho tác vụ dự kiến.

### 9.2 Separate environments and credentials / Tách biệt môi trường và credential

#### EN
Development, staging, and production must not share the same credentials unless there is an explicitly approved exception.

#### VI
Development, staging, và production không được dùng chung credential, trừ khi có ngoại lệ được phê duyệt rõ ràng.

### 9.3 Avoid human overreach through shared powerful credentials / Tránh cấp quyền quá mức qua credential dùng chung

#### EN
Do not normalize the use of highly privileged shared credentials in routine development or testing.

#### VI
Không được coi việc dùng credential dùng chung có quyền quá cao là chuyện bình thường trong phát triển hoặc test hằng ngày.

## 10. Dependency and package hygiene / Quy ước an toàn với dependency và package

### 10.1 Add dependencies intentionally / Thêm dependency có chủ đích

#### EN
New packages and SDKs must be added intentionally and reviewed for necessity and trustworthiness.

#### VI
Package và SDK mới phải được thêm vào có chủ đích và được review về mức cần thiết và độ tin cậy.

### 10.2 Avoid unreviewed code execution or hidden downloads / Tránh thực thi code hoặc tải xuống ngầm chưa được review

#### EN
Do not introduce libraries or scripts that fetch code, secrets, or binaries from unknown sources without explicit review.

#### VI
Không đưa vào thư viện hoặc script có hành vi tải code, secret, hoặc binary từ nguồn không rõ mà chưa được review rõ ràng.

### 10.3 Keep security updates practical and visible / Giữ việc cập nhật bảo mật ở mức thực dụng và có thể nhìn thấy

#### EN
Outdated critical dependencies should be reviewed and updated as part of regular maintenance.

#### VI
Dependency cũ có rủi ro cao phải được review và cập nhật như một phần của bảo trì định kỳ.

## 11. Notebook, script, and ML-specific safety / An toàn cho notebook, script, và ML

### 11.1 Notebooks must not become secret containers / Notebook không được trở thành nơi chứa secret

#### EN
Do not place real tokens, passwords, or credentials directly in notebooks.

#### VI
Không đặt token, mật khẩu, hoặc credential thật trực tiếp trong notebook.

### 11.2 Model and data workflows must not expose secrets through artifacts / Workflow model và data không được làm lộ secret qua artifact

#### EN
Ensure that:

- exported notebooks
- logs
- model metadata
- cached files
- temporary data

do not leak sensitive values or private data.

#### VI
Phải đảm bảo rằng:

- notebook export
- log
- model metadata
- file cache
- dữ liệu tạm

không làm lộ giá trị nhạy cảm hoặc dữ liệu riêng tư.

### 11.3 Training and inference configuration must remain safe / Cấu hình training và inference phải an toàn

#### EN
Dataset paths, cloud credentials, model registry tokens, and experiment tracking secrets must be handled through secure config channels.

#### VI
Dataset path, cloud credential, model registry token, và secret cho experiment tracking phải được xử lý qua kênh cấu hình an toàn.

## 12. CI/CD and deployment rules / Quy tắc cho CI/CD và triển khai

### 12.1 CI/CD must use secret stores, not inline secrets / CI/CD phải dùng secret store, không nhúng secret trực tiếp

#### EN
Pipeline configuration must reference secure secret sources rather than embedding secret values inline.

#### VI
Cấu hình pipeline phải tham chiếu tới nguồn secret an toàn thay vì nhúng trực tiếp giá trị secret.

### 12.2 Build logs must remain safe / Log build phải an toàn

#### EN
CI/CD logs must not print secret values, even during debugging.

#### VI
Log của CI/CD không được in ra giá trị secret, kể cả khi debug.

### 12.3 Deployment must preserve environment separation / Triển khai phải giữ tách biệt môi trường

#### EN
Deployment workflows must not accidentally reuse development secrets in staging or production.

#### VI
Workflow triển khai không được vô tình tái sử dụng secret của development cho staging hoặc production.

## 13. Coding agent rules / Luật dành cho coding agent

### 13.1 Agents must never invent or embed real secrets / Agent không được tự nghĩ ra hoặc nhúng secret thật

#### EN
Coding agents must use placeholders or documented secret-loading patterns, never invented live-looking credentials.

#### VI
Coding agent phải dùng placeholder hoặc pattern load secret đã được tài liệu hóa, không được tự tạo ra credential trông như thật.

### 13.2 Agents must prefer secure examples / Agent phải ưu tiên ví dụ an toàn

#### EN
Generated code should demonstrate secure patterns by default:

- environment loading
- redaction
- safe config separation
- no secret logging

#### VI
Code do agent sinh ra phải mặc định minh họa pattern an toàn:

- load từ environment
- che dữ liệu nhạy cảm
- tách config an toàn
- không log secret

### 13.3 Agents must flag unsafe patterns explicitly / Agent phải chỉ ra pattern không an toàn một cách rõ ràng

#### EN
If the user provides unsafe secret handling, the agent should refactor or warn rather than normalize it.

#### VI
Nếu người dùng đưa vào cách xử lý secret không an toàn, agent phải refactor hoặc cảnh báo thay vì bình thường hóa nó.

## 14. Anti-patterns / Mẫu xấu cần tránh

### EN
Avoid:

- hard-coding secrets in code
- committing .env files with real values
- logging tokens or passwords
- returning raw stack traces to external clients
- using production credentials in tests
- storing secrets in notebooks
- using shared high-privilege credentials casually
- embedding secret values in CI configs
- using fake security through obscurity as a replacement for proper secret handling

### VI
Tránh:

- hard-code secret trong code
- commit file .env có giá trị thật
- log token hoặc mật khẩu
- trả raw stack trace ra client bên ngoài
- dùng credential production trong test
- lưu secret trong notebook
- dùng credential dùng chung có quyền cao một cách tùy tiện
- nhúng giá trị secret trong config CI
- dùng kiểu “giấu đi là an toàn” thay cho xử lý secret đúng chuẩn

## 15. Review checklist / Checklist review

### EN
When reviewing security and secret handling, check:

- Is any secret hard-coded?
- Are runtime secrets loaded from approved secure sources?
- Are logs and errors free of sensitive values?
- Does any example file accidentally look like a real credential?
- Are environment files safe for version control?
- Are permissions limited to what is necessary?
- Is test data synthetic or safely anonymized?
- Are CI/CD workflows free from inline secrets?
- Does the change introduce any risky new dependency or unsafe pattern?

### VI
Khi review phần security và secret handling, cần kiểm tra:

- Có secret nào bị hard-code không?
- Secret runtime có được load từ nguồn an toàn được phê duyệt không?
- Log và lỗi có sạch dữ liệu nhạy cảm không?
- File ví dụ có vô tình trông giống credential thật không?
- File môi trường có an toàn để đưa vào version control không?
- Quyền có được giới hạn đúng mức cần thiết không?
- Test data có là dữ liệu giả hoặc đã ẩn danh an toàn không?
- Workflow CI/CD có tránh nhúng secret trực tiếp không?
- Thay đổi này có đưa vào dependency rủi ro hoặc pattern không an toàn không?

## 16. Definition of done / Điều kiện hoàn thành

### EN
A module, service, or change is security-secret compliant only if:

- no real secret is committed or hard-coded
- runtime secrets are loaded from approved secure sources
- sensitive data is not exposed through logs, errors, or outputs
- config and examples remain safe for sharing
- permissions follow least privilege
- test assets contain no real private data or credentials
- CI/CD and deployment paths handle secrets safely
- generated or reviewed code demonstrates secure defaults

### VI
Một module, service, hoặc thay đổi chỉ được coi là tuân thủ security-secret khi:

- không có secret thật bị commit hoặc hard-code
- secret runtime được load từ nguồn an toàn được phê duyệt
- dữ liệu nhạy cảm không bị lộ qua log, lỗi, hoặc output
- config và file ví dụ vẫn an toàn để chia sẻ
- quyền tuân theo nguyên tắc tối thiểu
- test asset không chứa dữ liệu riêng tư hoặc credential thật
- CI/CD và đường triển khai xử lý secret an toàn
- code được sinh ra hoặc review thể hiện mặc định an toàn
