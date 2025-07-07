import streamlit as st
import requests

st.title("Clause Generator")
st.caption("Powered by Llama.cpp")

# Sidebar controls
# with st.sidebar:
#     st.header("Generation Parameters")
#     language = st.radio("Language", ["fr", "en"], index=0)
#     max_length = st.slider("Max Length", 100, 1000, 300)
#     temperature = st.slider("Creativity", 0.1, 1.0, 0.7)

# Main interface
description = st.text_area("Describe the clause you need:",
                         placeholder="e.g., 'non-disclosure agreement for employees'")

def is_backend_reachable():
    try:
        response = requests.get("http://localhost:8000/health")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False

if st.button("Generate Clause"):
    if not description:
        st.warning("Please enter a description")
    else:
        if not is_backend_reachable():
            st.error("🚫 Could not connect to the backend (http://localhost:8000). "
                    "Make sure FastAPI is running.")
        else:
            with st.spinner("Generating legal clause..."):
                try:
                    # Create a placeholder for the streaming output
                    output_placeholder = st.empty()
                    full_response = ""
                    
                    # Make the streaming request
                    response = requests.post(
                        "http://localhost:8000/generate-clause",
                        json={
                            "description": description,
                            "language": "en",
                            "max_length": 200,
                            "temperature": 0.3
                        },
                        stream=True
                    )
                    
                    # Process the streaming response
                    for chunk in response.iter_content(chunk_size=None):
                        if chunk:
                            chunk_text = chunk.decode("utf-8")
                            full_response += chunk_text
                            # Update the placeholder with the current full response
                            output_placeholder.text_area(
                                "Result", 
                                value=full_response, 
                                height=300, 
                                label_visibility="collapsed"
                            )
                
                except requests.exceptions.ConnectionError:
                    st.error("🚫 Could not connect to the backend (http://localhost:8000). "
                            "Make sure FastAPI is running.")
                except Exception as e:
                    st.error(f"❌ Unexpected error: {str(e)}")