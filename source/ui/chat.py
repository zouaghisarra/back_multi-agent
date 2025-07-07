import streamlit as st
import requests
import json
import os
import tempfile

st.set_page_config(page_title="Chatlaw", layout="centered")

API_URL = "http://localhost:8000/router"  # change if deployed

st.markdown("### ⚖️ Chatlaw")
st.markdown("## Ask Your Legal Question:")

# 1. Input question
query = st.text_input(" ", placeholder="Enter your question.")

# 2. File uploader with conditional confirmation
add_file = False
uploaded_file = st.file_uploader("📎 Attach", type=["pdf", "docx", "txt"], key="file_upload")

# 2.1 If file uploaded, ask for confirmation
if uploaded_file:
    st.warning("⚠️ Do you want to add this file to the database?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Yes, add file"):
            add_file = True
            st.success(f"File `{uploaded_file.name}` will be sent to the backend.")
    with col2:
        if st.button("❌ No, skip file"):
            uploaded_file = None  # Clear the file
            st.info("File upload ignored.")

# 3. Submit to /router
if st.button("🔄 Send to Chatlaw"):
    if not query:
        st.warning("Please enter a legal question.")
    else:
        file_path = None

        if uploaded_file and add_file:
            # Save to a temporary location
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file.write(uploaded_file.read())
            temp_file.close()
            file_path = temp_file.name  # path to be sent to the backend

        payload = {
            "current_query": query,
            "file_path": file_path
        }

        try:
            with st.spinner("🧠 Chatlaw is analyzing your request..."):
                response = requests.post(API_URL, json=payload, stream=True)

                if response.status_code == 200:
                    st.success("📝 Response:")
                    full_response = ""
                    for line in response.iter_lines():
                        if line:
                            decoded = json.loads(line.decode("utf-8"))
                            content = decoded.get("content", "")
                            full_response += content + "\n"
                            st.write(content)
                    st.text_area("Full Response", value=full_response.strip(), height=300)
                else:
                    st.error(f"🚫 Error {response.status_code}: {response.text}")

        except Exception as e:
            st.error(f"⚠️ Could not connect to backend: {str(e)}")

        # Cleanup temp file
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
