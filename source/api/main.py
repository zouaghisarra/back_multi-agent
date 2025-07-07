import os
from fastapi import FastAPI, HTTPException
import json
from pydantic import BaseModel
# from source.agents.generator_clauses.generator import generate_legal_clause
# from source.agents.q_a.q_a import generate_answer
# from source.agents.summarizer.graph import create_summarizer_graph
# from source.agents.q_a.schema import QARequest
from typing import Literal, Optional
from fastapi.responses import StreamingResponse
from fastapi.responses import PlainTextResponse
from source.agents.orchestrator.graph import create_graph
import traceback
#from typing import List
from source.agents.orchestrator.schema import AgentState
from langchain_core.messages import HumanMessage
from fastapi.middleware.cors import CORSMiddleware

from source.agents.rag.process_data import process_document

app = FastAPI()


# ----------------------------
# Configuration CORS
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ----------------------------
# Request Models
# ----------------------------

# class ClauseRequest(BaseModel):
#     description: str
#     language: Literal["fr", "en"] = "fr"
#     max_length: int = 300
#     temperature: float = 0.7

# class SummarizeRequest(BaseModel):
#     document: str
#     chunk_size: Optional[int] = None
#     chunk_overlap: Optional[int] = None
#     temperature: float = 0.3
#     max_summary_tokens: int = 150


# Request Schema (for FastAPI endpoint)
class RouterRequest(BaseModel):
    current_query: str       # The new query to process
    #user_id: Optional[str] = None 
    file_path:Optional[str]=None

# ----------------------------
# Endpoints
# ----------------------------

# @app.post("/generate-clause")
# async def generate_clause_endpoint(request: ClauseRequest):
#     """Endpoint for generating legal clauses"""
#     try:
#         return StreamingResponse(
#             generate_legal_clause(
#                 clause_description=request.description,
#                 language=request.language,
#                 max_length=request.max_length,
#                 temperature=request.temperature
#             ),
#             media_type="text/plain"
#         )
#     except Exception as e:
#         print(f"❌ Error in generating clause: {e}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error generating clause: {str(e)}"
#         )

# @app.post("/q_a")
# async def q_a_endpoint(request: QARequest):
#     """Endpoint for question answering"""
#     try:
#         return StreamingResponse(
#             generate_answer(question=request.question,
#                 max_length=request.max_length,
#                 temperature=request.temperature,
#                 language=request.language),
#             media_type="text/plain"
#         )
#     except Exception as e:
#         print(f"❌ Error in answering question: {e}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error answering question: {str(e)}"
#         )
# @app.post("/summarize")
# async def summarize_document(request: SummarizeRequest):
#     print("✅ Received summarization request")
#     print(f"Document length: {len(request.document)} chars")
    
#     try:
#         app = create_summarizer_graph()
      
        
#         initial_state = {
#             "document": request.document,
#             "chunks": [],
#             "chunk_summaries": [],
#             "final_summary": None
#         }
        
#         # Debug: Print initial state
#         print(f"Initial state: {initial_state.keys()}")
        
#         # Execute with intermediate checks
#         result = await app.ainvoke(initial_state)
        
#         # Debug: Print workflow execution trace
#         print("\nWorkflow Execution Trace:")
#         print(f"1. Chunks generated: {len(result.get('chunks', []))}")
#         print(f"2. Chunk summaries: {len(result.get('chunk_summaries', []))}")
#         print(f"3. Final summary present: {'final_summary' in result}")
        
#         if not result.get("final_summary"):
#             print("❌ Failed at:", 
#                   "Chunking" if not result.get("chunks") else
#                   "Chunk Summarization" if not result.get("chunk_summaries") else
#                   "Final Summarization")
#             raise HTTPException(status_code=400, detail="Pipeline failed at intermediate step")
        
#         return {"summary": result["final_summary"]}
        
#     except Exception as e:
#         print(f"❌ Full error trace:\n{traceback.format_exc()}")
#         raise HTTPException(status_code=500, detail=str(e))


graph = create_graph()  # suppose create_graph() est synchrone, sinon await

# @app.post("/router")
# async def router_endpoint(request: RouterRequest):
#     try:
#         print("hi router")

#         # Création de l'état initial
#         initial_state = AgentState(
            
#             messages=[HumanMessage(content=request.current_query)],
#             input_document=request.file_path,
#             extracted_document=None,
#             summarizer_response=None,
#             routing_decision=None,
#             generator_result=None,
#             graphrag_response=None,
#             q_a_result=None
#         )

#         # ✅ Conversion de l'état en dict pour LangGraph
#         state_dict = initial_state.dict()
#         print("DEBUG - state_dict contents:", state_dict)

#         async def event_generator():
#             async for item in graph.astream(state_dict):
                
#                 print("Current item (raw):", item)

#                 # item est un dict, donc on peut utiliser .get()
#                 content = item.get("q_a_result") or item.get("generator_result") or str(item)

#                 yield json.dumps({"content": content}) + "\n"

#         return StreamingResponse(event_generator(), media_type="application/json")

#     except Exception as e:
#         print(f"❌ Error router: {e}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error router: {str(e)}"
#         )

@app.post("/router")
async def router_endpoint(request: RouterRequest):
    try:
        print("Router endpoint called")
        
        # 1. Validate graph is initialized
        if graph is None:
            raise HTTPException(
                status_code=503,
                detail="Graph workflow not initialized"
            )

        # 2. Create initial state with default routing
        initial_state = AgentState(
            messages=[HumanMessage(content=request.current_query)],
            input_document=request.file_path,
            extracted_document=None,
            summarizer_response=None,
            routing_decision=None,  # Hardcoded default
            generator_result=None,
            graphrag_response=None,
            q_a_result=None
        )

        # 3. Convert state to dict
        state_dict = initial_state.dict()
        print(f"DEBUG - Initial state: {state_dict}")

        # 4. Streaming response
        # async def event_generator():
        #     async for item in graph.astream(state_dict):
        #         content = (
        #             item.get("q_a_result") 
        #             or item.get("generator_result")
        #             or item.get("graphrag_response")
        #             or str(item)
        #         )
        #         yield json.dumps({"content": content}) + "\n"

        # return StreamingResponse(
        #     event_generator(),
        #     media_type="application/json"
        # )
        async def event_generator():
            async for item in graph.astream(state_dict):
                synth_response = item.get("synthesize_response")

                if synth_response:
                    try:
                        messages = synth_response.get("messages")
                        if messages and isinstance(messages, list):
                            for msg in messages:
                                # Use .content attribute (not dict)
                                content = getattr(msg, "content", "")
                                yield json.dumps({"content": content}) + "\n"
                        else:
                            yield json.dumps({"content": str(synth_response)}) + "\n"
                    except Exception as e:
                        yield json.dumps({"content": f"⚠️ Error parsing synthesize_response: {str(e)}"}) + "\n"

        return StreamingResponse(
            event_generator(),
            media_type="application/json"
        )
    except Exception as e:
        print(f"Router error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Router processing error: {str(e)}"
        )
import base64
import tempfile

class PDFRequest(BaseModel):
    base64_pdf: str
    filename: Optional[str] = "document.pdf"
    metadata: Optional[dict] = {}

@app.post("/process-pdf/")
async def process_pdf_endpoint(request: PDFRequest):
    try:
        # Décoder le base64
        pdf_data = base64.b64decode(request.base64_pdf)
        
        # Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(pdf_data)
            temp_path = temp_pdf.name
        
        # Traitement du PDF - Modification ici pour passer les arguments correctement
        metadata_dict = request.metadata or {"source": request.filename}
        metadata_dict["filename"] = request.filename
        
        process_document(
            file_path=temp_path,
            meta=metadata_dict,  # Changé de 'metadata' à 'meta'
            images=False,
            max_char=1000,
            new_after_n_chars=800,
            combine=200
        )
        
        # Nettoyage
        os.unlink(temp_path)
        
        return {"status": "success", "message": "PDF processed successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint for service monitoring"""
    return {"status": "ok"}



