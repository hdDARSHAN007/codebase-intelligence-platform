import os
import shutil
import tempfile
import uuid
from git import Repo, GitCommandError

class CloneError(Exception):
    pass

def clone_repo(repo_url: str, github_token: str | None = None) -> str:
    """
    Clones a GitHub repo into a fresh temp directory.
    Returns the local path to the cloned repo.
    """
    workspace_root = os.path.join(tempfile.gettempdir(), "codebase-intel")
    os.makedirs(workspace_root, exist_ok=True)

    job_id = str(uuid.uuid4())
    dest_path = os.path.join(workspace_root, job_id)

    clone_url = repo_url
    if github_token:
        # Inject token for private repo auth: https://<token>@github.com/owner/repo.git
        if repo_url.startswith("https://"):
            clone_url = repo_url.replace("https://", f"https://{github_token}@")

    try:
        Repo.clone_from(clone_url, dest_path, depth=1)  # depth=1: shallow clone, faster, no history
    except GitCommandError as e:
        # Strip token from error message if present, so it's never logged
        safe_msg = str(e).replace(github_token or "", "***") 
        raise CloneError(f"Failed to clone {repo_url}: {safe_msg}")

    return dest_path

def cleanup_repo(local_path: str):
    """Deletes a cloned repo's temp directory."""
    if os.path.exists(local_path) and "codebase-intel" in local_path:
        shutil.rmtree(local_path, ignore_errors=True)