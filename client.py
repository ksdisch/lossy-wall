"""client.py — minimal OpenRouter client for lossy-wall (ported from decay-pin's client.py).

A thin wrapper over the OpenRouter Chat Completions API (which is OpenAI-compatible).
The model slug is a required per-call argument — an arm's model is an experimental
variable here, and requiring it explicitly means no run can silently use the wrong one.

    from client import chat, MODELS
    resp = chat([{"role": "user", "content": "hi"}], model=MODELS["llama"])

lossy-wall's calls are plain message lists: session-1 drift induction and the session-2
[system, note, correction] frame. No tools, no agent loop — that part of decay-pin was
deliberately not ported (wrong shape for a two-session experiment).
"""
from __future__ import annotations

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # load lossy-wall/.env into the environment

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# The paper trio (KICKOFF.md D3). Slugs are OpenRouter model ids; they are verified
# against the live model list by ping.py before any arm spends tokens — if OpenRouter
# names one differently, fix it HERE and nowhere else.
MODELS = {
    "llama": "meta-llama/llama-3.1-8b-instruct",
    "deepseek": "deepseek/deepseek-chat",
    "qwen": "qwen/qwen-2.5-7b-instruct",
}

# Per-model request extras, reasoning ("thinking") config above all. decay-pin found two
# of its models think BY DEFAULT and burn the completion budget on hidden reasoning — at
# small max_tokens the visible answer comes back truncated or empty, silently biasing
# outcomes. Our trio predates that behavior (plain chat models), so all three start with
# no extra config; ping.py re-establishes this empirically (an empty/truncated pong is
# the tell), and any needed switch gets recorded HERE with the ping date.
MODEL_EXTRA_BODY: dict[str, dict] = {
    "meta-llama/llama-3.1-8b-instruct": {},
    "deepseek/deepseek-chat": {},
    "qwen/qwen-2.5-7b-instruct": {},
}


def reasoning_mode(model: str) -> str:
    """Human-readable reasoning config for a model, for run headers/logs."""
    extra = MODEL_EXTRA_BODY.get(model, {})
    if extra.get("reasoning", {}).get("enabled") is False:
        return "disabled"
    return "provider-default"


# Optional OpenRouter attribution headers (they show up on your activity page).
_DEFAULT_HEADERS = {
    "HTTP-Referer": os.getenv("OPENROUTER_APP_URL", "https://localhost/lossy-wall"),
    "X-Title": os.getenv("OPENROUTER_APP_TITLE", "lossy-wall"),
}


def client() -> OpenAI:
    """Return an OpenAI SDK client pointed at OpenRouter.

    Fails loudly with a setup hint if the key is missing, so a broken .env is
    obvious instead of producing a confusing 401 deep in your code.
    """
    key = os.getenv("OPENROUTER_API_KEY")
    if not key or "REPLACE" in key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Copy .env.example to .env and put "
            "your key in lossy-wall/.env (see README.md)."
        )
    return OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=key,
        default_headers=_DEFAULT_HEADERS,
        # Provider rate-limits (429) and transient 5xx are common on cheap/shared OpenRouter
        # routes; let the SDK ride them out with exponential backoff so a blip doesn't abort
        # a whole N-trial arm. HTTP-layer hygiene, not part of the experiment.
        max_retries=8,
    )


def chat(messages, *, model: str, **kwargs):
    """One-shot chat completion against `model`. Returns the full response object.

    `model` is required on purpose (see module docstring). `kwargs` are forwarded to the
    API (e.g. temperature, max_tokens). The per-model config (MODEL_EXTRA_BODY) is applied
    automatically; pass `extra_body=...` explicitly to override it.
    """
    if "extra_body" not in kwargs:
        extra = MODEL_EXTRA_BODY.get(model, {})
        if extra:
            kwargs["extra_body"] = extra
    return client().chat.completions.create(
        model=model,
        messages=messages,
        **kwargs,
    )
