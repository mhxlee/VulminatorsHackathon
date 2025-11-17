"""GitHub client helpers built on top of PyGithub.

These wrappers keep auth/token handling isolated from pipeline logic.
"""

from typing import Optional
from urllib.parse import urlparse

from github import Github, GithubException


def _extract_full_name(repo_url: str) -> str:
    parsed = urlparse(repo_url)
    path = parsed.path.strip("/")
    if path.endswith(".git"):
        path = path[: -len(".git")]
    return path


class GitHubService:
    def __init__(self, token: str) -> None:
        self.token = token
        self._client = Github(token)

    def get_repo(self, repo_url: str):
        """Fetch a repository object from a full HTTPS URL."""
        full_name = _extract_full_name(repo_url)
        return self._client.get_repo(full_name)

    def ensure_fork(self, repo_url: str):
        """Create or fetch the authenticated user's fork of the target repo."""
        repo = self.get_repo(repo_url)
        try:
            return repo.create_fork()
        except GithubException:
            user = self._client.get_user()
            return user.get_repo(repo.name)

    def get_default_branch(self, repo_url: str) -> str:
        return self.get_repo(repo_url).default_branch

    def get_authenticated_username(self) -> str:
        return self._client.get_user().login

    def create_pull_request(
        self,
        target_repo_url: str,
        head_reference: str,
        title: str,
        body: str,
        base_branch: Optional[str] = None,
        draft: bool = False,
    ) -> Optional[str]:
        repo = self.get_repo(target_repo_url)
        base = base_branch or repo.default_branch
        pr = repo.create_pull(
            title=title,
            body=body,
            base=base,
            head=head_reference,
            draft=draft,
        )
        return pr.html_url
