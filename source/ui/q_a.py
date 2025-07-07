import streamlit as st
import requests
from requests.exceptions import RequestException, ConnectionError, Timeout, ChunkedEncodingError
from typing import Iterator

st.title("⚖️ Legal Question Answering")
st.caption("Powered by your legal AI assistant")

# Configuration
BACKEND_URL = "http://localhost:8000/q_a"  # Update if your backend runs elsewhere
HEALTHCHECK_URL = "http://localhost:8000/health"

# Sidebar for parameters
# with st.sidebar:
#     st.header("Generation Parameters")
#     max_length = st.slider("Max Response Length", 100, 1000, 400)
#     temperature = st.slider("Temperature (Creativity)", 0.1, 1.0, 0.3)

# Main interface
question = st.text_area(
    "Enter your legal question:",
    placeholder="e.g., 'Ask me'"
)

def stream_qa_response(question: str) -> Iterator[str]:
    """Generator that yields chunks from the streaming response"""
    try:
        with requests.post(
            BACKEND_URL,
            json={
                "question": question,
                "language": "en",
                "max_length": 200,
                "temperature": 0.3
            },
            stream=True,
            timeout=30  # Adjust as needed
        ) as response:
            if response.status_code != 200:
                raise RuntimeError(f"Backend error {response.status_code}: {response.text}")

            for chunk in response.iter_content(chunk_size=None):
                if chunk:
                    try:
                        yield chunk.decode("utf-8")
                    except UnicodeDecodeError:
                        yield "[ERROR: Unable to decode chunk]\n"

    except (ConnectionError, Timeout):
        raise RuntimeError("Backend connection failed or timed out.")
    except ChunkedEncodingError:
        raise RuntimeError("Stream was interrupted — the response ended prematurely.")
    except RequestException as e:
        raise RuntimeError(f"Request error: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error during streaming: {e}")

def is_backend_available() -> bool:
    try:
        response = requests.get(HEALTHCHECK_URL, timeout=5)
        return response.status_code == 200
    except RequestException:
        return False

if st.button("Get Answer"):
    if not question.strip():
        st.warning("Please enter a question.")
    elif not is_backend_available():
        st.error("Backend service unavailable. Please ensure your FastAPI server is running.")
    else:
        with st.spinner("Researching your legal question..."):
            try:
                # Create a placeholder for streaming output
                answer_placeholder = st.empty()
                full_answer = ""
                
                # Stream the response
                for chunk in stream_qa_response(question):
                    full_answer += chunk
                    answer_placeholder.markdown(full_answer)
                
                answer_placeholder.markdown(f"## Answer\n{full_answer}")

            except RuntimeError as e:
                st.error(f"{e}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")
