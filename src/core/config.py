"""
Lab 11 — Configuration & API Key Setup

Two LLM backends are supported:
  1. Custom OpenAI-compatible provider (OmniRoute) — set LLM_ENDPOINT / API_KEY /
     MODEL in a .env file. Routed through ADK's LiteLlm. This avoids the Google
     free-tier rate limits and lets the whole lab run locally.
  2. Google Gemini direct — set GOOGLE_API_KEY (Colab-style). Used as the fallback
     when no custom provider is configured.
"""
import os

# Load .env (same LLM_ENDPOINT / API_KEY / MODEL convention as Day 03/04/09).
# Look in the cwd AND at the repo root (this file is src/core/config.py), so it works
# whether you run `python main.py` from src/ or a script from the repo root.
try:
    from pathlib import Path
    from dotenv import load_dotenv
    load_dotenv()
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
except Exception:
    pass


def _custom_endpoint():
    return os.getenv("CUSTOM_BASE_URL") or os.getenv("LLM_ENDPOINT")


def _custom_key():
    return os.getenv("CUSTOM_API_KEY") or os.getenv("API_KEY")


def _custom_model():
    return os.getenv("CUSTOM_MODEL") or os.getenv("MODEL")


def using_custom_provider() -> bool:
    """True if an OmniRoute / OpenAI-compatible provider is configured in .env."""
    return bool(_custom_endpoint() and _custom_key())


def setup_api_key():
    """Load credentials. Prefer the custom provider; else fall back to GOOGLE_API_KEY."""
    if using_custom_provider():
        print(f"Using custom LLM provider (OmniRoute) @ {_custom_endpoint()} "
              f"| model={_custom_model()}")
        return
    if "GOOGLE_API_KEY" not in os.environ:
        os.environ["GOOGLE_API_KEY"] = input("Enter Google API Key: ")
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "0"
    print("API key loaded (Google Gemini).")


def get_model(default: str = "gemini-2.5-flash-lite"):
    """Return the model to pass to an ADK LlmAgent.

    - Custom provider configured -> ADK LiteLlm pointing at OmniRoute (OpenAI-compatible),
      so every agent/judge in the lab is served by the router (no Gemini rate limits).
    - Otherwise -> a plain Gemini model-name string (ADK resolves it via GOOGLE_API_KEY).
    """
    if using_custom_provider():
        from google.adk.models.lite_llm import LiteLlm
        return LiteLlm(
            model=f"openai/{_custom_model() or default}",
            api_base=_custom_endpoint(),
            api_key=_custom_key(),
        )
    return default


def get_openai_client():
    """Return (openai.OpenAI, model) for the custom provider, or (None, None).

    Used for raw text generation (e.g. AI-generated attacks) that does not need ADK.
    """
    if not using_custom_provider():
        return None, None
    from openai import OpenAI
    return OpenAI(base_url=_custom_endpoint(), api_key=_custom_key()), _custom_model()


# Allowed banking topics (used by topic_filter)
ALLOWED_TOPICS = [
    "banking", "account", "transaction", "transfer",
    "loan", "interest", "savings", "credit",
    "deposit", "withdrawal", "balance", "payment",
    "tai khoan", "giao dich", "tiet kiem", "lai suat",
    "chuyen tien", "the tin dung", "so du", "vay",
    "ngan hang", "atm",
]

# Blocked topics (immediate reject)
BLOCKED_TOPICS = [
    "hack", "exploit", "weapon", "drug", "illegal",
    "violence", "gambling", "bomb", "kill", "steal",
]
