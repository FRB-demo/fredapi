"""PDF text extraction using PyMuPDF."""

import fitz  # PyMuPDF


class PDFParseError(Exception):
    """Raised when a PDF cannot be parsed."""

    pass


def parse_pdf(file_path: str) -> str:
    """Extract text content from a PDF file.

    Args:
        file_path: Path to the PDF file.

    Returns:
        Extracted text from all pages.

    Raises:
        PDFParseError: If the PDF cannot be opened or parsed.
    """
    try:
        doc = fitz.open(file_path)
    except Exception as e:
        raise PDFParseError(f"Failed to open PDF {file_path}: {e}") from e

    if doc.is_encrypted:
        doc.close()
        raise PDFParseError(f"PDF is password-protected: {file_path}")

    pages_text = []
    try:
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            if text.strip():
                pages_text.append(text)
    except Exception as e:
        doc.close()
        raise PDFParseError(f"Error extracting text from page {page_num} of {file_path}: {e}") from e
    finally:
        doc.close()

    if not pages_text:
        raise PDFParseError(f"No text content found in PDF: {file_path}")

    return "\n\n".join(pages_text)
