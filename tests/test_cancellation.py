import unittest
from pathlib import Path

from roger.dialogue import DialogueControl, DialogueDecision
from roger.pi_rpc.runner import CancellationResult, PiAgentRunner
from roger.pi_rpc.sessions import PiSessionManager
from roger.routing.registry import SessionRegistry
from roger import cli


class FakeAbortClient:
    def __init__(self, response=None):
        self.response = response or {"success": True}
        self.aborts = []

    def abort(self):
        self.aborts.append("abort")
        return self.response

    def abort_bash(self):
        self.aborts.append("abort_bash")
        return self.response

    def abort_retry(self):
        self.aborts.append("abort_retry")
        return self.response


class CancellationTests(unittest.TestCase):
    def test_dialogue_control_detects_stop_intent(self):
        control = DialogueControl()

        for text in ["para Roger", "cancela Roger", "detente roger", "stop roger"]:
            with self.subTest(text=text):
                self.assertEqual(control.decide(text), DialogueDecision.STOP)

    def test_runner_cancel_active_task_accepts_abort(self):
        registry = SessionRegistry.default(project_dir=Path("/tmp/project"))
        manager = PiSessionManager(registry=registry, session_dir=Path("/tmp/sessions"))
        runner = PiAgentRunner(session_manager=manager)
        client = FakeAbortClient()
        runner.track_active_task("system", "instala steam", client)

        result = runner.cancel_active("system")

        self.assertIsInstance(result, CancellationResult)
        self.assertTrue(result.accepted)
        self.assertEqual(result.status, "cancel_requested")
        self.assertEqual(client.aborts, ["abort"])

    def test_runner_reports_no_active_task(self):
        registry = SessionRegistry.default(project_dir=Path("/tmp/project"))
        manager = PiSessionManager(registry=registry, session_dir=Path("/tmp/sessions"))
        runner = PiAgentRunner(session_manager=manager)

        result = runner.cancel_active("system")

        self.assertFalse(result.accepted)
        self.assertEqual(result.status, "no_active_task")

    def test_runner_rejects_ambiguous_active_task_without_session(self):
        registry = SessionRegistry.default(project_dir=Path("/tmp/project"))
        manager = PiSessionManager(registry=registry, session_dir=Path("/tmp/sessions"))
        runner = PiAgentRunner(session_manager=manager)
        runner.track_active_task("system", "instala steam", FakeAbortClient())
        runner.track_active_task("current-project", "corre tests", FakeAbortClient())

        result = runner.cancel_active()

        self.assertFalse(result.accepted)
        self.assertEqual(result.status, "ambiguous_active_task")

    def test_runner_reports_rejected_abort(self):
        registry = SessionRegistry.default(project_dir=Path("/tmp/project"))
        manager = PiSessionManager(registry=registry, session_dir=Path("/tmp/sessions"))
        runner = PiAgentRunner(session_manager=manager)
        runner.track_active_task("system", "instala steam", FakeAbortClient({"success": False, "error": "no active operation"}))

        result = runner.cancel_active("system")

        self.assertFalse(result.accepted)
        self.assertEqual(result.status, "abort_rejected")
        self.assertIn("no active operation", result.message)

    def test_runner_reports_unavailable_abort_capability(self):
        registry = SessionRegistry.default(project_dir=Path("/tmp/project"))
        manager = PiSessionManager(registry=registry, session_dir=Path("/tmp/sessions"))
        runner = PiAgentRunner(session_manager=manager)
        runner.track_active_task("system", "instala steam", object())

        result = runner.cancel_active("system")

        self.assertFalse(result.accepted)
        self.assertEqual(result.status, "abort_unavailable")
        self.assertIn("unavailable", result.message)

    def test_runner_can_send_specific_bash_and_retry_abort_commands(self):
        for command in ["abort_bash", "abort_retry"]:
            with self.subTest(command=command):
                registry = SessionRegistry.default(project_dir=Path("/tmp/project"))
                manager = PiSessionManager(registry=registry, session_dir=Path("/tmp/sessions"))
                runner = PiAgentRunner(session_manager=manager)
                client = FakeAbortClient()
                runner.track_active_task("system", "instala steam", client)

                result = runner.cancel_active("system", command=command)

                self.assertTrue(result.accepted)
                self.assertEqual(client.aborts, [command])

    def test_cli_cancel_reports_runner_result(self):
        class FakeRunner:
            def cancel_active(self, session_name=None, command="abort"):
                return CancellationResult(status="cancel_requested", accepted=True, message="Cancellation accepted", session_name=session_name)

        exit_code, output = cli.run(
            ["cancel", "--session", "system"],
            dependencies=cli.RuntimeDependencies(create_pi_runner=lambda config, registry, offline=False: FakeRunner()),
        )

        self.assertEqual(exit_code, 0)
        self.assertIn("status: cancel_requested", output)
        self.assertIn("accepted: yes", output)


if __name__ == "__main__":
    unittest.main()
