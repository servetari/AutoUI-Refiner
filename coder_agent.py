import os
from openai import OpenAI
from dotenv import load_dotenv
from utils import load_prompts

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

def generate_initial_code(user_prompt, workspace="workspace"):
    """Generates the initial HTML file based on the user's prompt."""
    model_name = os.getenv("CODER_MODEL", "deepseek/deepseek-chat")
    
    if not os.path.exists(workspace):
        os.makedirs(workspace)
        
    prompts = load_prompts("config.md")
    base_prompt = prompts.get("Coder Initial Prompt", "You are an expert Frontend Developer. Build what the user wants: {user_prompt}")
    prompt = base_prompt.replace("{user_prompt}", user_prompt)

    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}]
    )

    new_code = response.choices[0].message.content.strip()
    _save_cleaned_code(new_code, os.path.join(workspace, "index.html"))
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

    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}]
    )

    new_code = response.choices[0].message.content.strip()
    _save_cleaned_code(new_code, file_path)
    return True

def _save_cleaned_code(raw_code, file_path):
    if raw_code.startswith("```"):
        raw_code = raw_code.split("\n", 1)[1]
    if raw_code.endswith("```"):
        raw_code = raw_code.rsplit("\n", 1)[0]
    
    if raw_code.startswith("html\n"):
        raw_code = raw_code.split("\n", 1)[1]
        
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(raw_code)
