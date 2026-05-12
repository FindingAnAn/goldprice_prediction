# 04-Dependencies-Imports / Quy ước về Dependencies và Imports

## 1. Purpose / Mục đích

**EN**  
This document defines the rules for imports and dependencies across the codebase.  
It separates code-style concerns from architecture concerns so that the project remains both readable and structurally correct.

**VI**  
Tài liệu này định nghĩa các quy tắc về imports và dependencies trong toàn bộ codebase.  
Tài liệu tách riêng vấn đề style code và vấn đề kiến trúc để hệ thống vừa dễ đọc vừa đúng cấu trúc.

---

## 2. Scope / Phạm vi

**EN**  
This document covers:
- import placement and formatting
- import grouping and ordering
- absolute versus relative import usage
- allowed and forbidden module dependencies
- circular dependency avoidance
- enforcement through tools and review

**VI**  
Tài liệu này bao gồm:
- vị trí và cách viết import
- cách nhóm và sắp xếp import
- nguyên tắc dùng absolute import và relative import
- luật dependency được phép và bị cấm
- cách tránh circular dependency
- cách thực thi bằng tool và code review

---

## 3. Core principle / Nguyên tắc cốt lõi

**EN**  
Imports are a code-style concern.  
Dependencies are an architecture concern.  
Both must be controlled separately.

**VI**  
Imports là vấn đề về style code.  
Dependencies là vấn đề về kiến trúc.  
Hai phần này phải được kiểm soát riêng.

---

## 4. Import conventions / Quy ước về import

### 4.1 Imports must be placed at the top of the file / Import phải đặt ở đầu file

**EN**  
Imports must appear at the top of the file, after the module docstring and before constants, class definitions, and executable code.

**VI**  
Import phải được đặt ở đầu file, sau module docstring và trước constant, class, và phần code thực thi.

**Allowed / Hợp lệ**
```python
"""User service module."""

import os
from pathlib import Path

from app.domain.user import User
```

**Avoid / Tránh**
```python
MAX_RETRY = 3

import os
```

---

### 4.2 Imports must be grouped in three sections / Import phải được nhóm thành ba phần

**EN**  
Imports must be grouped in this order:
1. standard library
2. third-party packages
3. local application imports

Each group must be separated by one blank line.

**VI**  
Import phải được nhóm theo thứ tự:
1. thư viện chuẩn
2. thư viện bên thứ ba
3. module nội bộ của dự án

Mỗi nhóm phải cách nhau bằng một dòng trống.

**Example / Ví dụ**
```python
import os
import sys

import requests

from app.services.user_service import UserService
```

---

### 4.3 Prefer one import per line / Ưu tiên một import trên mỗi dòng

**EN**  
Prefer one import per line for clarity and clean diffs.

**VI**  
Ưu tiên một import trên mỗi dòng để dễ đọc và dễ review diff.

**Preferred / Ưu tiên**
```python
import os
import sys
```

**Avoid / Tránh**
```python
import os, sys
```

**Note / Ghi chú**  
Using `from x import A, B` is acceptable when the imported names are closely related and readability remains good.

---

### 4.4 Prefer absolute imports by default / Mặc định ưu tiên absolute import

**EN**  
Use absolute imports as the default import style across the project.

**VI**  
Mặc định dùng absolute import trong toàn bộ dự án.

**Preferred / Ưu tiên**
```python
from app.application.user_service import UserService
```

**Less preferred / Ít ưu tiên hơn**
```python
from ..application.user_service import UserService
```

**Rule note / Ghi chú**
- Use absolute imports for cross-package access.
- Relative imports are acceptable only when they remain short and obvious.

- Dùng absolute import khi truy cập qua package khác.
- Relative import chỉ chấp nhận được khi ngắn và rõ ràng.

---

### 4.5 Relative imports are allowed only inside closely related packages / Chỉ cho phép relative import trong package nội bộ gần nhau

**EN**  
Relative imports may be used only when:
- the modules are in the same package or directly adjacent subpackages
- the relative path is short and obvious
- readability is not reduced

**VI**  
Relative import chỉ được dùng khi:
- các module nằm trong cùng package hoặc subpackage gần nhau
- đường dẫn tương đối ngắn và dễ hiểu
- không làm giảm khả năng đọc code

**Allowed / Hợp lệ**
```python
from .validators import validate_user
from .schemas import UserRequest
```

**Avoid / Tránh**
```python
from ...infrastructure.database.repositories.user_repository import UserRepository
```

---

### 4.6 Wildcard imports are forbidden by default / Cấm wildcard import theo mặc định

**EN**  
`from module import *` is forbidden unless a package intentionally re-exports a controlled public API.

**VI**  
`from module import *` bị cấm theo mặc định, trừ khi package đó cố ý re-export một public API đã được kiểm soát.

**Avoid / Tránh**
```python
from utils import *
```

**Allowed exception / Ngoại lệ được phép**
```python
# package public API only, with explicit review
from .public_types import *
```

---

### 4.7 Local imports inside functions are exceptions, not the default / Import bên trong function là ngoại lệ, không phải mặc định

**EN**  
Imports inside functions are allowed only when there is a clear technical reason, such as:
- optional dependencies
- performance-sensitive lazy loading
- temporary isolation from circular imports during refactoring

**VI**  
Import bên trong function chỉ được phép khi có lý do kỹ thuật rõ ràng, ví dụ:
- dependency tùy chọn
- lazy loading vì hiệu năng
- cô lập tạm thời để xử lý circular import trong lúc refactor

**Rule / Luật**
- document the reason in a short comment when the reason is not obvious
- do not use local imports to hide poor architecture

- ghi chú ngắn lý do nếu không hiển nhiên
- không dùng local import để che kiến trúc kém

---

## 5. Dependency conventions / Quy ước về dependency

### 5.1 Purpose / Mục đích

**EN**  
Dependency rules define which layers, modules, and packages are allowed to depend on each other.  
Their purpose is to preserve architectural boundaries, reduce coupling, and keep business logic stable.

**VI**  
Luật dependency định nghĩa layer, module, và package nào được phép phụ thuộc vào nhau.  
Mục tiêu là giữ ranh giới kiến trúc, giảm coupling, và làm cho business logic ổn định.

---

### 5.2 Core principle / Nguyên tắc cốt lõi

**EN**  
Dependencies must follow architectural direction, not convenience.  
No module may depend on another module simply because it is easy to import.

**VI**  
Dependency phải đi theo hướng kiến trúc, không đi theo sự tiện tay.  
Không module nào được phép phụ thuộc vào module khác chỉ vì nó dễ import.

---

### 5.3 Dependency direction / Hướng phụ thuộc

**EN**  
Dependencies must flow inward toward business logic.

Default direction:
- interfaces -> application
- application -> domain
- infrastructure -> application or domain contracts
- domain -> no outward dependency

**VI**  
Dependency phải đi từ ngoài vào trong, hướng về business logic.

Hướng mặc định:
- interfaces -> application
- application -> domain
- infrastructure -> application hoặc domain contracts
- domain -> không phụ thuộc ra ngoài

---

### 5.4 Layer rules / Luật theo từng layer

#### Domain layer / Lớp domain

**EN**  
The domain layer contains business rules and core concepts.  
It must not depend on frameworks, transport logic, infrastructure adapters, or deployment concerns.

**VI**  
Lớp domain chứa luật nghiệp vụ và khái niệm cốt lõi.  
Lớp này không được phụ thuộc vào framework, transport logic, adapter hạ tầng, hay concern triển khai.

**Allowed / Được phép**
- domain entities
- domain value objects
- domain services
- domain validations
- small shared abstractions with no framework coupling

**Forbidden / Bị cấm**
- HTTP framework objects
- ORM sessions and database clients
- API request/response schema
- queue clients, cloud SDKs, file system adapters

---

#### Application layer / Lớp application

**EN**  
The application layer coordinates use cases and workflows.  
It may depend on domain logic and abstract contracts, but should avoid direct dependence on framework-specific transport objects.

**VI**  
Lớp application điều phối use case và workflow.  
Lớp này có thể phụ thuộc vào domain logic và abstract contract, nhưng nên tránh phụ thuộc trực tiếp vào transport object đặc thù của framework.

**Allowed / Được phép**
- domain modules
- use-case services
- repository interfaces
- service contracts
- DTOs internal to application

**Avoid / Tránh**
- direct framework request/response objects
- direct cloud or deployment runtime objects
- embedding infrastructure implementation details

---

#### Interface layer / Lớp interface

**EN**  
The interface layer handles transport and entrypoints such as HTTP routes, CLI commands, schedulers, or message consumers.  
It may depend on the application layer and framework code, but it must remain thin.

**VI**  
Lớp interface xử lý transport và entrypoint như HTTP route, CLI command, scheduler, hoặc message consumer.  
Lớp này có thể phụ thuộc vào application layer và framework code, nhưng phải giữ mỏng.

**Allowed / Được phép**
- application services
- serializers
- request/response schemas
- framework code
- input/output mapping

**Forbidden / Bị cấm**
- embedding business rules directly
- orchestrating infrastructure details directly when application services already exist
- direct cross-layer shortcuts into deep infrastructure modules without justification

---

#### Infrastructure layer / Lớp infrastructure

**EN**  
Infrastructure implements technical concerns such as persistence, messaging, filesystem access, and third-party integrations.  
It may depend on domain contracts and application interfaces, but it must not become the place where business workflows are defined.

**VI**  
Lớp infrastructure triển khai các concern kỹ thuật như persistence, messaging, filesystem access, và third-party integrations.  
Lớp này có thể phụ thuộc vào contract của domain và interface của application, nhưng không được trở thành nơi định nghĩa workflow nghiệp vụ.

**Allowed / Được phép**
- database drivers
- SDKs
- repository implementations
- adapter implementations
- provider-specific integrations

**Forbidden / Bị cấm**
- domain decision making
- business orchestration
- transport-layer responsibilities

---

### 5.5 Depend on abstractions, not concrete implementations / Phụ thuộc vào abstraction, không phụ thuộc vào triển khai cụ thể

**EN**  
Application and domain logic should depend on contracts, interfaces, or abstractions whenever possible.  
Concrete implementations should live in infrastructure and be wired at the composition boundary.

**VI**  
Application và domain logic nên phụ thuộc vào contract, interface, hoặc abstraction khi có thể.  
Phần triển khai cụ thể phải nằm ở infrastructure và được nối tại composition boundary.

**Preferred / Ưu tiên**
- `UserRepository` interface in application or domain
- `PostgresUserRepository` implementation in infrastructure

**Avoid / Tránh**
- application services importing `PostgresUserRepository` directly unless the project is intentionally simple and the exception is documented

---

### 5.6 No forbidden cross-layer shortcuts / Cấm đi tắt sai layer

**EN**  
A higher-level layer must not bypass the intended architecture just to reach a lower-level technical implementation directly.

**VI**  
Một layer không được phép đi tắt phá kiến trúc chỉ để chạm trực tiếp vào implementation kỹ thuật ở layer khác.

**Examples / Ví dụ**

**Forbidden / Bị cấm**
- route -> database repository directly, when application service exists
- domain -> ORM model
- domain -> HTTP exception
- application -> concrete cloud SDK client when an adapter boundary should exist

---

### 5.7 Public and internal package boundaries / Ranh giới package public và internal

**EN**  
Each package should define what is safe to import from the outside and what is internal-only.

**VI**  
Mỗi package nên xác định rõ phần nào được phép import từ bên ngoài và phần nào chỉ dùng nội bộ.

**Rules / Luật**
- public modules should be stable and documented
- internal modules may be prefixed or kept undocumented
- other packages must not depend on deep internal modules unless explicitly allowed

---

### 5.8 Circular dependency policy / Chính sách với circular dependency

**EN**  
Circular dependencies are treated as an architectural smell.  
They must be fixed through restructuring, not hidden with random local imports.

**VI**  
Circular dependency được xem là dấu hiệu mùi kiến trúc xấu.  
Chúng phải được xử lý bằng tái cấu trúc, không phải che lại bằng local import ngẫu nhiên.

**Preferred fixes / Cách sửa ưu tiên**
1. extract a shared abstraction
2. move shared contracts to a lower layer
3. separate responsibilities more clearly
4. split modules by concern

**Avoid / Tránh**
- fixing cycles by scattering imports inside functions without architectural reason
- keeping mutually dependent services in the same unstable design

---

### 5.9 Dependency review checklist / Checklist review dependency

**EN**  
When reviewing code, check:
- Is the dependency direction correct?
- Does this layer import something it should not know about?
- Is there any direct dependence on infrastructure where an abstraction should exist?
- Is any business logic leaking into interface or infrastructure?
- Is there any sign of circular dependency?

**VI**  
Khi review code, cần kiểm tra:
- Hướng dependency đã đúng chưa?
- Layer này có import thứ mà nó không nên biết không?
- Có phụ thuộc trực tiếp vào infrastructure trong khi đáng ra phải qua abstraction không?
- Có business logic nào đang rò sang interface hoặc infrastructure không?
- Có dấu hiệu circular dependency không?

---

### 5.10 Definition of dependency compliance / Điều kiện tuân thủ dependency

**EN**  
A module is dependency-compliant only if:
- it depends only on allowed layers
- it does not import forbidden framework or infrastructure objects
- it respects package boundaries
- it avoids concrete implementation coupling where abstractions are required
- it does not introduce circular dependency

**VI**  
Một module chỉ được coi là tuân thủ dependency khi:
- nó chỉ phụ thuộc vào các layer được phép
- nó không import framework hoặc infrastructure object bị cấm
- nó tôn trọng ranh giới package
- nó không ghép chặt vào implementation cụ thể khi đáng ra phải qua abstraction
- nó không tạo ra circular dependency

---

## 6. Enforcement / Cách thực thi

### 6.1 Automated tools / Công cụ tự động

**EN**  
Use automated tooling to enforce import style consistently.

Recommended tools:
- `isort` for import grouping and ordering
- `black` for formatting
- `flake8` for lint checks
- `pylint` for additional static checks

**VI**  
Dùng công cụ tự động để đảm bảo import style được nhất quán.

Công cụ khuyến nghị:
- `isort` để nhóm và sắp xếp import
- `black` để format code
- `flake8` để lint
- `pylint` để kiểm tra tĩnh bổ sung

### 6.2 Code review checks / Checklist khi review

**EN**  
Reviewers must check:
- Is the import order correct?
- Is wildcard import avoided?
- Is the dependency direction correct?
- Is a local import being used for a justified reason?
- Is any layer importing a forbidden module?

**VI**  
Reviewer phải kiểm tra:
- Thứ tự import đã đúng chưa?
- Có tránh wildcard import chưa?
- Chiều dependency có đúng không?
- Local import có lý do chính đáng không?
- Có layer nào import module bị cấm không?

### 6.3 CI expectations / Kỳ vọng ở CI

**EN**  
CI should fail when:
- import formatting is incorrect
- unused imports remain
- forbidden dependency patterns are detected by linting or architecture checks

**VI**  
CI nên fail khi:
- format import sai
- còn unused import
- phát hiện dependency pattern bị cấm qua lint hoặc architecture checks

---

## 7. Anti-patterns / Mẫu xấu cần tránh

**EN**  
Avoid:
- importing infrastructure directly into domain
- importing repositories directly into routes when application services exist
- deep relative imports across unrelated packages
- wildcard imports
- import cycles hidden behind local imports
- mixing framework objects into business logic

**VI**  
Tránh:
- import infrastructure trực tiếp vào domain
- import repository trực tiếp vào route khi đã có application service
- relative import sâu giữa các package không liên quan
- wildcard import
- giấu import cycle bằng local import
- trộn object của framework vào business logic

---

## 8. Definition of done / Điều kiện hoàn thành

**EN**  
A module is compliant only if:
- imports are grouped correctly
- absolute imports are used by default
- relative imports are limited and justified
- wildcard imports are absent unless explicitly approved
- dependency direction respects architecture
- no forbidden cross-layer imports exist
- no circular dependency is introduced

**VI**  
Một module chỉ được coi là tuân thủ khi:
- import được nhóm đúng
- absolute import được dùng làm mặc định
- relative import bị giới hạn và có lý do rõ
- không có wildcard import trừ khi được phê duyệt rõ ràng
- chiều dependency tôn trọng kiến trúc
- không có cross-layer import bị cấm
- không tạo ra circular dependency
