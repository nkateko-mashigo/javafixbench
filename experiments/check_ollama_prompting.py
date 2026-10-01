import json

import requests

BASE_URL = "http://127.0.0.1:11434"
MODEL = "gemma4:e2b-it-qat"

SYSTEM = "Your reply must be exactly SYSTEM_OK, with no other text."
PROMPT = "Your reply must be exactly USER_OK, with no other text."

COMMON = {
    "model": MODEL,
    "stream": False,
    "think": False,
    "options": {
        "temperature": 0.0,
        "num_ctx": 4096,
        "num_predict": 32,
        "seed": 42,
    },
}

CHECKS = (
    ("generate without system", "/api/generate",
     {"prompt": PROMPT}, "USER_OK"),
    ("generate with system", "/api/generate",
     {"prompt": PROMPT, "system": SYSTEM}, "SYSTEM_OK"),
    ("chat with system", "/api/chat",
     {"messages": [
         {"role": "system", "content": SYSTEM},
         {"role": "user", "content": PROMPT},
     ]}, "SYSTEM_OK"),
)


def main():
    for label, endpoint, extra, expected in CHECKS:
        print(f"\n--- {label} ---", flush=True)
        try:
            response = requests.post(
                BASE_URL + endpoint,
                json={**COMMON, **extra},
                timeout=900,
            )
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as error:
            print(f"Request failed: {error}")
            continue

        answer = (
            data.get("message", {}).get("content", "")
            if endpoint == "/api/chat"
            else data.get("response", "")
        )
        print(json.dumps({
            "answer": answer,
            "expected": expected,
            "exact_match": answer.strip() == expected,
            "done": data.get("done"),
            "done_reason": data.get("done_reason"),
            "prompt_tokens": data.get("prompt_eval_count"),
            "output_tokens": data.get("eval_count"),
            "error": data.get("error"),
        }, indent=2))


if __name__ == "__main__":
    main()