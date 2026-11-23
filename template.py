from pathlib import Path

# Files to create (parent directories are created automatically)
FILES = [
    "app/__init__.py",
    "app/main.py",
    "app/api/__init__.py",
    "app/api/routes/__init__.py",
    "app/core/__init__.py",
    "app/utils/__init__.py",
    "tests/__init__.py",
    ".env",
    ".gitignore",
]

for file_path in FILES:
    path = Path(file_path)
    # Create parent directories
    path.parent.mkdir(parents=True, exist_ok=True)

    # Create empty file if it doesn't already exist
    if not path.exists():
        path.touch()
        print(f"Created: {file_path}")
    else:
        print(f"Already exists: {file_path}")
