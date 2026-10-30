"""Smoke test that the installed ADK discovers the configured root agent."""

from pathlib import Path
import unittest

try:
    from google.adk.cli.utils.agent_loader import AgentLoader
except ImportError:
    AgentLoader = None


@unittest.skipIf(AgentLoader is None, "google-adk is not installed")
class ADKLoadingTests(unittest.TestCase):
    def test_web_loader_discovers_root_agent(self):
        agents_dir = Path(__file__).resolve().parents[1] / "adk_agents"
        loader = AgentLoader(str(agents_dir))

        self.assertEqual(loader.list_agents(), ["hiring_agent"])
        loaded = loader.load_agent("hiring_agent")
        self.assertEqual(loaded.name, "ConversationalHiringOrchestrator")
        self.assertEqual(len(loaded.tools), 5)


if __name__ == "__main__":
    unittest.main()
