# VulminatorsHackathon
Vulnerability destroyers

## Overview
This repo hosts the Vulminators hackathon MVP: paste a GitHub repo URL, let our FastAPI backend clone + scan it, generate AI summaries, and (soon) open a pull request with the findings/refactors.

Detailed architecture & milestone plan lives in `docs/architecture.md`.

## Backend (FastAPI + scanners)
```
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
- Install Semgrep CLI (needed for scans): `pip install semgrep` or `brew install semgrep`.
- Ensure Node.js/npm are available for dependency audits (`npm --version`).
- Drop secrets (e.g., `OPENAI_API_KEY`, `VULMINATOR_GITHUB_TOKEN`) into a root-level `.env`; the backend auto-loads it.

Example `.env`:
```
OPENAI_API_KEY=sk-...
VULMINATOR_GITHUB_TOKEN=ghp_...
```

Endpoints (initial scaffold):
- `GET /health` – service status + workspace path.
- `POST /analyze` – accepts `{ repo_url, github_token, preset }`, returns `run_id`.
- `GET /runs/{run_id}` – fetches job status, findings, PR link.

Scanners wired today:
- Semgrep rulesets (`fast/balanced/exhaustive`) for source-level findings.
- `npm audit --package-lock-only` to surface dependency CVEs from any `package-lock.json`.
- With `VULMINATOR_GITHUB_TOKEN` (or a token in the request body), each run drops `reports/VulminatorReport.md`, pushes it to a fork branch (`vulminator/<timestamp>`), and opens a PR automatically.

## Frontend (Vite + React)
```
cd frontend
npm install
npm run dev
```
- By default, the UI proxies to `http://localhost:8000`. Override by setting `VITE_BACKEND_URL`.
- Form defaults to scanning `https://github.com/IbrahimKhanGH/finalDemo`. Supply a GitHub token once we enable PR creation.

## Roadmap
- Integrate repo cloning + Semgrep/dependency scanners.
- Generate Markdown reports via OpenAI and commit them into the target repo.
- Automate PR creation with PyGithub using supplied PAT.
- Build a tiny demo UI to trigger runs and preview PR links.
