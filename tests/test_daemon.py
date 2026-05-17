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
    def __init__(self, dispatched=False):
        self.dispatched = dispatched


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


if __name__ == "__main__":
    unittest.main()
