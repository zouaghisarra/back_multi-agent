import streamlit as st
import requests
import PyPDF2
from io import BytesIO
from requests.exceptions import RequestException, ConnectionError, Timeout, ChunkedEncodingError

st.title("📄 Streamlined Document Analyzer")
st.caption("Real-time contract analysis with streaming")

# Configuration
BACKEND_URL = "http://localhost:8000/analyse"

def extract_text_from_pdf(uploaded_file) -> str:
    """Extracts text from PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(BytesIO(uploaded_file.getvalue()))
        document_text = "\n".join([page.extract_text() for page in pdf_reader.pages])
        return document_text if document_text.strip() else None
    except PyPDF2.PdfReadError:
        return None

def stream_analyse_response(document_text: str):
    """Streams analysis response from backend"""
    try:
        buffer = ""
        with requests.post(
            BACKEND_URL,
            json={"extracted_text": document_text},
            stream=True,
            timeout=30,
            headers={"Accept": "text/event-stream"}
        ) as response:
            response.raise_for_status()
            
            for chunk in response.iter_content(chunk_size=8192):  # Increased chunk size
                if chunk:
                    try:
                        decoded = chunk.decode('utf-8').strip()
                        if decoded:
                            # Preserve word boundaries
                            buffer += decoded
                            last_space = buffer.rfind(' ')
                            if last_space > 0:
                                yield buffer[:last_space] + ' '
                                buffer = buffer[last_space+1:]
                    except UnicodeDecodeError:
                        yield "[ERROR: Unable to decode chunk]"
            
            # Yield any remaining content
            if buffer:
                yield buffer
    
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Connection error: {str(e)}")
# Main UI
uploaded_file = st.file_uploader("Upload employment contract (PDF)", type="pdf")

if uploaded_file and st.button("Analyze Contract"):
    with st.spinner("Extracting text..."):
        document_text = extract_text_from_pdf(uploaded_file)
        
        if not document_text:
            st.error("Failed to extract text (scanned/encrypted PDF?)")
            st.stop()
        
        st.success("Text extracted successfully!")
        st.divider()
        
        # Setup analysis display
        analysis_placeholder = st.empty()
        full_analysis = ""
        
        st.subheader("Real-time Analysis")
        
        # Process streaming response
        try:
            for chunk in stream_analyse_response(document_text):
                full_analysis += chunk
                
                # Update display - no need for rerun in modern Streamlit
                analysis_placeholder.markdown(full_analysis)
            
            # Final output
            st.divider()
            st.subheader("Final Analysis Report")
            st.markdown(full_analysis)
            
            # Debug info
            with st.expander("Debug Info"):
                st.code(f"Text length: {len(document_text)} characters")
                st.code(f"Analysis length: {len(full_analysis)} characters")
                
        except Exception as e:
            st.error(f"Analysis failed: {str(e)}")