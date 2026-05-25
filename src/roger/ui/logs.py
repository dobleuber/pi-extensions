from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import re
from pathlib import Path
from typing import Any, Callable


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class TaskLogEvent:
    kind: str
    data: dict[str, Any]
    timestamp: str

    def to_json(self) -> dict[str, Any]:
        return {"kind": self.kind, "timestamp": self.timestamp, **self.data}


@dataclass
class ToolLog:
    name: str
    call_id: str
    args_summary: str = ""
    partial_output: str = ""
    final_output: str = ""
    is_error: bool = False


@dataclass
class TaskLog:
    session_name: str
    model_mode: str = "online"
    visible_limit: int = 4000
    clock: Callable[[], str] = _now_iso
    status: str = "pending"
    instruction: str = ""
    text: str = ""
    entries: list[str] = field(default_factory=list)
    events: list[TaskLogEvent] = field(default_factory=list)
    tools: dict[str, ToolLog] = field(default_factory=dict)
    started_at: str = ""
    completed_at: str = ""
    status_context: str = ""
    path: str = ""

    def start(self, instruction: str) -> None:
        self.status = "running"
        self.instruction = instruction
        self.started_at = self.clock()
        self.entries.append(f"started:{self.session_name}:{instruction}")
        self._append("start", {
            "session_name": self.session_name,
            "instruction": instruction,
            "model_mode": self.model_mode,
            "status": self.status,
        })

    def record_event(self, event: dict[str, Any]) -> None:
        event_type = event.get("type", "unknown")
        if event_type == "message_update":
            self._record_message_update(event)
            return
        if event_type.startswith("tool_execution"):
            self._record_tool_event(event_type, event)
            return
        if event_type in {"retry", "queue", "error"}:
            self.status_context = str(event.get("message") or event.get("error") or event_type)
            self._append(event_type, {"event": event})
            self.entries.append(event_type)
            return
        self.entries.append(event_type)
        self._append("event", {"event_type": event_type, "event": event})

    def complete(self) -> None:
        self.status = "complete"
        self.completed_at = self.clock()
        self.entries.append("complete")
        self._append("complete", {"status": self.status})

    def fail(self, message: str) -> None:
        self.status = "failed"
        self.status_context = message
        self.completed_at = self.clock()
        self.entries.append(f"failed:{message}")
        self._append("error", {"message": message, "status": self.status})

    def reject(self, message: str) -> None:
        self.fail(message)

    def render_visible(self) -> str:
        lines = [
            f"status: {self.status}",
            f"session: {self.session_name}",
            f"mode: {self.model_mode}",
        ]
        if self.status_context:
            lines.append(f"context: {self.status_context}")
        if self.text:
            lines.append("assistant:")
            lines.append(self.text)
        for tool in self.tools.values():
            output = tool.final_output or tool.partial_output
            suffix = " error" if tool.is_error else ""
            lines.append(f"tool {tool.name}{suffix}: {output}".strip())
        rendered = "\n".join(lines)
        if len(rendered) <= self.visible_limit:
            return rendered
        marker = "\n[truncated]"
        return rendered[: max(0, self.visible_limit - len(marker))] + marker

    def _record_message_update(self, event: dict[str, Any]) -> None:
        update = event.get("assistantMessageEvent", {})
        update_type = update.get("type")
        if update_type == "text_delta":
            delta = update.get("delta", "")
            self.text += delta
            self.entries.append(f"text:{delta}")
            self._append("assistant", {"delta": delta})
            return
        reason = update.get("reason")
        if reason in {"error", "abort", "aborted", "cancelled"}:
            self.status_context = str(reason)
        self.entries.append(f"message_update:{update_type or 'unknown'}")
        self._append("assistant_status", {"reason": reason, "update_type": update_type})

    def _record_tool_event(self, event_type: str, event: dict[str, Any]) -> None:
        name = str(event.get("toolName") or event.get("name") or "unknown")
        call_id = str(event.get("toolCallId") or event.get("id") or name)
        tool = self.tools.setdefault(call_id, ToolLog(name=name, call_id=call_id))
        if event_type == "tool_execution_start":
            tool.args_summary = _safe_args_summary(event.get("args") or event.get("arguments") or {})
            self._append("tool_start", {"tool_name": name, "tool_call_id": call_id, "args_summary": tool.args_summary})
        elif event_type == "tool_execution_update":
            tool.partial_output = str(event.get("partialResult") or event.get("partial_result") or "")
            self._append("tool_update", {"tool_name": name, "tool_call_id": call_id, "partial_output": tool.partial_output})
        elif event_type == "tool_execution_end":
            tool.final_output = str(event.get("result") or event.get("output") or "")
            tool.is_error = bool(event.get("isError", False))
            self._append("tool_end", {"tool_name": name, "tool_call_id": call_id, "output": tool.final_output, "is_error": tool.is_error})
        self.entries.append(f"{event_type}:{name}:{event.get('isError', '')}")

    def _append(self, kind: str, data: dict[str, Any]) -> None:
        self.events.append(TaskLogEvent(kind=kind, data=data, timestamp=self.clock()))


@dataclass
class TaskLogStore:
    root: Path = Path(".roger/logs")
    max_logs: int = 50

    def save(self, log: TaskLog) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / _log_filename(log)
        with path.open("w", encoding="utf-8") as file:
            for event in log.events:
                file.write(json.dumps(event.to_json(), ensure_ascii=False) + "\n")
        log.path = str(path)
        self.prune()
        return path

    def prune(self) -> None:
        files = sorted(self.root.glob("*.jsonl"), key=lambda path: (path.stat().st_mtime, path.name))
        for path in files[: max(0, len(files) - self.max_logs)]:
            path.unlink(missing_ok=True)


def _safe_args_summary(args: Any, max_chars: int = 240) -> str:
    if isinstance(args, str):
        summary = args
    else:
        summary = json.dumps(args, ensure_ascii=False, sort_keys=True, default=str)
    summary = re.sub(r'("?(?:password|token|secret|api_key)"?\s*[:=]\s*)"?[^",}\s]+"?', r"\1[redacted]", summary, flags=re.I)
    if len(summary) > max_chars:
        return summary[: max_chars - 1] + "…"
    return summary


def _log_filename(log: TaskLog) -> str:
    stamp = re.sub(r"[^0-9A-Za-z]+", "-", log.started_at or log.clock()).strip("-")
    session = re.sub(r"[^0-9A-Za-z_-]+", "-", log.session_name).strip("-") or "session"
    return f"{stamp}-{session}.jsonl"
