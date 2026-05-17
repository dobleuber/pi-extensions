from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol


class Loop(Protocol):
    def run_once(self): ...


@dataclass(frozen=True)
class DaemonResult:
    status: str
    cycles: int
    dispatched: int


class RogerDaemon:
    def __init__(self, loop: Loop, before_cycle: Callable[[], None] | None = None):
        self.loop = loop
        self.before_cycle = before_cycle

    def run(self, max_cycles: int | None = None) -> DaemonResult:
        cycles = 0
        dispatched = 0
        try:
            while max_cycles is None or cycles < max_cycles:
                if self.before_cycle is not None:
                    self.before_cycle()
                result = self.loop.run_once()
                cycles += 1
                if getattr(result, "dispatched", False):
                    dispatched += 1
        except KeyboardInterrupt:
            return DaemonResult(status="interrupted", cycles=cycles, dispatched=dispatched)
        return DaemonResult(status="complete", cycles=cycles, dispatched=dispatched)
