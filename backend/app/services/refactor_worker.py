"""Applies simple AI-style refactors by annotating risky files."""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from .refactor_queue import RefactorTask

COMMENT_PREFIX = {
    ".js": "//",
    ".jsx": "//",
    ".ts": "//",
    ".tsx": "//",
    ".py": "#",
    ".java": "//",
    ".rb": "#",
    ".go": "//",
    ".kt": "//",
}

VERIFY_COMMAND = {
    ".js": ["npx", "eslint", "--quiet"],
    ".ts": ["npx", "eslint", "--quiet"],
    ".jsx": ["npx", "eslint", "--quiet"],
    ".tsx": ["npx", "eslint", "--quiet"],
}


@dataclass
class RefactorResult:
    task: RefactorTask
    applied: bool
    message: str


def _make_comment(task: RefactorTask, prefix: str) -> str:
    summary = task.summary.strip().splitlines()[0][:160]
    return f"{prefix} Vulminator {task.severity.upper()} refactor: {summary}\n"


def _verify_file(repo_dir: Path, file_rel: Path, suffix: str) -> Optional[str]:
    cmd = VERIFY_COMMAND.get(suffix)
    if not cmd:
        return None

    full_cmd = cmd + [str(file_rel)]
    process = subprocess.run(
        full_cmd,
        cwd=repo_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    if process.returncode == 0:
        return None
    return process.stderr.strip() or process.stdout.strip() or "Verification failed"


def apply_refactor_tasks(repo_dir: Path, tasks: Iterable[RefactorTask]) -> List[RefactorResult]:
    results: List[RefactorResult] = []

    for task in tasks:
        suffix = task.file_path.suffix
        prefix = COMMENT_PREFIX.get(suffix)
        file_path = repo_dir / task.file_path

        if not prefix:
            results.append(
                RefactorResult(task=task, applied=False, message="Unsupported file type")
            )
            continue

        if not file_path.exists():
            results.append(
                RefactorResult(task=task, applied=False, message="File missing on disk")
            )
            continue

        try:
            original = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            results.append(
                RefactorResult(task=task, applied=False, message=f"Read error: {exc}")
            )
            continue

        comment = _make_comment(task, prefix)
        if comment.strip() in original:
            results.append(
                RefactorResult(task=task, applied=False, message="Comment already present")
            )
            continue

        new_contents = comment + original
        try:
            file_path.write_text(new_contents, encoding="utf-8")
        except OSError as exc:
            results.append(
                RefactorResult(task=task, applied=False, message=f"Write error: {exc}")
            )
            continue

        verification_error = _verify_file(repo_dir, task.file_path, suffix)
        if verification_error:
            file_path.write_text(original, encoding="utf-8")
            results.append(
                RefactorResult(
                    task=task,
                    applied=False,
                    message=f"Verification failed: {verification_error}",
                )
            )
            continue

        results.append(
            RefactorResult(task=task, applied=True, message="Inserted Vulminator comment")
        )

    return results
