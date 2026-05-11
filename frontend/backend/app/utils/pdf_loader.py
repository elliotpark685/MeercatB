from pathlib import Path


def load_pdf_text_with_page_markers(file_path: str) -> str:
    """Extract UTF-8 text from PDF and include page markers."""
    import fitz

    pdf_path = Path(file_path)
    with fitz.open(pdf_path) as document:
        parts: list[str] = []
        for idx, page in enumerate(document, start=1):
            page_text = page.get_text("text").strip()
            parts.append(f"[PAGE:{idx}]")
            parts.append(page_text)
        return "\n".join(parts).strip()
