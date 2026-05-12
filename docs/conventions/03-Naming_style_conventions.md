# 03-Naming Style Guide / Quy ước đặt tên mã nguồn

## 1. Purpose / Mục đích

**EN**  
This document defines the naming rules for source code so that all modules, files, classes, functions, variables, and constants follow one consistent style across the project.

**VI**  
Tài liệu này định nghĩa các quy tắc đặt tên cho mã nguồn nhằm đảm bảo tất cả module, file, class, function, variable, và constant tuân theo một phong cách thống nhất trong toàn bộ dự án.

> [!IMPORTANT]
> **Tham chiếu code mẫu tại:** [Example/naming_style_example.md](Example/naming_style_example.md)

---

## 2. Core principle / Nguyên tắc cốt lõi

**EN**  
Code naming must prioritize readability, consistency, and predictability.  
A project must use one naming style consistently.

**VI**  
Việc đặt tên trong code phải ưu tiên tính dễ đọc, nhất quán, và dễ đoán.  
Một dự án phải dùng một kiểu đặt tên thống nhất.

---

## 3. Naming rules / Luật đặt tên

### 3.1 Classes / Tên class

**EN**  
Class names must use `PascalCase`.

**VI**  
Tên class phải dùng `PascalCase`.

**Allowed / Hợp lệ**
- `UserAccount`
- `DataProcessor`
- `InvoiceService`

**Avoid / Tránh**
- `user_account`
- `userAccount`
- `USER_ACCOUNT`

**Rule note / Ghi chú**
- Class names should be nouns or noun phrases.
- Avoid vague names such as `Data`, `Manager`, `Helper`, or `Processor` unless the responsibility is clear.

- Tên class nên là danh từ hoặc cụm danh từ.
- Tránh các tên mơ hồ như `Data`, `Manager`, `Helper`, hoặc `Processor` nếu không thể hiện rõ trách nhiệm.

---

### 3.2 Variables / Tên biến

**EN**  
Variable names must use `snake_case`.

**VI**  
Tên biến phải dùng `snake_case`.

**Allowed / Hợp lệ**
- `user_name`
- `total_price`
- `retry_count`

**Avoid / Tránh**
- `userName`
- `UserName`
- `USERNAME`

**Rule note / Ghi chú**
- Variable names should describe meaning, not implementation detail.
- Use full words unless the abbreviation is universally understood.

- Tên biến phải mô tả ý nghĩa, không mô tả mẹo cài đặt.
- Dùng từ đầy đủ, trừ khi viết tắt là phổ biến và rõ nghĩa.

---

### 3.3 Functions and methods / Tên hàm và phương thức

**EN**  
Function and method names must use `snake_case`.

**VI**  
Tên function và method phải dùng `snake_case`.

**Allowed / Hợp lệ**
- `get_user_name`
- `calculate_total_price`
- `load_config`
- `validate_input`

**Avoid / Tránh**
- `getUserName`
- `CalculateTotalPrice`

**Rule note / Ghi chú**
- Function names should start with a verb when they perform an action.
- Prefer names that express intent clearly: `load_user_profile`, not `handle_data`.

- Tên hàm nên bắt đầu bằng động từ nếu có hành động.
- Ưu tiên tên thể hiện rõ ý đồ: `load_user_profile`, không phải `handle_data`.

---

### 3.4 Constants / Hằng số

**EN**  
Constants must use `UPPER_CASE_WITH_UNDERSCORES`.

**VI**  
Hằng số phải dùng `UPPER_CASE_WITH_UNDERSCORES`.

**Allowed / Hợp lệ**
- `MAX_CONNECTION`
- `DEFAULT_TIMEOUT`
- `API_URL`

**Avoid / Tránh**
- `max_connection`
- `DefaultTimeout`

**Rule note / Ghi chú**
- Use constants only for values intended to remain stable and shared.
- Do not turn ordinary local variables into constants unnecessarily.

- Chỉ dùng constant cho giá trị ổn định và dùng chung.
- Không biến mọi biến cục bộ thành constant một cách máy móc.

---

### 3.5 Private members / Thành phần private

**EN**  
Private attributes and helper methods must use a single leading underscore.

**VI**  
Thuộc tính private và helper method phải dùng một dấu gạch dưới ở đầu tên.

**Allowed / Hợp lệ**
- `_token`
- `_generate_token`
- `_build_payload`

**Avoid / Tránh**
- `token` for internal-only members
- `__token` unless name mangling is explicitly required

**Rule note / Ghi chú**
- A single underscore means “internal use”.
- Do not use double underscore for normal private methods.

- Một dấu gạch dưới thể hiện “chỉ dùng nội bộ”.
- Không dùng hai dấu gạch dưới cho private method thông thường.

---

### 3.6 Special methods / Phương thức đặc biệt

**EN**  
Python special methods must use the standard double-underscore form.

**VI**  
Các phương thức đặc biệt của Python phải dùng đúng dạng double underscore chuẩn.

**Allowed / Hợp lệ**
- `__init__`
- `__str__`
- `__repr__`

**Avoid / Tránh**
- custom names such as `__calculate__` unless they are actual Python dunder methods

**Rule note / Ghi chú**
- Double-underscore names are reserved for Python special methods and framework-defined protocol methods.

- Tên double underscore được dành cho special method của Python hoặc protocol method do framework định nghĩa.

---

### 3.7 File names / Tên file

**EN**  
Python source files must use `snake_case`.

**VI**  
Tên file Python phải dùng `snake_case`.

**Allowed / Hợp lệ**
- `user_service.py`
- `data_processor.py`
- `config_loader.py`

**Avoid / Tránh**
- `UserService.py`
- `dataProcessor.py`

**Rule note / Ghi chú**
- File names should reflect the main responsibility of the file.
- One file should usually have one primary purpose.

- Tên file nên phản ánh trách nhiệm chính của file.
- Một file thường chỉ nên có một mục đích chính.

---

### 3.8 Module and package names / Tên module và package

**EN**  
Module and package names must use short, descriptive `snake_case`.

**VI**  
Tên module và package phải dùng `snake_case`, ngắn gọn và mô tả rõ ý nghĩa.

**Allowed / Hợp lệ**
- `services`
- `data_ingestion`
- `model_registry`

**Avoid / Tránh**
- `Services`
- `DataIngestion`
- `misc_stuff`

**Rule note / Ghi chú**
- Avoid generic package names such as `common`, `misc`, or `helpers` unless their scope is truly generic and well-defined.

- Tránh các tên package quá chung chung như `common`, `misc`, hoặc `helpers` trừ khi phạm vi của chúng thực sự chung và rõ ràng.

---

### 3.9 Boolean names / Tên biến boolean

**EN**  
Boolean names should read like true/false statements.

**VI**  
Tên biến boolean nên đọc lên như một mệnh đề đúng/sai.

**Preferred / Ưu tiên**
- `is_active`
- `has_access`
- `can_retry`
- `should_validate`

**Avoid / Tránh**
- `active_flag`
- `status_check`

---

### 3.10 Collection names / Tên biến tập hợp

**EN**  
Collection names should indicate plurality or grouped meaning.

**VI**  
Tên biến dạng tập hợp nên thể hiện ý nghĩa số nhiều hoặc một nhóm dữ liệu.

**Preferred / Ưu tiên**
- `users`
- `failed_records`
- `invoice_items`

**Avoid / Tránh**
- `user_data` when it is actually a list
- `item` when it is actually a collection

---

### 3.11 Exception names / Tên exception

**EN**  
Custom exception names must use `PascalCase` and end with `Error` unless the project uses another explicit exception suffix convention.

**VI**  
Tên custom exception phải dùng `PascalCase` và kết thúc bằng `Error`, trừ khi dự án có quy ước suffix khác được định nghĩa rõ.

**Allowed / Hợp lệ**
- `ConfigError`
- `ValidationError`
- `ModelRegistryError`

---

### 3.12 Test naming / Đặt tên test

**EN**  
Test file names must use `snake_case` (e.g. `test_user_service.py`).
For detailed test function naming rules and patterns, follow `07-Testing` §8.

**VI**  
Tên file test phải dùng `snake_case` (ví dụ `test_user_service.py`).
Về quy tắc đặt tên hàm test chi tiết, tuân theo `07-Testing` §8.

---

### 3.13 Environment variable names / Tên biến môi trường

**EN**  
Environment variables must use `UPPER_CASE_WITH_UNDERSCORES` and should include subsystem-specific prefixes where relevant.

**VI**  
Biến môi trường phải dùng `UPPER_CASE_WITH_UNDERSCORES` và nên có prefix theo phân hệ khi cần.

**Examples / Ví dụ**
- `PG_HOST`
- `PG_PORT`
- `FS_INCOMING_DIR`
- `API_TIMEOUT`

---

## 4. Class member order / Thứ tự thành phần trong class

**EN**  
Classes should follow this recommended order:
1. class-level constants
2. `__init__`
3. public methods
4. private methods

**VI**  
Class nên theo thứ tự khuyến nghị sau:
1. constant cấp class
2. `__init__`
3. public method
4. private method

**Note / Ghi chú**
- Keep related methods close to each other when readability benefits from it.
- The purpose of this rule is consistency, not rigidity.

- Giữ các method liên quan gần nhau nếu điều đó giúp dễ đọc hơn.
- Mục đích của rule này là tạo tính nhất quán, không phải cứng nhắc máy móc.

---

## 5. Adjacent style rules / Các quy tắc kề cận nên giữ cùng file

### 5.1 Spacing / Khoảng trắng

**EN**  
Use spaces around operators and after commas.

**VI**  
Dùng khoảng trắng quanh toán tử và sau dấu phẩy.

**Correct / Đúng**
- `total = price + tax`
- `print(name, age)`

**Incorrect / Sai**
- `total=price+tax`
- `print(name,age)`

### 5.2 Line length / Độ dài dòng

**EN**  
Prefer lines of 88 characters or fewer (standard Black configuration). Wrap long expressions across multiple lines.

**VI**  
Ưu tiên dòng dài không quá 88 ký tự (theo chuẩn mặc định của trình format Black). Nếu dài hơn thì tách nhiều dòng.

### 5.3 Import order / Thứ tự import

**EN**  
For all import ordering and grouping rules, follow `04-Dependencies_import_conventions` §4.

**VI**  
Về tất cả quy tắc sắp xếp và nhóm import, tuân theo `04-Dependencies_import_conventions` §4.

---

## 6. Enforcement / Cách thực thi

**EN**  
The project should use automated tools to enforce naming and style consistency where possible.

Recommended tools:
- `black`
- `flake8`
- `pylint`
- `isort`

**VI**  
Dự án nên dùng công cụ tự động để đảm bảo naming và style được nhất quán khi có thể.

Công cụ khuyến nghị:
- `black` (Formatter chính, mặc định 88 ký tự)
- `flake8` (Linter)
- `pylint` (Trình phân tích tĩnh chuyên sâu)
- `isort` (Trình sắp xếp import)

### 6.1 Linter & Formatter configuration / Cấu hình Linter và Formatter

**EN**  
To prevent conflicts between tools, `flake8`, `isort`, and `pylint` must be explicitly configured to be compatible with `black` (88-character line length).

**VI**  
Để tránh xung đột công cụ, `flake8`, `isort` và `pylint` phải được cấu hình tường minh để tương thích với `black` (giới hạn dòng 88 ký tự).

**Example `pyproject.toml` or `setup.cfg` snippet / Cấu hình mẫu:**
- **flake8**: `--max-line-length=88` and `--extend-ignore=E203`
- **isort**: `--profile black`
- **pylint**: `max-line-length=88`

---

## 7. Anti-patterns / Mẫu xấu cần tránh

**EN**
Avoid:
- mixed naming styles in the same project
- vague names such as `data`, `info`, `manager`, `helper`, `temp`
- abbreviations that are not widely understood
- one-letter variable names outside very small local scopes
- file names that do not reflect responsibility

**VI**
Tránh:
- trộn nhiều kiểu đặt tên trong cùng một dự án
- tên mơ hồ như `data`, `info`, `manager`, `helper`, `temp`
- viết tắt khó hiểu
- biến một ký tự ngoài các phạm vi cục bộ rất nhỏ
- tên file không phản ánh trách nhiệm chính

---

## 8. Definition of done / Điều kiện hoàn thành

**EN**  
A code unit is naming-compliant only if:
- class names use `PascalCase`
- functions and variables use `snake_case`
- constants use `UPPER_CASE`
- private members use a single underscore
- special methods use Python dunder names only
- file names use `snake_case`
- import grouping is correct
- no vague or inconsistent names remain

**VI**  
Một đơn vị code chỉ được coi là tuân thủ naming convention khi:
- tên class dùng `PascalCase`
- function và variable dùng `snake_case`
- constant dùng `UPPER_CASE`
- private member dùng một dấu gạch dưới
- special method chỉ dùng dunder chuẩn của Python
- tên file dùng `snake_case`
- thứ tự nhóm import đúng
- không còn tên mơ hồ hoặc thiếu nhất quán