"""Phase 1: raw text extraction from uploaded resume files (PDF / DOCX / TXT).

OCR fallback (scanned/image PDFs) is isolated in `ocr_fallback` so the happy
path never pays the pytesseract/poppler cost, and so OCR can be swapped or
disabled without touching the rest of the pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MIN_CHARS_BEFORE_OCR_FALLBACK = 40


class UnsupportedFileTypeError(ValueError):
    pass


class DocumentParseError(ValueError):
    pass


@dataclass
class ExtractionResult:
    text: str
    used_ocr: bool
    page_count: int | None = None


def validate_extension(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{ext}'. Supported: {sorted(SUPPORTED_EXTENSIONS)}"
        )
    return ext


def extract_text(file_bytes: bytes, filename: str) -> ExtractionResult:
    ext = validate_extension(filename)
    if ext == ".pdf":
        return _extract_pdf(file_bytes)
    if ext == ".docx":
        return _extract_docx(file_bytes)
    if ext == ".txt":
        return ExtractionResult(text=file_bytes.decode("utf-8", errors="ignore"), used_ocr=False)
    raise UnsupportedFileTypeError(ext)


def _extract_pdf(file_bytes: bytes) -> ExtractionResult:
    import io

    import pdfplumber

    text_parts: list[str] = []
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            page_count = len(pdf.pages)
            for page in pdf.pages:
                text_parts.append(page.extract_text() or "")
    except Exception as exc:  # malformed PDF
        raise DocumentParseError(f"Failed to parse PDF: {exc}") from exc

    text = "\n".join(text_parts).strip()
    if len(text) >= MIN_CHARS_BEFORE_OCR_FALLBACK:
        return ExtractionResult(text=text, used_ocr=False, page_count=page_count)

    # Likely a scanned/image-based PDF: fall back to OCR.
    ocr_text = _ocr_pdf(file_bytes)
    return ExtractionResult(text=ocr_text, used_ocr=True, page_count=page_count)


def _ocr_pdf(file_bytes: bytes) -> str:
    """Best-effort OCR fallback. Requires poppler + tesseract to be installed;
    if unavailable, raises a clear, actionable error rather than crashing.
    """
    try:

        import pytesseract
        from pdf2image import convert_from_bytes

        images = convert_from_bytes(file_bytes)
        pages_text = [pytesseract.image_to_string(img) for img in images]
        return "\n".join(pages_text).strip()
    except Exception as exc:
        raise DocumentParseError(
            "This looks like a scanned/image-based resume and OCR is unavailable "
            "in this environment (requires poppler + tesseract). "
            f"Original error: {exc}"
        ) from exc


def _extract_docx(file_bytes: bytes) -> ExtractionResult:
    import io

    from docx import Document

    try:
        doc = Document(io.BytesIO(file_bytes))
    except Exception as exc:
        raise DocumentParseError(f"Failed to parse DOCX: {exc}") from exc

    parts: list[str] = []
    for para in doc.paragraphs:
        if para.text.strip():
            parts.append(para.text)
    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells if c.text.strip()]
            if cells:
                parts.append(" | ".join(cells))
    return ExtractionResult(text="\n".join(parts).strip(), used_ocr=False)
