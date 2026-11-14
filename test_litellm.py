"""Quick smoke test for the local LiteLLM proxy.

Usage:
    python test_litellm.py                         # mock-model, no provider key needed
    python test_litellm.py --model claude-sonnet
    python test_litellm.py --model gpt-4o-mini --stream
    python test_litellm.py --list-models
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


def main() -> int:
    if not MASTER_KEY:
        print("❌ LITELLM_MASTER_KEY is not set. Add it to .env (see .env.example).")
        return 1

    parser = argparse.ArgumentParser(description="Smoke-test the LiteLLM proxy.")
    parser.add_argument("--model", default="mock-model", help="model_name from litellm_config.yaml")
    parser.add_argument("--prompt", default="Say hello in one short sentence.")
    parser.add_argument("--stream", action="store_true", help="stream the response")
    parser.add_argument("--list-models", action="store_true", help="list models the proxy exposes")
    args = parser.parse_args()

    client = OpenAI(base_url=PROXY_URL, api_key=MASTER_KEY)
    print(f"Proxy: {PROXY_URL}")

    try:
        if args.list_models:
            for m in client.models.list().data:
                print(f"  - {m.id}")
            return 0

        print(f"Model: {args.model}\nPrompt: {args.prompt}\n")
        messages = [{"role": "user", "content": args.prompt}]
        start = time.perf_counter()

        if args.stream:
            stream = client.chat.completions.create(model=args.model, messages=messages, stream=True)
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    print(chunk.choices[0].delta.content, end="", flush=True)
            print()
        else:
            resp = client.chat.completions.create(model=args.model, messages=messages)
            print(resp.choices[0].message.content)
            if resp.usage:
                print(
                    f"\nTokens: prompt={resp.usage.prompt_tokens} "
                    f"completion={resp.usage.completion_tokens} total={resp.usage.total_tokens}"
                )
            print(f"Served by: {resp.model}")

        print(f"Latency: {time.perf_counter() - start:.2f}s")
        print("\n✅ Success")
        return 0

    except APIConnectionError:
        print(f"❌ Could not reach the proxy at {PROXY_URL}. Is it running?\n"
              "   Start it with: dotenv run -- litellm --config litellm_config.yaml --port 4000")
    except APIStatusError as e:
        print(f"❌ Proxy returned HTTP {e.status_code}:\n{e.response.text}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
