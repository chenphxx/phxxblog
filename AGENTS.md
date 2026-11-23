# Repository Guidelines

## Project Structure & Module Organization

- `backend/app/` contains the FastAPI service; shared code belongs in `core/`, `models/`, `schemas/`, and `services/`
- Backend capabilities use `modules/<id>/spec.py` for metadata and `router.py` for endpoints; matching entries are required in `frontend/src/modules/registry.ts`
- `frontend/src/` contains the Vue 3 and TypeScript client; pages use `views/`, reusable UI uses `components/`, and state uses `stores/`
- `docs/` contains Chinese technical documentation; `backend/scripts/` contains seed, migration, documentation, and consistency checks

## Build, Test, and Development Commands

- `start.bat` runs the backend on `:8000` and frontend on `:5173`
- `cd backend && .venv/Scripts/python.exe -m app.seed` initializes roles, defaults, and the admin account
- `cd backend && .venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000` starts the API
- `cd frontend && npm run dev` starts Vite; `npm run build` type-checks and creates the production build
- `backend/.venv/Scripts/python.exe backend/scripts/verify_all.py` runs the repository acceptance gate
- `cd backend && .venv/Scripts/python.exe scripts/gen_api_doc.py` regenerates `docs/接口文档.md` after route changes

## Coding Style & Naming Conventions

- Use four-space indentation and place opening braces and brackets for multiline blocks on their own line
- Python uses Ruff with a 100-character limit; frontend files use Prettier with 120 characters, single quotes, and no semicolons
- Use lowercase module IDs; settings follow `module.<id>.<key>`; reuse existing Vue and Element Plus patterns
- Comments, docstrings, and technical docs are Chinese; public APIs use Doxygen tags such as `@brief` and `@return`

## Testing Guidelines

- No unit-test framework exists; `verify_all.py` gates imports, consistency, Ruff, `vue-tsc`, themes, icons, Element Plus styles, and ESLint
- Extend `check_modules.py` or `check_settings_keys.py` when module registries or settings change
- Model changes require matching migration SQL; startup validates the schema against the models
- Verify UI changes in a browser; include screenshots in PRs

## Commit & Pull Request Guidelines

- Use Conventional Commits with one purpose per commit: `fix: 修复模块未启用时的前台报错`
- PRs should explain intent, list verification results, link issues, and include screenshots for UI changes
- Never commit `backend/.env`, credentials, or other secrets

## Security & Configuration Tips

- Configure services through `PHXXBLOG_*` variables or `backend/.env`
- Do not weaken secret-key, trusted-proxy, or authentication checks
- Do not change schema, delete data, rewrite Git history, or revert unrelated changes without confirmation

## Agent-Specific Instructions

- Inspect relevant code, configuration, and `docs/` first; use the smallest compatible change
- Preserve user-created worktree changes and avoid unrelated refactoring, dependency changes, or cleanup
