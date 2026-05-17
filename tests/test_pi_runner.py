import unittest
from pathlib import Path

from roger.pi_rpc.runner import PiAgentRunner
from roger.pi_rpc.sessions import PiSessionManager
from roger.routing.registry import SessionRegistry


class FakeClient:
    def __init__(self):
        self.started = None
        self.prompted = None
        self.collected_text = "Hecho"
        self.stopped = False

    def start(self, command):
        self.started = command

    def prompt(self, message):
        self.prompted = message
        return {"success": True}

    def stream_until_agent_end(self):
        yield {"type": "agent_end"}

    def stop(self):
        self.stopped = True


class PiAgentRunnerTests(unittest.TestCase):
    def test_runner_dispatches_to_session_command_and_returns_collected_text(self):
        client = FakeClient()
        registry = SessionRegistry.default(project_dir=Path("/tmp/project"))
        manager = PiSessionManager(registry=registry, session_dir=Path("/tmp/sessions"))
        calls = []

        def factory(command, cwd):
            calls.append((command, cwd))
            return client

        runner = PiAgentRunner(session_manager=manager, client_factory=factory)

        result = runner.run_task("current-project", "corre los tests")

        self.assertEqual(result, "Hecho")
        self.assertEqual(client.prompted, "corre los tests")
        self.assertEqual(calls[0][1], Path("/tmp/project"))
        self.assertIn("/tmp/sessions/current-project", calls[0][0])
        self.assertTrue(client.stopped)

    def test_runner_reports_prompt_rejection(self):
        class RejectingClient(FakeClient):
            def prompt(self, message):
                return {"success": False, "error": "no model"}

        registry = SessionRegistry.default(project_dir=Path("/tmp/project"))
        manager = PiSessionManager(registry=registry, session_dir=Path("/tmp/sessions"))
        runner = PiAgentRunner(session_manager=manager, client_factory=lambda command, cwd: RejectingClient())

        with self.assertRaisesRegex(RuntimeError, "no model"):
            runner.run_task("system", "actualiza el sistema")


if __name__ == "__main__":
    unittest.main()
