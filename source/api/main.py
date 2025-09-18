# import json
# from pydantic import BaseModel
# from source.agents.generator_clauses.generator import generate_legal_clause
# from source.agents.q_a.q_a import generate_answer
# from source.agents.summarizer.graph import create_summarizer_graph
# from source.agents.q_a.schema import QARequest
# from typing import Literal, Optional
# from fastapi.responses import StreamingResponse
# from fastapi.responses import PlainTextResponse
# from source.agents.orchestrator.graph import create_graph
# import traceback
#from typing import List
# from source.agents.orchestrator.schema import AgentState
# from langchain_core.messages import HumanMessage
from fastapi.middleware.cors import CORSMiddleware

# from source.agents.rag.process_data import process_document



from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
import os

from source.agents.researcher.my_research_agent import HuggingFaceResearcher
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


# # Request Schema (for FastAPI endpoint)
# class RouterRequest(BaseModel):
#     current_query: str       # The new query to process
#     #user_id: Optional[str] = None 
#     file_path:Optional[str]=None

# # ----------------------------
# # Endpoints
# # ----------------------------

# # @app.post("/generate-clause")
# # async def generate_clause_endpoint(request: ClauseRequest):
# #     """Endpoint for generating legal clauses"""
# #     try:
# #         return StreamingResponse(
# #             generate_legal_clause(
# #                 clause_description=request.description,
# #                 language=request.language,
# #                 max_length=request.max_length,
# #                 temperature=request.temperature
# #             ),
# #             media_type="text/plain"
# #         )
# #     except Exception as e:
# #         print(f"❌ Error in generating clause: {e}")
# #         raise HTTPException(
# #             status_code=500,
# #             detail=f"Error generating clause: {str(e)}"
# #         )

# # @app.post("/q_a")
# # async def q_a_endpoint(request: QARequest):
# #     """Endpoint for question answering"""
# #     try:
# #         return StreamingResponse(
# #             generate_answer(question=request.question,
# #                 max_length=request.max_length,
# #                 temperature=request.temperature,
# #                 language=request.language),
# #             media_type="text/plain"
# #         )
# #     except Exception as e:
# #         print(f"❌ Error in answering question: {e}")
# #         raise HTTPException(
# #             status_code=500,
# #             detail=f"Error answering question: {str(e)}"
# #         )
# # @app.post("/summarize")
# # async def summarize_document(request: SummarizeRequest):
# #     print("✅ Received summarization request")
# #     print(f"Document length: {len(request.document)} chars")
    
# #     try:
# #         app = create_summarizer_graph()
      
        
# #         initial_state = {
# #             "document": request.document,
# #             "chunks": [],
# #             "chunk_summaries": [],
# #             "final_summary": None
# #         }
        
# #         # Debug: Print initial state
# #         print(f"Initial state: {initial_state.keys()}")
        
# #         # Execute with intermediate checks
# #         result = await app.ainvoke(initial_state)
        
# #         # Debug: Print workflow execution trace
# #         print("\nWorkflow Execution Trace:")
# #         print(f"1. Chunks generated: {len(result.get('chunks', []))}")
# #         print(f"2. Chunk summaries: {len(result.get('chunk_summaries', []))}")
# #         print(f"3. Final summary present: {'final_summary' in result}")
        
# #         if not result.get("final_summary"):
# #             print("❌ Failed at:", 
# #                   "Chunking" if not result.get("chunks") else
# #                   "Chunk Summarization" if not result.get("chunk_summaries") else
# #                   "Final Summarization")
# #             raise HTTPException(status_code=400, detail="Pipeline failed at intermediate step")
        
# #         return {"summary": result["final_summary"]}
        
# #     except Exception as e:
# #         print(f"❌ Full error trace:\n{traceback.format_exc()}")
# #         raise HTTPException(status_code=500, detail=str(e))


# graph = create_graph()  # suppose create_graph() est synchrone, sinon await

# # @app.post("/router")
# # async def router_endpoint(request: RouterRequest):
# #     try:
# #         print("hi router")

# #         # Création de l'état initial
# #         initial_state = AgentState(
            
# #             messages=[HumanMessage(content=request.current_query)],
# #             input_document=request.file_path,
# #             extracted_document=None,
# #             summarizer_response=None,
# #             routing_decision=None,
# #             generator_result=None,
# #             graphrag_response=None,
# #             q_a_result=None
# #         )

# #         # ✅ Conversion de l'état en dict pour LangGraph
# #         state_dict = initial_state.dict()
# #         print("DEBUG - state_dict contents:", state_dict)

# #         async def event_generator():
# #             async for item in graph.astream(state_dict):
                
# #                 print("Current item (raw):", item)

# #                 # item est un dict, donc on peut utiliser .get()
# #                 content = item.get("q_a_result") or item.get("generator_result") or str(item)

# #                 yield json.dumps({"content": content}) + "\n"

# #         return StreamingResponse(event_generator(), media_type="application/json")

# #     except Exception as e:
# #         print(f"❌ Error router: {e}")
# #         raise HTTPException(
# #             status_code=500,
# #             detail=f"Error router: {str(e)}"
# #         )

# @app.post("/router")
# async def router_endpoint(request: RouterRequest):
#     try:
#         print("Router endpoint called")
        
#         # 1. Validate graph is initialized
#         if graph is None:
#             raise HTTPException(
#                 status_code=503,
#                 detail="Graph workflow not initialized"
#             )

#         # 2. Create initial state with default routing
#         initial_state = AgentState(
#             messages=[HumanMessage(content=request.current_query)],
#             input_document=request.file_path,
#             extracted_document=None,
#             summarizer_response=None,
#             routing_decision=None,  # Hardcoded default
#             generator_result=None,
#             graphrag_response=None,
#             q_a_result=None
#         )

#         # 3. Convert state to dict
#         state_dict = initial_state.dict()
#         print(f"DEBUG - Initial state: {state_dict}")

#         # 4. Streaming response
#         # async def event_generator():
#         #     async for item in graph.astream(state_dict):
#         #         content = (
#         #             item.get("q_a_result") 
#         #             or item.get("generator_result")
#         #             or item.get("graphrag_response")
#         #             or str(item)
#         #         )
#         #         yield json.dumps({"content": content}) + "\n"

#         # return StreamingResponse(
#         #     event_generator(),
#         #     media_type="application/json"
#         # )
#         async def event_generator():
#             async for item in graph.astream(state_dict):
#                 synth_response = item.get("synthesize_response")

#                 if synth_response:
#                     try:
#                         messages = synth_response.get("messages")
#                         if messages and isinstance(messages, list):
#                             for msg in messages:
#                                 # Use .content attribute (not dict)
#                                 content = getattr(msg, "content", "")
#                                 yield json.dumps({"content": content}) + "\n"
#                         else:
#                             yield json.dumps({"content": str(synth_response)}) + "\n"
#                     except Exception as e:
#                         yield json.dumps({"content": f"⚠️ Error parsing synthesize_response: {str(e)}"}) + "\n"

#         return StreamingResponse(
#             event_generator(),
#             media_type="application/json"
#         )
#     except Exception as e:
#         print(f"Router error: {str(e)}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Router processing error: {str(e)}"
#         )
# import base64
# import tempfile

# class PDFRequest(BaseModel):
#     base64_pdf: str
#     filename: Optional[str] = "document.pdf"
#     metadata: Optional[dict] = {}

# @app.post("/process-pdf/")
# async def process_pdf_endpoint(request: PDFRequest):
#     try:
#         # Décoder le base64
#         pdf_data = base64.b64decode(request.base64_pdf)
        
#         # Créer un fichier temporaire
#         with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
#             temp_pdf.write(pdf_data)
#             temp_path = temp_pdf.name
        
#         # Traitement du PDF - Modification ici pour passer les arguments correctement
#         metadata_dict = request.metadata or {"source": request.filename}
#         metadata_dict["filename"] = request.filename
        
#         process_document(
#             file_path=temp_path,
#             meta=metadata_dict,  # Changé de 'metadata' à 'meta'
#             images=False,
#             max_char=1000,
#             new_after_n_chars=800,
#             combine=200
#         )
        
#         # Nettoyage
#         os.unlink(temp_path)
        
#         return {"status": "success", "message": "PDF processed successfully"}
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

from source.agents.researcher.utils.show_prompts import format_messages
from source.agents.scope.test_scope import show_prompt 
from source.agents.scope.prompts import clarify_with_user_prompt , transform_messages_prompt
from source.agents.researcher.utils.utils import get_today_str
from langchain_core.messages import HumanMessage
from source.agents.researcher.research_agent import researcher_agent
from source.agents.scope.agent import scope_agent
from datetime import datetime

from rich.console import Console
from rich.text import Text
from rich.markdown import Markdown as RichMarkdown
from fastapi.responses import JSONResponse
from langchain_core.messages import HumanMessage
from source.agents.workflows.main_workflow import  main_agent , RootState
import uuid
from source.agents.workflows.session_store import _active_conversations
from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
from rich.panel import Panel

# Console pour les logs (optionnel)
console = Console()
# === ENDPOINT 1 : Health Check (simple) ===
# @app.get("/health")
# async def health_check():
#     """Health check endpoint for service monitoring"""
#     return {"status": "ok"}
# @app.get("/test1")
# async def health_check():
#         # === TEST 1 : Requête floue → clarification ===
#     console.print(Panel("🧪 TEST 1 : Requête floue", style="bold red", expand=False))

#     initial_state = {
#         "messages": [
#             HumanMessage(content="Je veux une recherche sur la loi travail en France.")
#         ],
#         "country": "France",
#         "official_domains": ["legifrance.gouv.fr"]
#     }

#     console.print("📥 Entrée initiale :")
#     format_messages(initial_state["messages"])

#     # === Étape 1 : clarify_node ===
#     console.print("\n🔍 [bold]Étape 1 : clarify_node[/bold]")
#     show_prompt(
#         clarify_with_user_prompt.format(
#             messages="\n".join([f"{m.type.upper()}: {m.content}" for m in initial_state["messages"]]),
#             date=get_today_str()
#         ),
#         title="📝 Prompt envoyé à clarify_node"
#     )

#     # Exécuter clarify_node
#     result = scope_agent.invoke(initial_state)

#     console.print("\n💬 [green]Réponse de clarify_node :[/green]")
#     last_msg = result["messages"][-1]
#     console.print(Panel(last_msg.content, title="🤖 Assistant", border_style="green"))
#     print(type(result))
#     if "?" in last_msg.content:
#         console.print("✅ [bold green]Décision : clarification nécessaire → arrêt[/bold green]")
#     else:
#         console.print("⚠️ [bold yellow]Le brief va être généré...[/bold yellow]")
#     return {"status": "ok"}

# @app.get("/test2")
# async def health_check():
#     # === TEST 2 : Requête claire → génération brief ===
#     console.print(Panel("🧪 TEST 2 : Requête claire", style="bold green", expand=False))

#     clear_state = {
#         "messages": [
#             HumanMessage(content="Je veux une analyse des dernières modifications de la loi Travail en France (2023-2024), avec les articles modifiés, les impacts sur les salariés à temps partiel, et les sources officielles (laws-lois.justice.gc.ca)."),
#         ],
#         "country": "Canada",
#         "official_domains": ["laws-lois.justice.gc.ca"]
#     }
    

#     intermediate = scope_agent.invoke(clear_state)


#     return {"status": f"📄 research_brief :\n{intermediate['research_brief']}"}


# === ENDPOINT 2 : Recherche juridique paramétrée ===
@app.post("/research/legal")
async def legal_research(
    country: str,
    query: str,
    
    language: str = "fr",
    conversation_id: str = None 
):
    try:
         # --- 1. Gérer l'ID de conversation ---
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())
            new_conversation = True
        else:
            new_conversation = False

        country_domains = {"France": "gouv.fr", "Canada": "canada.ca", "Maroc": "gov.ma"}
        country_domain = country_domains.get(country, "gov")
        official_domains = {
            "France": "legifrance.gouv.fr,courdecassation.fr",
            "Canada": "laws-lois.justice.gc.ca",
            "Maroc": "majid.alouina.gov.ma"
        }.get(country, "official.site")

        if new_conversation:
            # Nouvelle conversation
            state = RootState(
                messages=[HumanMessage(content=query)],
                research_topic=query,
                country=country,
                country_domain=country_domain,
                official_domains=official_domains,
                tool_call_iterations=0,
                compressed_research="",
                research_brief="",
                raw_notes=[],
                final_answer=""  # ou champ spécifique
            )
            _active_conversations[conversation_id] = state
        else:
            # Charger la conversation existante
            if conversation_id not in _active_conversations:
                raise HTTPException(status_code=404, detail="Conversation not found")
            state = _active_conversations[conversation_id]
            # Ajouter le nouveau message
            state["messages"].append(HumanMessage(content=query))


        # main.py   
        result = main_agent.invoke(state)
        # print(result["messages"])

        # --- 4. Sauvegarder le nouvel état ---
        _active_conversations[conversation_id] = result  # Mettre à jour l'état

       # --- 5. Détecter si on est en attente ou terminé ---
        # Hypothèse : si `compressed_research` est rempli → fini
        if result.get("compressed_research") and len(result["compressed_research"]) > 10:
            return JSONResponse({
                "status": "complete",
                "conversation_id": conversation_id,
                "final_answer": result["compressed_research"],
                "query": query,
                "country": country,
                "timestamp": datetime.now().isoformat()
            })

        # Sinon, l'agent a dû poser une question via scope
        last_message = result["messages"][-1]
        if isinstance(last_message, AIMessage):
            return JSONResponse({
                "status": "awaiting_response",
                "query": query,
                "country": country,
                "conversation_id": conversation_id,
                "question": last_message.content,
                "timestamp": datetime.now().isoformat()
            })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

