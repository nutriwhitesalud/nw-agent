"""
Side-by-side model evaluation for the NutriWhite agent.

Loads cases from seeds.yaml, runs each against each selected model, and writes
JSONL outputs for manual review. No automatic scoring yet — Phase 1 is just
producing comparable outputs.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

EVAL_DIR = Path(__file__).resolve().parent
RESULTS_DIR = EVAL_DIR / "results"


@dataclass(slots=True)
class EvalCase:
    id: str
    category: str
    sender_phone: str
    input: str
    expected: list[dict[str, Any]]


@dataclass(slots=True)
class ModelOutput:
    model: str
    case_id: str
    response: str
    latency_ms: int
    error: str | None = None


def load_cases() -> list[EvalCase]:
    raw = yaml.safe_load((EVAL_DIR / "seeds.yaml").read_text(encoding="utf-8"))
    return [EvalCase(**case) for case in raw["cases"]]


def load_system_prompt() -> str:
    return (EVAL_DIR / "system_prompt.md").read_text(encoding="utf-8")


def build_user_prompt(case: EvalCase) -> str:
    return (
        f"[sender_phone: {case.sender_phone}]\n"
        f"[message]:\n{case.input}"
    )


# === Model adapters ============================================================
# Each adapter: (system, user) -> response text. No tool calls in v1; we only
# evaluate raw response quality and whether the model says it would hand off.


def call_anthropic(model: str, system: str, user: str) -> str:
    from anthropic import Anthropic

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model=model,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(block.text for block in message.content if block.type == "text")


def call_openai(model: str, system: str, user: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model=model,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content or ""


def call_gemini(model: str, system: str, user: str) -> str:
    import google.generativeai as genai

    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    gen_model = genai.GenerativeModel(model_name=model, system_instruction=system)
    response = gen_model.generate_content(user)
    return response.text or ""


MODEL_REGISTRY = {
    "haiku-4.5": ("anthropic", "claude-haiku-4-5-20251001"),
    "sonnet-4.6": ("anthropic", "claude-sonnet-4-6"),
    "gpt-5-mini": ("openai", "gpt-5-mini"),
    "gpt-5-nano": ("openai", "gpt-5-nano"),
    "gemini-3-flash": ("google", "gemini-3-flash-preview"),
    "gemini-3-flash-lite": ("google", "gemini-3-1-flash-lite"),
}


def call_model(model_alias: str, system: str, user: str) -> str:
    if model_alias not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model alias: {model_alias}")
    provider, model_id = MODEL_REGISTRY[model_alias]

    if provider == "anthropic":
        return call_anthropic(model_id, system, user)
    if provider == "openai":
        return call_openai(model_id, system, user)
    if provider == "google":
        return call_gemini(model_id, system, user)
    raise ValueError(f"Unknown provider: {provider}")


# === Runner ===================================================================


def run_one(model_alias: str, case: EvalCase, system: str) -> ModelOutput:
    user = build_user_prompt(case)
    start = time.monotonic()
    try:
        text = call_model(model_alias, system, user)
        return ModelOutput(
            model=model_alias,
            case_id=case.id,
            response=text,
            latency_ms=int((time.monotonic() - start) * 1000),
        )
    except Exception as exc:  # noqa: BLE001 — eval harness records errors
        return ModelOutput(
            model=model_alias,
            case_id=case.id,
            response="",
            latency_ms=int((time.monotonic() - start) * 1000),
            error=f"{type(exc).__name__}: {exc}",
        )


def run(models: list[str]) -> Path:
    cases = load_cases()
    system = load_system_prompt()

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = RESULTS_DIR / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    summary = {"timestamp": timestamp, "models": models, "case_count": len(cases)}
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    for model in models:
        out_path = run_dir / f"{model}.jsonl"
        print(f"running {model} → {out_path.name}")
        with out_path.open("w", encoding="utf-8") as fh:
            for case in cases:
                output = run_one(model, case, system)
                line = {
                    "case_id": output.case_id,
                    "category": case.category,
                    "input": case.input,
                    "expected": case.expected,
                    "model": output.model,
                    "response": output.response,
                    "latency_ms": output.latency_ms,
                    "error": output.error,
                }
                fh.write(json.dumps(line, ensure_ascii=False) + "\n")
                marker = "ERR" if output.error else "ok"
                print(f"  {case.id:35s} [{marker}] {output.latency_ms}ms")

    print(f"\nresults: {run_dir}")
    return run_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="NutriWhite agent model evaluation")
    parser.add_argument(
        "--models",
        default="haiku-4.5,gemini-3-flash,gpt-5-mini",
        help=f"Comma-separated model aliases. Available: {', '.join(MODEL_REGISTRY)}",
    )
    args = parser.parse_args()

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    run(models)


if __name__ == "__main__":
    main()
