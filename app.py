import streamlit as st
import fitz  # PyMuPDF
import pdfplumber
import tabula
import os
from PIL import Image
import io
import base64
from openai import OpenAI

# ---- CONFIG ----
st.set_page_config(page_title="PDF to Text & Graph Reader", layout="wide")
st.title("📄 PDF Reader with GPT-4o Vision")
st.write("Upload a PDF → Extract **text**, **tables**, and **graphs** → Send graphs to GPT-4o Vision.")

# ---- API KEY ----
openai_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
if not openai_key:
    st.error("⚠️ No OpenAI API key found. Please add it in Streamlit secrets.")
else:
    client = OpenAI(api_key=openai_key)

# ---- FILE UPLOAD ----
uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

if uploaded_file and openai_key:
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

            # ---- Send to GPT-4o Vision ----
            if st.button(f"Send to GPT-4o (Image {img_count})", key=f"gpt_{page_index}_{img_index}"):
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

    # Cleanup temp file
    os.remove(pdf_name)
