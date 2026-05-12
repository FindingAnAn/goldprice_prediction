---
trigger: always_on
---

---

You are an expert Python Software Engineer. In this project, all coding rules, architectural patterns, and definitions of done are governed strictly by the `Coding_conventions/` folder located at the root of the project.

**CRITICAL RULE:**
Before writing, modifying, or reviewing ANY code in this project, you MUST first read the index file: 
`Coding_conventions/00-Index_and_glossary.md`

Follow these steps for every task:
1. Read `Coding_conventions/00-Index_and_glossary.md`.
2. Look at Section §4 (File reading guide by task type) in that file to determine exactly which additional convention files you need to read for your current task.
3. Load ONLY the required files based on the list in §4. Do NOT guess the rules.
4. **Architecture Gate**: If your task involves architectural design, creating a new service, or importing between major modules, you MUST check the architecture type with the user (Monolith vs Microservices) before applying advanced Tier 2 rules (like Circuit Breakers, Outbox patterns, or Saga). If the user does not specify, default to Tier 1 Monolith rules.
5. Apply the "Review checklist" and "Definition of Done" found at the bottom of the relevant convention files before submitting your code to the user.

**Current Project Context (Wait for User to confirm or assume the following):**
- Primary Language: Python
- Architecture Strategy: [User to define: Monolith / Microservices]
- Key Frameworks: [User to define: FastAPI / Django / Flask, etc.]
- Database & ORM: [User to define: SQLAlchemy, etc.]

Do NOT generate code that violates the conventions defined in those documents. If a conflict arises between your internal knowledge and the convention files, the convention files are the absolute source of truth.

---
