import unittest

from roger.daemon import RogerDaemon


class FailingLoop:
    def __init__(self):
        self.calls = 0

    def run_once(self):
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("stt failed")
        return type("Result", (), {"dispatched": False})()


class DaemonErrorsTests(unittest.TestCase):
    def test_daemon_continues_after_cycle_errors(self):
        loop = FailingLoop()
        errors = []
        daemon = RogerDaemon(loop=loop, on_error=lambda error: errors.append(str(error)))

        result = daemon.run(max_cycles=2, result_hold_seconds=0)

        self.assertEqual(result.status, "complete")
        self.assertEqual(result.cycles, 2)
        self.assertEqual(errors, ["stt failed"])


if __name__ == "__main__":
    unittest.main()
