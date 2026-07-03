import re


def load_prompts(file_path="config.md"):
    """
    Reads the config file and parses level-1 markdown headings ('# ' at the
    start of a line) into a {title: body} dictionary. '# ' occurring anywhere
    else (mid-line, or deeper headings like '## ') stays part of the body.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"[-] Config file {file_path} not found.")
        return {}

    sections = re.split(r"^# ", content, flags=re.MULTILINE)
    prompts = {}
    for section in sections:
        if not section.strip():
            continue
        lines = section.split("\n", 1)
        title = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""
        prompts[title] = body

    return prompts
