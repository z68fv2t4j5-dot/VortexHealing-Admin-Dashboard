---
name: VortexHealing project rules
alwaysApply: true
---

Summary of AGENTS.md for small local models. AGENTS.md wins on any conflict.

Stack: React 18 + TypeScript + Vite (frontend/, port 3000, /api proxied to 8000);
FastAPI + SQLAlchemy + SQLite (backend/). React Query v3 + axios with relative
/api URLs. Inline styles, primary #667eea, lucide-react icons. No UI libraries.

Rules:
- Only use endpoints, fields and files that exist. If unsure, say so and ask.
  Never invent an API route or a response shape.
- Copy patterns from the file named in the request (e.g. Tasks.tsx for modals).
- Class eligibility comes only from backend/app/class_rules.py; reminder timing from docs/CLASS_RULES.md.
- Email goes to the APAC Wizards list only; filter by full-word class tags only.
- One change per answer. Output the complete changed file, no tutorial.
- Student data stays local. Never put emails, names or keys in code or logs.
- Don't suggest creating new projects or servers; extend backend/app/api/.
