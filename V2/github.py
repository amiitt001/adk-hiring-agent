"""GitHub REST and GraphQL evidence used by optional profile validation."""

from datetime import datetime, timedelta, timezone
import os
import re
from urllib.parse import urlparse

import requests


_GRAPHQL_ENDPOINT = "https://api.github.com/graphql"
_MAX_CONTRIBUTION_REPOSITORIES = 100
_CONTRIBUTION_QUERY = """
query PublicContributions($login: String!, $from: DateTime!, $to: DateTime!, $maxRepositories: Int!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      commitContributionsByRepository(maxRepositories: $maxRepositories) {
        repository { nameWithOwner url isPrivate isFork isArchived }
        contributions(first: 1) { totalCount }
      }
      pullRequestContributionsByRepository(maxRepositories: $maxRepositories) {
        repository { nameWithOwner url isPrivate isFork isArchived }
        contributions(first: 1) { totalCount }
      }
      issueContributionsByRepository(maxRepositories: $maxRepositories) {
        repository { nameWithOwner url isPrivate isFork isArchived }
        contributions(first: 1) { totalCount }
      }
      pullRequestReviewContributionsByRepository(maxRepositories: $maxRepositories) {
        repository { nameWithOwner url isPrivate isFork isArchived }
        contributions(first: 1) { totalCount }
      }
    }
  }
}
"""


def _unavailable_contributions(status: str, error: str) -> dict:
    return {
        "status": status,
        "error": error,
        "period": "last 365 days",
        "repositories": [],
        "leading_contribution_repository": None,
        "leading_commit_repository": None,
    }


def _parse_public_contributions(data: dict, from_date: str, to_date: str) -> dict:
    """Aggregate only visible public repository contribution counts."""
    try:
        collection = data["data"]["user"]["contributionsCollection"]
        field_names = {
            "commits": "commitContributionsByRepository",
            "pull_requests": "pullRequestContributionsByRepository",
            "issues": "issueContributionsByRepository",
            "reviews": "pullRequestReviewContributionsByRepository",
        }
        repositories = {}
        for metric, field_name in field_names.items():
            groups = collection[field_name]
            if not isinstance(groups, list):
                raise ValueError("Malformed contribution groups")
            for group in groups:
                repository = group.get("repository")
                contribution = group.get("contributions")
                if not isinstance(repository, dict) or repository.get("isPrivate") is not False:
                    continue
                name = repository.get("nameWithOwner")
                url = repository.get("url")
                count = contribution.get("totalCount") if isinstance(contribution, dict) else None
                if not isinstance(name, str) or not isinstance(url, str):
                    raise ValueError("Malformed repository contribution")
                if not isinstance(count, int) or count < 0:
                    raise ValueError("Malformed contribution count")
                row = repositories.setdefault(name, {
                    "name": name,
                    "url": url,
                    "is_fork": bool(repository.get("isFork")),
                    "is_archived": bool(repository.get("isArchived")),
                    "commits": 0,
                    "pull_requests": 0,
                    "issues": 0,
                    "reviews": 0,
                })
                row[metric] = count
    except (KeyError, TypeError, ValueError, AttributeError):
        return _unavailable_contributions(
            "UNAVAILABLE", "GitHub returned an invalid contribution response."
        )

    rows = list(repositories.values())
    for row in rows:
        row["total_contributions"] = sum(
            row[metric] for metric in ("commits", "pull_requests", "issues", "reviews")
        )
    rows_by_commits = sorted(rows, key=lambda row: (-row["commits"], row["name"].casefold()))
    rows_by_total = sorted(rows, key=lambda row: (-row["total_contributions"], row["name"].casefold()))
    leading_commit = next((row for row in rows_by_commits if row["commits"] > 0), None)
    leading_overall = next((row for row in rows_by_total if row["total_contributions"] > 0), None)
    totals = {
        metric: sum(row[metric] for row in rows)
        for metric in ("commits", "pull_requests", "issues", "reviews")
    }
    if leading_commit:
        leading_commit = {
            "name": leading_commit["name"],
            "url": leading_commit["url"],
            "commit_contributions": leading_commit["commits"],
        }
    if leading_overall:
        leading_overall = {
            "name": leading_overall["name"],
            "url": leading_overall["url"],
            "total_contributions": leading_overall["total_contributions"],
        }
    return {
        "status": "AVAILABLE",
        "period": "last 365 days",
        "period_from": from_date,
        "period_to": to_date,
        "scope": (
            "Visible contributions in public repositories. Totals and leading repositories are "
            "calculated across the up-to-100 repositories returned by GraphQL, not all-time activity."
        ),
        "totals_in_reported_repositories": totals,
        "repositories_reported": len(rows),
        "repositories_shown": min(10, len(rows_by_total)),
        "repositories": rows_by_total[:10],
        "leading_contribution_repository": leading_overall,
        "leading_commit_repository": leading_commit,
    }


def fetch_public_contributions(username: str, token: str | None = None) -> dict:
    """Fetch a bounded one-year public contribution breakdown with GraphQL."""
    if not token:
        return _unavailable_contributions(
            "AUTH_REQUIRED", "Set GITHUB_TOKEN to retrieve the public contribution breakdown."
        )

    now = datetime.now(timezone.utc).replace(microsecond=0)
    from_date = (now - timedelta(days=365)).isoformat().replace("+00:00", "Z")
    to_date = now.isoformat().replace("+00:00", "Z")
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "ADK-Hiring-Agent",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    try:
        response = requests.post(
            _GRAPHQL_ENDPOINT,
            headers=headers,
            json={
                "query": _CONTRIBUTION_QUERY,
                "variables": {
                    "login": username,
                    "from": from_date,
                    "to": to_date,
                    "maxRepositories": _MAX_CONTRIBUTION_REPOSITORIES,
                },
            },
            timeout=(3.05, 10),
        )
    except requests.exceptions.Timeout:
        return _unavailable_contributions("UNAVAILABLE", "GitHub contribution request timed out.")
    except requests.exceptions.RequestException:
        return _unavailable_contributions("UNAVAILABLE", "GitHub contribution API could not be reached.")

    if response.status_code in {403, 429}:
        return _unavailable_contributions("UNAVAILABLE", "GitHub rate or permission limit prevented contribution lookup.")
    if response.status_code != 200:
        return _unavailable_contributions("UNAVAILABLE", f"GitHub contribution API returned HTTP {response.status_code}.")
    try:
        payload = response.json()
        if not isinstance(payload, dict) or payload.get("errors"):
            raise ValueError("GraphQL returned errors")
        if payload.get("data", {}).get("user") is None:
            raise ValueError("GraphQL user missing")
    except (ValueError, TypeError, AttributeError):
        return _unavailable_contributions("UNAVAILABLE", "GitHub contribution API returned an invalid response.")
    return _parse_public_contributions(payload, from_date, to_date)


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
    """Verify a public profile and optionally summarize public activity; no scoring."""
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
        "public_repos": data.get("public_repos"),
        "public_repo_count": data.get("public_repos"),
        "public_contributions": fetch_public_contributions(username, token),
        "account_age_years": account_age_years,
        "profile_url": data.get("html_url", f"https://github.com/{username}"),
        "assessment": (
            "Public account verified. Public repository and contribution counts are descriptive only; "
            "repository quality and candidate skill have not been assessed."
        ),
    }
