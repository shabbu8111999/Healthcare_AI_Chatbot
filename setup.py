"""
Run this once to scaffold the healthcare chatbot project.
It only creates folders and empty files. The actual code for each file
will be filled in one by one in later steps.

Usage:
    python setup_project.py
"""

from pathlib import Path

BASE_DIR = Path("healthcare_chatbot")

FOLDERS = [
    BASE_DIR,
    BASE_DIR / "data",
    BASE_DIR / "graph",
]

FILES = [
    BASE_DIR / "app.py",
    BASE_DIR / "config.py",
    BASE_DIR / "prompts.py",
    BASE_DIR / "guardrails.py",
    BASE_DIR / "knowledge_base.py",
    BASE_DIR / "graph" / "__init__.py",
    BASE_DIR / "graph" / "state.py",
    BASE_DIR / "graph" / "nodes.py",
    BASE_DIR / "graph" / "workflow.py",
    BASE_DIR / "data" / "medical_kb.json",
    BASE_DIR / "templates" / "index.html",
    BASE_DIR / "css" / "style.css",
    BASE_DIR / "js" / "app.js"
]


def scaffold():
    for folder in FOLDERS:
        folder.mkdir(parents=True, exist_ok=True)
        print(f"Folder ready: {folder}")

    for file_path in FILES:
        if file_path.exists():
            print(f"Already exists, skipped: {file_path}")
            continue
        file_path.touch()
        print(f"File created: {file_path}")

    print("\nScaffold complete.")
    print("Place requirements.txt and .env inside the healthcare_chatbot folder next.")


if __name__ == "__main__":
    scaffold()