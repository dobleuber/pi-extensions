from __future__ import annotations

from pathlib import Path
from typing import Callable

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
    return cleaned.strip()


class PiAgentRunner:
    def __init__(
        self,
        session_manager: PiSessionManager,
        client_factory: Callable[[list[str], Path], PiRpcClient] | None = None,
        offline: bool = False,
    ):
        self.session_manager = session_manager
        self.client_factory = client_factory or self._default_client_factory
        self.offline = offline

    def run_task(self, session_name: str, instruction: str) -> str:
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
            return clean_model_response_text(client.collected_text)
        finally:
            client.stop()

    @staticmethod
    def _default_client_factory(command: list[str], cwd: Path) -> PiRpcClient:
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

        return PiRpcClient(process_factory=process_factory)
