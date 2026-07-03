import base64
import json
import os
import re

from llm_client import call_llm
from utils import load_prompts


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def _parse_evaluation(raw):
    """
    Parses the evaluator's response into {"score", "verdict", "issues", "raw"}.
    Falls back to a FAIL verdict with the raw text as a single issue if the
    model did not return valid JSON.
    """
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            verdict = str(data.get("verdict", "FAIL")).strip().upper()
            issues = [str(issue) for issue in data.get("issues", []) if str(issue).strip()]
            return {
                "score": max(0, min(10, int(data.get("score", 0)))),
                "verdict": "PASS" if verdict == "PASS" else "FAIL",
                "issues": issues,
                "raw": raw,
            }
        except (ValueError, TypeError):
            pass
    return {"score": 0, "verdict": "FAIL", "issues": [raw.strip()], "raw": raw}


def evaluate_ui(image_paths, original_prompt, previous_issues=None, console_errors=None):
    """
    Evaluates the screenshots against the original prompt.
    Returns a dict {"score": 0-10, "verdict": "PASS"|"FAIL", "issues": [...], "raw": str}
    or None if the API call failed.
    """
    existing = [p for p in image_paths if os.path.exists(p)]
    if not existing:
        print("[-] No screenshots found to evaluate.")
        return None

    model_name = os.getenv("VISION_MODEL", "openai/gpt-4o-mini")

    prompts = load_prompts("config.md")
    base_prompt = prompts.get(
        "Visual Evaluator Prompt", "Evaluate this UI based on: {original_prompt}"
    )
    prompt = base_prompt.replace("{original_prompt}", original_prompt)

    if previous_issues:
        lines = [
            "",
            "Feedback you gave in earlier iterations (do NOT repeat points that are"
            " now resolved; focus on remaining or new problems):",
        ]
        for entry in previous_issues[-3:]:
            for issue in entry["issues"]:
                lines.append(f"- (iteration {entry['iteration']}) {issue}")
        prompt += "\n".join(lines)

    if console_errors:
        prompt += (
            "\n\nThe browser console reported these errors, so the page may not"
            " render as intended:\n"
            + "\n".join(f"- {err}" for err in console_errors[:10])
        )

    content = [{"type": "text", "text": prompt}]
    for path in existing:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{encode_image(path)}"},
            }
        )

    raw = call_llm(
        [{"role": "user", "content": content}], model=model_name, max_tokens=1024
    )
    if raw is None:
        return None
    return _parse_evaluation(raw)


def format_critique(evaluation, console_errors=None):
    """Builds the critique text handed to the coder agent."""
    lines = []
    if console_errors:
        lines.append("Browser console errors (fix these first):")
        lines.extend(f"- {err}" for err in console_errors[:10])
        lines.append("")
    if evaluation["issues"]:
        lines.append("Visual critique:")
        lines.extend(f"- {issue}" for issue in evaluation["issues"])
    return "\n".join(lines).strip()
