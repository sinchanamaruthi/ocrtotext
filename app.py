import streamlit as st
from utils import extract_text_from_pdf

st.set_page_config(page_title="PDF OCR with EasyOCR", layout="wide")
st.title("📄 PDF OCR Reader - Works on Any PDF (Text, Scans, Graphs)")

uploaded_file = st.file_uploader("Upload your PDF", type=["pdf"])

if uploaded_file:
    with st.spinner("Processing PDF... This may take a few seconds for large files."):
        text = extract_text_from_pdf(uploaded_file)
    st.success("✅ Extraction Complete!")

    st.subheader("Extracted Text")
    st.text_area("Text Output", text, height=400)

    st.download_button(
        "Download as TXT",
        text,
        file_name="extracted_text.txt",
        mime="text/plain"
    )
