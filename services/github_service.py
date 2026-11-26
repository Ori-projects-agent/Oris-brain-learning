"""
GitHub Integration Service for Ori.
Enables Ori to communicate with GitHub via the GitHub REST API without requiring
external git binaries or third-party libraries (standard library urllib).
Supports syncing the Museum Relic Library directly to the `astral-archive` web game repo.
"""

import base64
import datetime
import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from config.settings import settings

logger = logging.getLogger("Ori.GitHub")


class GitHubService:
    def __init__(self, token: Optional[str] = None):
        self._explicit_token = token

    def _resolve_token(self, custom_token: Optional[str] = None) -> str:
        return (
            custom_token
            or self._explicit_token
            or os.getenv("GITHUB_TOKEN", "")
            or settings.github_token
            or settings.persona.get("github_token", "")
        ).strip()

    def _headers(self, custom_token: Optional[str] = None) -> Dict[str, str]:
        tok = self._resolve_token(custom_token)
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "OriAutonomousSolarium/1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if tok:
            headers["Authorization"] = f"Bearer {tok}"
        return headers

    def get_authenticated_user(self, token: Optional[str] = None) -> Dict[str, Any]:
        """Fetch details about the signed-in GitHub account."""
        tok = self._resolve_token(token)
        if not tok:
            return {"authenticated": False, "error": "No GITHUB_TOKEN configured."}

        url = "https://api.github.com/user"
        try:
            req = urllib.request.Request(url, headers=self._headers(tok), method="GET")
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return {
                    "authenticated": True,
                    "username": data.get("login"),
                    "name": data.get("name"),
                    "html_url": data.get("html_url"),
                    "public_repos": data.get("public_repos"),
                }
        except urllib.error.HTTPError as e:
            return {"authenticated": False, "error": f"GitHub HTTP {e.code}: {e.reason}"}
        except Exception as e:
            return {"authenticated": False, "error": str(e)}

    def create_gist(
        self,
        description: str,
        filename: str,
        content: str,
        public: bool = True,
        token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Publishes an ASCII sketch, technical schematic, or code snippet as a public GitHub Gist."""
        tok = self._resolve_token(token)
        if not tok:
            return {"status": "error", "message": "No GITHUB_TOKEN configured in .env."}

        url = "https://api.github.com/gists"
        payload = {
            "description": description,
            "public": public,
            "files": {filename: {"content": content}},
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=self._headers(tok),
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                logger.info(f"✨ Successfully created GitHub Gist: {data.get('html_url')}")
                return {
                    "status": "success",
                    "gist_id": data.get("id"),
                    "html_url": data.get("html_url"),
                    "description": description,
                }
        except Exception as e:
            logger.error(f"Failed to create GitHub Gist: {e}")
            return {"status": "error", "message": str(e)}

    def create_repository(
        self,
        name: str,
        description: str = "",
        private: bool = False,
        token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Creates a new repository under Ori's GitHub account."""
        tok = self._resolve_token(token)
        if not tok:
            return {"status": "error", "message": "No GITHUB_TOKEN configured in .env."}

        url = "https://api.github.com/user/repos"
        payload = {
            "name": name,
            "description": description,
            "private": private,
            "auto_init": True,
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=self._headers(tok),
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                logger.info(f"✨ Successfully created GitHub Repository: {data.get('html_url')}")
                return {
                    "status": "success",
                    "repo_name": data.get("name"),
                    "html_url": data.get("html_url"),
                }
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            logger.error(f"Failed to create GitHub repository: HTTP {e.code} {body[:120]}")
            return {"status": "error", "message": f"HTTP {e.code}: {body[:120]}"}
        except Exception as e:
            logger.error(f"Failed to create GitHub repository: {e}")
            return {"status": "error", "message": str(e)}

    def get_file_sha(
        self,
        repo: str,
        path: str,
        owner: str,
        token: Optional[str] = None,
    ) -> Optional[str]:
        """Look up existing file SHA on GitHub so PUT /contents/{path} updates cleanly."""
        tok = self._resolve_token(token)
        clean_path = path.lstrip("/")
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{clean_path}"
        try:
            req = urllib.request.Request(url, headers=self._headers(tok), method="GET")
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("sha")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            logger.warning(f"Could not read SHA for {owner}/{repo}/{clean_path}: HTTP {e.code}")
            return None
        except Exception:
            return None

    def commit_file(
        self,
        repo: str,
        path: str,
        content: str,
        commit_message: str,
        owner: Optional[str] = None,
        token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Creates or updates a file directly in a repository via GitHub REST API."""
        tok = self._resolve_token(token)
        if not tok:
            return {"status": "error", "message": "No GITHUB_TOKEN configured in .env."}

        resolved_owner = (owner or os.getenv("GITHUB_OWNER", "") or settings.github_owner).strip()
        if not resolved_owner:
            user_info = self.get_authenticated_user(tok)
            resolved_owner = user_info.get("username", "")
            if not resolved_owner:
                return {"status": "error", "message": user_info.get("error", "Could not determine GitHub repository owner.")}

        clean_path = path.lstrip("/")
        url = f"https://api.github.com/repos/{resolved_owner}/{repo}/contents/{clean_path}"
        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")

        payload: Dict[str, Any] = {
            "message": commit_message,
            "content": encoded_content,
        }
        existing_sha = self.get_file_sha(repo, clean_path, resolved_owner, tok)
        if existing_sha:
            payload["sha"] = existing_sha

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=self._headers(tok),
                method="PUT",
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                commit_url = data.get("commit", {}).get("html_url", "")
                html_url = data.get("content", {}).get("html_url", "")
                return {
                    "status": "success",
                    "owner": resolved_owner,
                    "repo": repo,
                    "path": clean_path,
                    "commit_url": commit_url,
                    "html_url": html_url,
                }
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            return {"status": "error", "message": f"GitHub HTTP {e.code}: {body[:160]}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def sync_relic_library(
        self,
        relics: List[Dict[str, Any]],
        repo: Optional[str] = None,
        owner: Optional[str] = None,
        path: Optional[str] = None,
        token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Push the full Custom Relic Library JSON to the connected web game repo (`astral-archive`)."""
        target_repo = (repo or os.getenv("GITHUB_REPO", "") or settings.github_repo or "astral-archive").strip()
        target_path = (path or os.getenv("GITHUB_RELICS_PATH", "") or settings.github_relics_path or "data/custom_relic_library.json").strip()
        target_owner = (owner or os.getenv("GITHUB_OWNER", "") or settings.github_owner).strip() or None

        payload = {
            "library_name": "Ori's Zenith Archival Relic Library",
            "synced_at": datetime.datetime.now().isoformat(),
            "total_relics": len(relics),
            "relics": relics,
        }
        res = self.commit_file(
            repo=target_repo,
            path=target_path,
            content=json.dumps(payload, indent=2) + "\n",
            commit_message=f"Sync {len(relics)} curated museum relics from Ori Solarium",
            owner=target_owner,
            token=token,
        )
        if res.get("status") == "success":
            logger.info(f"🐙 Synced {len(relics)} relics to {res.get('owner')}/{target_repo}:{target_path}")
        return res


github_service = GitHubService()
