"""Smoke test for the zero-cost LiteLLM proxy sandbox.

Sends a chat completion through the proxy (OpenAI SDK -> http://localhost:4000/v1)
to each model alias and prints a pass/fail summary.

Usage:
    python test_litellm.py                         # test free-local and free-cloud
    python test_litellm.py --models free-cloud     # test one alias
    python test_litellm.py --stream                # stream the replies
"""

import argparse
import os
import sys
import time

from dotenv import load_dotenv
from openai import APIConnectionError, APIStatusError, OpenAI

load_dotenv()

BASE_URL = os.getenv("LITELLM_PROXY_URL", "http://localhost:4000/v1")
MASTER_KEY = os.getenv("LITELLM_MASTER_KEY", "sk-local-free")
DEFAULT_MODELS = ["free-local", "free-cloud"]


def short_error(e: APIStatusError) -> str:
    try:
        msg = e.response.json()["error"]["message"]
    except Exception:
        msg = e.response.text
    return f"HTTP {e.status_code}: {msg.splitlines()[0][:160]}"


def test_model(client: OpenAI, model: str, prompt: str, stream: bool) -> tuple[bool, str]:
    print(f"\n=== {model} ===")
    messages = [{"role": "user", "content": prompt}]
    start = time.perf_counter()
    try:
        if stream:
            served_by = None
            for chunk in client.chat.completions.create(model=model, messages=messages, stream=True):
                served_by = served_by or chunk.model
                if chunk.choices and chunk.choices[0].delta.content:
                    print(chunk.choices[0].delta.content, end="", flush=True)
            print()
        else:
            raw = client.chat.completions.with_raw_response.create(model=model, messages=messages)
            resp = raw.parse()
            served_by = resp.model
            print(resp.choices[0].message.content)
            if raw.headers.get("x-litellm-attempted-fallbacks", "0") not in ("0", ""):
                served_by += f" (fell back to {raw.headers.get('x-litellm-model-group')})"
        elapsed = time.perf_counter() - start
        print(f"Served by: {served_by}  |  {elapsed:.2f}s")
        return True, f"{elapsed:.1f}s, served by {served_by}"
    except APIStatusError as e:
        print(f"❌ {short_error(e)}")
        return False, short_error(e)


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test the LiteLLM proxy.")
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS, help="model aliases to test")
    parser.add_argument("--prompt", default="Say hello in one short sentence.")
    parser.add_argument("--stream", action="store_true", help="stream the replies")
    args = parser.parse_args()

    client = OpenAI(base_url=BASE_URL, api_key=MASTER_KEY)
    print(f"Proxy: {BASE_URL}")

    try:
        available = {m.id for m in client.models.list().data}
    except APIConnectionError:
        print(f"❌ Could not reach the proxy at {BASE_URL}. Is it running?\n"
              "   Start it with: dotenv run -- litellm --config litellm_config.yaml --port 4000")
        return 1
    except APIStatusError as e:
        print(f"❌ Proxy rejected the request: {short_error(e)}")
        return 1
    print(f"Models on proxy: {', '.join(sorted(available))}")

    results = {}
    for model in args.models:
        if model not in available:
            results[model] = (False, "not in litellm_config.yaml")
            continue
        results[model] = test_model(client, model, args.prompt, args.stream)

    print("\n=== Summary ===")
    for model, (ok, detail) in results.items():
        print(f"{'✅' if ok else '❌'} {model:<12} {detail}")
    return 0 if all(ok for ok, _ in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
