import unittest

from roger import cli


class FakeOverlay:
    def __init__(self):
        self.calls = []

    def show(self, title, body, state="active", timeout_ms=None):
        self.calls.append((title, body, state, timeout_ms))


class CliOverlayDemoTests(unittest.TestCase):
    def test_overlay_demo_displays_sample_transcript_and_result(self):
        overlay = FakeOverlay()

        exit_code, output = cli.run(
            ["overlay-demo", "--transcript", "corre pwd", "--result", "Listo", "--duration", "0"],
            dependencies=cli.RuntimeDependencies(
                create_overlay_feedback=lambda config: __import__("roger.overlay", fromlist=["OverlayFeedback"]).OverlayFeedback(overlay),
            ),
        )

        self.assertEqual(exit_code, 0)
        self.assertIn("overlay demo sent", output)
        bodies = [call[1] for call in overlay.calls]
        self.assertIn("corre pwd", bodies)
        self.assertIn("Listo", bodies)


if __name__ == "__main__":
    unittest.main()
