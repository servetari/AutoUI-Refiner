import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from datetime import datetime

from browser_tools import capture_page
from coder_agent import generate_initial_code, update_code
from llm_client import print_usage_summary, validate_api_key
from vision_evaluator import evaluate_ui, format_critique

WORKSPACE_DIR = "workspace"
HISTORY_DIR = "history"


def find_free_port(start_port):
    for port in range(start_port, start_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError(f"No free port found in range {start_port}-{start_port + 49}.")


def start_server(port):
    """Starts a simple HTTP server and waits until it actually responds."""
    os.makedirs(WORKSPACE_DIR, exist_ok=True)

    print(f"[*] Starting development server on port {port}...")
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "http.server",
            str(port),
            "--bind",
            "127.0.0.1",
            "--directory",
            WORKSPACE_DIR,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    url = f"http://127.0.0.1:{port}"
    for _ in range(20):
        if process.poll() is not None:
            print("[-] Server process exited unexpectedly.")
            return None
        try:
            urllib.request.urlopen(url, timeout=1)
            return process
        except Exception:
            time.sleep(0.5)

    print("[-] Server did not respond in time.")
    process.terminate()
    return None


def parse_args():
    parser = argparse.ArgumentParser(
        description="UI/UX Auto-Refiner: generate a web UI from a prompt and "
        "iteratively refine it with vision-model feedback."
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        help="Design prompt. If omitted, you will be asked interactively.",
    )
    parser.add_argument(
        "--iterations", type=int, default=5, help="Maximum refinement iterations (default: 5)."
    )
    parser.add_argument(
        "--port", type=int, default=5173, help="Preferred dev server port (default: 5173)."
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=8,
        help="Minimum score (1-10) required to accept the design (default: 8).",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Refine the existing workspace/index.html instead of generating from scratch.",
    )
    return parser.parse_args()


def run_feedback_loop(args):
    print("=" * 50)
    print("UI/UX Auto-Refiner System")
    print("                by pixelly")
    print("=" * 50)

    validate_api_key()

    user_prompt = args.prompt
    if not user_prompt:
        print("\nPlease describe the target web interface:")
        print("(e.g., 'A modern dashboard with a dark theme, left sidebar, and 3 stat cards.')")
        user_prompt = input("> ").strip()
    if not user_prompt:
        user_prompt = "A modern dark-themed index page with a large clock in the center"
        print(f"Empty input. Using default: '{user_prompt}'")

    index_exists = os.path.exists(os.path.join(WORKSPACE_DIR, "index.html"))
    if args.resume and index_exists:
        print("\n[*] Resuming from existing workspace/index.html...")
    else:
        if args.resume:
            print("[!] --resume requested but workspace/index.html not found; generating from scratch.")
        print("\n[*] Initializing project layout...")
        if not generate_initial_code(user_prompt, workspace=WORKSPACE_DIR):
            print("[-] Initial code generation failed.")
            return 1

    port = find_free_port(args.port)
    if port != args.port:
        print(f"[!] Port {args.port} is busy, using {port} instead.")
    server_process = start_server(port)
    if server_process is None:
        return 1
    app_url = f"http://127.0.0.1:{port}"

    run_dir = os.path.join(HISTORY_DIR, datetime.now().strftime("run_%Y%m%d_%H%M%S"))
    os.makedirs(run_dir, exist_ok=True)
    index_path = os.path.join(WORKSPACE_DIR, "index.html")

    best = {"score": -1, "iteration": None, "html_path": None}
    previous_issues = []
    last_score = -1

    try:
        for i in range(1, args.iterations + 1):
            print(f"\n--- Iteration {i}/{args.iterations} ---")
            iter_dir = os.path.join(run_dir, f"iter_{i:02d}")
            os.makedirs(iter_dir, exist_ok=True)

            screenshots = {
                "desktop": os.path.join(iter_dir, "desktop.png"),
                "mobile": os.path.join(iter_dir, "mobile.png"),
            }
            success, console_errors = capture_page(app_url, screenshots)
            if not success:
                print("[-] Failed to capture screenshots. The server or page might be down.")
                break
            if console_errors:
                print(f"[!] {len(console_errors)} browser error(s) captured.")

            shutil.copy(index_path, os.path.join(iter_dir, "index.html"))

            evaluation = evaluate_ui(
                image_paths=list(screenshots.values()),
                original_prompt=user_prompt,
                previous_issues=previous_issues,
                console_errors=console_errors,
            )
            if evaluation is None:
                print("[-] Evaluation failed.")
                break

            with open(os.path.join(iter_dir, "critique.json"), "w", encoding="utf-8") as f:
                json.dump(
                    {**evaluation, "console_errors": console_errors},
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

            print("\n--- Visual Analysis Report ---")
            print(f"Score: {evaluation['score']}/10 | Verdict: {evaluation['verdict']}")
            for issue in evaluation["issues"]:
                print(f"- {issue}")
            print("------------------------------")

            last_score = evaluation["score"]
            if evaluation["score"] > best["score"]:
                best = {
                    "score": evaluation["score"],
                    "iteration": i,
                    "html_path": os.path.join(iter_dir, "index.html"),
                }

            if evaluation["verdict"] == "PASS" and evaluation["score"] >= args.threshold:
                print("[+] Target quality achieved. Terminating optimization loop.")
                break

            if not evaluation["issues"] and not console_errors:
                # A PASS below threshold (or a FAIL without issues) leaves the
                # coder with nothing actionable — refining on an empty critique
                # just produces random changes.
                print(
                    f"[+] Evaluator reported no remaining issues "
                    f"(score {evaluation['score']}/10). Stopping."
                )
                break

            previous_issues.append({"iteration": i, "issues": evaluation["issues"]})

            if i == args.iterations:
                # Refining now would produce code that never gets evaluated.
                break

            print("[*] Refactoring source code based on analysis...")
            critique_text = format_critique(evaluation, console_errors)
            if not evaluation["issues"] and console_errors:
                # Visual review passed; only technical errors remain. Without
                # this, coder models tend to "fix" the errors by rewriting or
                # gutting the whole page.
                critique_text = (
                    "The design already passed visual review — DO NOT redesign,"
                    " restructure or remove ANY existing content. Apply the"
                    " smallest possible change that fixes only the browser"
                    " errors below.\n\n" + critique_text
                )
            if not update_code(
                critique=critique_text, original_prompt=user_prompt, workspace=WORKSPACE_DIR
            ):
                print("[-] An error occurred while updating the code.")
                break

        if best["iteration"] is not None and best["score"] > last_score:
            print(
                f"\n[*] Restoring best version "
                f"(iteration {best['iteration']}, score {best['score']}/10)."
            )
            shutil.copy(best["html_path"], index_path)

        print_usage_summary()
        print("\n=== Optimization complete. Environment is running. ===")
        print(f"-> {app_url}")
        print(f"-> Iteration history: {run_dir}")

        try:
            input("\nPress ENTER to terminate the server and exit...")
        except (EOFError, KeyboardInterrupt):
            pass
    finally:
        server_process.terminate()
        server_process.wait()
    return 0


if __name__ == "__main__":
    sys.exit(run_feedback_loop(parse_args()))
