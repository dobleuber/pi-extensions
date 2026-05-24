import unittest
from pathlib import Path

from roger.pi_rpc.runner import PiAgentRunner
from roger.pi_rpc.sessions import PiSessionManager
from roger.routing.registry import SessionRegistry


class FakeClient:
    def __init__(self, collected_text="Hecho"):
        self.started = None
        self.prompted = None
        self.collected_text = collected_text
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

    def test_runner_strips_local_chat_template_tokens_from_collected_text(self):
        client = FakeClient(collected_text="ok<|im_end|>")
        registry = SessionRegistry.default(project_dir=Path("/tmp/project"))
        manager = PiSessionManager(registry=registry, session_dir=Path("/tmp/sessions"))
        runner = PiAgentRunner(session_manager=manager, client_factory=lambda command, cwd: client)

        result = runner.run_task("system", "responde exactamente: ok")

        self.assertEqual(result, "ok")

    def test_runner_strips_repeated_chat_transcript_from_local_model_response(self):
        client = FakeClient(collected_text="ok\nuser\nresponde exactamente: ok\nassistant\nok<|")
        registry = SessionRegistry.default(project_dir=Path("/tmp/project"))
        manager = PiSessionManager(registry=registry, session_dir=Path("/tmp/sessions"))
        runner = PiAgentRunner(session_manager=manager, client_factory=lambda command, cwd: client)

        result = runner.run_task("system", "responde exactamente: ok")

        self.assertEqual(result, "ok")

    def test_offline_runner_reports_llama_cpp_preflight_failure(self):
        registry = SessionRegistry.default(project_dir=Path("/tmp/project"))
        manager = PiSessionManager(registry=registry, session_dir=Path("/tmp/sessions"))
        runner = PiAgentRunner(
            session_manager=manager,
            client_factory=lambda command, cwd: FakeClient(),
            offline=True,
            preflight_check=lambda: "llama.cpp server unavailable at http://127.0.0.1:11434/v1",
        )

        with self.assertRaisesRegex(RuntimeError, "llama.cpp server unavailable"):
            runner.run_task("system", "responde exactamente: ok")

    def test_runner_rejects_empty_collected_response(self):
        client = FakeClient(collected_text="<|im_end|>")
        registry = SessionRegistry.default(project_dir=Path("/tmp/project"))
        manager = PiSessionManager(registry=registry, session_dir=Path("/tmp/sessions"))
        runner = PiAgentRunner(session_manager=manager, client_factory=lambda command, cwd: client)

        with self.assertRaisesRegex(RuntimeError, "pi-agent returned no response"):
            runner.run_task("system", "responde exactamente: ok")

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
