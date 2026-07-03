import os
import sys
import time

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

_client = None

usage_totals = {"prompt_tokens": 0, "completion_tokens": 0, "calls": 0}


def validate_api_key():
    """Exits with a clear message if the OpenRouter API key is not configured."""
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key or api_key == "your_api_key_here":
        print("[-] OPENROUTER_API_KEY is missing.")
        print("    Copy .env.example to .env and set your OpenRouter API key.")
        sys.exit(1)


def get_client():
    global _client
    if _client is None:
        validate_api_key()
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
    return _client


def call_llm(messages, model, max_tokens=None, retries=3):
    """
    Calls the chat completions API with retries and exponential backoff.
    Returns the response content, or None if all attempts fail.
    """
    client = get_client()
    delay = 2
    for attempt in range(1, retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
            )
            usage_totals["calls"] += 1
            usage = getattr(response, "usage", None)
            if usage:
                usage_totals["prompt_tokens"] += usage.prompt_tokens or 0
                usage_totals["completion_tokens"] += usage.completion_tokens or 0

            content = response.choices[0].message.content if response.choices else None
            if content and content.strip():
                return content
            print(f"[-] Empty response from {model} (attempt {attempt}/{retries}).")
        except Exception as e:
            print(f"[-] LLM call to {model} failed (attempt {attempt}/{retries}): {e}")

        if attempt < retries:
            time.sleep(delay)
            delay *= 2
    return None


def print_usage_summary():
    print("\n--- Token Usage ---")
    print(f"API calls:         {usage_totals['calls']}")
    print(f"Prompt tokens:     {usage_totals['prompt_tokens']}")
    print(f"Completion tokens: {usage_totals['completion_tokens']}")
