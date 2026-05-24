import unittest

from roger.daemon import RogerDaemon


class FakeLoop:
    def __init__(self, results):
        self.results = list(results)
        self.calls = 0

    def run_once(self):
        self.calls += 1
        result = self.results.pop(0)
        if result is KeyboardInterrupt:
            raise KeyboardInterrupt
        return result


class Result:
    def __init__(self, dispatched=False, status="complete"):
        self.dispatched = dispatched
        self.status = status


class RogerDaemonTests(unittest.TestCase):
    def test_daemon_runs_until_max_cycles(self):
        loop = FakeLoop([Result(dispatched=True), Result(dispatched=False), Result(dispatched=True)])
        daemon = RogerDaemon(loop=loop)

        result = daemon.run(max_cycles=3)

        self.assertEqual(result.status, "complete")
        self.assertEqual(result.cycles, 3)
        self.assertEqual(result.dispatched, 2)
        self.assertEqual(loop.calls, 3)

    def test_daemon_runs_before_cycle_hook_each_cycle(self):
        loop = FakeLoop([Result(), Result()])
        calls = []
        daemon = RogerDaemon(loop=loop, before_cycle=lambda: calls.append("trigger"))

        daemon.run(max_cycles=2)

        self.assertEqual(calls, ["trigger", "trigger"])

    def test_daemon_handles_keyboard_interrupt_cleanly(self):
        loop = FakeLoop([Result(dispatched=True), KeyboardInterrupt])
        daemon = RogerDaemon(loop=loop)

        result = daemon.run(max_cycles=10)

        self.assertEqual(result.status, "interrupted")
        self.assertEqual(result.cycles, 1)
        self.assertEqual(result.dispatched, 1)

    def test_daemon_holds_result_between_cycles(self):
        loop = FakeLoop([Result(dispatched=True), Result(dispatched=False)])
        sleeps = []
        daemon = RogerDaemon(loop=loop, sleep=sleeps.append)

        daemon.run(max_cycles=2, result_hold_seconds=8)

        self.assertEqual(sleeps, [8, 8])

    def test_daemon_does_not_hold_no_input_cycles(self):
        loop = FakeLoop([Result(status="no_input"), Result(dispatched=True)])
        sleeps = []
        daemon = RogerDaemon(loop=loop, sleep=sleeps.append)

        daemon.run(max_cycles=2, result_hold_seconds=8, quick_close_seconds=2.5)

        self.assertEqual(sleeps, [2.5, 8])


if __name__ == "__main__":
    unittest.main()
