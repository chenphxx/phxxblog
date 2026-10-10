# Repository Guidelines

## Project Structure & Module Organization

- `backend/app/` — FastAPI service. One capability per module package: `modules/<id>/spec.py` (metadata) plus `router.py` (endpoints), imported by `modules/__init__.py`. Shared code stays outside modules: `core/`, `models/`, `schemas/`, `services/`.
- `frontend/src/` — Vue 3 + TypeScript. `modules/registry.ts` holds module ids, nav entries and routes; pages live in `views/`, shared pieces in `components/`, `stores/`, `api/`.
- `docs/` — Chinese technical docs (`架构与实现.md`, `数据库设计.md`, `接口文档.md`); `backend/scripts/` holds seed, doc and check scripts.
- Adding a capability means a backend module package plus a matching `frontend/src/modules/registry.ts` entry; `check_modules.py` enforces that both id sets agree.

## Build, Test, and Development Commands

- `start.bat` — start backend (`:8000`) and frontend (`:5173`) together.
- `cd backend && .venv/Scripts/python.exe -m app.seed` — initialise roles, admin and default settings.
- `cd backend && .venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000` — API server.
- `cd frontend && npm run dev` / `npm run build` — Vite dev server / type check plus production build.
- `backend/.venv/Scripts/python.exe backend/scripts/verify_all.py` — the full gate (ruff, consistency checks, `vue-tsc`, eslint, prettier, theme/icon/style audits); run it before every commit.
- `cd backend && .venv/Scripts/python.exe scripts/gen_api_doc.py` — regenerate `docs/接口文档.md` after route changes; never hand-edit generated files.

## Coding Style & Naming Conventions

- 4 spaces per indent level; the opening brace or bracket of functions, classes, conditionals and loops goes on its own line.
- Python: `ruff format`, line length 100. Module ids are lowercase (`backtotop`, `sitelinks`); module settings are stored as `module.<id>.<key>`.
- Frontend: Prettier (no semicolons, single quotes, width 120) with Element Plus components.
- Comments, docstrings and docs are Chinese, with Doxygen tags (`@brief`, `@param`, `@return`, `@throws`) on public APIs.

## Testing Guidelines

- No unit-test framework: `scripts/verify_all.py` is the acceptance gate. `check_modules.py` and `check_settings_keys.py` keep registries, defaults and frontend types aligned — extend them when you add a module or setting.
- Startup validates the MySQL schema against the models; model changes need the matching migration SQL.

## Commit & Pull Request Guidelines

- Conventional Commits with a concise Chinese description, one purpose per commit: `fix: 修复模块未启用时的前台报错`.
- Never commit `backend/.env` or other secrets.
- Pull requests state the intent, paste the `verify_all.py` summary, add screenshots for UI changes, and link the issue.

## Security & Configuration Tips

- Configure via `PHXXBLOG_*` environment variables or `backend/.env`; do not weaken the secret-key or trusted-proxy checks.
- Do not change the schema, delete data, or rewrite Git history without explicit confirmation.
