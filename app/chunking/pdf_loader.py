from pathlib import Path

from pypdf import PdfReader


def load_pdf_pages(path: str | Path) -> list[str]:
    reader = PdfReader(path)
    return [page.extract_text() for page in reader.pages]
