from __future__ import annotations

from dataclasses import dataclass

import requests

DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "gemma4:e2b-it-qat"


class OllamaError(RuntimeError):
    """Raised when JavaFixBench cannot communicate with Ollama."""


@dataclass(frozen=True)
class GenerationResult:
    text: str
    model: str
    prompt_tokens: int
    output_tokens: int
    duration_seconds: float


class OllamaClient:
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_OLLAMA_URL,
        timeout_seconds: int = 900,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def available_models(self) -> tuple[str, ...]:
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as error:
            raise OllamaError(
                f"Could not connect to Ollama: {error}"
            ) from error

        return tuple(
            sorted(
                item["name"]
                for item in payload.get("models", [])
                if item.get("name")
            )
        )

    def model_is_available(self) -> bool:
        models = self.available_models()

        return self.model in models or any(
            name.startswith(f"{self.model}:")
            for name in models
        )

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.0,
        context_size: int = 4096,
        max_tokens: int = 768,
        seed: int = 42,
    ) -> GenerationResult:
        payload: dict[str, object] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": {
                "temperature": temperature,
                "num_ctx": context_size,
                "num_predict": max_tokens,
                "seed": seed,
            },
        }

        if system:
            payload["system"] = system

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as error:
            raise OllamaError(
                f"Gemma generation failed: {error}"
            ) from error

        return GenerationResult(
            text=str(data.get("response", "")).strip(),
            model=str(data.get("model", self.model)),
            prompt_tokens=int(data.get("prompt_eval_count", 0)),
            output_tokens=int(data.get("eval_count", 0)),
            duration_seconds=(
                int(data.get("total_duration", 0)) / 1_000_000_000
            ),
        )