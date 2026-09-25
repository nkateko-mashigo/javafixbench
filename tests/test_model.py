from javafixbench.model import OllamaClient


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self.payload


def test_lists_available_models(monkeypatch) -> None:
    def fake_get(url: str, timeout: int) -> FakeResponse:
        return FakeResponse(
            {
                "models": [
                    {"name": "gemma4:e2b-it-qat"},
                    {"name": "llama3.2:3b"},
                ]
            }
        )

    monkeypatch.setattr(
        "javafixbench.model.requests.get",
        fake_get,
    )

    client = OllamaClient()

    assert client.available_models() == (
        "gemma4:e2b-it-qat",
        "llama3.2:3b",
    )


def test_generates_without_thinking(monkeypatch) -> None:
    captured: dict = {}

    def fake_post(
        url: str,
        json: dict,
        timeout: int,
    ) -> FakeResponse:
        captured["payload"] = json

        return FakeResponse(
            {
                "model": "gemma4:e2b-it-qat",
                "response": "JavaFixBench ready",
                "prompt_eval_count": 10,
                "eval_count": 5,
                "total_duration": 2_000_000_000,
            }
        )

    monkeypatch.setattr(
        "javafixbench.model.requests.post",
        fake_post,
    )

    result = OllamaClient().generate("Test prompt")

    assert result.text == "JavaFixBench ready"
    assert result.output_tokens == 5
    assert result.duration_seconds == 2.0
    assert captured["payload"]["think"] is False
    assert captured["payload"]["options"]["num_ctx"] == 4096