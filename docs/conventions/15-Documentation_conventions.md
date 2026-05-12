# 15-Documentation-Conventions / Quy ước về tài liệu và chú thích code

## 1. Purpose / Mục đích

### EN
This document defines the conventions for writing documentation inside code (docstrings, type hints, inline comments) and outside code (README, CHANGELOG, Architecture Decision Records).
Its purpose is to ensure that documentation is consistent, actionable, maintainable, and useful for both human developers and coding agents.

### VI
Tài liệu này định nghĩa các quy ước về viết tài liệu bên trong code (docstring, type hint, comment nội tuyến) và bên ngoài code (README, CHANGELOG, Architecture Decision Record).
Mục tiêu là đảm bảo tài liệu nhất quán, hành động được, dễ bảo trì, và hữu ích cho cả developer lẫn coding agent.

---

## 2. Scope / Phạm vi

### EN
This document applies to:

- docstrings for functions, classes, and modules
- type hints and type annotations
- inline comments and markers (TODO, FIXME)
- README files
- CHANGELOG files
- Architecture Decision Records (ADR)
- agent-generated documentation

### VI
Tài liệu này áp dụng cho:

- docstring cho function, class, và module
- type hint và type annotation
- comment nội tuyến và marker (TODO, FIXME)
- file README
- file CHANGELOG
- Architecture Decision Record (ADR)
- tài liệu do agent sinh ra

---

## 3. Core principles / Nguyên tắc cốt lõi

### 3.1 Document the WHY, not the WHAT / Tài liệu hóa LÝ DO, không phải ĐIỀU GÌ

#### EN
Documentation must explain intent, context, constraints, and non-obvious decisions.
Code that is well-named and well-structured already communicates what it does.
Documentation adds value when it explains why a design choice was made, what trade-offs were considered, and what assumptions are in effect.

#### VI
Tài liệu phải giải thích ý đồ, ngữ cảnh, ràng buộc, và các quyết định không hiển nhiên.
Code được đặt tên tốt và cấu trúc tốt đã tự truyền tải được nó làm gì.
Tài liệu tạo giá trị khi nó giải thích vì sao chọn thiết kế đó, trade-off nào đã được cân nhắc, và giả định nào đang có hiệu lực.

---

### 3.2 Documentation is part of the change, not an afterthought / Tài liệu là một phần của thay đổi, không phải việc nghĩ tới sau

#### EN
Documentation must be created or updated as part of the same change that modifies behavior.
A change that alters a function's contract, a module's responsibility, or a project's setup requirements is not done until the relevant documentation is updated.

#### VI
Tài liệu phải được tạo hoặc cập nhật như một phần của cùng thay đổi mà nó ảnh hưởng.
Một thay đổi làm thay đổi contract của function, trách nhiệm của module, hoặc yêu cầu setup của dự án chưa được coi là done cho đến khi tài liệu liên quan được cập nhật.

---

### 3.3 Stale documentation is worse than no documentation / Tài liệu cũ kỹ tệ hơn không có tài liệu

#### EN
Outdated documentation actively misleads developers and agents.
If documentation cannot be kept current, it must be removed or marked as potentially stale with a clear warning.

#### VI
Tài liệu lỗi thời chủ động đánh lừa developer và agent.
Nếu tài liệu không thể được giữ cập nhật, nó phải được xóa hoặc đánh dấu rõ ràng là có thể đã cũ kèm cảnh báo.

---

### 3.4 Self-documenting code does not replace structured documentation / Code tự giải thích không thay thế được tài liệu có cấu trúc

#### EN
Clean naming and clear structure reduce the need for inline comments, but they do not eliminate the need for:

- docstrings that describe contracts (parameters, returns, exceptions)
- README files that explain how to set up and use the project
- ADRs that explain why the architecture is the way it is

#### VI
Tên gọi sạch và cấu trúc rõ ràng giảm nhu cầu comment nội tuyến, nhưng không loại bỏ nhu cầu có:

- docstring mô tả contract (tham số, giá trị trả về, exception)
- file README giải thích cách cài đặt và sử dụng dự án
- ADR giải thích vì sao kiến trúc lại như vậy

---

## 4. Docstring conventions / Quy ước docstring

### 4.1 Choose one docstring style and enforce it project-wide / Chọn một kiểu docstring và áp dụng nhất quán toàn dự án

#### EN
The project must use exactly one docstring format.

Recommended:
- **Google style** — preferred for new projects due to readability and tooling support

Accepted:
- **NumPy style** — acceptable if the team has an existing convention from scientific or data-heavy projects

Forbidden:
- mixing docstring styles within the same project

#### VI
Dự án phải dùng chính xác một format docstring.

Khuyến nghị:
- **Google style** — ưu tiên cho dự án mới vì dễ đọc và được tool hỗ trợ tốt

Chấp nhận:
- **NumPy style** — chấp nhận nếu team đã có convention sẵn từ dự án khoa học hoặc data

Bị cấm:
- trộn kiểu docstring trong cùng một dự án

#### Google style example / Ví dụ Google style

```python
def calculate_churn_probability(
    customer_features: pd.DataFrame,
    model: ChurnModel,
    threshold: float = 0.5,
) -> pd.Series:
    """Calculate churn probability for each customer.

    Applies the trained model to customer features and returns
    a probability score per customer. Customers with probability
    above the threshold are flagged as likely to churn.

    Args:
        customer_features: DataFrame with one row per customer.
            Must contain all features the model was trained on.
        model: A trained ChurnModel instance.
        threshold: Probability cutoff for churn classification.
            Defaults to 0.5.

    Returns:
        Series of float probabilities, indexed by customer_id.

    Raises:
        ValueError: If customer_features is missing required columns.
        ModelNotTrainedError: If model.predict() is called before training.

    Example:
        >>> probs = calculate_churn_probability(features_df, trained_model)
        >>> high_risk = probs[probs > 0.8]
    """
```

---

### 4.2 When is a docstring mandatory? / Khi nào docstring là bắt buộc?

#### EN
Docstrings are mandatory for:

- every public function (no leading underscore)
- every public class
- every public method
- every module (`__init__.py` or top-level module file)

Docstrings are recommended but not mandatory for:

- private functions (`_prefix`) with complex logic
- private methods that implement non-obvious behavior

Docstrings may be omitted for:

- trivial dunder methods whose behavior is standard (`__repr__`, `__str__`, `__eq__`)
- single-line property getters whose name already communicates the intent
- test functions (test function names must be self-descriptive per `07-Testing`)

#### VI
Docstring bắt buộc cho:

- mọi public function (không có dấu gạch dưới đầu)
- mọi public class
- mọi public method
- mọi module (`__init__.py` hoặc file module cấp cao nhất)

Docstring được khuyến nghị nhưng không bắt buộc cho:

- private function (`_prefix`) có logic phức tạp
- private method triển khai hành vi không hiển nhiên

Docstring có thể bỏ qua cho:

- dunder method đơn giản có hành vi chuẩn (`__repr__`, `__str__`, `__eq__`)
- property getter một dòng mà tên đã truyền tải đủ ý đồ
- test function (tên test function phải tự mô tả theo `07-Testing`)

---

### 4.3 Docstring content rules / Quy tắc nội dung docstring

#### EN
A complete docstring must contain:

1. **Summary line** — one line, imperative mood, no period at end for single-line docstrings
   - Use: `Calculate total revenue for the period`
   - Avoid: `This function calculates the total revenue for the period.`

2. **Extended description** (when needed) — separated from summary by a blank line, explains context, constraints, or non-obvious behavior

3. **Args / Parameters** — one entry per parameter, including type and description

4. **Returns** — return type and description of the returned value

5. **Raises** — each exception type that may be raised, with the condition that triggers it

6. **Example** (recommended for complex functions) — a short usage example

#### VI
Một docstring đầy đủ phải chứa:

1. **Dòng tóm tắt** — một dòng, dạng mệnh lệnh, không chấm cuối cho docstring một dòng
   - Dùng: `Calculate total revenue for the period`
   - Tránh: `This function calculates the total revenue for the period.`

2. **Mô tả mở rộng** (khi cần) — cách dòng tóm tắt bằng một dòng trống, giải thích ngữ cảnh, ràng buộc, hoặc hành vi không hiển nhiên

3. **Args / Parameters** — mỗi tham số một entry, bao gồm type và mô tả

4. **Returns** — return type và mô tả giá trị trả về

5. **Raises** — mỗi loại exception có thể bị raise, kèm điều kiện kích hoạt

6. **Example** (khuyến nghị cho hàm phức tạp) — ví dụ sử dụng ngắn

---

### 4.4 Class docstrings / Docstring cho class

#### EN
A class docstring must include:

- a summary of the class's purpose and responsibility
- a description of constructor parameters (in the class docstring or `__init__` docstring, not both)
- important attributes that are part of the public interface

```python
class ChurnModel:
    """Binary classifier for predicting customer churn.

    Wraps a scikit-learn pipeline with preprocessing and prediction.
    The model must be trained before calling predict() or evaluate().

    Args:
        config: Model configuration containing hyperparameters.
        random_state: Seed for reproducibility across all random operations.

    Attributes:
        is_trained: Whether the model has been fitted on training data.
        feature_names: List of feature names expected during prediction.
    """
```

#### VI
Docstring cho class phải bao gồm:

- tóm tắt mục đích và trách nhiệm của class
- mô tả tham số constructor (trong docstring class hoặc `__init__`, không trùng cả hai)
- các attribute quan trọng thuộc interface công khai

---

### 4.5 Module docstrings / Docstring cho module

#### EN
Every module must have a module-level docstring at the top of the file (after any `from __future__` imports) that describes:

- the module's purpose
- what it contains (key classes, functions, or constants)
- where it fits in the project structure

```python
"""Feature engineering functions for customer behavior signals.

This module provides transformation functions that operate on customer
transaction DataFrames and produce derived features for the churn model.
All functions follow the stateless transformer pattern defined in
13-Data-ML-Conventions §6.4.

Functions:
    calculate_transaction_frequency: Compute transactions per time window.
    calculate_recency_score: Days since last transaction, normalized.
    flag_dormant_customer: Boolean flag for inactive customers.
"""
```

#### VI
Mọi module phải có docstring ở cấp module, nằm ở đầu file (sau các `from __future__` import nếu có), mô tả:

- mục đích của module
- chứa gì (class, function, hoặc constant chính)
- vị trí trong cấu trúc dự án

---

### 4.6 Docstring anti-patterns / Mẫu xấu cần tránh với docstring

#### EN
Avoid:

- docstrings that repeat the function name: `"""Calculate the total."""` for `calculate_total()` adds no value
- docstrings that describe HOW instead of WHAT: `"""Loops through rows and sums values"""` should be `"""Calculate the total across all rows"""`
- docstrings that reference parameters that no longer exist
- empty or placeholder docstrings: `"""TODO: add docs"""` or `"""..."""`
- docstrings longer than the function body for trivial functions

#### VI
Tránh:

- docstring lặp lại tên hàm: `"""Calculate the total."""` cho `calculate_total()` không thêm giá trị
- docstring mô tả CÁCH LÀM thay vì LÀM GÌ: `"""Loops through rows and sums values"""` nên là `"""Calculate the total across all rows"""`
- docstring tham chiếu tham số không còn tồn tại
- docstring rỗng hoặc placeholder: `"""TODO: add docs"""` hoặc `"""..."""`
- docstring dài hơn thân hàm cho các hàm đơn giản

---

## 5. Type hints conventions / Quy ước type hints

### 5.1 Type hints are mandatory for all public functions / Type hint bắt buộc cho mọi public function

#### EN
All public functions must have type annotations for every parameter and for the return value.
This rule extends the ML-specific requirement in `13-Data-ML-Conventions` §13.1 to all project code.

#### VI
Mọi public function phải có type annotation cho mỗi tham số và cho giá trị trả về.
Quy tắc này mở rộng yêu cầu đặc thù ML trong `13-Data-ML-Conventions` §13.1 ra toàn bộ code dự án.

---

### 5.2 Prefer specific types over generic / Ưu tiên kiểu cụ thể hơn kiểu chung

#### EN
Use the most specific type that accurately describes the data:

- `list[str]` not `list`
- `dict[str, int]` not `dict`
- `tuple[str, int, float]` not `tuple`
- `str | None` (Python 3.10+) or `Optional[str]` not bare `str` when None is possible
- `pd.DataFrame` not `Any` for data functions
- `np.ndarray` not `Any` for array operations

Avoid `Any` unless the function genuinely operates on arbitrary types.

#### VI
Dùng kiểu cụ thể nhất có thể mô tả chính xác dữ liệu:

- `list[str]` không phải `list`
- `dict[str, int]` không phải `dict`
- `tuple[str, int, float]` không phải `tuple`
- `str | None` (Python 3.10+) hoặc `Optional[str]` không phải `str` trần khi None có thể xảy ra
- `pd.DataFrame` không phải `Any` cho hàm xử lý data
- `np.ndarray` không phải `Any` cho phép toán trên array

Tránh `Any` trừ khi hàm thực sự hoạt động trên kiểu tùy ý.

---

### 5.3 Complex types should use TypeAlias / Kiểu phức tạp nên dùng TypeAlias

#### EN
When a type annotation becomes long or is reused across multiple functions, define a TypeAlias.

```python
from typing import TypeAlias

MetricsDict: TypeAlias = dict[str, float]
FeatureMatrix: TypeAlias = pd.DataFrame
PredictionArray: TypeAlias = np.ndarray

def evaluate_model(y_true: np.ndarray, y_pred: np.ndarray) -> MetricsDict:
    ...
```

#### VI
Khi type annotation trở nên dài hoặc được tái sử dụng ở nhiều function, hãy định nghĩa TypeAlias.

---

### 5.4 Return type is always required for public functions / Kiểu trả về luôn bắt buộc cho public function

#### EN
Every public function must declare its return type, including functions that return `None`.

```python
# Correct
def save_model(model: ChurnModel, path: Path) -> None:
    ...

# Incorrect — missing return type
def save_model(model: ChurnModel, path: Path):
    ...
```

#### VI
Mọi public function phải khai báo kiểu trả về, kể cả function trả về `None`.

---

### 5.5 Enforcement tools / Công cụ kiểm tra

#### EN
Use a static type checker to enforce type correctness:

- `mypy` — recommended, use strict mode (`--strict`) for new projects
- `pyright` — acceptable alternative, especially in VS Code environments

Configure the chosen tool in `pyproject.toml` or a dedicated config file and include it in the CI pipeline.

#### VI
Dùng static type checker để kiểm tra tính đúng của type:

- `mypy` — khuyến nghị, dùng strict mode (`--strict`) cho dự án mới
- `pyright` — alternative chấp nhận được, đặc biệt trong môi trường VS Code

Cấu hình tool đã chọn trong `pyproject.toml` hoặc file config riêng và đưa vào CI pipeline.

---

## 6. Inline comment conventions / Quy ước comment nội tuyến

### 6.1 Comment WHY, not WHAT / Comment LÝ DO, không phải ĐIỀU GÌ

#### EN
Inline comments must explain non-obvious intent, business context, or constraints.
They must not restate what the code already says.

Preferred:
```python
# Use 90-day window because churn analysis showed this is the
# optimal lookback period for this customer segment.
lookback_days = 90
```

Avoid:
```python
# Set lookback days to 90
lookback_days = 90
```

#### VI
Comment nội tuyến phải giải thích ý đồ không hiển nhiên, ngữ cảnh nghiệp vụ, hoặc ràng buộc.
Chúng không được lặp lại điều code đã nói.

---

### 6.2 Avoid commented-out code / Tránh code bị comment bỏ

#### EN
Do not leave commented-out code in the codebase.
Use version control to preserve history.

If code must be temporarily disabled for debugging, it must be removed before merge.
A reviewer must not approve a PR that contains commented-out code without explicit justification.

#### VI
Không để code bị comment bỏ trong codebase.
Dùng version control để lưu giữ lịch sử.

Nếu code phải tạm thời bị vô hiệu hóa cho debugging, nó phải được xóa trước khi merge.
Reviewer không được approve PR có chứa code bị comment bỏ mà không có giải thích rõ ràng.

---

### 6.3 TODO format must be consistent / Format TODO phải nhất quán

#### EN
TODO markers must follow this format:

```python
# TODO(author_initials): Brief description — TICKET-123 or target date
# TODO(tn): Add retry logic for transient API failures — CHURN-456
# TODO(tn): Remove this fallback after v2 migration — 2026-Q2
```

A TODO must:
- identify the responsible person or team
- describe the action needed clearly
- include a ticket reference or target date when possible

A TODO must not be a hidden blocker. If the TODO describes work that must be completed before the change is safe, it is not a TODO — it is incomplete work.

#### VI
Marker TODO phải theo format sau:

```python
# TODO(initials_tác_giả): Mô tả ngắn — TICKET-123 hoặc thời hạn
```

TODO phải:
- xác định người hoặc team chịu trách nhiệm
- mô tả hành động cần làm rõ ràng
- bao gồm tham chiếu ticket hoặc thời hạn khi có thể

TODO không được là blocker ẩn. Nếu TODO mô tả công việc phải hoàn thành trước khi thay đổi an toàn, nó không phải TODO — nó là công việc chưa xong.

---

### 6.4 FIXME and HACK markers / Marker FIXME và HACK

#### EN
Use `FIXME` to mark known defects or fragile code that needs repair:

```python
# FIXME(tn): This calculation overflows for accounts older than 20 years
```

Use `HACK` to mark intentional shortcuts that work but violate design principles:

```python
# HACK(tn): Hardcoded timeout because the config system doesn't support
# per-endpoint values yet — see CHURN-789
```

Both markers must follow the same format rules as TODO (author, description, ticket).

#### VI
Dùng `FIXME` để đánh dấu lỗi đã biết hoặc code mong manh cần sửa.

Dùng `HACK` để đánh dấu shortcut có chủ đích hoạt động được nhưng vi phạm nguyên tắc thiết kế.

Cả hai marker phải theo cùng quy tắc format như TODO (tác giả, mô tả, ticket).

---

### 6.5 Comment anti-patterns / Mẫu xấu cần tránh với comment

#### EN
Avoid:

- noise comments: `x = x + 1  # increment x by one`
- journal comments: `# 2025-03-01: Changed threshold to 0.5` — use version control instead
- closing brace comments: `}  # end of if block` — if the block is long enough to need this, refactor
- commented-out code left in the codebase
- comments that apologize: `# Sorry, this is ugly but it works`

#### VI
Tránh:

- comment nhiễu: `x = x + 1  # tăng x lên 1`
- comment nhật ký: `# 2025-03-01: Đổi threshold thành 0.5` — dùng version control thay thế
- comment đóng ngoặc: `}  # end of if block` — nếu block đủ dài để cần comment này, hãy refactor
- code bị comment bỏ còn lại trong codebase
- comment xin lỗi: `# Sorry, this is ugly but it works`

---

## 7. README conventions / Quy ước README

### 7.1 Every project must have a root README.md / Mọi dự án phải có README.md ở root

#### EN
The root `README.md` is the entry point for any developer or agent encountering the project for the first time.
It must exist and be up to date.

#### VI
File `README.md` ở root là điểm vào cho bất kỳ developer hoặc agent nào tiếp xúc với dự án lần đầu.
Nó phải tồn tại và được cập nhật.

---

### 7.2 README must contain at minimum / README phải chứa tối thiểu

#### EN
A root README must include:

1. **Project name and short description** — one or two sentences explaining what the project does
2. **Prerequisites** — Python version, system dependencies, required tools
3. **Quick start / Setup** — step-by-step instructions to get a working development environment
4. **How to run** — commands for development, testing, and production modes
5. **Project structure overview** — a brief directory tree or description of major components
6. **Link to detailed documentation** — if more documentation exists in `docs/`

Optional but recommended:
- contributing guidelines
- license
- contact or ownership information

#### VI
README ở root phải bao gồm:

1. **Tên dự án và mô tả ngắn** — một hoặc hai câu giải thích dự án làm gì
2. **Điều kiện tiên quyết** — Python version, system dependency, tool cần thiết
3. **Khởi đầu nhanh / Setup** — hướng dẫn từng bước để có môi trường phát triển hoạt động
4. **Cách chạy** — lệnh cho development, testing, và production mode
5. **Tổng quan cấu trúc dự án** — cây thư mục ngắn hoặc mô tả các component chính
6. **Link tới tài liệu chi tiết** — nếu có tài liệu thêm trong `docs/`

Tùy chọn nhưng khuyến nghị:
- hướng dẫn đóng góp
- giấy phép
- thông tin liên hệ hoặc ownership

---

### 7.3 Sub-module README / README cho sub-module

#### EN
A README inside a sub-directory or package is recommended when:

- the module is a shared library used by multiple parts of the system
- the module has its own setup, configuration, or usage pattern that differs from the project root
- a new developer would need context specific to that module to work effectively

A sub-module README should be short and focused. It must not duplicate the root README.

#### VI
README bên trong sub-directory hoặc package được khuyến nghị khi:

- module là shared library được dùng bởi nhiều phần của hệ thống
- module có setup, cấu hình, hoặc cách sử dụng riêng khác với root dự án
- developer mới cần ngữ cảnh đặc thù cho module đó để làm việc hiệu quả

README cho sub-module nên ngắn gọn và tập trung. Nó không được lặp lại nội dung README root.

---

## 8. CHANGELOG conventions / Quy ước CHANGELOG

### 8.1 CHANGELOG.md must exist for versioned projects / CHANGELOG.md phải tồn tại cho dự án có version

#### EN
Every project that uses versioned releases must maintain a `CHANGELOG.md` file at the project root.

#### VI
Mọi dự án sử dụng versioned release phải duy trì file `CHANGELOG.md` ở root dự án.

---

### 8.2 Follow Keep a Changelog format / Tuân theo format Keep a Changelog

#### EN
Use the [Keep a Changelog](https://keepachangelog.com/) format with the following categories:

- **Added** — new features or capabilities
- **Changed** — changes to existing functionality
- **Deprecated** — features that will be removed in a future version
- **Removed** — features that have been removed
- **Fixed** — bug fixes
- **Security** — vulnerability fixes or security improvements

Each entry should be a human-readable description, not a raw commit message.

```markdown
## [1.2.0] - 2026-03-18

### Added
- Churn prediction endpoint with batch scoring support (#PR-123)

### Changed
- Updated feature engineering to use 90-day lookback window (#PR-119)

### Fixed
- Fixed null handling in transaction frequency calculation (#PR-121)
```

#### VI
Dùng format [Keep a Changelog](https://keepachangelog.com/) với các danh mục sau:

- **Added** — tính năng hoặc khả năng mới
- **Changed** — thay đổi chức năng hiện có
- **Deprecated** — tính năng sẽ bị loại bỏ ở phiên bản tương lai
- **Removed** — tính năng đã bị loại bỏ
- **Fixed** — sửa lỗi
- **Security** — sửa lỗ hổng hoặc cải thiện bảo mật

Mỗi entry nên là mô tả dễ đọc cho con người, không phải raw commit message.

---

### 8.3 Link entries to PRs or commits when possible / Liên kết entry về PR hoặc commit khi có thể

#### EN
Each changelog entry should reference the pull request or commit that introduced the change.
This enables traceability as defined in `09-Git-PR-Release` §3.1.

#### VI
Mỗi changelog entry nên tham chiếu pull request hoặc commit đã đưa vào thay đổi.
Điều này đảm bảo khả năng truy vết theo `09-Git-PR-Release` §3.1.

---

## 9. Architecture Decision Records (ADR) / Ghi nhận quyết định kiến trúc

### 9.1 When to create an ADR / Khi nào tạo ADR

#### EN
Create an ADR when the team makes a decision that:

- affects the project's architecture or technology stack
- involves a significant trade-off between competing approaches
- will be difficult or expensive to reverse later
- would confuse a future developer who asks "why is it done this way?"

Examples:
- choosing a database technology
- selecting an ML framework
- deciding the pipeline orchestration approach
- choosing between monolith and microservice for a component

#### VI
Tạo ADR khi team đưa ra quyết định mà:

- ảnh hưởng tới kiến trúc hoặc technology stack của dự án
- liên quan tới trade-off đáng kể giữa các cách tiếp cận cạnh tranh
- sẽ khó hoặc tốn kém để đảo ngược về sau
- sẽ gây khó hiểu cho developer tương lai khi hỏi "tại sao lại làm kiểu này?"

---

### 9.2 ADR content / Nội dung ADR

#### EN
Each ADR must contain:

1. **Title** — a short, descriptive name for the decision
2. **Status** — one of: `Proposed`, `Accepted`, `Deprecated`, `Superseded by ADR-XXX`
3. **Date** — when the decision was made
4. **Context** — what is the problem or situation that requires a decision?
5. **Decision** — what was decided?
6. **Consequences** — what are the positive and negative results of this decision?

```markdown
# ADR-003: Use XGBoost as primary model framework

## Status
Accepted

## Date
2026-03-15

## Context
The churn prediction system needs a model framework that supports
structured/tabular data, provides feature importance, and integrates
well with scikit-learn pipelines.

## Decision
Use XGBoost as the primary model framework for all tabular classification tasks.

## Consequences
- Positive: strong performance on tabular data, built-in feature importance
- Positive: scikit-learn compatible API, works with existing pipeline
- Negative: requires careful hyperparameter tuning
- Negative: does not support unstructured data natively
```

#### VI
Mỗi ADR phải chứa:

1. **Title** — tên ngắn, mô tả cho quyết định
2. **Status** — một trong: `Proposed`, `Accepted`, `Deprecated`, `Superseded by ADR-XXX`
3. **Date** — ngày quyết định được đưa ra
4. **Context** — vấn đề hoặc tình huống đòi hỏi quyết định là gì?
5. **Decision** — quyết định là gì?
6. **Consequences** — kết quả tích cực và tiêu cực của quyết định này là gì?

---

### 9.3 ADR location and naming / Vị trí và đặt tên ADR

#### EN
ADRs must be stored in `docs/adr/` or `docs/decisions/`.
Each ADR file should be named with a sequential number and a short slug:

- `001-use-xgboost-for-tabular-models.md`
- `002-choose-postgres-over-mysql.md`
- `003-adopt-github-actions-for-ci.md`

ADRs must not be deleted when superseded. Instead, update the status to `Superseded by ADR-XXX`.

#### VI
ADR phải được lưu trong `docs/adr/` hoặc `docs/decisions/`.
Mỗi file ADR nên được đặt tên với số thứ tự và slug ngắn:

- `001-use-xgboost-for-tabular-models.md`
- `002-choose-postgres-over-mysql.md`
- `003-adopt-github-actions-for-ci.md`

ADR không được xóa khi bị thay thế. Thay vào đó, cập nhật status thành `Superseded by ADR-XXX`.

---

## 10. Agent and automation rules / Quy ước cho agent và tự động hóa

### 10.1 Agent-generated code must include docstrings / Code do agent sinh ra phải có docstring

#### EN
When a coding agent generates a new function, class, or module, it must include a docstring that follows the conventions in this document.
The docstring must not be a placeholder or a repetition of the function name.

#### VI
Khi coding agent sinh ra function, class, hoặc module mới, nó phải bao gồm docstring tuân theo quy ước trong tài liệu này.
Docstring không được là placeholder hoặc lặp lại tên function.

---

### 10.2 Agent must update documentation when changing behavior / Agent phải cập nhật tài liệu khi thay đổi hành vi

#### EN
When an agent modifies a function's parameters, return value, exceptions, or a module's responsibilities, it must update the corresponding docstring and any affected README or documentation.

#### VI
Khi agent thay đổi tham số, giá trị trả về, exception, hoặc trách nhiệm của function hay module, nó phải cập nhật docstring tương ứng và mọi README hoặc tài liệu bị ảnh hưởng.

---

### 10.3 Agent must not generate placeholder documentation / Agent không được sinh tài liệu placeholder

#### EN
Forbidden patterns in agent-generated documentation:

- `"""TODO: add docs"""`
- `"""..."""`
- `"""Docstring for function_name."""`
- `# TODO: document this`

If the agent cannot produce meaningful documentation, it must state explicitly that the documentation is incomplete and explain what is missing.

#### VI
Các mẫu bị cấm trong tài liệu do agent sinh ra:

- `"""TODO: add docs"""`
- `"""..."""`
- `"""Docstring for function_name."""`
- `# TODO: document this`

Nếu agent không thể tạo tài liệu có ý nghĩa, nó phải nêu rõ rằng tài liệu chưa đầy đủ và giải thích thiếu gì.

---

## 11. Anti-patterns / Mẫu xấu cần tránh

### EN
Avoid:

- functions without docstrings that have non-obvious behavior
- docstrings that repeat the function name without adding information
- docstrings that describe the implementation instead of the contract
- mixing multiple docstring styles in the same project
- type annotations that use `Any` when a specific type is known
- missing return type on public functions
- commented-out code committed to the repository
- TODOs without an owner or action
- README files that are out of date with the current setup process
- changelog entries that are just copy-pasted commit messages
- placeholder documentation that pretends to be real documentation

### VI
Tránh:

- function không có docstring mà có hành vi không hiển nhiên
- docstring lặp lại tên function mà không thêm thông tin
- docstring mô tả implementation thay vì contract
- trộn nhiều kiểu docstring trong cùng một dự án
- type annotation dùng `Any` khi đã biết kiểu cụ thể
- thiếu return type trên public function
- code bị comment bỏ được commit vào repository
- TODO không có người chịu trách nhiệm hoặc hành động
- file README lỗi thời so với quy trình setup hiện tại
- changelog entry chỉ là copy-paste commit message
- tài liệu placeholder giả vờ là tài liệu thật

---

## 12. Review checklist / Checklist review

### EN
When reviewing documentation quality, check:

- Does every public function, class, and module have a docstring?
- Do docstrings follow the chosen project style (Google or NumPy)?
- Do docstrings describe the contract (Args, Returns, Raises), not just the implementation?
- Are type hints present and specific for all public functions?
- Are inline comments explaining WHY, not WHAT?
- Is there any commented-out code that should be removed?
- Are TODO/FIXME markers properly formatted with owner and reference?
- Is the README accurate and sufficient for a new developer to get started?
- Is the CHANGELOG up to date with the latest release?
- Are architectural decisions recorded in ADRs where relevant?
- Has agent-generated documentation been reviewed for accuracy and completeness?

### VI
Khi review chất lượng tài liệu, cần kiểm tra:

- Mọi public function, class, và module đã có docstring chưa?
- Docstring có tuân theo style đã chọn cho dự án (Google hoặc NumPy) không?
- Docstring có mô tả contract (Args, Returns, Raises) không, hay chỉ mô tả implementation?
- Type hint có đầy đủ và cụ thể cho mọi public function không?
- Comment nội tuyến có giải thích LÝ DO thay vì ĐIỀU GÌ không?
- Có code bị comment bỏ nào cần xóa không?
- Marker TODO/FIXME có đúng format với tác giả và tham chiếu không?
- README có chính xác và đủ để developer mới bắt đầu được không?
- CHANGELOG có được cập nhật theo release mới nhất không?
- Các quyết định kiến trúc có được ghi nhận trong ADR khi phù hợp không?
- Tài liệu do agent sinh ra đã được review về tính chính xác và đầy đủ chưa?

---

## 13. Definition of done / Điều kiện hoàn thành

### EN
Documentation is considered convention-compliant only if:

- every public function, class, and module has a docstring in the project's chosen style
- docstrings describe the contract: parameters, return values, and exceptions
- type hints are present and specific for all public function signatures
- inline comments explain intent and context, not code mechanics
- no commented-out code remains in the codebase
- TODO, FIXME, and HACK markers follow the standard format with owner and reference
- the root README is accurate, complete, and sufficient for project onboarding
- the CHANGELOG reflects all versioned releases in Keep a Changelog format
- architectural decisions are documented in ADRs when they meet the threshold
- agent-generated documentation meets the same quality standards as human-written documentation
- the change satisfies the definition of done in `11-Definition_of_done`

### VI
Tài liệu chỉ được coi là tuân thủ convention khi:

- mọi public function, class, và module có docstring theo style đã chọn cho dự án
- docstring mô tả contract: tham số, giá trị trả về, và exception
- type hint đầy đủ và cụ thể cho mọi public function signature
- comment nội tuyến giải thích ý đồ và ngữ cảnh, không phải cơ chế code
- không còn code bị comment bỏ trong codebase
- marker TODO, FIXME, và HACK tuân theo format chuẩn với tác giả và tham chiếu
- README ở root chính xác, đầy đủ, và đủ để onboard dự án
- CHANGELOG phản ánh mọi versioned release theo format Keep a Changelog
- các quyết định kiến trúc được tài liệu hóa trong ADR khi đạt ngưỡng
- tài liệu do agent sinh ra đạt cùng tiêu chuẩn chất lượng như tài liệu do con người viết
- thay đổi thỏa mãn definition of done trong `11-Definition_of_done`
