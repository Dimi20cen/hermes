import json
import subprocess
import tempfile
from pathlib import Path

from app.config import Settings
from app.providers.base import ProviderError, ProviderRequest, ProviderResult
from app.schemas import Message


def _messages_to_prompt(messages: list[Message]) -> str:
    return "\n\n".join(f"{message.role.upper()}:\n{message.content}" for message in messages)


class CodexCLIProvider:
    name = "codex_cli"

    def __init__(self, settings: Settings):
        self.settings = settings

    def _check_version(self) -> None:
        if not self.settings.codex_expected_version:
            return
        try:
            result = subprocess.run(
                [self.settings.codex_command, "--version"],
                text=True,
                capture_output=True,
                check=True,
            )
        except FileNotFoundError as exc:
            raise ProviderError(
                f"Codex CLI not found at '{self.settings.codex_command}'."
            ) from exc
        except subprocess.CalledProcessError as exc:
            details = (exc.stderr or exc.stdout or str(exc)).strip()
            raise ProviderError(f"Could not read Codex CLI version: {details}") from exc

        version = (result.stdout or result.stderr or "").strip()
        if version == self.settings.codex_expected_version:
            return
        if self.settings.codex_version_strict:
            raise ProviderError(
                f"Codex CLI version mismatch: expected '{self.settings.codex_expected_version}', got '{version}'."
            )

    def _base_command(self, output_path: Path) -> list[str]:
        command = [
            self.settings.codex_command,
            "exec",
            "--skip-git-repo-check",
            "--sandbox",
            self.settings.codex_sandbox,
            "--output-last-message",
            str(output_path),
            "-",
        ]
        if self.settings.codex_model:
            command[2:2] = ["--model", self.settings.codex_model]
        if self.settings.codex_profile:
            command[2:2] = ["--profile", self.settings.codex_profile]
        return command

    def _run(self, prompt: str, extra_args: list[str] | None = None) -> str:
        self._check_version()
        with tempfile.TemporaryDirectory(prefix="hermes-codex-") as temp_dir:
            temp_path = Path(temp_dir)
            output_path = temp_path / "output.txt"
            command = self._base_command(output_path)
            if extra_args:
                command[2:2] = extra_args
            try:
                subprocess.run(
                    command,
                    input=prompt,
                    text=True,
                    capture_output=True,
                    cwd=self.settings.codex_workdir,
                    timeout=self.settings.codex_timeout_seconds,
                    check=True,
                )
            except FileNotFoundError as exc:
                raise ProviderError(
                    f"Codex CLI not found at '{self.settings.codex_command}'."
                ) from exc
            except subprocess.TimeoutExpired as exc:
                raise ProviderError(
                    f"Codex generation timed out after {self.settings.codex_timeout_seconds} seconds."
                ) from exc
            except subprocess.CalledProcessError as exc:
                details = (exc.stderr or exc.stdout or str(exc)).strip()
                raise ProviderError(f"Codex execution failed: {details}") from exc

            if not output_path.exists():
                raise ProviderError("Codex did not produce an output payload.")
            return output_path.read_text(encoding="utf-8").strip()

    def chat(self, request: ProviderRequest) -> ProviderResult:
        prompt = (
            "You are Hermes, a thin AI gateway. Return only the answer text.\n\n"
            f"{_messages_to_prompt(request.messages)}"
        )
        content = self._run(prompt)
        if not content:
            raise ProviderError("Codex returned an empty completion.")
        used_model = self.settings.codex_model or "codex-cli"
        return ProviderResult(provider=self.name, used_model=used_model, content=content)

    def structured(self, request: ProviderRequest, schema: dict) -> ProviderResult:
        schema_text = json.dumps(schema, ensure_ascii=True)
        prompt = (
            "You are Hermes, a thin AI gateway. Return only valid JSON matching the schema.\n\n"
            f"Schema:\n{schema_text}\n\n"
            f"{_messages_to_prompt(request.messages)}"
        )
        with tempfile.TemporaryDirectory(prefix="hermes-codex-") as temp_dir:
            temp_path = Path(temp_dir)
            output_path = temp_path / "output.txt"
            schema_path = temp_path / "schema.json"
            schema_path.write_text(json.dumps(schema), encoding="utf-8")
            command = self._base_command(output_path)
            command[2:2] = ["--output-schema", str(schema_path)]
            try:
                subprocess.run(
                    command,
                    input=prompt,
                    text=True,
                    capture_output=True,
                    cwd=self.settings.codex_workdir,
                    timeout=self.settings.codex_timeout_seconds,
                    check=True,
                )
            except FileNotFoundError as exc:
                raise ProviderError(
                    f"Codex CLI not found at '{self.settings.codex_command}'."
                ) from exc
            except subprocess.TimeoutExpired as exc:
                raise ProviderError(
                    f"Codex generation timed out after {self.settings.codex_timeout_seconds} seconds."
                ) from exc
            except subprocess.CalledProcessError as exc:
                details = (exc.stderr or exc.stdout or str(exc)).strip()
                raise ProviderError(f"Codex execution failed: {details}") from exc
            if not output_path.exists():
                raise ProviderError("Codex did not produce an output payload.")
            content = output_path.read_text(encoding="utf-8").strip()
        if not content:
            raise ProviderError("Codex returned an empty structured completion.")
        used_model = self.settings.codex_model or "codex-cli"
        return ProviderResult(provider=self.name, used_model=used_model, content=content)

