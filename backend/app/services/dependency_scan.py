"""Dependency vulnerability scanning helpers (npm audit)."""

import json
import shutil
import subprocess
from pathlib import Path
from typing import List


class DependencyScannerError(RuntimeError):
    pass


def _ensure_npm() -> None:
    if not shutil.which("npm"):
        raise DependencyScannerError(
            "npm CLI not found. Install Node.js/npm to enable dependency audits."
        )


def _parse_vulnerabilities(payload: dict, lockfile_path: Path) -> List[dict]:
    vulnerabilities = payload.get("vulnerabilities", {})
    findings: List[dict] = []

    for package_name, vuln in vulnerabilities.items():
        via = vuln.get("via") or []
        advisory = None
        if isinstance(via, list):
            for item in via:
                if isinstance(item, dict):
                    advisory = item
                    break
        elif isinstance(via, dict):
            advisory = via

        title = advisory.get("title") if advisory else f"{package_name} vulnerability"
        url = advisory.get("url") if advisory else ""
        severity = vuln.get("severity", "info")
        range_spec = vuln.get("range")
        detail_parts = [title]
        if range_spec:
            detail_parts.append(f"Affected versions: {range_spec}")
        if url:
            detail_parts.append(url)

        findings.append(
            {
                "title": f"{package_name} ({severity})",
                "severity": severity,
                "file_path": str(lockfile_path),
                "summary": " — ".join(detail_parts),
            }
        )

    return findings


def run_dependency_audits(repo_path: str) -> List[dict]:
    _ensure_npm()
    root = Path(repo_path)
    lockfiles = list(root.rglob("package-lock.json"))

    if not lockfiles:
        return [
            {
                "title": "Dependency audit",
                "severity": "info",
                "file_path": None,
                "summary": "No npm lockfiles found; skipped npm audit.",
            }
        ]

    all_findings: List[dict] = []
    for lockfile in lockfiles:
        cmd = ["npm", "audit", "--json", "--package-lock-only"]
        process = subprocess.run(
            cmd,
            cwd=lockfile.parent,
            capture_output=True,
            text=True,
            check=False,
        )

        if process.returncode not in (0, 1):
            raise DependencyScannerError(
                f"npm audit failed for {lockfile} (code {process.returncode}): "
                f"{process.stderr.strip()}"
            )

        try:
            data = json.loads(process.stdout or "{}")
        except json.JSONDecodeError as exc:
            raise DependencyScannerError(
                f"Unable to parse npm audit output for {lockfile}"
            ) from exc

        findings = _parse_vulnerabilities(data, lockfile.relative_to(root))
        all_findings.extend(findings)

    if not all_findings:
        all_findings.append(
            {
                "title": "Dependency audit",
                "severity": "info",
                "file_path": None,
                "summary": "npm audit reported no vulnerabilities.",
            }
        )

    return all_findings
