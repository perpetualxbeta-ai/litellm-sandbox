"""Smoke test for the zero-cost LiteLLM proxy sandbox.

Usage:
    python test_litellm.py                          # mock-model: no key, no network
    python test_litellm.py --model openrouter-free
    python test_litellm.py --model groq-gpt-oss-20b --stream
    python test_litellm.py --list-models
    python test_litellm.py --all                    # try every model, print a summary
"""

import argparse
import os
import sys
import time

from dotenv import load_dotenv
from openai import APIConnectionError, APIStatusError, OpenAI

load_dotenv()

PROXY_URL = os.getenv("LITELLM_PROXY_URL", "http://localhost:4000")
MASTER_KEY = os.getenv("LITELLM_MASTER_KEY")


def chat(client: OpenAI, model: str, prompt: str, stream: bool) -> None:
    messages = [{"role": "user", "content": prompt}]
    start = time.perf_counter()
    if stream:
        for chunk in client.chat.completions.create(model=model, messages=messages, stream=True):
            if chunk.choices and chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
        print()
    else:
        resp = client.chat.completions.create(model=model, messages=messages)
        print(resp.choices[0].message.content)
        if resp.usage:
            print(f"\nTokens: prompt={resp.usage.prompt_tokens} "
                  f"completion={resp.usage.completion_tokens} total={resp.usage.total_tokens}")
        print(f"Served by: {resp.model}")
    print(f"Latency: {time.perf_counter() - start:.2f}s")


def short_error(e: APIStatusError) -> str:
    try:
        msg = e.response.json()["error"]["message"]
    except Exception:
        msg = e.response.text
    return f"HTTP {e.status_code}: {msg.splitlines()[0][:140]}"


def run_all(client: OpenAI, prompt: str) -> int:
    models = [m.id for m in client.models.list().data]
    results = []
    for model in models:
        start = time.perf_counter()
        try:
            resp = client.chat.completions.create(
                model=model, messages=[{"role": "user", "content": prompt}], max_tokens=200
            )
            reply = (resp.choices[0].message.content or "").strip().replace("\n", " ")
            results.append((model, True, f"{time.perf_counter() - start:.1f}s  {reply[:60]}"))
        except APIStatusError as e:
            results.append((model, False, short_error(e)))
    print()
    for model, ok, detail in results:
        print(f"{'✅' if ok else '❌'} {model:<20} {detail}")
    return 0 if any(ok for _, ok, _ in results) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test the LiteLLM proxy.")
    parser.add_argument("--model", default="mock-model", help="model_name from litellm_config.yaml")
    parser.add_argument("--prompt", default="Say hello in one short sentence.")
    parser.add_argument("--stream", action="store_true", help="stream the response")
    parser.add_argument("--list-models", action="store_true", help="list models the proxy exposes")
    parser.add_argument("--all", action="store_true", help="try every model and summarise")
    args = parser.parse_args()

    if not MASTER_KEY:
        print("❌ LITELLM_MASTER_KEY is not set. Add it to .env (see .env.example).")
        return 1

    client = OpenAI(base_url=PROXY_URL, api_key=MASTER_KEY)
    print(f"Proxy: {PROXY_URL}")

    try:
        if args.list_models:
            for m in client.models.list().data:
                print(f"  - {m.id}")
            return 0
        if args.all:
            return run_all(client, args.prompt)

        print(f"Model: {args.model}\nPrompt: {args.prompt}\n")
        chat(client, args.model, args.prompt, args.stream)
        print("\n✅ Success")
        return 0

    except APIConnectionError:
        print(f"❌ Could not reach the proxy at {PROXY_URL}. Is it running?\n"
              "   Start it with: dotenv run -- litellm --config litellm_config.yaml --port 4000")
    except APIStatusError as e:
        print(f"❌ Proxy returned {short_error(e)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
