import streamlit as st
import fitz  # PyMuPDF
import pdfplumber
import tabula
import os
from PIL import Image
import io
import base64
import requests
from openai import OpenAI

# ---- CONFIG ----
st.set_page_config(page_title="PDF to Text & Graph Reader", layout="wide")
st.title("📄 PDF Reader with GPT/Gemini Vision")
st.write("Upload a PDF → Extract **text**, **tables**, and **graphs** → Send graphs to GPT-4o or Gemini Vision.")

# ---- API KEYS ----
openai_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
gemini_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))

# Initialize OpenAI client if key exists
client = None
if openai_key:
    client = OpenAI(api_key=openai_key)

# ---- FILE UPLOAD ----
uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

if uploaded_file:
    pdf_bytes = uploaded_file.read()
    pdf_name = uploaded_file.name
    
    # Save locally for tabula
    with open(pdf_name, "wb") as f:
        f.write(pdf_bytes)

    # ---- TEXT EXTRACTION ----
    st.subheader("🔹 Extracted Text")
    with pdfplumber.open(pdf_name) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() or ""
        st.text_area("PDF Text", full_text, height=200)

    # ---- TABLE EXTRACTION ----
    st.subheader("🔹 Extracted Tables")
    try:
        dfs = tabula.read_pdf(pdf_name, pages="all", multiple_tables=True)
        if dfs:
            for i, df in enumerate(dfs):
                st.write(f"Table {i+1}")
                st.dataframe(df)
        else:
            st.write("⚠️ No tables detected.")
    except Exception as e:
        st.write("Table extraction error:", e)

    # ---- IMAGE EXTRACTION ----
    st.subheader("🔹 Extracted Images (Graphs/Charts)")
    doc = fitz.open(pdf_name)
    img_count = 0
    for page_index in range(len(doc)):
        for img_index, img in enumerate(doc.get_page_images(page_index)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            pil_img = Image.open(io.BytesIO(image_bytes))
            img_count += 1

            st.image(pil_img, caption=f"Page {page_index+1}, Image {img_count}", use_container_width=True)

            col1, col2 = st.columns(2)

            # ---- GPT-4o Vision ----
            if client and col1.button(f"Send to GPT-4o (Image {img_count})", key=f"gpt_{page_index}_{img_index}"):
                buffered = io.BytesIO()
                pil_img.save(buffered, format="PNG")
                img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

                with st.spinner("Asking GPT-4o Vision..."):
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are a financial report assistant. Extract any chart/graph into structured text or JSON."},
                            {"role": "user", "content": [
                                {"type": "text", "text": "Read this financial chart and return structured data."},
                                {"type": "image_url", "image_url": f"data:image/png;base64,{img_b64}"}
                            ]}
                        ],
                        max_tokens=800
                    )
                st.success("✅ GPT-4o Output:")
                st.write(response.choices[0].message["content"])

            # ---- Gemini Vision ----
            if gemini_key and col2.button(f"Send to Gemini (Image {img_count})", key=f"gem_{page_index}_{img_index}"):
                buffered = io.BytesIO()
                pil_img.save(buffered, format="PNG")
                img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

                with st.spinner("Asking Gemini Vision..."):
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
                    headers = {"Content-Type": "application/json"}
                    payload = {
                        "contents": [
                            {"parts": [
                                {"text": "Extract this chart into structured JSON or text."},
                                {"inline_data": {"mime_type": "image/png", "data": img_b64}}
                            ]}
                        ]
                    }
                    r = requests.post(url, headers=headers, json=payload)
                    result = r.json()

                st.success("✅ Gemini Output:")
                st.write(result)

    # Cleanup temp file
    os.remove(pdf_name)
