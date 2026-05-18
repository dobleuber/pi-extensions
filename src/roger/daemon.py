from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Callable, Protocol


class Loop(Protocol):
    def run_once(self): ...


@dataclass(frozen=True)
class DaemonResult:
    status: str
    cycles: int
    dispatched: int


class RogerDaemon:
    def __init__(
        self,
        loop: Loop,
        before_cycle: Callable[[], None] | None = None,
        sleep: Callable[[float], None] = time.sleep,
        on_error: Callable[[Exception], None] | None = None,
    ):
        self.loop = loop
        self.before_cycle = before_cycle
        self.sleep = sleep
        self.on_error = on_error

    def run(
        self,
        max_cycles: int | None = None,
        result_hold_seconds: float = 0.0,
        quick_close_seconds: float = 2.5,
    ) -> DaemonResult:
        cycles = 0
        dispatched = 0
        try:
            while max_cycles is None or cycles < max_cycles:
                if self.before_cycle is not None:
                    self.before_cycle()
                try:
                    result = self.loop.run_once()
                except Exception as error:
                    if self.on_error is not None:
                        self.on_error(error)
                    cycles += 1
                    if result_hold_seconds > 0:
                        self.sleep(result_hold_seconds)
                    continue
                cycles += 1
                if getattr(result, "dispatched", False):
                    dispatched += 1
                status = getattr(result, "status", "")
                if status in {"no_input", "goodbye"} and quick_close_seconds > 0:
                    self.sleep(quick_close_seconds)
                elif result_hold_seconds > 0:
                    self.sleep(result_hold_seconds)
        except KeyboardInterrupt:
            return DaemonResult(status="interrupted", cycles=cycles, dispatched=dispatched)
        return DaemonResult(status="complete", cycles=cycles, dispatched=dispatched)
