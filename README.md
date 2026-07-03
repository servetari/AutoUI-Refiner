# UI/UX Auto-Refiner

A self-refining UI/UX development tool that automatically generates, visualizes, and optimizes web interfaces based on natural language descriptions. Built to operate locally with continuous feedback loops.

## How It Works
1. Accepts a frontend design prompt via CLI (argument or interactive input).
2. Generates semantic HTML using modern utility-first frameworks (TailwindCSS, DaisyUI).
3. Spawns a local development server and captures desktop **and mobile** renderings using headless Playwright, while collecting browser console errors (failed CDNs, JS exceptions).
4. Performs a deep visual analysis using Vision Language Models (VLMs), which return a structured verdict: `{"score": 1-10, "verdict": "PASS"/"FAIL", "issues": [...]}`.
5. Recursively applies code refactoring until the score threshold is reached. Every iteration (HTML + screenshots + critique) is archived under `history/`, and if the loop ends on a worse version, the best-scoring one is restored automatically.

## Installation

1. Create and activate a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

3. Environment Variables:
Copy `.env.example` to `.env` and fill in your OpenRouter API key.
```bash
cp .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | — | Required. Your OpenRouter API key. |
| `VISION_MODEL` | `openai/gpt-4o-mini` | Vision model used to critique screenshots. |
| `CODER_MODEL` | `deepseek/deepseek-chat` | Model used to generate and refactor the HTML. |

## Usage

Run the optimization loop:
```bash
# Interactive prompt
python agent_manager.py

# Or pass everything on the command line
python agent_manager.py "A modern dashboard with a dark theme and 3 stat cards" --iterations 8 --port 5173 --threshold 8
```

Options:
- `prompt` — design description (optional; asked interactively if omitted)
- `--iterations` — maximum refinement iterations (default: 5)
- `--port` — preferred dev server port; the next free port is picked automatically if busy (default: 5173)
- `--threshold` — minimum score (1-10) required to accept the design (default: 8)

The final page is served at the printed URL and written to `workspace/index.html`. Full iteration history (per-iteration HTML, desktop/mobile screenshots, and critique JSON) is stored in `history/run_<timestamp>/`.

Token usage across all API calls is printed at the end of every run.

## Customizing Prompts

All agent prompts live in [config.md](config.md) — each level-1 heading (`# Visual Evaluator Prompt`, `# Coder Initial Prompt`, `# Coder Update Prompt`) is a template with `{placeholder}` variables filled in at runtime. Edit them freely without touching the code.

## Tests

```bash
python -m pytest tests -q
```
