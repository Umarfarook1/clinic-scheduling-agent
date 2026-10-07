from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICIES_DIR = ROOT / "policies"
SCENARIOS_DIR = ROOT / "evals" / "scenarios"
RUNS_DIR = ROOT / "runs"


def _load_dotenv() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            if v.strip():
                os.environ.setdefault(k.strip(), v.strip())


_load_dotenv()

PROVIDER = os.getenv("LLM_PROVIDER", "bedrock")  # bedrock | anthropic | openai
AWS_REGION = os.getenv("AWS_REGION", "eu-north-1")

# Who plays which part. The agent is a small fast model on purpose: on a phone call every
# second of model latency is dead air, so the production agent will be a small model, and
# the loop has to make a small model behave. The judge and the improver can be slow.
DEFAULT_MODELS = {
    "bedrock": {
        "agent": "eu.anthropic.claude-haiku-4-5-20251001-v1:0",
        "patient": "eu.anthropic.claude-sonnet-4-6",
        "judge": "eu.anthropic.claude-sonnet-4-6",
        "judge2": "openai.gpt-oss-120b-1:0",
        "improver": "eu.anthropic.claude-sonnet-5-5",
    },
    "anthropic": {
        "agent": "claude-haiku-4-5",
        "patient": "claude-sonnet-4-6",
        "judge": "claude-sonnet-4-6",
        "judge2": "claude-sonnet-4-6",
        "improver": "claude-sonnet-4-6",
    },
    "openai": {
        "agent": "gpt-4.1-mini",
        "patient": "gpt-4.1",
        "judge": "gpt-4.1",
        "judge2": "gpt-4.1",
        "improver": "gpt-4.1",
    },
}


def model_for(role: str) -> str:
    return os.getenv(f"{role.upper()}_MODEL", DEFAULT_MODELS[PROVIDER][role])


# Rough list prices, USD per million tokens (input, output), for the cost line in reports.
PRICES = {
    "haiku-4-5": (1.0, 5.0),
    "sonnet-4-6": (3.0, 15.0),
    "sonnet-5-5": (3.0, 15.0),
    "gpt-oss-120b": (0.15, 0.6),
}


def price_for(model: str) -> tuple[float, float]:
    for k, v in PRICES.items():
        if k in model:
            return v
    return (0.0, 0.0)
