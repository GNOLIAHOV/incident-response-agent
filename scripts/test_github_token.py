import sys
from pathlib import Path
import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.core.config import settings
from src.tools.github_client import GitHubClient

def test_github():
    print("Testing GitHub Client authentication...")
    print(f"Owner: {settings.GITHUB_OWNER}")
    print(f"Repo: {settings.GITHUB_DEFAULT_REPO}")
    print(f"Token: {settings.GITHUB_TOKEN[:8]}...{settings.GITHUB_TOKEN[-4:]}")
    
    headers = {
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    
    with httpx.Client(headers=headers, timeout=10.0) as client:
        # Check user auth
        user_resp = client.get("https://api.github.com/user")
        if user_resp.status_code == 200:
            print("✓ GitHub User Authenticated:", user_resp.json().get("login"))
        else:
            print("✗ User auth failed:", user_resp.status_code, user_resp.text)
            return
            
        # Check repo access
        repo_resp = client.get(f"https://api.github.com/repos/{settings.GITHUB_OWNER}/{settings.GITHUB_DEFAULT_REPO}")
        if repo_resp.status_code == 200:
            print("✓ Repository Access OK:", repo_resp.json().get("full_name"))
            print("  Default branch:", repo_resp.json().get("default_branch"))
        else:
            print("✗ Repository access failed:", repo_resp.status_code, repo_resp.text)

if __name__ == "__main__":
    test_github()
