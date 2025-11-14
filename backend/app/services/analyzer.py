import asyncio
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .. import schemas
from ..config import get_settings
from .dependency_scan import DependencyScannerError, run_dependency_audits
from .pr_publisher import publish_report_pr
from .repo_workspace import RepoWorkspace
from .reporting import generate_markdown_report
from .scanners import ScannerError, run_semgrep_scan


@dataclass
class PipelineResult:
    findings: List[dict]
    pr_url: Optional[str]
    message: str


async def run_analysis_pipeline(
    run_id: str,
    request: schemas.AnalyzeRequest,
) -> PipelineResult:
    settings = get_settings()
    repo_url = str(request.repo_url)
    workspace = RepoWorkspace(run_id)
    repo_dir = workspace.clone(repo_url)

    findings: List[dict] = []
    messages: List[str] = []

    try:
        semgrep_findings = await asyncio.to_thread(
            run_semgrep_scan, str(repo_dir), request.preset
        )
        findings.extend(semgrep_findings)
        messages.append(
            f"Semgrep finished {len(semgrep_findings)} finding(s) "
            f"at {datetime.utcnow().isoformat()}"
        )
    except ScannerError as exc:
        findings.append(
            {
                "title": "Semgrep",
                "severity": "error",
                "summary": str(exc),
                "file_path": None,
            }
        )
        messages.append("Semgrep failed")

    try:
        dependency_findings = await asyncio.to_thread(
            run_dependency_audits, str(repo_dir)
        )
        findings.extend(dependency_findings)
        messages.append(
            f"Dependency audit returned {len(dependency_findings)} finding(s)"
        )
    except DependencyScannerError as exc:
        findings.append(
            {
                "title": "Dependency audit",
                "severity": "error",
                "summary": str(exc),
                "file_path": None,
            }
        )
        messages.append("Dependency audit failed")

    finding_models = [schemas.FindingSummary(**finding) for finding in findings]
    report_relative_path = Path("reports") / "VulminatorReport.md"

    try:
        report_contents = await generate_markdown_report(finding_models)
        messages.append("Generated Markdown report")
    except Exception as exc:  # pragma: no cover
        report_contents = "Report generation failed.\n\n" + str(exc)
        messages.append("Report generation failed; using fallback text")

    report_path = repo_dir / report_relative_path
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_contents, encoding="utf-8")

    pr_url: Optional[str] = None
    token = (request.github_token or settings.github_token or "").strip()
    if token and token.lower() != "placeholder":
        try:
            pr_url = await asyncio.to_thread(
                publish_report_pr,
                repo_dir,
                repo_url,
                token,
                report_relative_path,
                report_contents,
                len(finding_models),
            )
            if pr_url:
                messages.append("Opened pull request")
        except Exception as exc:  # pragma: no cover
            messages.append(f"Pull request failed: {exc}")
    else:
        messages.append("Skipped PR (no GitHub token provided)")

    return PipelineResult(
        findings=findings,
        pr_url=pr_url,
        message="; ".join(messages),
    )
