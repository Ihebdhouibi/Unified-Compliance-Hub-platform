import os
import tempfile
from PyPDF2 import PdfReader
import pytesseract
from pdf2image import convert_from_path
from PIL import Image


def extract_text_from_pdf(pdf_path):
    # Try text extraction first
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        if text.strip():
            return text
    except Exception as e:
        print(f"Text extraction error: {e}")

    # Fallback to OCR
    try:
        images = convert_from_path(pdf_path)
        text = ""
        for img in images:
            text += pytesseract.image_to_string(img) + "\n"
        return text
    except Exception as e:
        print(f"OCR error: {e}")
        return ""
