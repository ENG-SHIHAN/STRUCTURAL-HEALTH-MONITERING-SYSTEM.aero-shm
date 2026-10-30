"""
Aero-SHM: GitHub Remote Sync & Push Utility
Allows connecting this local repository to any GitHub repository.

Usage:
    python push_to_github.py <github_repo_url> [github_token_or_pat]

Examples:
    python push_to_github.py https://github.com/my-username/aero-shm.git
    python push_to_github.py https://github.com/my-username/aero-shm.git ghp_xxxxxxxxxxxxxxxxxxxx
"""

import sys
import os
from dulwich.repo import Repo
import dulwich.porcelain as porcelain

def sync_github(repo_url: str, token: str = None):
    repo_path = os.path.dirname(os.path.abspath(__file__))
    repo = Repo(repo_path)
    
    # Configure remote origin
    if token and repo_url.startswith("https://"):
        # Format URL with authenticated token
        clean_url = repo_url.replace("https://", "")
        auth_url = f"https://oauth2:{token}@{clean_url}"
    else:
        auth_url = repo_url

    print(f"Connecting local repository to: {repo_url}")
    
    # Update or add remote
    config = repo.get_config()
    config.set((b"remote", b"origin"), b"url", auth_url.encode("utf-8"))
    config.write_to_path()
    print("Remote 'origin' successfully configured!")

    print("Pushing branch 'main' to GitHub...")
    try:
        porcelain.push(repo, auth_url.encode("utf-8"), refspecs=b"refs/heads/main:refs/heads/main")
        print("\nSUCCESS! Successfully pushed Aero-SHM project to GitHub!")
        print(f"Repository URL: {repo_url}")
        print("\nNext Step for 24/7 Cloud Deployment:")
        print("1. Go to https://share.streamlit.io")
        print("2. Click 'Create App' -> select your GitHub repository")
        print("3. Set Main file path: app.py")
        print("4. Click 'Deploy' to get your free public https://<your-app>.streamlit.app website!")
    except Exception as e:
        print(f"\nNotice during push: {e}")
        print("If authentication is required, make sure to pass a GitHub Personal Access Token (PAT):")
        print("python push_to_github.py <repo_url> <your_github_token>")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        url = input("Enter your GitHub repository URL (e.g. https://github.com/username/aero-shm.git): ").strip()
        if not url:
            sys.exit(1)
        pat = input("Enter GitHub Personal Access Token (leave empty if using credential helper): ").strip() or None
        sync_github(url, pat)
    else:
        repo_url = sys.argv[1]
        token = sys.argv[2] if len(sys.argv) > 2 else None
        sync_github(repo_url, token)
