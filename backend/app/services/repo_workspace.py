from pathlib import Path
from typing import Optional

from git import Repo

from ..config import get_settings


class RepoWorkspace:
    def __init__(self, run_id: str) -> None:
        settings = get_settings()
        self.root = settings.workspace_root / run_id
        self.root.mkdir(parents=True, exist_ok=True)

    def clone(self, repo_url: str, branch: Optional[str] = None) -> Path:
        target_dir = self.root / "repo"
        if target_dir.exists():
            return target_dir
        Repo.clone_from(repo_url, target_dir, depth=1, branch=branch)
        return target_dir

    def cleanup(self) -> None:
        # Deferred to future implementation; callers can delete dirs when safe.
        pass
