import PyPDF2
import pdfplumber
from pdf2image import convert_from_path
import pytesseract

def extract_text_pdf(file_path):
    text = ""
    try:
        # Try PyPDF2 first
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
    except:
        pass

    # Use pdfplumber as fallback
    if not text:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
    
    return text

def extract_text_from_images(file_path):
    text = ""
    pages = convert_from_path(file_path)
    for page in pages:
        text += pytesseract.image_to_string(page) + "\n"
    return text

def extract_full_text(file_path):
    # Combine both text extraction and OCR
    text = extract_text_pdf(file_path)
    text_ocr = extract_text_from_images(file_path)
    
    # Merge results
    if not text:
        return text_ocr
    else:
        return text + "\n" + text_ocr
