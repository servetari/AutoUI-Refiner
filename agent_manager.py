import time
import subprocess
import os
from browser_tools import take_screenshot
from vision_evaluator import evaluate_ui
from coder_agent import generate_initial_code, update_code

PORT = 5173
APP_URL = f"http://localhost:{PORT}"
WORKSPACE_DIR = "workspace"

def start_server():
    """Starts a simple Python HTTP server."""
    if not os.path.exists(WORKSPACE_DIR):
        os.makedirs(WORKSPACE_DIR)
        
    print(f"[*] Starting development server on port {PORT}...")
    process = subprocess.Popen(
        ["python", "-m", "http.server", str(PORT), "--directory", WORKSPACE_DIR],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(2)
    return process

def run_feedback_loop(max_iterations=5):
    print("="*50)
    print("UI/UX Auto-Refiner System")
    print("                by pixelly")
    print("="*50)
    
    print("\nPlease describe the target web interface:")
    print("(e.g., 'A modern dashboard with a dark theme, left sidebar, and 3 stat cards.')")
    user_prompt = input("> ")
    
    if not user_prompt.strip():
        user_prompt = "A modern dark-themed index page with a large clock in the center"
        print(f"Empty input. Using default: '{user_prompt}'")
    
    print("\n[*] Initializing project layout...")
    generate_initial_code(user_prompt, workspace=WORKSPACE_DIR)
    
    server_process = start_server()
    
    try:
        for i in range(1, max_iterations + 1):
            print(f"\n--- Iteration {i}/{max_iterations} ---")
            
            success = take_screenshot(url=APP_URL, output_path="current_ui.png")
            if not success:
                print("[-] Failed to capture screenshot. The server or page might be down.")
                break
                
            critique = evaluate_ui(image_path="current_ui.png", original_prompt=user_prompt)
            print("\n--- Visual Analysis Report ---")
            print(critique)
            print("------------------------------\n")
            
            if "PASS" in critique.upper() and len(critique) < 150: 
                print("[+] Target quality achieved. Terminating optimization loop.")
                break
                
            print("[*] Refactoring source code based on analysis...")
            update_success = update_code(critique=critique, original_prompt=user_prompt, workspace=WORKSPACE_DIR)
            
            if not update_success:
                print("[-] An error occurred while updating the code.")
                break
                
            print("[*] Waiting for the new design to render...")
            time.sleep(2) 
            
        print("\n=== Optimization complete. Environment is running. ===")
        print(f"-> {APP_URL}")
        
        input("\nPress ENTER to terminate the server and exit...")
        
    finally:
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    run_feedback_loop()
