import os
import base64
from openai import OpenAI
from dotenv import load_dotenv
from utils import load_prompts

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def evaluate_ui(image_path, original_prompt):
    """
    Evaluates the screenshot by comparing it to the original prompt.
    """
    if not os.path.exists(image_path):
        return "ERROR: Screenshot not found."

    base64_image = encode_image(image_path)
    model_name = os.getenv("VISION_MODEL", "openai/gpt-4o-mini")
    
    prompts = load_prompts("config.md")
    base_prompt = prompts.get("Visual Evaluator Prompt", "Evaluate this UI based on: {original_prompt}")
    prompt = base_prompt.replace("{original_prompt}", original_prompt)

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=1024
    )

    return response.choices[0].message.content
