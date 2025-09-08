import streamlit as st
from utils import extract_full_text

st.set_page_config(page_title="PDF Reader OCR", layout="wide")
st.title("📄 PDF Reader with OCR & Image Support")

uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

if uploaded_file:
    with st.spinner("Processing PDF..."):
        text = extract_full_text(uploaded_file)
    st.success("✅ Extraction Complete!")
    
    st.subheader("Extracted Text")
    st.text_area("Text Output", text, height=400)

    st.download_button(
        "Download as TXT",
        text,
        file_name="extracted_text.txt",
        mime="text/plain"
    )
