import pytest

from app.pipelines.document_extractor import UnsupportedFileTypeError, extract_text


def test_extract_text_plain_txt():
    result = extract_text(b"hello world", "resume.txt")
    assert result.text == "hello world"
    assert result.used_ocr is False


def test_extract_text_rejects_unsupported_extension():
    with pytest.raises(UnsupportedFileTypeError):
        extract_text(b"data", "resume.xyz")
