# LiteLLM Sandbox (zero-cost)

A local playground for the [LiteLLM](https://docs.litellm.ai/) proxy that uses only free models: one OpenAI-compatible endpoint in front of a mock model, a local Ollama model, and the OpenRouter and Groq free tiers.

## Layout

```
litellm-sandbox/
├── litellm_config.yaml   # free models, fallbacks, proxy settings
├── .env.example          # master key + optional free OpenRouter/Groq keys
├── requirements.txt      # Python dependencies
├── test_litellm.py       # smoke test: chat completion through the proxy
└── README.md
```

## Models

| Alias | Backend | Needs |
|---|---|---|
| `mock-model` | Canned reply from LiteLLM | nothing |
| `local-llama` | Ollama `llama3.2` on your machine | [Ollama](https://ollama.com) + `ollama pull llama3.2` |
| `openrouter-free` | OpenRouter's free auto-router | free `OPENROUTER_API_KEY` |
| `openrouter-gpt-oss` | `openai/gpt-oss-120b:free` on OpenRouter | free `OPENROUTER_API_KEY` |
| `groq-gpt-oss-20b` | Groq free tier | free `GROQ_API_KEY` |
| `groq-gpt-oss-120b` | Groq free tier | free `GROQ_API_KEY` |

Free tiers are rate-limited (OpenRouter free models: about 20 requests/min and 50/day on a new account), and free model IDs change from time to time. The config sets fallbacks between providers, and `python test_litellm.py --all` shows which models are answering right now.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# generate a master key and paste it into LITELLM_MASTER_KEY in .env:
python -c "import secrets; print('sk-' + secrets.token_hex(32))"
# optionally add free OpenRouter / Groq keys
```

The proxy won't start without a master key, or with a well-known one like `sk-1234`, so you need one even for the mock model.

## Run

Terminal 1, start the proxy (`dotenv run` loads `.env`, which the `litellm` CLI doesn't reliably find on its own):

```bash
dotenv run -- litellm --config litellm_config.yaml --port 4000
```

Terminal 2, run the test:

```bash
python test_litellm.py                          # mock-model
python test_litellm.py --model local-llama      # Ollama
python test_litellm.py --model openrouter-free --stream
python test_litellm.py --all                    # try every model
```

Or with curl:

```bash
curl http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "mock-model", "messages": [{"role": "user", "content": "hi"}]}'
```

## Adding a free model

Browse [OpenRouter's free models](https://openrouter.ai/collections/free-models) (IDs end in `:free`) or [Groq's model list](https://console.groq.com/docs/models), add an entry under `model_list`, and restart the proxy.
