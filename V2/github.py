"""GitHub REST API access used by the optional profile validation step."""

from datetime import datetime, timezone
import os
import re
from urllib.parse import urlparse

import requests


def normalize_username(value: str) -> str:
    """Accept a username, @username, or github.com profile URL."""
    value = (value or "").strip()
    if value.startswith("@"):  # Plain @handle
        value = value[1:]
    if "github.com" in value.lower():
        parsed = urlparse(value if "://" in value else f"https://{value}")
        if parsed.hostname and parsed.hostname.lower() not in {"github.com", "www.github.com"}:
            return ""
        value = parsed.path.strip("/").split("/")[0]
    else:
        value = value.split("?", 1)[0].strip("/")
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", value):
        return ""
    return value


def github_validator(username: str) -> dict:
    """Check whether a public GitHub profile exists; absence is not candidate evidence."""
    username = normalize_username(username)
    if not username:
        return {
            "status": "INVALID_INPUT",
            "username": "",
            "exists": None,
            "error": "Enter a GitHub username or github.com profile URL.",
        }

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ADK-Hiring-Agent",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.get(
            f"https://api.github.com/users/{username}", headers=headers, timeout=(3.05, 10)
        )
    except requests.exceptions.Timeout:
        return {"status": "UNAVAILABLE", "username": username, "exists": None,
                "error": "GitHub API request timed out."}
    except requests.exceptions.RequestException:
        # Do not return exception reprs: they can include secret-bearing request URLs.
        return {"status": "UNAVAILABLE", "username": username, "exists": None,
                "error": "GitHub API could not be reached."}

    if response.status_code == 404:
        return {"status": "NOT_FOUND", "username": username, "exists": False,
                "error": "No public GitHub account was found. This does not affect candidate scoring."}
    if response.status_code == 403 or response.status_code == 429:
        return {"status": "UNAVAILABLE", "username": username, "exists": None,
                "error": "GitHub API rate or permission limit prevented verification."}
    if response.status_code != 200:
        return {"status": "UNAVAILABLE", "username": username, "exists": None,
                "error": f"GitHub API returned HTTP {response.status_code}."}

    try:
        data = response.json()
        if not isinstance(data, dict) or data.get("login", "").lower() != username.lower():
            raise ValueError("Unexpected profile response")
        created_at = data.get("created_at", "")
        account_age_years = None
        if created_at:
            created = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            account_age_years = round((datetime.now(timezone.utc) - created).days / 365.25, 1)
    except (ValueError, TypeError, AttributeError):
        return {"status": "UNAVAILABLE", "username": username, "exists": None,
                "error": "GitHub API returned an invalid profile response."}

    # Do not use profile completeness, repo count, followers, location, or account age
    # as quality signals. They are returned only when useful for verification.
    return {
        "status": "VERIFIED", "username": data["login"], "exists": True,
        "public_repos": data.get("public_repos"), "account_age_years": account_age_years,
        "profile_url": data.get("html_url", f"https://github.com/{username}"),
        "assessment": "Public account verified. Repository quality has not been assessed.",
    }
