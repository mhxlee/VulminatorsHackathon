"""Helpers to automatically upgrade vulnerable npm dependencies."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Set

import subprocess


@dataclass
class UpgradeAction:
    lockfile: Path
    package: str
    command: List[str]
    success: bool
    message: str


class DependencyUpgradeError(RuntimeError):
    pass


def _npm_install(package: str, working_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["npm", "install", f"{package}@latest"],
        cwd=working_dir,
        capture_output=True,
        text=True,
        check=False,
    )


def apply_dependency_upgrades(repo_dir: Path, upgrade_plan: Dict[Path, Set[str]]) -> List[UpgradeAction]:
    actions: List[UpgradeAction] = []

    for lockfile_rel, packages in upgrade_plan.items():
        if not packages:
            continue
        lockfile_dir = (repo_dir / lockfile_rel).parent
        for package in sorted(packages):
            result = _npm_install(package, lockfile_dir)
            success = result.returncode == 0
            message = result.stderr.strip() or result.stdout.strip() or "Command executed"
            actions.append(
                UpgradeAction(
                    lockfile=lockfile_rel,
                    package=package,
                    command=["npm", "install", f"{package}@latest"],
                    success=success,
                    message=message[:4000],
                )
            )

            if not success:
                raise DependencyUpgradeError(
                    f"Failed to upgrade {package} in {lockfile_rel}: {message}"
                )

    return actions
