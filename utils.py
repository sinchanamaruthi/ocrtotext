from pdf2image import convert_from_path
import easyocr
from PIL import Image
import io

reader = easyocr.Reader(['en'])  # Initialize once for English

def pdf_to_images(file):
    """
    Convert uploaded PDF (in-memory file) to list of PIL images.
    """
    images = convert_from_path(file, dpi=300)
    return images

def ocr_from_images(images):
    """
    Run EasyOCR on a list of images and return combined text.
    """
    full_text = ""
    for i, img in enumerate(images):
        # Convert PIL Image to RGB if not already
        if img.mode != "RGB":
            img = img.convert("RGB")
        results = reader.readtext(img)
        page_text = "\n".join([res[1] for res in results])
        full_text += f"--- Page {i+1} ---\n{page_text}\n"
    return full_text

def extract_text_from_pdf(file):
    """
    Full PDF → Images → OCR workflow.
    """
    images = pdf_to_images(file)
    text = ocr_from_images(images)
    return text
