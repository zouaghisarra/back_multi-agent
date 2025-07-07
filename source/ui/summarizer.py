import streamlit as st
import requests

st.title("📄 Document Summarizer")

uploaded_file = st.file_uploader("Upload a document (PDF)", type="pdf")

if uploaded_file:
    with st.spinner("Summarizing..."):
        try:
            # Prepare the files dictionary for the POST request
            files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}

            # Send POST request to FastAPI endpoint
            response = requests.post("http://localhost:8000/summarize", files=files)

            if response.status_code == 200:
                result = response.json()
                st.subheader("Summary:")
                st.write(result.get("summary", "No summary returned."))

                # Display metadata if available
                if "metadata" in result:
                    with st.expander("View Processing Details"):
                        st.json(result["metadata"])
            else:
                error_detail = response.json().get("detail", "Unknown error")
                st.error(f"API Error: {error_detail}")

        except Exception as e:
            st.error(f"Failed to process document: {str(e)}")
