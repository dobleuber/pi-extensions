from __future__ import annotations

from pathlib import Path
from typing import Callable
from roger.pi_rpc.availability import (
    ModelAvailabilityMode,
    ModelAvailabilityPolicy,
    probe_llama_cpp_fallback,
)
from roger.pi_rpc.client import PiRpcClient
from roger.pi_rpc.sessions import PiSessionManager
from roger.ui.logs import TaskLog, TaskLogStore


_CHAT_TEMPLATE_TOKENS = (
    "<|im_end|>",
    "<|im_start|>",
    "<end_of_turn>",
    "<start_of_turn>",
)


def clean_model_response_text(text: str) -> str:
    cleaned = text
    for token in _CHAT_TEMPLATE_TOKENS:
        cleaned = cleaned.replace(token, "")
    for marker in ("\nuser\n", "\nassistant\n", "\nmodel\n", "<|"):
        if marker in cleaned:
            cleaned = cleaned.split(marker, 1)[0]
    return cleaned.strip()


class PiAgentRunner:
    def __init__(
        self,
        session_manager: PiSessionManager,
        client_factory: Callable[[list[str], Path], PiRpcClient] | None = None,
        offline: bool = False,
        preflight_check: Callable[[], str | None] | None = None,
        availability_policy: ModelAvailabilityPolicy | None = None,
        event_observer: Callable[[dict], None] | None = None,
        task_log_store: TaskLogStore | None = None,
    ):
        self.session_manager = session_manager
        self.client_factory = client_factory or self._default_client_factory
        self.offline = offline
        self.preflight_check = preflight_check
        self.availability_policy = availability_policy or ModelAvailabilityPolicy(explicit_offline=offline)
        self.event_observer = event_observer
        self.task_log_store = task_log_store
        self.last_task_log: TaskLog | None = None

    def run_task(self, session_name: str, instruction: str) -> str:
        decision = self.availability_policy.decide()
        if decision.mode == ModelAvailabilityMode.UNAVAILABLE:
            raise RuntimeError(decision.reason)
        offline = decision.mode == ModelAvailabilityMode.OFFLINE_FALLBACK
        try:
            return self._run_task_once(session_name, instruction, offline=offline)
        except Exception as error:
            if offline or not self.availability_policy.should_retry_offline(error):
                raise
            return self._run_task_once(session_name, instruction, offline=True)

    def _run_task_once(self, session_name: str, instruction: str, offline: bool) -> str:
        log = TaskLog(session_name=session_name, model_mode="offline-fallback" if offline else "online")
        log.start(instruction)
        self.last_task_log = log
        preflight_error = self._preflight_error(offline=offline)
        if preflight_error is not None:
            log.fail(preflight_error)
            self._persist_log(log)
            raise RuntimeError(preflight_error)
        command = self.session_manager.build_command(session_name, offline=offline)
        cwd = self.session_manager.cwd_for(session_name)
        client = self.client_factory(command, cwd)
        try:
            client.start(command)
            response = client.prompt(instruction)
            if not response.get("success"):
                message = response.get("error", "pi-agent rejected prompt")
                log.reject(message)
                self._persist_log(log)
                raise RuntimeError(message)
            for event in client.stream_until_agent_end():
                log.record_event(event)
                if self.event_observer is not None:
                    self.event_observer(event)
            text = clean_model_response_text(client.collected_text)
            if not text:
                message = "pi-agent returned no response"
                log.fail(message)
                self._persist_log(log)
                raise RuntimeError(message)
            log.complete()
            self._persist_log(log)
            return text
        except Exception as error:
            if log.status not in {"failed", "complete"}:
                log.fail(str(error))
                self._persist_log(log)
            raise
        finally:
            client.stop()

    def _preflight_error(self, offline: bool) -> str | None:
        if not offline:
            return None
        if self.preflight_check is not None:
            return self.preflight_check()
        if self.session_manager.offline_provider != "llama-cpp":
            return None
        return probe_llama_cpp_fallback(
            self.session_manager.offline_base_url,
            self.session_manager.offline_model,
        )

    def _persist_log(self, log: TaskLog) -> None:
        if self.task_log_store is not None:
            self.task_log_store.save(log)

    def _default_client_factory(self, command: list[str], cwd: Path) -> PiRpcClient:
        def process_factory(cmd: list[str]):
            import subprocess

            return subprocess.Popen(
                cmd,
                cwd=str(cwd),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

        timeout = self.session_manager.offline_timeout_seconds if "--offline" in command else None
        return PiRpcClient(process_factory=process_factory, event_timeout_seconds=timeout)
