import streamlit as st
import pathlib
from PyPDF2 import PdfReader
from app_driver import AppDriver  # Import the AppDriver class

# Initialize the AppDriver instance
driver = AppDriver()

# ──────────────────────────────────────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="StorageInvesting.ai", layout="wide")
st.title("📄 StorageInvesting.ai — Learn How Self‑Storage Fits Into Your Plan")

# ──────────────────────────────────────────────────────────────────────────────
# Session‑state defaults
# ──────────────────────────────────────────────────────────────────────────────
for k, v in {
    "history": [],              # chat transcript
    "show_advanced": False,     # advanced sidebar toggle
    "temperature": 0.7,         # model params (default)
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ──────────────────────────────────────────────────────────────────────────────
# Sidebar — controls & utilities
# ──────────────────────────────────────────────────────────────────────────────
st.sidebar.title("⚙️ Settings")

# Model settings
with st.sidebar.expander("LLM Settings", expanded=False):
    st.session_state["temperature"] = st.slider(
        "Temperature", 0.0, 1.0, st.session_state["temperature"], 0.05
    )

# Utilities
st.sidebar.button("🧹 Clear History", on_click=lambda: st.session_state["history"].clear())
st.sidebar.button("🔄 Rerun App", on_click=lambda: st.experimental_rerun())

# ──────────────────────────────────────────────────────────────────────────────
# File upload
# ──────────────────────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "👉 Upload a PDF (financial plan, OM, etc.)", type="pdf", accept_multiple_files=False
)
file_text = ""
if uploaded_file:
    try:
        reader = PdfReader(uploaded_file)
        file_text = "".join(page.extract_text() or "" for page in reader.pages)
        st.success("✅ File uploaded & parsed.")
        # Preview first 1 000 chars so user knows what was read
        with st.expander("📄 Preview extracted text (first 1 000 chars)"):
            st.text(file_text[:1000])
    except Exception as e:
        st.error(f"Could not parse PDF: {e}")

# ──────────────────────────────────────────────────────────────────────────────
# Question input & submission
# ──────────────────────────────────────────────────────────────────────────────
question = st.text_area(
    "Ask a question about your document, your portfolio, or passive self‑storage investing:",
    placeholder="e.g. “How would adding 10 % self‑storage syndications affect my income?”",
    height=90,
)

def submit_question():
    if not question.strip():
        st.warning("Please type a question first.")
        return
    answer = driver.ask_llm(  # Use the AppDriver instance to call ask_llm
        question=question,
        file_text=file_text,
        temperature=st.session_state["temperature"],
    )
    st.session_state["history"].append((question, answer))
    st.session_state["rerun"] = True  # Set a flag to indicate a rerun is needed

st.button("🚀 Submit", on_click=submit_question)

# ──────────────────────────────────────────────────────────────────────────────
# Chat history (newest first)
# ──────────────────────────────────────────────────────────────────────────────
if st.session_state["history"]:
    st.markdown("### 💬 Conversation History")
    for q, a in reversed(st.session_state["history"]):
        st.markdown(f"**🧠 Question:** {q}")
        st.markdown(f"**📘 Answer:** {a}")
        st.markdown("---")
