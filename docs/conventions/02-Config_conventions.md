# Configuration Conventions / Quy ước viết cấu hình

## 1. Purpose / Mục đích

**EN**  
This document defines the standard rules for writing configuration code across projects.  
The goal is to make configuration predictable, typed, validated, environment-aware, and easy for both developers and agents to extend.

**VI**  
Tài liệu này định nghĩa các quy tắc chuẩn để viết code cấu hình trong các dự án.  
Mục tiêu là giúp phần cấu hình luôn dễ đoán, có kiểu dữ liệu rõ ràng, có kiểm tra hợp lệ, tách theo môi trường, và dễ mở rộng cho cả developer lẫn agent.

> [!TIP]
> **Tùy chọn tham khảo code mẫu tại:** [Example/config_example.py](Example/config_example.py)

---

## 2. Core principles / Nguyên tắc cốt lõi

**EN**
Configuration must be:
- separated from business logic
- organized by component
- loaded from environment or approved config sources
- strongly typed
- validated before use
- safe for multiple environments

**VI**
Cấu hình phải:
- tách khỏi business logic
- được tổ chức theo từng thành phần
- được nạp từ environment hoặc nguồn cấu hình chuẩn
- có kiểu dữ liệu rõ ràng
- được kiểm tra hợp lệ trước khi sử dụng
- an toàn cho nhiều môi trường khác nhau
---

## 3. Structural rules / Luật về cấu trúc

### 3.1 One config object per subsystem / Một đối tượng config cho mỗi phân hệ

**EN**  
Each subsystem must have its own config object.  
Examples: file system, database, cache, message queue, API client, model serving, monitoring.

**VI**  
Mỗi phân hệ phải có đối tượng config riêng.  
Ví dụ: file system, database, cache, message queue, API client, model serving, monitoring.

### 3.2 Use a root config object / Dùng một config gốc

**EN**  
Projects should expose one root config object such as `AppConfig` to compose all subsystem configs.

**VI**  
Dự án nên có một config gốc như `AppConfig` để gom toàn bộ config của các phân hệ.

### 3.3 Keep config code in a dedicated module / Đặt code config trong module riêng

**EN**  
Configuration code must live in a dedicated config module or package.  
Do not scatter environment reads across the codebase.

**VI**  
Code cấu hình phải nằm trong module hoặc package riêng.  
Không được đọc environment rải rác khắp codebase.

---

## 4. Source of configuration / Nguồn cấu hình

### 4.1 Centralized loading / Nạp tập trung

**EN**  
All configuration must be loaded through centralized constructors such as:
- `from_env()`
- `from_file()`
- `from_settings()`

**VI**  
Mọi cấu hình phải được nạp thông qua constructor tập trung như:
- `from_env()`
- `from_file()`
- `from_settings()`

### 4.2 Environment-first for runtime values / Ưu tiên environment cho giá trị runtime

**EN**  
Runtime-sensitive values must come from environment variables or secret managers, especially:
- credentials
- tokens
- passwords
- service endpoints
- deployment-specific paths

**VI**  
Các giá trị nhạy cảm theo môi trường chạy phải lấy từ environment variable hoặc secret manager, đặc biệt là:
- thông tin xác thực
- token
- mật khẩu
- endpoint dịch vụ
- đường dẫn đặc thù theo môi trường triển khai

### 4.3 No scattered os.getenv calls / Không gọi os.getenv rải rác

**EN**  
`os.getenv()` or equivalent must not appear throughout feature code.  
Read env values only inside config loading code.

**VI**  
`os.getenv()` hoặc cách tương đương không được xuất hiện rải rác trong feature code.  
Chỉ được đọc env bên trong code load config.

---

## 5. Typing rules / Luật về kiểu dữ liệu

### 5.1 Strong typing is mandatory / Bắt buộc có kiểu dữ liệu rõ ràng

**EN**  
All config fields must have explicit types.

**VI**  
Mọi field config phải có kiểu dữ liệu tường minh.

### 5.2 Use domain-appropriate types / Dùng kiểu phù hợp với ngữ nghĩa

**EN**  
Use the most meaningful type available:
- `Path` for file paths
- `int` for ports, retries, and limits
- `bool` for flags
- `Optional[T]` only for truly optional values
- enums for bounded choices

**VI**  
Dùng kiểu dữ liệu phản ánh đúng ngữ nghĩa:
- `Path` cho đường dẫn file/thư mục
- `int` cho port, retry, limit
- `bool` cho cờ bật/tắt
- `Optional[T]` chỉ khi thực sự không bắt buộc
- enum cho các lựa chọn có tập giá trị cố định

---

## 6. Validation rules / Luật kiểm tra hợp lệ

### 6.1 Every config object must validate itself / Mọi config object phải tự kiểm tra hợp lệ

**EN**  
Each config object must provide validation logic.

**VI**  
Mỗi config object phải có logic kiểm tra hợp lệ.

### 6.2 Validation must not mutate system state / Validation không được làm thay đổi trạng thái hệ thống

**EN**  
Validation must only check correctness.  
It must not create folders, modify files, connect to services, or change state.

**VI**  
Validation chỉ được kiểm tra tính đúng đắn.  
Không được tạo thư mục, sửa file, kết nối dịch vụ, hay làm thay đổi trạng thái hệ thống.

### 6.3 Fail fast on invalid config / Fail sớm khi config sai

**EN**  
Invalid config must fail early with explicit errors.  
Do not silently ignore invalid values.

**VI**  
Config sai phải bị fail sớm với lỗi rõ ràng.  
Không được âm thầm bỏ qua giá trị sai.

### 6.4 Avoid broad exception swallowing / Không nuốt lỗi quá rộng

**EN**  
Do not use `except Exception: return False` in validation unless the error is logged and preserved elsewhere.

**VI**  
Không dùng `except Exception: return False` trong validation trừ khi lỗi đã được log và lưu ngữ cảnh ở nơi khác.

---

## 7. Derived values / Giá trị dẫn xuất

### 7.1 Derived properties are allowed / Cho phép có giá trị dẫn xuất

**EN**  
Config objects may expose derived values such as:
- database connection strings
- normalized URLs
- resolved paths
- computed cache keys

**VI**  
Config object được phép có giá trị dẫn xuất như:
- chuỗi kết nối database
- URL đã chuẩn hóa
- đường dẫn đã resolve
- cache key được tính sẵn

### 7.2 Derived values must not hide secrets in logs / Giá trị dẫn xuất không được làm lộ secret trong log

**EN**  
If a derived value contains secrets, provide a masked representation for logging.

**VI**  
Nếu giá trị dẫn xuất chứa secret, phải có cách che giấu khi log.

---

## 8. Defaults / Giá trị mặc định

### 8.1 Defaults are allowed only for safe local development values / Chỉ cho phép default an toàn cho local dev

**EN**  
Default values are allowed only when they are safe and non-sensitive.

Good examples:
- localhost
- local relative paths
- non-production ports

Bad examples:
- real credentials
- production endpoints
- private tokens

**VI**  
Chỉ cho phép giá trị mặc định khi chúng an toàn và không nhạy cảm.

Ví dụ tốt:
- localhost
- đường dẫn local tương đối
- port không phải production

Ví dụ xấu:
- thông tin xác thực thật
- endpoint production
- token riêng tư

### 8.2 Required secrets must not have silent production defaults / Secret bắt buộc không được có default im lặng ở production

**EN**  
Passwords, API keys, and tokens must be required for production-bound systems.
For the complete safe-default policy and secret classification rules, follow `08-Security_secrets_conventions` §6.

**VI**  
Password, API key, và token phải là trường bắt buộc đối với hệ thống hướng production.
Về chính sách safe-default đầy đủ và phân loại secret, tuân theo `08-Security_secrets_conventions` §6.

---

## 9. Naming rules / Luật đặt tên

### 9.1 Config classes / Tên class config

**EN**  
Config classes must be named by subsystem:
Example :
- `FSConfig`
- `PostgresConfig`
- `RedisConfig`
- `APIClientConfig`
- `MonitoringConfig`

**VI**  
Tên class config phải đặt theo phân hệ:
Ví dụ :
- `FSConfig`
- `PostgresConfig`
- `RedisConfig`
- `APIClientConfig`
- `MonitoringConfig`

### 9.2 Environment variable names / Tên biến môi trường

**EN**  
Environment variables must be uppercase and use clear prefixes by subsystem.

Examples:
- `PG_HOST`
- `PG_PORT`
- `PG_DATABASE`
- `FS_INCOMING_DIR`
- `FS_SAVED_DIR`

**VI**  
Biến môi trường phải viết hoa và có prefix rõ theo từng phân hệ.

Ví dụ:
- `PG_HOST`
- `PG_PORT`
- `PG_DATABASE`
- `FS_INCOMING_DIR`
- `FS_SAVED_DIR`

---

## 10. Separation of responsibilities / Tách trách nhiệm

### 10.1 Config is not business logic / Config không phải business logic

**EN**  
Config classes must not contain business workflows, data processing, or application rules.

**VI**  
Config class không được chứa workflow nghiệp vụ, xử lý dữ liệu, hay luật ứng dụng.

### 10.2 Bootstrap is separate from validation / Bootstrap tách khỏi validation

**EN**  
If the system needs to prepare folders, initialize connections, or provision resources, that logic must live in bootstrap/setup code, not in config validation.

**VI**  
Nếu hệ thống cần tạo thư mục, khởi tạo kết nối, hay chuẩn bị tài nguyên, logic đó phải nằm ở bootstrap/setup code, không nằm trong validate của config.

---

## 11. Recommended standard methods / Các method chuẩn nên có

**EN**  
Each config object should preferably support:
- `from_env()`
- `validate()`
- `to_safe_dict()` for logging or debugging
- derived properties when needed

**VI**  
Mỗi config object nên hỗ trợ:
- `from_env()`
- `validate()`
- `to_safe_dict()` để log hoặc debug an toàn
- property dẫn xuất nếu cần

---

## 12. Anti-patterns / Mẫu xấu cần tránh

**EN**
Do not:
- read env variables directly inside services
- hard-code connection strings in application code
- mix validation with side effects
- silently ignore parsing errors
- expose secrets in repr/logs
- put unrelated config into one giant flat class
- duplicate env parsing logic in many files

**VI**
Không được:
- đọc env trực tiếp trong service
- hard-code connection string trong application code
- trộn validation với side effect
- âm thầm bỏ qua lỗi parse
- làm lộ secret trong repr/log
- nhét mọi loại config vào một class phẳng khổng lồ
- lặp lại logic parse env ở nhiều file

---

## 13. Definition of done / Điều kiện hoàn thành

**EN**  
A config module is considered complete only if:
- subsystem configs are separated
- fields are typed
- env loading is centralized
- validation exists
- sensitive values are handled safely
- defaults are intentional
- runtime code can consume config without direct env access

**VI**  
Một module config chỉ được coi là hoàn chỉnh khi:
- config theo phân hệ đã được tách riêng
- field có kiểu dữ liệu rõ ràng
- việc load env được tập trung
- có validation
- dữ liệu nhạy cảm được xử lý an toàn
- default được đặt có chủ đích
- code runtime có thể dùng config mà không cần đọc env trực tiếp