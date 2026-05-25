from __future__ import annotations

import json
import selectors
import subprocess
from typing import Any, Callable, Iterable, TextIO


class PiRpcClient:
    def __init__(
        self,
        process_factory: Callable[[list[str]], Any] | None = None,
        event_timeout_seconds: float | None = None,
    ):
        self._process_factory = process_factory or self._default_process_factory
        self.event_timeout_seconds = event_timeout_seconds
        self._process: Any | None = None
        self._next_id = 1
        self.collected_text = ""

    def start(self, command: list[str] | None = None) -> None:
        if self._process is not None:
            return
        self._process = self._process_factory(command or ["pi", "--mode", "rpc"])

    def prompt(
        self,
        message: str,
        streaming_behavior: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        command: dict[str, Any] = {
            "id": self._request_id(),
            "type": "prompt",
            "message": message,
        }
        if streaming_behavior is not None:
            command["streamingBehavior"] = streaming_behavior
        if metadata is not None:
            command["metadata"] = metadata
        self.send(command)
        return self.read_response(command["id"])

    def abort(self) -> dict[str, Any]:
        return self._control_command("abort")

    def abort_bash(self) -> dict[str, Any]:
        return self._control_command("abort_bash")

    def abort_retry(self) -> dict[str, Any]:
        return self._control_command("abort_retry")

    def send(self, command: dict[str, Any]) -> None:
        process = self._require_process()
        process.stdin.write(json.dumps(command, ensure_ascii=False) + "\n")
        process.stdin.flush()

    def read_response(self, request_id: str | None = None) -> dict[str, Any]:
        for event in self._read_events():
            if event.get("type") != "response":
                continue
            if request_id is None or event.get("id") == request_id:
                return event
        raise RuntimeError("pi RPC stream ended before response was received")

    def stream_until_agent_end(self) -> Iterable[dict[str, Any]]:
        for event in self._read_events():
            self._collect_text(event)
            yield event
            if event.get("type") == "agent_end":
                break

    def stop(self) -> None:
        if self._process is not None:
            self._process.terminate()
            self._process = None

    def _control_command(self, command_type: str) -> dict[str, Any]:
        command: dict[str, Any] = {"id": self._request_id(), "type": command_type}
        self.send(command)
        return self.read_response(command["id"])

    def _request_id(self) -> str:
        request_id = f"req-{self._next_id}"
        self._next_id += 1
        return request_id

    def _read_events(self) -> Iterable[dict[str, Any]]:
        process = self._require_process()
        while True:
            line = self._readline(process.stdout)
            if not line:
                break
            if isinstance(line, bytes):
                line = line.decode("utf-8")
            line = line.rstrip("\n")
            if line.endswith("\r"):
                line = line[:-1]
            if not line:
                continue
            yield json.loads(line)

    def _readline(self, stdout: TextIO) -> str:
        if self.event_timeout_seconds is None:
            return stdout.readline()
        try:
            fileno = stdout.fileno()
        except (AttributeError, OSError):
            return stdout.readline()
        selector = selectors.DefaultSelector()
        try:
            selector.register(fileno, selectors.EVENT_READ)
            if not selector.select(self.event_timeout_seconds):
                raise TimeoutError(f"Timed out waiting for pi RPC event after {self.event_timeout_seconds} seconds")
            return stdout.readline()
        finally:
            selector.close()

    def _collect_text(self, event: dict[str, Any]) -> None:
        if event.get("type") == "message_update":
            update = event.get("assistantMessageEvent", {})
            if update.get("type") == "text_delta":
                self.collected_text += update.get("delta", "")
            return
        if event.get("type") != "message_end":
            return
        message = event.get("message", {})
        if message.get("role") != "assistant":
            return
        text = self._extract_text_content(message.get("content"))
        if text.strip():
            self.collected_text = text

    def _extract_text_content(self, content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text" and isinstance(part.get("text"), str):
                    parts.append(part["text"])
            return "".join(parts)
        return ""

    def _require_process(self) -> Any:
        if self._process is None:
            raise RuntimeError("pi RPC client has not been started")
        return self._process

    @staticmethod
    def _default_process_factory(command: list[str]) -> subprocess.Popen[str]:
        return subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
