# LiteLLM Sandbox

A local playground for testing the [LiteLLM](https://docs.litellm.ai/) proxy: one OpenAI-compatible endpoint in front of OpenAI, Anthropic and Gemini models.

## Layout

```
litellm-sandbox/
├── litellm_config.yaml   # proxy model list + settings
├── .env.example          # template for API keys (copy to .env)
├── requirements.txt      # Python dependencies
├── test_litellm.py       # smoke test: chat completion through the proxy
└── README.md
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# generate a master key and paste it into LITELLM_MASTER_KEY in .env:
python -c "import secrets; print('sk-' + secrets.token_hex(32))"
# then add whichever provider keys you have
```

The proxy refuses to start without a master key (or with a well-known one like `sk-1234`), so this step is required even for the mock model.

## Run

Terminal 1 — start the proxy. `dotenv run` loads `.env` first; the `litellm` CLI doesn't reliably pick up a `.env` in your folder on its own:

```bash
dotenv run -- litellm --config litellm_config.yaml --port 4000
```

Terminal 2 — run the test:

```bash
python test_litellm.py                          # mock-model, no provider key needed
python test_litellm.py --model claude-sonnet
python test_litellm.py --model gpt-4o-mini --stream
python test_litellm.py --list-models
```

Or with curl:

```bash
curl http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "mock-model", "messages": [{"role": "user", "content": "hi"}]}'
```

## Adding a model

Add an entry under `model_list` in `litellm_config.yaml`. `model_name` is the alias clients use; `litellm_params.model` is `<provider>/<model-id>`. Restart the proxy afterwards.
