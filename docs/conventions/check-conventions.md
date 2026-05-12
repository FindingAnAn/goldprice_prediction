# Hướng Dẫn Coding Conventions — Đầy Đủ 18 Luật

> **Dành cho ai?** Developer muốn nắm nhanh toàn bộ bộ quy tắc mà không đọc hết 18 file gốc.
> Mỗi luật đều có: **Giải thích đơn giản** — **Ví dụ xấu** — **Ví dụ tốt** — **Lý do**

---

## Mục Lục

| # | Chủ đề | File gốc |
|---|--------|----------|
| 01 | [Cấu trúc dự án & 4 lớp kiến trúc](#phan-1--cau-truc-du-an) | 01-Structure |
| 02 | [Quy tắc viết Config](#phan-2--cau-hinh) | 02-Config |
| 03 | [Quy tắc đặt tên](#phan-3--quy-tac-dat-ten) | 03-Naming |
| 04 | [Import & Phụ thuộc](#phan-4--import--phu-thuoc) | 04-Dependencies |
| 05 | [Xử lý lỗi](#phan-5--xu-ly-loi) | 05-Error_handling |
| 06 | [Logging & Quan sát hệ thống](#phan-6--logging--quan-sat-he-thong) | 06-Logging |
| 07 | [Viết Test](#phan-7--viet-test) | 07-Testing |
| 08 | [Bảo mật & Secret](#phan-8--bao-mat--secret) | 08-Security |
| 09 | [Git, PR & Release](#phan-9--git-pr--release) | 09-Git_PR |
| 10 | [Thiết kế Code & SOLID](#phan-10--thiet-ke-code--solid) | 10-Code_design |
| 11 | [Definition of Done (DoD)](#phan-11--definition-of-done) | 11-DoD |
| 12 | [Thiết kế API](#phan-12--thiet-ke-api) | 12-Api |
| 13 | [Data & Machine Learning](#phan-13--data--machine-learning) | 13-Data_ML |
| 14 | [Infrastructure & Deployment](#phan-14--infrastructure--deployment) | 14-Infrastructure |
| 15 | [Tài liệu & Docstring](#phan-15--tai-lieu--docstring) | 15-Documentation |
| 16 | [Kiến trúc hệ thống](#phan-16--kien-truc-he-thong) | 16-Architecture |
| 17 | [Feature Flags](#phan-17--feature-flags) | 17-Feature_flags |
| 18 | [Observability & Orchestration nâng cao](#phan-18--observability--orchestration-nang-cao) | 18-Observability |

---

## Phần 1 — Cấu Trúc Dự Án

### Luật 1.1 — Mọi dự án phải có cấu trúc thư mục chuẩn

**Giải thích:** Khi bắt đầu dự án, bạn phải tạo các thư mục theo đúng cấu trúc này, không để code lộn xộn ở thư mục gốc.

```
project-root/
├── src/            <- Code chạy thật của hệ thống
├── tests/          <- Code test (tách riêng khỏi src/)
├── config/         <- Cấu hình (database, env, v.v.)
├── docs/           <- Tài liệu
├── scripts/        <- Script hỗ trợ (migration, seed data...)
├── infrastructure/ <- Dockerfile, Terraform, K8s
├── README.md
└── .env.example    <- Mẫu biến môi trường (không chứa giá trị thật!)
```

**Xấu**

```
project/
├── main.py
├── db.py
├── test_main.py   <- test để chung với code thật
└── config.py
```

**Tốt**

```
project/
├── src/
│   ├── domain/
│   ├── application/
│   └── infrastructure/
├── tests/
├── config/
└── README.md
```

> Khi 10 người cùng làm, cấu trúc thống nhất giúp ai cũng tìm được file cần sửa trong 10 giây.

---

### Luật 1.2 — Code được tổ chức thành 4 lớp, hướng phụ thuộc đi từ ngoài vào trong

**"Phụ thuộc" (dependency) là gì?** Khi file A cần `import` từ file B thì A phụ thuộc B.

| Lớp | Tên | Chứa gì | Ví dụ |
|-----|-----|---------|-------|
| 1 (ngoài cùng) | Interface | Điểm vào hệ thống | HTTP route, CLI |
| 2 | Application | Điều phối luồng xử lý | Use case, workflow |
| 3 | Domain | Luật nghiệp vụ cốt lõi | Entity, business rule |
| 4 (trong cùng) | Infrastructure | Kết nối kỹ thuật | Database, API ngoài |

Hướng gọi: `Interface → Application → Domain ← Infrastructure`

**Xấu** — Domain gọi thẳng database

```python
# src/domain/user.py
import psycopg2  # Cấm! Domain không được biết đến database

class User:
    def save(self):
        conn = psycopg2.connect(...)  # Vi phạm lớp!
```

**Tốt**

```python
# src/domain/user.py
class User:
    def validate_age(self, age: int) -> bool:
        return age >= 18  # Chỉ viết luật nghiệp vụ

# src/infrastructure/user_repository.py
import psycopg2
class UserRepository:
    def save(self, user: User): ...  # Database thuộc về đây
```

---

## Phần 2 — Cấu Hình

### Luật 2.1 — Không đọc `os.getenv()` rải rác trong code

**"Biến môi trường" là gì?** Giá trị lưu ngoài code, trong file `.env` hoặc máy chủ. Ví dụ: `DATABASE_URL`, `API_KEY`.

**Xấu**

```python
# email_service.py
import os
def send_email(to):
    api_key = os.getenv("SENDGRID_KEY")  # Đọc env rải rác

# payment_service.py
import os
def charge(amount):
    secret = os.getenv("STRIPE_SECRET")  # Lại ở đây nữa
```

**Tốt** — Tập trung đọc env vào một chỗ duy nhất

```python
# src/config/app_config.py
import os
from dataclasses import dataclass

@dataclass
class EmailConfig:
    api_key: str

    @classmethod
    def from_env(cls) -> "EmailConfig":
        return cls(api_key=os.getenv("SENDGRID_KEY", ""))

# src/services/email_service.py
def send_email(config: EmailConfig, to: str):
    # Nhận config từ ngoài vào, không tự đọc env
    ...
```

---

### Luật 2.2 — Config phải có kiểu dữ liệu rõ ràng và tự kiểm tra hợp lệ

**Xấu**

```python
config = {
    "port": os.getenv("PORT"),   # Kiểu str, nhưng port phải là int
    "debug": os.getenv("DEBUG"), # Kiểu str, nhưng debug phải là bool
}
```

**Tốt**

```python
@dataclass
class ServerConfig:
    port: int = 8080
    debug: bool = False

    @classmethod
    def from_env(cls):
        return cls(
            port=int(os.getenv("PORT", "8080")),
            debug=os.getenv("DEBUG", "false").lower() == "true",
        )

    def validate(self):
        if not (1024 <= self.port <= 65535):
            raise ValueError(f"Port không hợp lệ: {self.port}")
```

---

### Luật 2.3 — Không hard-code credential

**"Hard-code" là gì?** Viết giá trị cố định trực tiếp vào code thay vì đọc từ biến môi trường.

**Xấu**

```python
DB_PASSWORD = "my_super_secret_123"  # Ai clone repo đều thấy!
```

**Tốt**

```python
DB_PASSWORD = os.getenv("DB_PASSWORD")
if not DB_PASSWORD:
    raise ValueError("DB_PASSWORD chưa được thiết lập!")
```

---

## Phần 3 — Quy Tắc Đặt Tên

### Luật 3.1 — Bảng quy tắc đặt tên

| Thứ gì | Kiểu viết | Ví dụ tốt | Ví dụ xấu |
|--------|-----------|-----------|-----------|
| Class | `PascalCase` | `UserAccount`, `InvoiceService` | `user_account`, `userAccount` |
| Hàm / Biến | `snake_case` | `get_user`, `total_price` | `getUser`, `TotalPrice` |
| Hằng số | `UPPER_CASE` | `MAX_RETRY`, `DEFAULT_TIMEOUT` | `max_retry`, `defaultTimeout` |
| Private | `_tên` | `_token`, `_build_payload` | `token` (khi chỉ dùng nội bộ) |
| File | `snake_case` | `user_service.py` | `UserService.py` |
| Package / Module | `snake_case` ngắn | `data_ingestion`, `services` | `DataIngestion`, `misc_stuff` |

- **PascalCase:** Hoa chữ đầu của mỗi từ — `MyUserAccount`
- **snake_case:** Thường toàn bộ, dùng `_` giữa các từ — `my_user_account`
- **UPPER_CASE:** Hoa toàn bộ, dùng `_` giữa các từ — `MY_CONSTANT`

---

### Luật 3.2 — Tên phải nói lên ý nghĩa

**Xấu**

```python
d = get_data()      # d là gì?
def handle(x):      # handle cái gì? x là gì?
    temp = x * 2
    return temp
```

**Tốt**

```python
user_list = fetch_active_users()

def calculate_double_price(original_price: float) -> float:
    discounted_price = original_price * 2
    return discounted_price
```

---

### Luật 3.3 — Biến boolean đọc như câu hỏi đúng/sai

**Tốt**

```python
is_active = True       # "Có đang active không?"
has_access = False     # "Có quyền truy cập không?"
can_retry = True       # "Có thể thử lại không?"
should_validate = True # "Có cần validate không?"
```

**Xấu**

```python
active = True
check = False
flag = True
```

---

## Phần 4 — Import & Phụ Thuộc

### Luật 4.1 — Sắp xếp import theo 3 nhóm, cách nhau bằng dòng trống

**Tốt**

```python
# Nhóm 1: Thư viện chuẩn của Python
import os
import sys

# Nhóm 2: Thư viện cài qua pip (bên thứ ba)
import requests
import pandas as pd

# Nhóm 3: Code nội bộ của dự án
from app.services import UserService
from app.domain.user import User
```

**Xấu**

```python
from app.services import UserService
import os
import requests
import sys
```

---

### Luật 4.2 — Dùng absolute import (đường dẫn đầy đủ) làm mặc định

- **Absolute import:** Import theo đường dẫn đầy đủ từ gốc project.
- **Relative import:** Import theo đường dẫn tương đối với file hiện tại (dùng dấu `.`).

**Tốt**

```python
from app.infrastructure.database.repositories.user_repository import UserRepository
```

**Xấu** — relative import dài, khó đếm dấu chấm

```python
from ...infrastructure.database.repositories.user_repository import UserRepository
```

---

### Luật 4.3 — Cấm `import *`

**Xấu**

```python
from utils import *  # Không biết import được gì, gây xung đột tên
```

**Tốt**

```python
from utils import format_date, parse_currency  # Rõ ràng, kiểm soát được
```

---

### Luật 4.4 — Domain không được import từ Infrastructure

Hướng phụ thuộc không bao giờ đi ngược từ trong ra ngoài:

```
CẤMM : Domain  → Infrastructure
OK   : Infrastructure → Domain
```

---

## Phần 5 — Xử Lý Lỗi

### Luật 5.1 — Phân loại lỗi thành 5 nhóm

| Loại | Ví dụ | Cách xử lý |
|------|-------|------------|
| **Validation** | Email sai định dạng, thiếu trường | Trả lỗi rõ cho client |
| **Domain** (Nghiệp vụ) | Tài khoản không đủ tiền | Raise exception nghiệp vụ riêng |
| **Application** | Không tìm thấy resource trong workflow | Báo lỗi use case |
| **Infrastructure** | Mất kết nối DB, API timeout | Thử lại hoặc fallback |
| **Unexpected** (Bug) | NullPointerError, lỗi lập trình | Log đầy đủ, alert team |

---

### Luật 5.2 — Không bắt lỗi quá rộng rồi bỏ qua

**Xấu**

```python
def load_user(user_id: int):
    try:
        return db.get(user_id)
    except Exception:
        return None  # Nuốt hết lỗi! Không biết gì xảy ra
```

**Tốt**

```python
def load_user(user_id: int):
    try:
        return db.get(user_id)
    except DatabaseConnectionError as e:
        logger.error("Không kết nối được database", exc_info=e)
        raise  # Re-raise để lớp trên xử lý tiếp
    except UserNotFoundError:
        return None  # Trường hợp bình thường, xử lý rõ ràng
```

---

### Luật 5.3 — Domain không được raise exception của Framework

**Xấu**

```python
# src/domain/order.py
from fastapi import HTTPException  # Cấm! Domain không biết FastAPI

class Order:
    def cancel(self):
        if self.is_shipped:
            raise HTTPException(status_code=400, ...)  # Vi phạm!
```

**Tốt**

```python
# src/domain/order.py
class OrderCancellationError(Exception):  # Exception riêng của domain
    pass

class Order:
    def cancel(self):
        if self.is_shipped:
            raise OrderCancellationError("Không thể hủy đơn đã giao")

# src/interfaces/http/order_router.py
@app.post("/orders/{id}/cancel")
def cancel_order(id: int):
    try:
        order_service.cancel(id)
    except OrderCancellationError as e:
        raise HTTPException(status_code=400, detail=str(e))  # Chuyển ở đây
```

---

## Phần 6 — Logging & Quan Sát Hệ Thống

### Luật 6.1 — Dùng đúng log level cho từng tình huống

| Level | Dùng khi nào | Ví dụ |
|-------|-------------|-------|
| `DEBUG` | Chi tiết chẩn đoán, chỉ bật khi debug | `logger.debug("Đang xử lý record 42")` |
| `INFO` | Sự kiện quan trọng thành công | `logger.info("Đơn hàng #123 đã được tạo")` |
| `WARNING` | Bất thường nhưng còn phục hồi được | `logger.warning("Retry lần 2/3")` |
| `ERROR` | Thao tác thất bại cần chú ý | `logger.error("Không gửi được email")` |
| `CRITICAL` | Lỗi nghiêm trọng ảnh hưởng hệ thống | `logger.critical("Database không phản hồi")` |

---

### Luật 6.2 — Dùng structured logging thay vì chuỗi tự do

**"Structured logging" là gì?** Log dưới dạng key-value rõ ràng thay vì câu văn tự do, giúp dễ tìm kiếm và lọc sau này.

**Xấu** — chuỗi tự do

```python
logger.info(f"Invoice {invoice_id} processed for customer {customer_id}")
```

**Tốt** — structured

```python
logger.info(
    "Invoice processed",
    extra={"invoice_id": invoice_id, "customer_id": customer_id}
)
```

> Với structured log, bạn có thể tìm `invoice_id=123` trong hàng triệu dòng log chỉ trong vài giây.

---

### Luật 6.3 — Log một lần tại đúng boundary, không log lặp ở nhiều lớp

**Xấu** — Log cùng một lỗi ở 3 lớp khác nhau

```python
# infrastructure layer
except DatabaseError as e:
    logger.error("DB lỗi", exc_info=e)         # Log lần 1
    raise

# application layer
except DatabaseError as e:
    logger.error("App không lấy được user", exc_info=e)  # Log lần 2 (thừa!)
    raise

# interface layer
except Exception as e:
    logger.error("Request thất bại", exc_info=e)         # Log lần 3 (thừa!)
```

**Tốt** — Log một lần ở nơi có ý nghĩa nhất

```python
# interface layer — đây là boundary vận hành, log ở đây là đủ
except Exception as e:
    logger.error("Request thất bại", exc_info=e)
    return {"error": "Internal server error"}, 500
```

---

### Luật 6.4 — Không log secret hoặc dữ liệu nhạy cảm

**Xấu**

```python
logger.info(f"Đang dùng API key: {api_key}")  # Ai xem log đều thấy key!
logger.debug(f"User password: {password}")     # Cực kỳ nguy hiểm!
```

**Tốt**

```python
logger.info(f"Đang dùng API key: {api_key[:4]}...{api_key[-4:]}")
# Hoặc đơn giản:
logger.info("Đang kết nối với payment API")
```

---

### Luật 6.5 — Dùng Correlation ID để theo dõi request xuyên suốt hệ thống

**"Correlation ID" là gì?** Một mã định danh duy nhất gắn với từng request, để khi có lỗi có thể tìm lại toàn bộ hành trình của request đó qua các log.

```python
import uuid

@app.middleware("http")
async def add_correlation_id(request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

---

### Luật 6.6 — Health check phải nhẹ và không làm thay đổi dữ liệu

**"Health check" là gì?** Endpoint `/health` để hệ thống orchestration (như Kubernetes) biết service có đang sống không.

**Xấu**

```python
@app.get("/health")
def health():
    db.execute("INSERT INTO health_log VALUES (...)")  # Ghi dữ liệu! Không được!
    return {"status": "ok"}
```

**Tốt**

```python
@app.get("/health/live")
def liveness():
    return {"status": "alive"}  # Chỉ kiểm tra process có chạy không

@app.get("/health/ready")
def readiness():
    try:
        db.execute("SELECT 1")  # Kiểm tra nhẹ xem DB có kết nối không
        return {"status": "ready"}
    except:
        return {"status": "not ready"}, 503
```

---

## Phần 7 — Viết Test

### Luật 7.1 — Test phải độc lập, không phụ thuộc vào nhau

**Xấu**

```python
# Test 2 phụ thuộc vào Test 1
_shared_user = None

def test_create_user():
    global _shared_user
    _shared_user = create_user("alice@test.com")

def test_update_user():
    # Nếu test_create_user chưa chạy -> test này fail!
    update_user(_shared_user.id, name="Alice Updated")
```

**Tốt**

```python
def test_create_user():
    user = create_user("alice@test.com")
    assert user.email == "alice@test.com"

def test_update_user():
    user = create_user("bob@test.com")  # Tự tạo dữ liệu riêng
    updated = update_user(user.id, name="Bob Updated")
    assert updated.name == "Bob Updated"
```

---

### Luật 7.2 — Unit test không được gọi database thật, API thật

**"Mock" là gì?** Tạo một đối tượng giả thay thế dependency thật (database, API) để test có thể chạy nhanh và không phụ thuộc môi trường ngoài.

**Tốt**

```python
from unittest.mock import MagicMock

def test_get_user_returns_correct_data():
    # Tạo repository giả (mock), không cần database thật
    mock_repo = MagicMock()
    mock_repo.find_by_id.return_value = User(id=1, name="Alice")

    service = UserService(repo=mock_repo)
    user = service.get_user(1)

    assert user.name == "Alice"
    mock_repo.find_by_id.assert_called_once_with(1)
```

---

### Luật 7.3 — Đặt tên test rõ ràng: `test_[điều kiện]_[kết quả mong đợi]`

**Xấu**

```python
def test_user():         # Test cái gì? Kỳ vọng gì?
def test_login_fail():   # Fail vì lý do gì?
```

**Tốt**

```python
def test_login_with_wrong_password_returns_401():
def test_create_order_with_insufficient_balance_raises_error():
def test_load_config_with_missing_env_var_raises_value_error():
```

---

### Luật 7.4 — Ưu tiên test theo thứ tự: happy path → failure path → edge case

- **Happy path:** Luồng bình thường khi mọi thứ đúng.
- **Failure path:** Luồng khi có lỗi đã biết trước.
- **Edge case:** Trường hợp biên — giá trị 0, chuỗi rỗng, list rỗng.

```python
def test_calculate_discount_happy_path():
    assert calculate_discount(100, rate=0.1) == 90.0

def test_calculate_discount_with_zero_rate():
    assert calculate_discount(100, rate=0.0) == 100.0  # Edge case

def test_calculate_discount_with_negative_price_raises_error():  # Failure path
    with pytest.raises(ValueError):
        calculate_discount(-100, rate=0.1)
```

---

## Phần 8 — Bảo Mật & Secret

### Luật 8.1 — Secret không bao giờ được commit lên Git

**Secret bao gồm:** password, API key, access token, refresh token, private key, connection string có credential, signing secret, encryption key, cloud credential, webhook secret.

**Xấu**

```python
# config.py — đã bị push lên GitHub!
OPENAI_API_KEY = "sk-proj-abc123xyz..."
DATABASE_URL = "postgres://admin:password123@prod-server/db"
```

**Tốt**

```bash
# .env (file này trong .gitignore, KHÔNG BAO GIỜ commit)
OPENAI_API_KEY=sk-proj-abc123xyz...
```

```python
# config.py (được commit, không chứa giá trị thật)
import os
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
```

---

### Luật 8.2 — File `.env.example` chỉ được chứa placeholder, không chứa giá trị thật

**Xấu**

```bash
# .env.example
API_KEY=sk-proj-abc123xyz...  # Key thật trong file example!
```

**Tốt**

```bash
# .env.example
API_KEY=YOUR_API_KEY_HERE
DATABASE_URL=postgres://user:password@localhost:5432/mydb
```

---

### Luật 8.3 — Quyền tối thiểu (Least Privilege)

**"Quyền tối thiểu" là gì?** Mỗi service, user, token chỉ được cấp đúng mức quyền tối thiểu cần thiết để làm việc của mình, không nhiều hơn.

Ví dụ thực tế:

- Service chỉ đọc data → chỉ cấp quyền `SELECT`, không cần `INSERT/DELETE`
- API key chỉ dùng để gửi email → chỉ cấp quyền gửi, không cấp quyền xóa
- CI/CD pipeline chỉ cần deploy → không cấp quyền admin toàn hệ thống

---

## Phần 9 — Git, PR & Release

### Luật 9.1 — Tên branch phải có prefix rõ ràng

| Prefix | Dùng khi | Ví dụ |
|--------|----------|-------|
| `feat/` | Thêm tính năng mới | `feat/add-payment-gateway` |
| `fix/` | Sửa bug | `fix/login-timeout-issue` |
| `refactor/` | Tổ chức lại code | `refactor/extract-user-service` |
| `docs/` | Cập nhật tài liệu | `docs/update-api-readme` |
| `chore/` | Việc vặt (update dep, CI...) | `chore/upgrade-python-3.12` |
| `test/` | Thêm/sửa test | `test/add-order-service-tests` |

Tránh: `update`, `new-branch`, `fix-stuff`, `temp`, `misc`

---

### Luật 9.2 — Commit message phải rõ ràng theo format chuẩn

**Format:** `[loại]: [mô tả ngắn gọn, viết thường]`

**Xấu**

```
fix bug
update code
wip
asdfgh
```

**Tốt**

```
feat: add stripe payment gateway integration
fix: handle timeout when fetching user profile
refactor: extract order validation to separate class
test: add unit tests for invoice calculation
docs: add API authentication section to README
chore: upgrade pandas from 1.5 to 2.0
```

---

### Luật 9.3 — Mỗi commit chỉ chứa một việc, không trộn lẫn

**Xấu**

```
feat: add new checkout flow, fix bug in login, update README, refactor user model
```

**Tốt** — Tách thành nhiều commit riêng

```
feat: add new checkout flow
fix: handle null email in login validation
docs: update README with checkout API examples
refactor: simplify user model validation logic
```

---

### Luật 9.4 — Branch `main` phải được bảo vệ, không commit trực tiếp

Mọi thay đổi phải đi qua Pull Request và được ít nhất 1 người review trước khi merge.

---

## Phần 10 — Thiết Kế Code & SOLID

### Luật 10.1 — Mỗi hàm chỉ làm một việc

**Dấu hiệu vi phạm:**
- Tên hàm cần dùng "and", "then", hoặc nhiều vế
- Hàm làm nhiều side effect không liên quan
- Khó tóm tắt hàm trong một câu ngắn

**Xấu** — Một hàm làm 5 việc

```python
def process_order(order_data: dict):
    # Validate + Tính giá + Lưu DB + Gửi email + Ghi log
    if "user_id" not in order_data:
        raise ValueError("Thiếu user_id")
    total = sum(item["price"] for item in order_data["items"])
    db.save(order_data)
    email.send(order_data["email"], f"Đơn hàng {total}đ")
    logger.info("Đã xử lý")
```

**Tốt**

```python
def validate_order(data: dict) -> None:
    if "user_id" not in data:
        raise ValidationError("Thiếu user_id")

def calculate_total(items: list) -> float:
    return sum(item["price"] for item in items)

def save_order(order: Order) -> None:
    db.save(order)

def notify_customer(email: str, total: float) -> None:
    email_service.send(email, f"Đơn hàng {total}đ")
```

---

### Luật 10.2 — Hàm ngắn vừa nhìn hiểu được (~30 dòng logic)

| Độ dài | Đánh giá |
|--------|----------|
| Dưới 30 dòng | Bình thường |
| 30–50 dòng | Nên xem lại có thể tách không |
| Trên 50 dòng | Phải có lý do rõ ràng hoặc tách ra |

---

### Luật 10.3 — Không quá nhiều tham số (thường ≤ 4)

**Xấu**

```python
def create_user(name, email, phone, address, city, country, zip_code, age, gender):
    ...
```

**Tốt** — Nhóm tham số liên quan vào một object

```python
@dataclass
class UserProfile:
    name: str
    email: str
    phone: str
    address: str
    city: str
    country: str

def create_user(profile: UserProfile, age: int):
    ...
```

---

### Luật 10.4 — SOLID

| Nguyên tắc | Giải thích đơn giản |
|------------|---------------------|
| **S** — Single Responsibility | Mỗi class chỉ làm một việc. Nếu class cần thay đổi vì 2 lý do khác nhau thì tách ra. |
| **O** — Open/Closed | Thêm tính năng mới = thêm code mới, KHÔNG sửa code cũ đang hoạt động. |
| **L** — Liskov Substitution | Class con phải hoạt động đúng khi thay thế class cha. |
| **I** — Interface Segregation | Không ép class implement những phương thức nó không dùng. |
| **D** — Dependency Inversion | Code cốt lõi phụ thuộc vào abstraction (interface), không phụ thuộc trực tiếp vào chi tiết kỹ thuật. |

**Ví dụ nguyên tắc D:**

```python
# Xấu: OrderService gắn chặt với MySQL
class OrderService:
    def __init__(self):
        self.db = MySQLDatabase()  # Không thể đổi sang PostgreSQL

# Tốt: Phụ thuộc vào interface, không phụ thuộc implementation
from abc import ABC, abstractmethod

class OrderRepository(ABC):
    @abstractmethod
    def save(self, order: Order): ...

class OrderService:
    def __init__(self, repo: OrderRepository):  # Nhận bất kỳ implementation nào
        self.repo = repo
```

---

## Phần 11 — Definition of Done

**"Definition of Done" (DoD) là gì?** Danh sách điều kiện phải thỏa mãn trước khi code được coi là hoàn thành. "Code viết xong" không bằng "Done".

### Luật 11.1 — Code chỉ được coi là Done khi đáp ứng đủ các điều kiện

**Một đơn vị code là Done khi:**

- [ ] Hành vi dự kiến đã được implement
- [ ] Cả happy path và failure path đều được xử lý
- [ ] Đặt tên và cấu trúc đúng convention
- [ ] Có ít nhất 1 test cho logic mới
- [ ] Không có secret hard-code
- [ ] Có docstring cho hàm public
- [ ] Không vi phạm hướng phụ thuộc giữa các lớp

**Một PR là Done khi:**

- [ ] Tất cả điều kiện code ở trên đã đáp ứng
- [ ] CI/CD đã pass (test + lint)
- [ ] Được ít nhất 1 người review và approve
- [ ] Không có conflict với branch main
- [ ] Mô tả PR giải thích được: cái gì thay đổi và tại sao

---

### Luật 11.2 — Không gọi code là Done nếu mới chỉ viết xong phần chức năng

Nếu chưa xong hoàn toàn, phải ghi rõ: **WIP** (Work In Progress), **Draft**, hoặc **Partial**.

---

## Phần 12 — Thiết Kế API

### Luật 12.1 — URL dùng danh từ số nhiều, không dùng động từ

**Xấu**

```
POST /createUser
GET  /getOrders
DELETE /deleteProduct/5
```

**Tốt**

```
POST   /api/v1/users          <- Tạo user
GET    /api/v1/orders         <- Lấy danh sách orders
DELETE /api/v1/products/5     <- Xóa product id=5
```

---

### Luật 12.2 — URL API phải chứa version

**Tốt**

```
GET /api/v1/users/123
POST /api/v1/orders
```

> Khi cần thay đổi format response, bạn tạo `/v2/` mà không phá vỡ client đang dùng `/v1/`.

---

### Luật 12.3 — Dùng HTTP method đúng ngữ nghĩa

| Method | Dùng khi | Ghi chú |
|--------|----------|---------|
| `GET` | Lấy dữ liệu | KHÔNG được thay đổi state |
| `POST` | Tạo mới | |
| `PUT` | Thay thế toàn bộ | |
| `PATCH` | Cập nhật một phần | |
| `DELETE` | Xóa | |

Cấm: `GET /run-job`, `GET /delete-user/5` — GET mà lại làm thay đổi dữ liệu.

---

### Luật 12.4 — Idempotent: Gọi nhiều lần = kết quả như gọi 1 lần

**"Idempotent" là gì?** Nếu gửi cùng một request nhiều lần (ví dụ do lỗi mạng), hệ thống chỉ thực hiện 1 lần, không tạo trùng dữ liệu.

**Cách thực hiện:** Dùng `Idempotency-Key` trong header

```http
POST /api/v1/orders
Idempotency-Key: uuid-abc-123-def

{ "product_id": 5, "quantity": 2 }
```

---

### Luật 12.5 — Response lỗi phải nhất quán

**Tốt** — Luôn trả cùng một format lỗi

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Email không hợp lệ",
    "field": "email"
  }
}
```

---

## Phần 13 — Data & Machine Learning

### Luật 13.1 — Notebook chỉ dùng để khám phá, không dùng làm production

**Xấu** — Chạy production từ notebook

```
# Jupyter notebook train_model.ipynb
# được chạy mỗi ngày bằng cron job -> Vi phạm!
```

**Tốt** — Code production phải là Python module

```
notebooks/          <- Chỉ để khám phá, thử nghiệm
src/modeling/
  training/
    train_pipeline.py  <- Code production, được test
```

---

### Luật 13.2 — Cấu trúc thư mục chuẩn cho dự án ML

```
src/
  data/
    ingestion/       <- Adapter cho từng nguồn dữ liệu
    validation/      <- Định nghĩa schema và validator
    preprocessing/   <- Logic làm sạch và biến đổi
  features/
    engineering/     <- Hàm biến đổi feature
  modeling/
    training/        <- Orchestration training
    evaluation/      <- Metrics và đánh giá
    serving/         <- Interface inference và load model
  monitoring/
    data_quality/    <- Kiểm tra drift và chất lượng data
    model_quality/   <- Monitoring hiệu suất model
  pipelines/         <- Định nghĩa pipeline và DAG
notebooks/           <- Chỉ dành cho khám phá
artifacts/           <- Model files (loại khỏi git!)
```

---

### Luật 13.3 — Reproducibility: Cùng data + config + seed → Cùng kết quả

**"Reproducibility" là gì?** Khả năng tái tạo lại kết quả training khi chạy lại với cùng điều kiện.

```python
import random
import numpy as np

def setup_reproducibility(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    # Thêm torch.manual_seed(seed) nếu dùng PyTorch

# Luôn ghi lại seed vào experiment config
experiment_config = {
    "seed": 42,
    "model_version": "v1.2.0",
    "data_version": "2024-01-15",
}
```

---

### Luật 13.4 — Artifact (model files, data files) phải loại khỏi Git

Thêm vào `.gitignore`:

```
# Model artifacts
*.pkl
*.joblib
*.h5
*.onnx

# Data files
*.parquet
*.csv
data/raw/
artifacts/
```

---

### Luật 13.5 — Dữ liệu phải được validate schema sớm trong pipeline

**Tốt**

```python
import pandera as pa

schema = pa.DataFrameSchema({
    "user_id": pa.Column(int, nullable=False),
    "age": pa.Column(int, pa.Check.greater_than(0)),
    "email": pa.Column(str, nullable=False),
})

def validate_input_data(df):
    try:
        schema.validate(df)
    except pa.SchemaError as e:
        raise DataValidationError(f"Schema không hợp lệ: {e}")
```

---

## Phần 14 — Infrastructure & Deployment

### Luật 14.1 — Infrastructure là code — phải được version control và review

**Xấu**

```
- Vào server, tay chỉnh file nginx.conf
- Tạo thủ công database tables trên production
- Không ai biết ai đã thay đổi gì
```

**Tốt**

```
- Mọi thay đổi infrastructure đều qua Terraform/Ansible/K8s manifest
- Được review qua PR như code thường
- Lịch sử thay đổi được lưu trên Git
```

---

### Luật 14.2 — Dockerfile phải dùng multi-stage build và chạy bằng non-root user

**"Multi-stage build" là gì?** Tách giai đoạn build (cài tool, compile) khỏi giai đoạn run (chỉ chứa code cần thiết). Kết quả: image nhỏ hơn, bảo mật hơn.

**Tốt**

```dockerfile
# Stage 1: Build
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Stage 2: Runtime (image cuối không chứa tool build)
FROM python:3.12-slim
WORKDIR /app

# Tạo non-root user để chạy app (không dùng root!)
RUN adduser --disabled-password --no-create-home appuser
USER appuser

COPY --from=builder /root/.local /home/appuser/.local
COPY src/ ./src/

CMD ["python", "-m", "src.main"]
```

---

### Luật 14.3 — Secret không bao giờ được hard-code trong Dockerfile, docker-compose, hay CI/CD

**Xấu**

```yaml
# docker-compose.yml
environment:
  - DATABASE_PASSWORD=my_secret_123  # Commit lên git!
```

**Tốt**

```yaml
# docker-compose.yml
environment:
  - DATABASE_PASSWORD=${DATABASE_PASSWORD}  # Đọc từ .env (không commit)
```

---

### Luật 14.4 — CI/CD pipeline phải có các bước: test → build → scan → deploy

**Ví dụ cấu trúc GitHub Actions:**

```yaml
jobs:
  test:
    steps:
      - run: pytest tests/       # Chạy test
      - run: flake8 src/         # Kiểm tra code style

  build:
    needs: test
    steps:
      - run: docker build .      # Build image

  scan:
    needs: build
    steps:
      - uses: aquasecurity/trivy-action  # Scan lỗ hổng bảo mật

  deploy:
    needs: scan
    steps:
      - run: kubectl apply ...   # Deploy (chỉ khi tất cả bước trên pass)
```

---

## Phần 15 — Tài Liệu & Docstring

### Luật 15.1 — Tài liệu giải thích TẠI SAO, không phải LÀM GÌ

**Xấu** — Chú thích giải thích cái đã rõ

```python
# Tăng i lên 1
i += 1

# Trả về user
return user
```

**Tốt** — Chú thích giải thích lý do không rõ

```python
# Dùng ceiling division thay vì floor để đảm bảo luôn có đủ batch
# ngay cả khi data không chia hết cho batch_size
num_batches = math.ceil(len(data) / batch_size)

# Retry 3 lần với exponential backoff — theo SLA của payment provider
MAX_PAYMENT_RETRIES = 3
```

---

### Luật 15.2 — Mọi hàm public phải có docstring theo Google style

**Tốt**

```python
def calculate_discount(price: float, rate: float, is_vip: bool) -> float:
    """Tính giá sau khi áp dụng giảm giá.

    VIP được giảm thêm 50% so với khách thường.

    Args:
        price: Giá gốc (VNĐ).
        rate: Tỷ lệ giảm, ví dụ 0.1 = giảm 10%.
        is_vip: True nếu là khách VIP.

    Returns:
        Giá sau khi giảm.

    Raises:
        ValueError: Nếu price hoặc rate âm.

    Example:
        >>> calculate_discount(100_000, 0.1, is_vip=True)
        85000.0
    """
    if price < 0 or rate < 0:
        raise ValueError("price và rate không được âm")
    multiplier = 1.5 if is_vip else 1.0
    return price * (1 - rate * multiplier)
```

---

### Luật 15.3 — Luôn dùng type hints cho tham số và giá trị trả về

**"Type hints" là gì?** Khai báo kiểu dữ liệu của tham số và giá trị trả về của hàm, giúp IDE phát hiện lỗi sớm.

**Xấu**

```python
def process(data, threshold, flag):
    ...
```

**Tốt**

```python
def process(data: pd.DataFrame, threshold: float, flag: bool) -> pd.Series:
    ...
```

---

### Luật 15.4 — Tài liệu lỗi thời phải được xóa hoặc cảnh báo rõ

**Tốt**

```python
# WARNING: Hàm này đang được deprecated, dùng `calculate_v2()` thay thế.
# Sẽ bị xóa sau 2025-06-01
def calculate_v1():
    ...
```

---

### Luật 15.5 — README.md phải có đủ thông tin để developer mới chạy được dự án

README tối thiểu cần có:

- Mô tả ngắn về dự án
- Hướng dẫn cài đặt và setup
- Cách chạy local
- Cách chạy test
- Cấu trúc dự án (tóm tắt)
- Thông tin liên hệ hoặc tài liệu thêm

---

## Phần 16 — Kiến Trúc Hệ Thống

### Luật 16.1 — Phân loại kiến trúc trước khi áp dụng quy ước

**Tier 1** — Áp dụng cho MỌI loại kiến trúc (Monolith, Modular Monolith, Microservices):
Các quy ước về module boundary, data ownership, giao tiếp giữa module.

**Tier 2** — Chỉ áp dụng khi đã xác nhận là Microservices:
Circuit Breaker, Saga Pattern, Transactional Outbox, Service Mesh.

> Không bao giờ áp dụng Tier 2 khi chưa xác nhận kiến trúc với team.

---

### Luật 16.2 — Tổ chức module theo nghiệp vụ, không theo kỹ thuật

**Xấu** — Tổ chức theo kỹ thuật

```
src/
  models/        <- gom tất cả model
  controllers/   <- gom tất cả controller
  services/      <- gom tất cả service
```

**Tốt** — Tổ chức theo nghiệp vụ

```
src/
  catalog/       <- toàn bộ code liên quan đến danh mục sản phẩm
  payment/       <- toàn bộ code liên quan đến thanh toán
  notification/  <- toàn bộ code liên quan đến thông báo
```

> Khi yêu cầu về thanh toán thay đổi, chỉ cần sửa trong thư mục `payment/`, không phải tìm trong 3-4 thư mục kỹ thuật.

---

### Luật 16.3 — Module không được truy cập trực tiếp vào data của module khác

**Xấu**

```python
# catalog/application/order_service.py
# Module catalog query thẳng bảng của module customer!
customers = db.execute("SELECT * FROM customer_accounts WHERE ...")
```

**Tốt**

```python
# catalog/application/order_service.py
# Gọi qua interface công khai của module customer
customer = await customer_service.get_by_id(customer_id)
```

---

### Luật 16.4 — Module giao tiếp qua interface, không import nội bộ của nhau

**Xấu**

```python
# catalog/application/order_service.py
from payment.infrastructure.stripe_client import StripeClient  # Import nội bộ!
```

**Tốt**

```python
# payment/contracts.py — interface công khai của module payment
class PaymentGateway(Protocol):
    async def charge(self, amount: Decimal, customer_id: str) -> PaymentResult: ...

# catalog/application/order_service.py
from payment.contracts import PaymentGateway  # Chỉ import interface
```

---

## Phần 17 — Feature Flags

**"Feature Flag" là gì?** Biến cấu hình để bật/tắt tính năng tại runtime mà không cần deploy lại code. Rất hữu ích để thả tính năng từ từ, A/B test, hoặc tắt khẩn cấp khi có lỗi.

### Luật 17.1 — Phân loại flag trước khi dùng

| Loại | Vòng đời | Mục đích |
|------|----------|---------|
| **Release flag** | Vài ngày–vài tuần | Ẩn tính năng chưa hoàn thiện |
| **Operational flag** | Vài tháng–vài năm | Tắt tính năng nặng khi quá tải |
| **Experiment / A-B flag** | Vài tuần–vài tháng | So sánh 2 version để đo hiệu quả |
| **Permission flag** | Vĩnh viễn | Cấp tính năng premium cho user cụ thể |

---

### Luật 17.2 — Luôn có giá trị mặc định an toàn (fallback về hành vi cũ)

**Xấu**

```python
use_new_payment = feature_flags.get("enable_new_payment")
# Nếu flag service bị lỗi -> trả về None -> crash!
if use_new_payment:
    ...
```

**Tốt**

```python
# default=False -> nếu flag service bị lỗi, dùng cách cũ (an toàn)
use_new_payment = feature_flags.get("enable_new_payment", default=False)
if use_new_payment:
    return new_payment_gateway.charge(amount)
return old_payment_gateway.charge(amount)  # Luôn có fallback
```

---

### Luật 17.3 — Kiểm tra flag ở tầng ngoài (Interface/Application), không sâu trong Domain

**Xấu**

```python
# src/domain/order.py <- DOMAIN
class Order:
    def process(self):
        if feature_flags.get("new_discount_logic"):  # Flag không nên ở đây
            ...
```

**Tốt**

```python
# src/interfaces/http/order_router.py <- INTERFACE (tầng ngoài)
@app.post("/orders")
def create_order(data: dict):
    use_new_logic = feature_flags.get("new_discount_logic", default=False)
    # Truyền xuống như tham số bình thường, không nhúng flag vào domain
    order_service.process(data, use_new_logic=use_new_logic)
```

---

### Luật 17.4 — Tạo ticket dọn dẹp flag ngay khi tạo flag

**Quy trình bắt buộc:**

1. Tạo flag mới trong code
2. **Ngay lập tức** tạo Jira/GitHub issue: "Xóa flag `enable_new_payment` sau khi rollout xong"
3. Set deadline: 2–4 tuần (với release flag)
4. Khi rollout 100% → xóa flag, xóa code cũ, đóng ticket

---

### Luật 17.5 — Tránh "flag spaghetti" — lồng ghép nhiều flag trong cùng một block

**Xấu**

```python
if feature_flags.get("flag_a"):
    if feature_flags.get("flag_b"):
        if feature_flags.get("flag_c"):
            # Logic ở đây
```

**Tốt** — Giải quyết logic rõ ràng hơn trước khi dùng flag

```python
use_new_flow = (
    feature_flags.get("flag_a", False) and
    feature_flags.get("flag_b", False)
)
if use_new_flow:
    ...
```

---

## Phần 18 — Observability & Orchestration Nâng Cao

> Phần này dành cho môi trường production với Kubernetes, Prometheus, Grafana, Terraform, Airflow. Với dự án nhỏ/local, bỏ qua hoặc tham khảo khi cần.

### Luật 18.1 — Docker image production phải có HEALTHCHECK

**"HEALTHCHECK" là gì?** Lệnh trong Dockerfile để Docker/Kubernetes tự kiểm tra container có còn hoạt động không.

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8000/health/live || exit 1
```

---

### Luật 18.2 — Không bao giờ deploy image tag `latest` lên staging/production

**Xấu**

```bash
docker build -t myapp:latest .
# deploy latest -> Không biết đang chạy version nào!
```

**Tốt**

```bash
# Tag với version + commit SHA để luôn biết chính xác đang chạy gì
docker build -t myapp:1.4.2 -t myapp:1.4.2-abc1234 .
```

---

### Luật 18.3 — Scan lỗ hổng bảo mật (vulnerability scan) trong CI

**"Vulnerability scan" là gì?** Kiểm tra image Docker có chứa thư viện có lỗ hổng bảo mật đã biết không.

```yaml
# GitHub Actions
- name: Scan image with Trivy
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: myapp:${{ github.sha }}
    exit-code: 1          # CI fail nếu tìm thấy lỗ hổng HIGH/CRITICAL
    severity: HIGH,CRITICAL
```

---

### Luật 18.4 — Terraform: đặt tên resource theo snake_case, không lặp lại loại resource

**Xấu**

```hcl
resource "aws_s3_bucket" "aws_s3_bucket_model_artifacts" { ... }
variable "dbInstanceClass" { ... }  # camelCase -> sai
```

**Tốt**

```hcl
resource "aws_s3_bucket" "model_artifacts" { ... }
variable "db_instance_class" { ... }  # snake_case -> đúng
output "db_instance_endpoint" { ... }  # format: {name}_{type}_{attribute}
```

---

### Luật 18.5 — Prometheus metrics phải có tên ổn định và nhãn không tăng vô hạn

**"Label cardinality" là gì?** Số lượng giá trị khác nhau của một label. Label với cardinality cao (ví dụ: `user_id`) sẽ tạo ra hàng triệu time series, làm Prometheus chậm hoặc crash.

**Xấu**

```python
# Label user_id có hàng triệu giá trị -> cardinality bùng nổ!
request_counter = Counter(
    "api_requests_total",
    labels=["user_id", "endpoint"]  # user_id không giới hạn!
)
```

**Tốt**

```python
# Chỉ dùng label có số lượng giá trị cố định, nhỏ
request_counter = Counter(
    "api_requests_total",
    labels=["endpoint", "method", "status_code"]  # Có giới hạn
)
```

---

### Luật 18.6 — Alert phải dựa trên triệu chứng ảnh hưởng user, không dựa trên nguyên nhân kỹ thuật

**Xấu** — Alert theo nguyên nhân kỹ thuật

```yaml
alert: HighCPU
expr: cpu_usage > 0.8  # CPU 80% chưa chắc ảnh hưởng user
```

**Tốt** — Alert theo triệu chứng người dùng cảm nhận được

```yaml
alert: HighLatencyP99
expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 0.5
# P99 latency > 500ms trong 5 phút -> user đang bị ảnh hưởng thật sự
```

---

## Bảng Thuật Ngữ

| Thuật ngữ | Giải thích đơn giản |
|-----------|---------------------|
| **Layer / Lớp** | Tầng trong kiến trúc, mỗi lớp có trách nhiệm riêng |
| **Domain** | Lớp chứa luật nghiệp vụ cốt lõi, không biết đến framework hay database |
| **Infrastructure** | Lớp kết nối kỹ thuật: database, API ngoài, file system |
| **Dependency** | A phụ thuộc B khi A phải import từ B |
| **Abstract class / Protocol** | "Hợp đồng" định nghĩa "phải có gì", chưa nói "làm thế nào" |
| **Hard-code** | Viết giá trị cố định vào code thay vì đọc từ config/env |
| **Idempotent** | Gọi nhiều lần = kết quả như gọi 1 lần |
| **Secret** | Password, API key, token — bất cứ thứ gì mà nếu lộ sẽ gây hại |
| **Feature Flag** | Công tắc bật/tắt tính năng mà không cần deploy lại |
| **Mock** | Đối tượng giả thay thế dependency thật (DB, API) trong test |
| **Fixture** | Dữ liệu hoặc đối tượng chuẩn bị sẵn cho nhiều test dùng chung |
| **Docstring** | Chuỗi mô tả đặt trong hàm/class giải thích nó làm gì |
| **Structured logging** | Log dưới dạng key-value thay vì chuỗi tự do |
| **Correlation ID** | Mã định danh gắn với request để theo dõi xuyên suốt hệ thống |
| **Health check** | Endpoint kiểm tra service có đang sống và sẵn sàng không |
| **Reproducibility** | Cùng điều kiện → cùng kết quả (quan trọng với ML) |
| **Cardinality** | Số lượng giá trị khác nhau của một label/thuộc tính |
| **Pull Request (PR)** | Yêu cầu merge code từ branch của mình vào branch chính |
| **Multi-stage build** | Tách giai đoạn build và run trong Dockerfile → image nhỏ hơn |
| **IaC (Infrastructure as Code)** | Quản lý infrastructure bằng code (Terraform, Ansible...) |
| **Liveness probe** | Kiểm tra process có còn sống không → fail thì restart container |
| **Readiness probe** | Kiểm tra service có sẵn sàng nhận traffic không |
| **Circuit Breaker** | Ngừng gửi request tới service đang lỗi để hệ thống phục hồi |
| **Saga Pattern** | Chuỗi transaction phân tán, có compensating action nếu lỗi |
| **Bounded Context** | Ranh giới ngữ nghĩa mà domain model được áp dụng hợp lệ |
| **Least Privilege** | Mỗi thành phần chỉ có quyền tối thiểu cần thiết |
| **DoD (Definition of Done)** | Tập điều kiện phải thỏa mãn trước khi coi là hoàn thành |
| **WIP (Work In Progress)** | Công việc đang làm dở, chưa hoàn thiện |
| **ADR (Architecture Decision Record)** | Tài liệu ghi nhận lý do đưa ra quyết định kiến trúc |
| **Flag spaghetti** | Anti-pattern: lồng ghép quá nhiều feature flag, code rối rắm |
| **Artifact** | File đầu ra của quá trình build/train: model file, compiled code... |

---

## Checklist Trước Khi Submit Code

### Đặt tên & cấu trúc

- [ ] Tên class dùng `PascalCase`, hàm/biến dùng `snake_case`, hằng số dùng `UPPER_CASE`
- [ ] Tên file dùng `snake_case`
- [ ] Không có tên mơ hồ như `data`, `info`, `manager`, `temp`, `handle`

### Import & phụ thuộc

- [ ] Import được nhóm đúng 3 nhóm (stdlib → thirdparty → local)
- [ ] Không dùng `from x import *`
- [ ] Không có Domain import từ Infrastructure

### Config & bảo mật

- [ ] Không có `os.getenv()` rải rác ngoài module config
- [ ] Không có password/API key hard-code trong code
- [ ] File `.env.example` chỉ có placeholder, không có giá trị thật

### Chất lượng code

- [ ] Mỗi hàm làm dưới ~30 dòng và 1 việc rõ ràng
- [ ] Không có `except Exception: pass` hay bắt lỗi quá rộng
- [ ] Hàm public có docstring với type hints

### Test

- [ ] Có ít nhất 1 test cho logic mới
- [ ] Test đặt tên rõ: `test_[điều kiện]_[kết quả mong đợi]`
- [ ] Test không gọi database thật, API thật (dùng mock)

### Git & PR

- [ ] Tên branch đúng format: `feat/`, `fix/`, `refactor/`...
- [ ] Commit message đúng format: `feat:`, `fix:`, `docs:`...
- [ ] PR có mô tả giải thích cái gì thay đổi và tại sao

### Feature flag (nếu có)

- [ ] Có fallback mặc định an toàn (`default=False`)
- [ ] Flag được kiểm tra ở tầng ngoài, không sâu trong Domain
- [ ] Đã tạo ticket dọn dẹp flag với deadline rõ ràng

---

*Tài liệu này tóm tắt từ bộ 18 coding conventions v1.2 (2026-03-30)*
*Để biết chi tiết đầy đủ, tham chiếu các file gốc trong thư mục `Coding_conventions/`*
