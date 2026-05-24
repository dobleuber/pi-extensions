import unittest
from pathlib import Path

from roger.pi_rpc.sessions import PiSessionManager, select_model_args
from roger.routing.registry import SessionRegistry


class PiSessionTests(unittest.TestCase):
    def test_session_manager_builds_rpc_command_with_domain_cwd(self):
        registry = SessionRegistry.default(project_dir=Path("/tmp/project"))
        manager = PiSessionManager(registry=registry, session_dir=Path("/tmp/roger-sessions"))

        command = manager.build_command("current-project", offline=False)

        self.assertEqual(command[:3], ["pi", "--mode", "rpc"])
        self.assertIn("--session-dir", command)
        self.assertIn("/tmp/roger-sessions/current-project", command)
        self.assertEqual(manager.cwd_for("current-project"), Path("/tmp/project"))

    def test_offline_model_args_use_configured_provider_and_model(self):
        args = select_model_args(offline=True, provider="llama-cpp", model="gemma4")

        self.assertEqual(args, ["--offline", "--provider", "llama-cpp", "--model", "gemma4"])

    def test_offline_model_args_can_select_provider_without_model(self):
        args = select_model_args(offline=True, provider="llama-cpp", model=None)

        self.assertEqual(args, ["--offline", "--provider", "llama-cpp"])

    def test_online_model_args_leave_pi_default_untouched(self):
        self.assertEqual(select_model_args(offline=False, provider="llama-cpp", model="gemma4"), [])


if __name__ == "__main__":
    unittest.main()
