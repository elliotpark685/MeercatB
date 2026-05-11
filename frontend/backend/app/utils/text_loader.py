from pathlib import Path


def load_text_file(file_path: str) -> str:
    """Read a UTF-8 text file and return full text."""
    text_path = Path(file_path)
    return text_path.read_text(encoding="utf-8")

