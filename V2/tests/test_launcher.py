"""Regression tests for launcher secret handling and local configuration writes."""

import sys
import tempfile
import types
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

try:
    import requests  # noqa: F401
except ImportError:
    requests_stub = types.ModuleType("requests")
    requests_stub.exceptions = types.SimpleNamespace(Timeout=Exception, RequestException=Exception)
    requests_stub.get = lambda *args, **kwargs: None
    sys.modules["requests"] = requests_stub

import launcher


class LauncherTests(unittest.TestCase):
    def test_page_does_not_echo_saved_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            env_path = Path(directory) / ".env"
            env_path.write_text(
                "GEMINI_API_KEY=gemini-secret\nGITHUB_TOKEN=github-secret\n"
                "MODEL_NAME=gemini-3.5-flash\nCUSTOM_KEY=custom-secret\n"
            )
            original_env_file = launcher.ENV_FILE
            launcher.ENV_FILE = str(env_path)
            try:
                page = launcher.render_setup_page()
                self.assertNotIn("gemini-secret", page)
                self.assertNotIn("github-secret", page)
                self.assertNotIn("custom-secret", page)
                self.assertIn("Configured (leave blank to keep)", page)
            finally:
                launcher.ENV_FILE = original_env_file

    def test_env_file_is_private_and_custom_values_cannot_inject_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            old_path = launcher.ENV_FILE
            launcher.ENV_FILE = str(Path(directory) / ".env")
            try:
                launcher.write_env(
                    "gemini-key", "github-key", "gemini-3.5-flash",
                    {"SAFE_KEY": "one\nINJECTED=two", "BAD KEY\nX": "ignored"},
                )
                content = Path(launcher.ENV_FILE).read_text()
                self.assertIn("GEMINI_API_KEY=gemini-key", content)
                self.assertNotIn("INJECTED=two", content)
                if hasattr(Path(launcher.ENV_FILE).stat(), "st_mode"):
                    self.assertEqual(Path(launcher.ENV_FILE).stat().st_mode & 0o777, 0o600)
            finally:
                launcher.ENV_FILE = old_path

    def test_rejects_newlines_in_standard_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            old_path = launcher.ENV_FILE
            launcher.ENV_FILE = str(Path(directory) / ".env")
            try:
                with self.assertRaises(ValueError):
                    launcher.write_env("key\nINJECTED=1", "", "gemini-3.5-flash")
            finally:
                launcher.ENV_FILE = old_path


if __name__ == "__main__":
    unittest.main()
