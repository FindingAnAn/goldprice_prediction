# 17-Feature-Flags-Convention / Quy ước Feature Flags và Progressive Delivery

## 1. Purpose / Mục đích

### EN
This document defines the conventions for using Feature Flags (Toggles) to decouple deployment from release, enable safer progressive delivery, and manage technical debt associated with temporary flags.

### VI
Tài liệu này định nghĩa các quy ước sử dụng Feature Flags (Toggles) để tách biệt việc deploy khỏi việc release, cho phép phát hành lũy tiến an toàn hơn, và quản lý nợ kỹ thuật liên quan đến các flag tạm thời.

---

## 2. Scope / Phạm vi

### EN
This document applies to:
- release flags (short-lived)
- operational flags (medium-lived)
- experimental/A-B testing flags (medium-lived)
- permission/entitlement flags (long-lived)
- flag cleanup process

### VI
Tài liệu này áp dụng cho:
- cờ phát hành (release flags - vòng đời ngắn)
- cờ vận hành (operational flags - vòng đời trung bình)
- cờ thử nghiệm/A-B test (experimental flags - vòng đời trung bình)
- cờ phân quyền (permission flags - vòng đời dài)
- quy trình dọn dẹp cờ

---

## 3. Flag categories and lifecycles / Phân loại và vòng đời cờ

### 3.1 Release Flags (Short-lived) / Cờ phát hành

**EN**  
Used to hide incomplete or risky features from users. Decouples deployment from release.  
- **Scope**: Internal or specific test groups  
- **Lifecycle**: Days to Weeks. Must be removed once the feature is 100% rolled out.  

**VI**  
Dùng để giấu tính năng chưa hoàn thiện hoặc rủi ro khỏi người dùng. Phân tách deploy và release.  
- **Phạm vi**: Nội bộ hoặc nhóm test cụ thể  
- **Vòng đời**: Vài ngày đến vài tuần. Phải gỡ bỏ khi tính năng đã rollout 100%.

### 3.2 Operational Flags (Medium to Long-lived) / Cờ vận hành

**EN**  
Used to control system behavior under load, such as disabling a non-critical heavy feature (Load Shedding) or switching to a degraded mode.  
- **Scope**: Global or Datacenter level  
- **Lifecycle**: Months to Years. Explicitly documented in runbooks.  

**VI**  
Dùng để kiểm soát hành vi hệ thống lúc tải cao, ví dụ: tắt tính năng nặng không thiết yếu (Load Shedding) hoặc chuyển mode suy giảm (degraded mode).  
- **Phạm vi**: Toàn cục hoặc cấp Datacenter  
- **Vòng đời**: Vài tháng đến vài năm. Phải được ghi chép rõ trong runbook.

### 3.3 Experiment / A-B Test Flags (Medium-lived) / Cờ thử nghiệm

**EN**  
Used to test different variations of a feature to measure business impact (e.g., Conversion Rate).  
- **Scope**: Percentage of users (cohorts)  
- **Lifecycle**: Weeks to Months. Must be removed when the experiment concludes.  

**VI**  
Dùng để test các biến thể của một tính năng nhằm đo lường tác động kinh doanh (ví dụ Tỷ lệ chuyển đổi).  
- **Phạm vi**: Phần trăm người dùng (cohorts)  
- **Vòng đời**: Vài tuần đến vài tháng. Phải gỡ bỏ khi thử nghiệm kết thúc.

### 3.4 Permission / Entitlement Flags (Long-lived) / Cờ phân quyền

**EN**  
Used to grant premium features to specific users or tenants.  
- **Scope**: Specific Users, Tenants, or Subscription tiers  
- **Lifecycle**: Permanent  

**VI**  
Dùng để cấp quyền dùng tính năng cao cấp cho user hoặc tenant cụ thể.  
- **Phạm vi**: User cụ thể, Tenant, hoặc cấp Subscription  
- **Vòng đời**: Vĩnh viễn

---

## 4. Feature Flag implementation rules / Quy tắc implement Feature Flag

### 4.1 Do not implement custom flag routing / Không tự viết logic định tuyến cờ

**EN**  
🔴 **MUST**: Use an established Feature Flag service or library (e.g., LaunchDarkly, Unleash, internal config service). Do not implement custom `if user_id % 2 == 0` logic in application code.

**VI**  
🔴 **MUST**: Dùng service hoặc thư viện Feature Flag chuyên dụng (ví dụ: LaunchDarkly, Unleash, config service nội bộ). Không tự viết logic `if user_id % 2 == 0` trong application code.

### 4.2 Flags must have default fallback values / Cờ phải có giá trị mặc định dự phòng

**EN**  
🔴 **MUST**: Always provide a safe fallback value in code in case the Feature Flag service is unreachable. The fallback must default to the *existing/old* behavior (safe side).

**VI**  
🔴 **MUST**: Luôn cung cấp giá trị mặc định an toàn trong code đề phòng Feature Flag service không gọi được. Giá trị mặc định phải là hành vi *hiện tại/cũ* (hướng an toàn).

**Example / Ví dụ:**
```python
# Preferred: safe fallback
use_new_payment = feature_flags.get("enable_new_payment_gateway", default=False)
if use_new_payment:
    return new_gateway.charge(...)
return old_gateway.charge(...)
```

### 4.3 Keep flag hooks at the edge / Đặt hook cờ ở vòng ngoài

**EN**  
🟡 **SHOULD**: Evaluate feature flags at the application boundary (Controller, API Route, or Application Service) and pass the basic data (boolean, config) down to the Domain layer.  
Do NOT inject the Feature Flag SDK deep into Domain models.

**VI**  
🟡 **SHOULD**: Đánh giá feature flag ở biên ứng dụng (Controller, API Route, hoặc Application Service) và truyền dữ liệu cơ bản (boolean, config) xuống tầng Domain.  
KHÔNG tiêm Feature Flag SDK sâu vào Domain model.

---

## 5. Technical debt management (The Cleanup Process) / Quản lý nợ kỹ thuật (Quy trình dọn dẹp)

### 5.1 Cleanup ticket must be created with the flag / Phải tạo ticket dọn dẹp cùng lúc với cờ

**EN**  
🔴 **MUST**: When a short or medium-lived flag (Release, Experiment) is added to the codebase, a corresponding cleanup task (Jira, GitHub specific issue) MUST be created and scheduled.

**VI**  
🔴 **MUST**: Khi một cờ vòng đời ngắn hoặc trung bình (Release, Experiment) được thêm vào source code, một task dọn dẹp tương ứng NGAY LẬP TỨC PHẢI được tạo và lên lịch hạn chót.

### 5.2 Expired flags break the build / Cờ hết hạn gây lỗi build

**EN**  
🟡 **SHOULD**: Use code annotations or static analysis tools (e.g., `eslint-plugin-feature-flags`, custom linters) to mark flags with an expiration date. If the date passes, the CI pipeline should fail, forcing the team to remove the dead code.

**VI**  
🟡 **SHOULD**: Dùng annotation trong code hoặc công cụ phân tích tĩnh (ví dụ `eslint-plugin-feature-flags`, linter tự viết) để đánh dấu ngày hết hạn của cờ. Nếu quá hạn, CI pipeline sẽ báo lỗi đỏ, buộc team phải gỡ bỏ code chết.

---

## 6. Anti-patterns / Mẫu xấu cần tránh

### EN
Avoid:
- flag spaghetti: nesting multiple feature flags within the same block
- failing to provide hard-coded fallback values in case the flag service is unreachable
- evaluating feature flags deep inside the Domain layer instead of the Application/Interface boundaries
- leaving short-lived release flags in the codebase indefinitely without a cleanup plan
- using feature flags as a substitute for proper environment separation (e.g. `is_production` flag)

### VI
Tránh:
- cờ rác (flag spaghetti): lồng ghép nhiều feature flag trong cùng một block code
- bỏ quên cung cấp hard-code giá trị dự phòng trong trường hợp service cờ không khả dụng
- đánh giá kiểm tra cờ ở quá sâu tầng Domain thay vì ở tầng Application/Interface
- để lại các cờ phát hành vòng đời ngắn trong mã nguồn vô thời hạn mà không có kế hoạch dọn dẹp
- dùng feature flags thay cho việc phân tách môi trường (ví dụ: dùng cờ `is_production`)

---

## 7. Review checklist / Checklist review

### EN
When reviewing code with feature flags, check:
- Is the flag lifecycle categorized (release vs operational)?
- Is an established flag service used instead of custom logic?
- Does the flag have a safe default fallback hard-coded?
- Is the flag evaluated at the edge boundaries instead of deep in domain logic?
- Has a cleanup ticket been created for this flag?

### VI
Khi review mã nguồn có chứa feature flag, kiểm tra:
- Vòng đời của cờ đã được phân loại chưa (phát hành hay vận hành)?
- Có sử dụng service cờ chuyên dụng thay vì logic kiểm tra thủ công không?
- Cờ có được hard-code với một giá trị mặc định dự phòng an toàn không?
- Cờ có được đánh giá ở biên thay vì sâu trong logic domain không?
- Task nội bộ dọn dẹp cờ đã được tạo kèm theo chưa?

---

## 8. Agent and automation rules / Quy ước cho agent và tự động hóa

### 8.1 Agent flag management / Agent quản lý cờ

#### EN
- When an agent adds a feature flag, it must always implement a safe default fallback.
- The agent must ask the user which established Feature Flag service or library is being used before generating code. It must not generate custom conditional routing logic.

#### VI
- Khi agent thêm feature flag, nó luôn phải cài đặt một giá trị mặc định dự phòng an toàn.
- Agent phải hỏi người dùng đang sử dụng service/thư viện Feature Flag nào trước khi sinh mã. Tuyệt đối không sinh logic định tuyến điều kiện thủ công.

---

## 9. Definition of done / Điều kiện hoàn thành

### EN
A module uses Feature Flags correctly if:
- flags are categorized by lifecycle (release vs operational)
- a dedicated config/flag service is used instead of custom logic
- safe defaults are hardcoded in the application
- flag evaluations are kept near the edge (controllers/boundaries) rather than deep in domain logic
- cleanup tickets exist for every short-lived flag

### VI
Một module sử dụng Feature Flags đúng nếu:
- cờ được phân loại theo vòng đời (phát hành vs vận hành)
- dùng service quản lý cờ chuyên dụng thay vì logic tự chế
- có hardcode giá trị mặc định an toàn
- việc đánh giá cờ nằm ở tầng biên (controller/boundary) thay vì sâu trong domain logic
- có task dọn dẹp (cleanup ticket) cho mọi cờ vòng đời ngắn
