from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TaskLog:
    session_name: str
    status: str = "pending"
    instruction: str = ""
    text: str = ""
    entries: list[str] = field(default_factory=list)

    def start(self, instruction: str) -> None:
        self.status = "running"
        self.instruction = instruction
        self.entries.append(f"started:{self.session_name}:{instruction}")

    def record_event(self, event: dict[str, Any]) -> None:
        event_type = event.get("type", "unknown")
        if event_type == "message_update":
            update = event.get("assistantMessageEvent", {})
            if update.get("type") == "text_delta":
                delta = update.get("delta", "")
                self.text += delta
                self.entries.append(f"text:{delta}")
                return
        if event_type.startswith("tool_execution"):
            self.entries.append(f"{event_type}:{event.get('toolName', 'unknown')}:{event.get('isError', '')}")
            return
        self.entries.append(event_type)

    def complete(self) -> None:
        self.status = "complete"
        self.entries.append("complete")

    def fail(self, message: str) -> None:
        self.status = "failed"
        self.entries.append(f"failed:{message}")
