import os
import re

from llm_client import call_llm
from utils import load_prompts


def generate_initial_code(user_prompt, workspace="workspace"):
    """Generates the initial HTML file based on the user's prompt."""
    model_name = os.getenv("CODER_MODEL", "deepseek/deepseek-chat")
    os.makedirs(workspace, exist_ok=True)

    prompts = load_prompts("config.md")
    base_prompt = prompts.get(
        "Coder Initial Prompt",
        "You are an expert Frontend Developer. Build what the user wants: {user_prompt}",
    )
    prompt = base_prompt.replace("{user_prompt}", user_prompt)

    response = call_llm([{"role": "user", "content": prompt}], model=model_name)
    if response is None:
        return False

    code = _extract_code(response)
    if not _looks_like_html(code):
        print("[-] Model output does not look like an HTML document.")
        return False

    _write_code(code, os.path.join(workspace, "index.html"))
    return True


def update_code(critique, original_prompt, workspace="workspace"):
    """Updates the code based on the Vision agent's critique."""
    file_path = os.path.join(workspace, "index.html")
    model_name = os.getenv("CODER_MODEL", "deepseek/deepseek-chat")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            current_code = f.read()
    except FileNotFoundError:
        return False

    prompts = load_prompts("config.md")
    base_prompt = prompts.get("Coder Update Prompt", "Update this code based on critique.")

    prompt = base_prompt.replace("{original_prompt}", original_prompt)
    prompt = prompt.replace("{critique}", critique)
    prompt = prompt.replace("{current_code}", current_code)

    response = call_llm([{"role": "user", "content": prompt}], model=model_name)
    if response is None:
        return False

    code = _extract_code(response)
    if not _looks_like_html(code):
        # Keep the last working version instead of overwriting it with garbage.
        print("[-] Model output does not look like an HTML document. Keeping current version.")
        return False

    _write_code(code, file_path)
    return True


def _extract_code(raw):
    """Extracts the HTML document from a raw model response."""
    raw = raw.strip()
    match = re.search(r"```(?:html)?\s*\n(.*?)```", raw, re.DOTALL)
    if match:
        return match.group(1).strip()

    lowered = raw.lower()
    for marker in ("<!doctype", "<html"):
        idx = lowered.find(marker)
        if idx == 0:
            return raw
        if idx > 0:
            return raw[idx:].strip()
    return raw


def _looks_like_html(code):
    lowered = code.lower()
    return "<!doctype" in lowered or "<html" in lowered


def _write_code(code, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(code)
