"""Regression coverage for the optional GitHub profile validation tool."""

import sys
import types
import unittest
from unittest.mock import Mock, patch

try:
    import requests  # noqa: F401
except ImportError:  # Keep the audit tests runnable in the minimal workspace image.
    requests_stub = types.ModuleType("requests")
    requests_stub.exceptions = types.SimpleNamespace(
        Timeout=type("Timeout", (Exception,), {}),
        RequestException=type("RequestException", (Exception,), {}),
    )
    requests_stub.get = Mock()
    requests_stub.post = Mock()
    sys.modules["requests"] = requests_stub

import github


class GitHubValidationTests(unittest.TestCase):
    def test_normalizes_supported_profile_inputs(self):
        self.assertEqual(github.normalize_username("@octocat"), "octocat")
        self.assertEqual(github.normalize_username("https://github.com/octocat/"), "octocat")
        self.assertEqual(github.normalize_username("github.com/octocat?tab=repositories"), "octocat")

    def test_rejects_non_github_hosts_and_invalid_names(self):
        self.assertEqual(github.normalize_username("https://evil.example/github.com/octocat"), "")
        self.assertEqual(github.normalize_username("bad username"), "")

    @patch.object(github.requests, "get")
    def test_existing_profile_is_verification_not_a_quality_score(self, get):
        response = Mock(status_code=200)
        response.json.return_value = {
            "login": "octocat", "public_repos": 0,
            "created_at": "2020-01-01T00:00:00Z", "html_url": "https://github.com/octocat",
        }
        get.return_value = response

        with patch.dict("os.environ", {"GITHUB_TOKEN": ""}):
            result = github.github_validator("octocat")

        self.assertEqual(result["status"], "VERIFIED")
        self.assertTrue(result["exists"])
        self.assertEqual(result["public_repo_count"], 0)
        self.assertEqual(result["public_contributions"]["status"], "AUTH_REQUIRED")
        self.assertNotIn("score", result)
        self.assertIn("not been assessed", result["assessment"])

    @patch.object(github.requests, "get")
    def test_not_found_is_not_candidate_evidence(self, get):
        get.return_value = Mock(status_code=404)
        result = github.github_validator("octocat")
        self.assertEqual(result["status"], "NOT_FOUND")
        self.assertIs(result["exists"], False)
        self.assertIn("does not affect candidate scoring", result["error"])

    @patch.object(github.requests, "get")
    def test_rate_limit_is_unknown(self, get):
        get.return_value = Mock(status_code=403)
        result = github.github_validator("octocat")
        self.assertEqual(result["status"], "UNAVAILABLE")
        self.assertIsNone(result["exists"])

    @patch.object(github.requests, "get")
    def test_network_error_does_not_expose_exception_details(self, get):
        error_type = github.requests.exceptions.RequestException
        get.side_effect = error_type("https://api.github.com/users/octocat?token=secret")
        result = github.github_validator("octocat")
        self.assertEqual(result["status"], "UNAVAILABLE")
        self.assertNotIn("secret", result["error"])

    @patch.object(github.requests, "get")
    def test_malformed_success_response_is_unavailable(self, get):
        response = Mock(status_code=200)
        response.json.side_effect = ValueError("bad JSON")
        get.return_value = response
        result = github.github_validator("octocat")
        self.assertEqual(result["status"], "UNAVAILABLE")
        self.assertIsNone(result["exists"])

    @patch.object(github.requests, "post")
    def test_public_contribution_summary_counts_and_ranks_repositories(self, post):
        response = Mock(status_code=200)
        response.json.return_value = {
            "data": {
                "user": {
                    "contributionsCollection": {
                        "commitContributionsByRepository": [
                            {"repository": {"nameWithOwner": "octocat/alpha", "url": "https://github.com/octocat/alpha", "isPrivate": False, "isFork": False, "isArchived": False}, "contributions": {"totalCount": 23}},
                            {"repository": {"nameWithOwner": "octocat/beta", "url": "https://github.com/octocat/beta", "isPrivate": False, "isFork": True, "isArchived": False}, "contributions": {"totalCount": 8}},
                            {"repository": {"nameWithOwner": "octocat/private", "url": "https://github.com/octocat/private", "isPrivate": True, "isFork": False, "isArchived": False}, "contributions": {"totalCount": 99}},
                        ],
                        "pullRequestContributionsByRepository": [
                            {"repository": {"nameWithOwner": "octocat/alpha", "url": "https://github.com/octocat/alpha", "isPrivate": False, "isFork": False, "isArchived": False}, "contributions": {"totalCount": 2}},
                        ],
                        "issueContributionsByRepository": [],
                        "pullRequestReviewContributionsByRepository": [],
                    }
                }
            }
        }
        post.return_value = response

        result = github.fetch_public_contributions("octocat", "test-token")

        self.assertEqual(result["status"], "AVAILABLE")
        self.assertEqual(result["totals_in_reported_repositories"]["commits"], 31)
        self.assertEqual(result["totals_in_reported_repositories"]["pull_requests"], 2)
        self.assertEqual(result["repositories_reported"], 2)
        self.assertEqual(result["leading_commit_repository"]["name"], "octocat/alpha")
        self.assertEqual(result["leading_commit_repository"]["commit_contributions"], 23)
        self.assertEqual(result["leading_contribution_repository"]["name"], "octocat/alpha")
        self.assertTrue(post.called)

    def test_public_contributions_require_token(self):
        result = github.fetch_public_contributions("octocat")
        self.assertEqual(result["status"], "AUTH_REQUIRED")
        self.assertEqual(result["repositories"], [])

    @patch.object(github.requests, "get")
    @patch.object(github.requests, "post")
    def test_validator_combines_profile_count_with_graphql_summary(self, post, get):
        profile = Mock(status_code=200)
        profile.json.return_value = {
            "login": "octocat", "public_repos": 12,
            "created_at": "2020-01-01T00:00:00Z", "html_url": "https://github.com/octocat",
        }
        get.return_value = profile
        graphql = Mock(status_code=200)
        graphql.json.return_value = {
            "data": {"user": {"contributionsCollection": {
                "commitContributionsByRepository": [],
                "pullRequestContributionsByRepository": [],
                "issueContributionsByRepository": [],
                "pullRequestReviewContributionsByRepository": [],
            }}}
        }
        post.return_value = graphql

        with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}):
            result = github.github_validator("octocat")

        self.assertEqual(result["status"], "VERIFIED")
        self.assertEqual(result["public_repo_count"], 12)
        self.assertEqual(result["public_contributions"]["status"], "AVAILABLE")
        self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer test-token")

    @patch.object(github.requests, "post")
    def test_graphql_failure_does_not_invalidate_profile(self, post):
        post.side_effect = github.requests.exceptions.Timeout("timeout")
        result = github.fetch_public_contributions("octocat", "test-token")
        self.assertEqual(result["status"], "UNAVAILABLE")
        self.assertIsNone(result["leading_commit_repository"])

    @patch.object(github.requests, "post")
    def test_malformed_graphql_payload_is_unavailable(self, post):
        response = Mock(status_code=200)
        response.json.return_value = {"errors": [{"message": "internal details"}]}
        post.return_value = response
        result = github.fetch_public_contributions("octocat", "test-token")
        self.assertEqual(result["status"], "UNAVAILABLE")
        self.assertNotIn("internal details", str(result))


if __name__ == "__main__":
    unittest.main()
