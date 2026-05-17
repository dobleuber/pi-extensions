import json
import unittest

from roger.overlay import GtkLayerShellFloatingOverlay


class FakeStdin:
    def __init__(self):
        self.lines = []
        self.flushed = False

    def write(self, text):
        self.lines.append(text)

    def flush(self):
        self.flushed = True


class FakeProcess:
    def __init__(self):
        self.stdin = FakeStdin()

    def poll(self):
        return None


class LayerShellProcessOverlayTests(unittest.TestCase):
    def test_layer_shell_overlay_sends_messages_to_external_helper_process(self):
        started = []
        process = FakeProcess()

        def start_process(command):
            started.append(command)
            return process

        overlay = GtkLayerShellFloatingOverlay(start_process=start_process, system_python="/usr/bin/python")

        overlay.show("Transcripción", "corre pwd", state="transcript")

        self.assertTrue(started)
        self.assertIn("overlay_layer_shell_helper.py", " ".join(started[0]))
        payload = json.loads(process.stdin.lines[0])
        self.assertEqual(payload["title"], "Transcripción")
        self.assertEqual(payload["body"], "corre pwd")
        self.assertEqual(payload["title_font"], "Sans Bold 36")
        self.assertEqual(payload["body_font"], "Sans 34")
        self.assertTrue(process.stdin.flushed)

    def test_layer_shell_overlay_can_hold_result_after_parent_exits(self):
        from roger.overlay_layer_shell_helper import quit_delay_after_stdin_close

        self.assertGreaterEqual(quit_delay_after_stdin_close(last_timeout_ms=15_000), 15_000)


if __name__ == "__main__":
    unittest.main()
