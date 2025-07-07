import streamlit as st
import httpx
import tempfile
import os
import asyncio
import json

API_URL = "http://localhost:8000/router"

# ----- PAGE CONFIG -----
st.set_page_config(page_title="Legal Document Router", page_icon="⚖️", layout="centered")

logo_url = "./image/image2.png"

# ----- HEADER WITH LOGO AND TITLE SIDE BY SIDE -----
col1, col2 = st.columns([1, 8], gap="small")

with col1:
    st.image(logo_url, width=100)

with col2:
    st.markdown("""
        <h1 style='margin-top: 10px;'>
            <span style='color: red;'>Chatlaw</span>
        </h1>
    """, unsafe_allow_html=True)

# ----- INPUT FIELD AND SUBMIT BUTTON CLOSE TOGETHER -----
col_input, col_button = st.columns([10, 2], gap="small")  # More space for input

with col_input:
    query = st.text_input("💬 Legal Query", placeholder="e.g., What clauses concern termination of contract?")

with col_button:
    submit_clicked = st.button("Send", use_container_width=True)

# ----- FILE UPLOADER (NO LABEL) -----
uploaded_file = st.file_uploader("", type=["pdf", "txt", "docx"])

# ----- HANDLE SUBMISSION -----
if submit_clicked:
    if not query:
        st.warning("⚠️ Please enter a legal query.")
    else:
        tmp_file_path = None

        if uploaded_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_file_path = tmp_file.name

        async def stream_from_api():
            async with httpx.AsyncClient(timeout=None) as client:
                try:
                    payload = {
                        "current_query": query,
                        "file_path": tmp_file_path
                    }

                    with st.spinner("🧠 Chatlaw is analyzing your input..."):
                        async with client.stream("POST", API_URL, json=payload) as response:
                            if response.status_code != 200:
                                st.error(f"❌ Error: {await response.aread()}")
                                return

                            st.markdown("### 📝 Response:")
                            full_response = ""

                            async for line in response.aiter_lines():
                                if line.strip():
                                    try:
                                        data = json.loads(line)
                                        content = data.get("content", "")
                                        full_response += content + "\n"
                                        st.write(content)
                                    except json.JSONDecodeError:
                                        st.warning(f"⚠️ Invalid response format: {line}")

                            if full_response.strip():
                                st.text_area("📋 Full Output", value=full_response.strip(), height=300)
                            else:
                                st.warning("⚠️ No response content received.")

                except Exception as e:
                    st.error(f"🚫 Request failed: {str(e)}")

        asyncio.run(stream_from_api())

        if tmp_file_path and os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)
