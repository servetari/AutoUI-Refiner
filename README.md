# UI/UX Auto-Refiner 

A self-refining UI/UX development tool that automatically generates, visualizes, and optimizes web interfaces based on natural language descriptions. Built to operate locally with continuous feedback loops.

## How It Works
1. Accepts a frontend design prompt via CLI.
2. Generates semantic HTML using modern utility-first frameworks (TailwindCSS, DaisyUI).
3. Spawns a local development server and captures a headless rendering using Playwright.
4. Performs a deep visual analysis using Vision Language Models (VLMs) to detect layout inconsistencies and suggest high-level improvements.
5. Recursively applies code refactoring until a production-ready quality threshold is reached.

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

## Usage

Run the optimization loop:
```bash
python agent_manager.py
```
