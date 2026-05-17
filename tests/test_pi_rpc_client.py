import io
import json
import unittest

from roger.pi_rpc.client import PiRpcClient


class FakeStdin(io.StringIO):
    def __init__(self):
        super().__init__()
        self.flushed = False

    def flush(self):
        self.flushed = True


class FakeStdout:
    def __init__(self, lines):
        self._lines = iter(lines)

    def readline(self):
        return next(self._lines, "")


class FakeProcess:
    def __init__(self, stdout_lines):
        self.stdin = FakeStdin()
        self.stdout = FakeStdout(stdout_lines)
        self.terminated = False

    def terminate(self):
        self.terminated = True


class PiRpcClientTests(unittest.TestCase):
    def test_prompt_sends_jsonl_command_and_returns_matching_response(self):
        process = FakeProcess([
            json.dumps({"type": "response", "id": "req-1", "command": "prompt", "success": True}) + "\n"
        ])
        client = PiRpcClient(process_factory=lambda _: process)
        client.start(["pi", "--mode", "rpc"])

        response = client.prompt("Hola")

        sent = json.loads(process.stdin.getvalue().strip())
        self.assertEqual(sent["type"], "prompt")
        self.assertEqual(sent["message"], "Hola")
        self.assertEqual(sent["id"], "req-1")
        self.assertTrue(process.stdin.flushed)
        self.assertTrue(response["success"])

    def test_stream_until_agent_end_collects_text_deltas(self):
        process = FakeProcess([
            json.dumps({"type": "message_update", "assistantMessageEvent": {"type": "text_delta", "delta": "Hecho"}}) + "\n",
            json.dumps({"type": "agent_end"}) + "\n",
        ])
        client = PiRpcClient(process_factory=lambda _: process)
        client.start(["pi", "--mode", "rpc"])

        events = list(client.stream_until_agent_end())

        self.assertEqual(len(events), 2)
        self.assertEqual(client.collected_text, "Hecho")


if __name__ == "__main__":
    unittest.main()
