def load_prompts(file_path="config.md"):
    """
    Reads the config.md file and parses sections starting with '# ' into a dictionary.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"[-] Config file {file_path} not found.")
        return {}

    sections = content.split("# ")
    prompts = {}
    for section in sections:
        if not section.strip(): 
            continue
        lines = section.split("\n", 1)
        title = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""
        prompts[title] = body
        
    return prompts
