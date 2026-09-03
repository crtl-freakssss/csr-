import io
import os
import re
from pathlib import Path
import pypdf


class PDFTextExtractor:
    """PDF text extractor adhering to Technical Contract Section 71."""

    MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB

    def extract_text_from_bytes(self, pdf_bytes: bytes) -> str:
        """Extract and clean text from raw PDF bytes."""
        if len(pdf_bytes) > self.MAX_FILE_SIZE_BYTES:
            raise ValueError("FILE_TOO_LARGE: Exceeds 20MB limit")

        if not pdf_bytes.startswith(b"%PDF-"):
            raise ValueError("FILE_INVALID: Not a valid PDF document")

        try:
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        except Exception as e:
            raise ValueError(f"FILE_INVALID: Unable to parse PDF ({e})")

        pages_text: list[str] = []
        for idx, page in enumerate(reader.pages):
            try:
                page_content = page.extract_text() or ""
                pages_text.append(page_content)
            except Exception:
                continue

        raw_text = "\n\n".join(pages_text)
        return self._clean_text(raw_text)

    def extract_text_from_path(self, file_path: str) -> str:
        """Read a PDF file from path and extract text."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = path.stat().st_size
        if file_size > self.MAX_FILE_SIZE_BYTES:
            raise ValueError("FILE_TOO_LARGE: Exceeds 20MB limit")

        with open(path, "rb") as f:
            pdf_bytes = f.read()

        return self.extract_text_from_bytes(pdf_bytes)

    def _clean_text(self, text: str) -> str:
        """Strip null bytes, non-printable control characters, and collapse repeated whitespace."""
        if not text:
            return ""

        # Remove null bytes
        cleaned = text.replace("\x00", "")

        # Remove non-printable control chars, preserving \n, \t, \r
        cleaned = "".join(
            ch for ch in cleaned
            if ch in ("\n", "\t", "\r") or (ord(ch) >= 32 and ord(ch) != 127)
        )

        # Collapse horizontal whitespace
        cleaned = re.sub(r"[ \t]+", " ", cleaned)

        # Collapse excessive newlines (max 2 consecutive newlines)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        return cleaned.strip()
