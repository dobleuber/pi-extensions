from __future__ import annotations

from pathlib import Path
from typing import Callable
from urllib.error import URLError
from urllib.request import urlopen

from roger.pi_rpc.client import PiRpcClient
from roger.pi_rpc.sessions import PiSessionManager


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
    ):
        self.session_manager = session_manager
        self.client_factory = client_factory or self._default_client_factory
        self.offline = offline
        self.preflight_check = preflight_check

    def run_task(self, session_name: str, instruction: str) -> str:
        preflight_error = self._preflight_error()
        if preflight_error is not None:
            raise RuntimeError(preflight_error)
        command = self.session_manager.build_command(session_name, offline=self.offline)
        cwd = self.session_manager.cwd_for(session_name)
        client = self.client_factory(command, cwd)
        try:
            client.start(command)
            response = client.prompt(instruction)
            if not response.get("success"):
                raise RuntimeError(response.get("error", "pi-agent rejected prompt"))
            for _event in client.stream_until_agent_end():
                pass
            text = clean_model_response_text(client.collected_text)
            if not text:
                raise RuntimeError("pi-agent returned no response")
            return text
        finally:
            client.stop()

    def _preflight_error(self) -> str | None:
        if not self.offline:
            return None
        if self.preflight_check is not None:
            return self.preflight_check()
        if self.session_manager.offline_provider != "llama-cpp":
            return None
        base_url = self.session_manager.offline_base_url
        if not base_url:
            return None
        url = base_url.rstrip("/") + "/models"
        try:
            with urlopen(url, timeout=2.0) as response:
                if response.status >= 400:
                    return f"llama.cpp server unavailable at {base_url}: HTTP {response.status}"
        except (OSError, URLError) as error:
            return f"llama.cpp server unavailable at {base_url}: {error}"
        return None

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

        timeout = self.session_manager.offline_timeout_seconds if self.offline else None
        return PiRpcClient(process_factory=process_factory, event_timeout_seconds=timeout)
