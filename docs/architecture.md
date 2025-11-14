# Vulminators MVP Architecture

## Goal
Given a GitHub repository URL and an access token, automatically:
1. Clone and analyze the repo for vulnerable/outdated code.
2. Summarize findings with AI.
3. Create a branch + pull request in the target repo with a human-friendly report (and eventually code fixes).

## High-Level Flow
```
Client → FastAPI API → Job Orchestrator → Repo Workspace
                                  ↓
                            Scanner Adapters
                                  ↓
                             AI Summarizer
                                  ↓
                              PR Service
                                  ↓
                              GitHub REST
```

## Components
- **FastAPI Service**
  - Endpoints: `/health`, `/analyze` (POST repo URL + PAT), `/runs/{id}` for status.
  - Handles input validation, kicks off analysis jobs, streams status to clients.
- **Job Orchestrator**
  - MVP: in-process async task queue (e.g., `asyncio` background tasks).
  - Stretch: Celery/Redis for parallelism.
- **Repo Service**
  - Clones repos into temp dirs (shallow clone), detects default branch, prepares fork if necessary.
  - Manages Git operations (create branch `vulminator/<timestamp>`, commit artifacts).
- **Scanner Adapters**
  - Semgrep baseline ruleset for general vulnerabilities.
  - Dependency audit per ecosystem (`npm audit`, `pip-audit`, `gradle dependencies`, etc.).
  - Secrets/entropy scan (future).
  - Normalizes outputs into a `Finding` model: `{file, severity, summary, raw_evidence}`.
- **AI Summarizer**
  - Uses OpenAI API to condense findings, explain impact, recommend fixes, and optionally propose patches.
  - Generates Markdown report sections per finding + overall TL;DR.
- **PR Service**
  - Uses PyGithub + PAT to fork (if needed), push branch, open PR with generated `VulminatorReport.md`.
  - Later: attach suggested code changes or apply patches directly.
- **Storage / Logs**
  - MVP: in-memory map keyed by `run_id` with statuses + artifacts persisted to disk.
  - Stretch: SQLite/Supabase for persistence + dashboard.

## End-to-End Step List
1. Client calls `/analyze` with `{repo_url, github_token, options}`.
2. FastAPI validates + spawns job, returns `run_id`.
3. Job clones repo, determines language(s), selects scanners.
4. Each scanner runs, results aggregated into `findings`.
5. Summarizer converts `findings` to Markdown + optional remediation plan.
6. Repo service creates branch, adds `reports/VulminatorReport.md`, commits, pushes.
7. PR service opens PR linking to the report + summary.
8. Job status updated to `completed` with PR URL; client polls `/runs/{id}`.

## Milestones
1. **Scaffold** FastAPI + job runner skeleton.
2. **GitHub Integration**: clone + branch + PR using PAT.
3. **Static Analysis**: wire Semgrep + simple dependency audit.
4. **AI Reporting**: OpenAI summary + Markdown generation.
5. **Demo CLI/UI**: minimal interface to trigger runs and display PR link.
6. **Stretch**: auto refactors, multi-repo queue, dashboard, Supabase.

## Security & Operational Notes
- Accept PAT over HTTPS only (or local demo). Keep tokens in memory; never log them.
- Clean temp workspaces post-run.
- Rate-limit requests, especially when cloning/scanning.
- Cache scanner installs (Semgrep, language package managers).

## Reference Inspiration
DependaPou pipeline (Modal + Groq + Supabase) inspired this flow; we adapt it with FastAPI + OpenAI for rapid hackathon delivery.

