# LiteLLM Sandbox (zero-cost)

A local playground for the [LiteLLM](https://docs.litellm.ai/) proxy using only free models: one OpenAI-compatible endpoint in front of a local Ollama model and an OpenRouter free model, with automatic fallback between them.

## Layout

```
litellm-sandbox/
├── litellm_config.yaml   # model aliases, fallback, master key
├── .env.example          # master key for the test script + optional OpenRouter key
├── requirements.txt      # Python dependencies
├── test_litellm.py       # smoke test: chat completion through the proxy
└── README.md
```

## Models

| Alias | Backend | Needs |
|---|---|---|
| `free-local` | `ollama/llama3.2` at `http://localhost:11434` | [Ollama](https://ollama.com) + `ollama pull llama3.2` |
| `free-cloud` | `openrouter/meta-llama/llama-3.3-70b-instruct:free` | free `OPENROUTER_API_KEY` |

If `free-cloud` fails (for example, a 429 rate limit), the proxy retries the request on `free-local` straight away.

> **Heads-up:** OpenRouter retired `meta-llama/llama-3.3-70b-instruct:free` on 2026-07-19, so `free-cloud` currently always falls back to `free-local`. For a working free cloud model, change its `model:` to `openrouter/openrouter/free` (OpenRouter's free auto-router). The swap is noted in the config.

The proxy's master key is `sk-local-free`. That's fine for a machine-local sandbox; don't expose the proxy on a network with it.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # optionally add OPENROUTER_API_KEY

ollama pull llama3.2               # for free-local
```

## Run

Terminal 1, start the proxy. `dotenv run` loads `.env`, which the `litellm` CLI doesn't reliably find on its own:

```bash
dotenv run -- litellm --config litellm_config.yaml --port 4000
```

Terminal 2, run the test:

```bash
python test_litellm.py                          # free-local
python test_litellm.py --model free-cloud       # "Served by" shows if it fell back
python test_litellm.py --all                    # try every model
```

Or with curl. The `x-litellm-attempted-fallbacks` response header shows when a fallback happened:

```bash
curl -i http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer sk-local-free" \
  -H "Content-Type: application/json" \
  -d '{"model": "free-cloud", "messages": [{"role": "user", "content": "hi"}]}'
```

## Adding a free model

Browse [OpenRouter's free models](https://openrouter.ai/collections/free-models) (IDs end in `:free`; the lineup changes every few weeks), add an entry under `model_list`, and restart the proxy.
