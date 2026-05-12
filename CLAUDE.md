# CLAUDE.md — Agent Configuration for This Project

## Role

You are an expert Python Software Engineer working on this project.

---

## CRITICAL: Convention Reading Protocol

**Before any code task**, you MUST:

1. Read `Coding_conventions/00-Index_and_glossary.md` first.
2. Identify the task type from the user's request.
3. Use **§4** of the index file to determine which convention files are relevant.
4. Load and read only those files (in the specified order) before generating or reviewing any code.

---

## §4 — File Reading Guide by Task Type

Use this table to determine which convention files to load for each task type.

### English

| Task type | Files to read (in order) |
|-----------|--------------------------|
| **Create a new project** | 01 → 03 → 04 → 10 → 02 → 08 → 14 |
| **Write a new feature** | 10 → 03 → 04 → 05 → 07 → 11 |
| **Write/review API** | 12 → 10 → 05 → 06 → 03 → 08 |
| **Write/review ML code** | 13 → 10 → 03 → 07 → 06 → 02 |
| **Write infrastructure** | 14 → 18 → 10 → 08 → 02 → 09 |
| **Write tests** | 07 → 10 → 03 → 13 (if ML) |
| **Create a PR** | 09 → 11 → 15 |
| **Review code** | 10 → 04 → 03 → 11 + domain-specific file |
| **Write documentation** | 15 → 03 |
| **Handle secrets/config** | 08 → 02 → 14 |
| **Design architecture/modules** | 16 → 01 → 05 → 06 → 12 |
| **Implement new feature** | 10 → 03 → 04 → 05 → 07 → 17 (if needed) → 11 |
| **Deploy monitoring stack** | 18 → 14 → 06 → 08 |
| **Deploy Airflow on K8s** | 18 → 14 → 13 → 08 |

### Vietnamese (Tiếng Việt)

| Loại task | File cần đọc (theo thứ tự) |
|-----------|----------------------------|
| **Tạo dự án mới** | 16 → 01 → 03 → 04 → 10 → 02 → 08 → 14 |
| **Viết tính năng mới** | 10 → 03 → 04 → 05 → 07 → 17 (nếu cần flag) → 11 |
| **Viết/review API** | 12 → 10 → 05 → 06 → 03 → 08 |
| **Viết/review ML code** | 13 → 10 → 03 → 07 → 06 → 02 |
| **Viết infrastructure** | 14 → 18 → 10 → 08 → 02 → 09 |
| **Viết test** | 07 → 10 → 03 → 13 (nếu ML) |
| **Tạo PR** | 09 → 11 → 15 |
| **Review code** | 10 → 04 → 03 → 11 + file chuyên biệt |
| **Viết tài liệu** | 15 → 03 |
| **Xử lý secret/config** | 08 → 02 → 14 |
| **Thiết kế kiến trúc/module** | 16 → 01 → 05 → 06 → 12 |
| **Deploy monitoring stack** | 18 → 14 → 06 → 08 |
| **Deploy Airflow trên K8s** | 18 → 14 → 13 → 08 |

---

## Architecture Gate (CRITICAL)

The default architecture for this project is **Tier 1 Monolith**.

Before applying any **Tier 2** architectural patterns — including:
- **Circuit Breaker**
- **Transactional Outbox**
- **Saga Pattern**

You **MUST ask the user** explicitly:

> "This change involves a Tier 2 architectural pattern (e.g., Circuit Breaker / Outbox / Saga). The project default is Tier 1 Monolith. Do you want to apply this pattern? Please confirm before I proceed."

Do not implement Tier 2 patterns without explicit user confirmation.

---

## Review Checklist & Definition of Done

Before submitting any code, you MUST apply:

- The **Review Checklist** from `Coding_conventions/10-Code_design_principles.md`
- The **Definition of Done** from `Coding_conventions/11-Definition_of_done.md`

Every piece of code must satisfy the DoD before it is considered complete. If any DoD item is not met, flag it explicitly to the user.

---

## Project Context

> Fill in these placeholders when starting the project or onboarding a new agent session.

| Field | Value |
|-------|-------|
| **Language** | `<e.g. Python 3.11>` |
| **Architecture** | `<e.g. Monolith / Modular Monolith / Microservices>` |
| **Framework** | `<e.g. FastAPI / Django / Flask>` |
| **Database / ORM** | `<e.g. PostgreSQL + SQLAlchemy / MongoDB + Beanie>` |
