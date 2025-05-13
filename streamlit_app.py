import os
import streamlit as st
import openai
from PyPDF2 import PdfReader

st.set_page_config(page_title="Storage Investing AI", layout="wide")

openai.api_key = os.getenv("OPENAI_API_KEY")

# Add legal note and consent checkbox
st.markdown("**Legal Note:** This tool is for educational purposes only and does not constitute financial, legal, or investment advice.")
consent = st.checkbox("I agree to the terms and give permission to process the uploaded document for educational analysis.")

if consent:
    uploaded_file = st.file_uploader("Upload a PDF (like your plan or portfolio)", type="pdf")

    if uploaded_file:
        try:
            reader = PdfReader(uploaded_file)
            raw_text = "".join(page.extract_text() or "" for page in reader.pages)

            if not raw_text.strip():
                st.error("The uploaded PDF appears to be empty or unreadable.")
            else:
                st.success("File uploaded and parsed.")
                st.text_area("Extracted Text (first 1000 characters)", raw_text[:1000])

                question = st.text_input("Ask a question about your portfolio or plan:")

                if question:

                    try:
                        response = openai.ChatCompletion.create(
                            model="gpt-4-turbo",
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.7
                        )
                        st.write(response.choices[0].message.content)
                    except Exception as e:
                        st.error(f"Error generating response: {e}")
        except Exception as e:
            st.error(f"Error processing the file: {e}")
else:
    st.warning("Please agree to the terms to upload your document.")
