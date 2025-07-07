import os
import re
import sys
from pathlib import Path

# Ajoute la racine du projet à sys.path (2 ou 3 niveaux au-dessus)
#sys.path.append(str(Path(__file__).resolve().parents[3]))
from pathlib import Path
from langgraph.graph import StateGraph, START, END
from configparser import ConfigParser
from langchain_community.vectorstores import Neo4jVector
#from langchain_community.graphs import Neo4jGraph
from langchain_neo4j import Neo4jGraph
#from langchain_core.pydantic_v1 import BaseModel, Field
from pydantic import BaseModel, Field
from typing import Tuple, List, Optional
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
#from langchain_community.vectorstores.neo4j_vector import remove_lucene_chars
#from langchain_neo4j.vectorstores.neo4j_vector import remove_lucene_chars
try:
    from langchain_neo4j.vectorstores.neo4j_vector import remove_lucene_chars
    #from langchain_community.vectorstores.neo4j_vector import remove_lucene_chars
except ImportError as e:
    print(f"ImportError: {e}. Falling back to alternative implementation.")
    def remove_lucene_chars(text: str) -> str:
        return text 
from source.agents.rag.schema import RagState

import ast
# from langchain_core.runnables import (
#     RunnableBranch,
#     RunnableLambda,
#     RunnableParallel,
#     RunnablePassthrough,
# )
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings
#from langchain_ollama import ChatOllama, OllamaEmbeddings
# Initialize graph and LLM
os.environ["NEO4J_URI"] = "bolt://localhost:7687"
os.environ["NEO4J_USERNAME"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "legal_tech"

graph = Neo4jGraph()

from source.config.config import get_model

llm = ChatOllama(model="interstellarninja/hermes-2-pro-llama-3-8b",
                 temperature=0.0,
                 num_ctx=2048,
                 stop=["<|im_end|>"])

embeddings = OllamaEmbeddings(model="mxbai-embed-large")
vector_index = Neo4jVector.from_existing_graph(
    embeddings,
    search_type="hybrid",
    node_label="Document",
    text_node_properties=["text"],
    embedding_node_property="embedding"
        )

def unstructured_data_node(state: RagState) -> RagState:
    """Retrieve documents from vector store"""
    if not vector_index:
        raise ValueError("Vector index not initialized")
    
    question = state.messages[-1].content
  
    docs = vector_index.similarity_search(question, k=3)
    # Retriever
    graph.query("CREATE FULLTEXT INDEX entity IF NOT EXISTS FOR (e:__Entity__) ON EACH [e.id]")
    state.unstructured_data = [doc.page_content for doc in docs] if docs else None
    print("*********UNSRTUCTURED DATA:",type(state.unstructured_data),state.unstructured_data)
    return state


# Extract entities from text
class Entities(BaseModel):
    """Identifying information about entities."""

    names: List[str] = Field(
        ...,
        description="All the noun entities that "
        "appear in the text",
    )

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are extracting noun entities from the text. Don't include any explanation or text.",
        ),
        (
            "human",
            "Please extract all the noun entities into a list from the following "
            "input: {question}",
        ),
    ]
)

entity_chain = prompt | llm
def generate_full_text_query(input: str) -> str:
    """
    Generate a full-text search query for a given input string.

    This function constructs a query string suitable for a full-text search.
    It processes the input string by splitting it into words and appending a
    similarity threshold (~2 changed characters) to each word, then combines
    them using the AND operator. Useful for mapping entities from user questions
    to database values, and allows for some misspelings.
    """
    # print(input)
    full_text_query = ""
    words = [el for el in remove_lucene_chars(input).split() if el]
    if len(words) > 1:
        for word in words[:-1]:
            full_text_query += f" {word}~2 AND"
        full_text_query += f" {words[-1]}~2"
    else:
        full_text_query = f"{words[0]}~2"
    return full_text_query.strip()

# Fulltext index query
def structured_retriever(state: RagState) -> RagState:
    """
    Collects the neighborhood of entities mentioned
    in the question
    """
    print("HI PROCESS STRUCTURED DATA")
    question = state.messages[-1].content
    print("THIS IS THE QUERY:",question)
    result = ""
    structured_results = []
    entities = entity_chain.invoke({"question": question})
    # Add missing quotes around list elements
    fixed_content = re.sub(r'\[([^\'"\]]+)\]', r"['\1']", entities.content)
    list_entities = ast.literal_eval(fixed_content)
    for entity in list_entities:
        response = graph.query(
            """CALL db.index.fulltext.queryNodes('entity', $query, {limit:2})
            YIELD node,score
            CALL {
              WITH node
              MATCH (node)-[r:!MENTIONS]->(neighbor)
              RETURN node.id + ' - ' + type(r) + ' -> ' + neighbor.id AS output
              UNION ALL
              WITH node
              MATCH (node)<-[r:!MENTIONS]-(neighbor)
              RETURN neighbor.id + ' - ' + type(r) + ' -> ' +  node.id AS output
            }
            RETURN output LIMIT 50
            """,
            {"query": generate_full_text_query(entity)},
        )
        result += "\n".join([el['output'] for el in response])
        print("**********************THIS IS GRAPH OUTPUT::",result)
        structured_results.extend([el['output'] for el in response])
        print("*********SRTUCTURED DATA:",structured_results)
        state.structured_data = "\n".join(structured_results) if structured_results else None
    return state

def get_qa_prompt(context: str,question:str) -> str:
   
        return f"""Answer the question {question} based only on the following context:
            {context}

            Use natural language and be concise.
            Answer:"""

def stream_answer(response_stream):
    answer = ""
    for chunk in response_stream:
        if isinstance(chunk, str):
            answer_chunk = chunk
        elif isinstance(chunk, dict) and "choices" in chunk:
            answer_chunk = chunk["choices"][0].get("text", "")
        else:
            answer_chunk = str(chunk)  # Fallback

        answer += answer_chunk

            # Optional: remove leading preamble once, if present
        if "Réponse :" in answer:
            answer = answer.split("Réponse :", 1)[1].lstrip()

        yield str(answer_chunk)

def retriever(state: RagState):
    # print(f"Search query: {question}")
    structured = state.structured_data
    unstructured = state.unstructured_data
    final_data = f"""Structured data:
    {structured}
    Unstructured data:
    {"#Document ". join(unstructured)}
    """
    print("******** THIS IS THE COMBINED DATA:",final_data)
    chatbot=get_model()
    prompt = get_qa_prompt(final_data,state.messages[-1].content)
    response = chatbot(
            prompt,
            max_tokens=300,
            temperature=0.3,
            stream=True
        )
    answer=""
    for chunk in stream_answer(response):
       print(chunk, end="", flush=True)
       answer+=chunk

    state.graphrag_response=answer

    return state



def create_graph_rag():
    try:
        print("HELLO GRAPHRAG")
        workflow = StateGraph(RagState)
        workflow.add_node("structured_retriever",structured_retriever)
        workflow.add_node("unstructured_data_node", unstructured_data_node)
        workflow.add_node("retrival_node", retriever)

        workflow.add_edge("unstructured_data_node","retrival_node")
        workflow.add_edge("structured_retriever", "unstructured_data_node")

        workflow.add_edge(START, "structured_retriever")
        workflow.add_edge("retrival_node",END)
        return workflow.compile()
    except Exception as e:
        print(f"GRAPH CONSTRUCTION ERROR: {type(e).__name__} - {str(e)}")

# def create_graph_rag():
#     try:
#         print("HELLO GRAPHRAG")
#         workflow = StateGraph(RagState)

#         # Nodes
#         workflow.add_node("structured_retriever", structured_retriever)
#         workflow.add_node("unstructured_data_node", unstructured_data_node)
#         workflow.add_node("retrival_node", retriever)

#         # Parallel branches from START
#         workflow.add_edge(START, "structured_retriever")
#         workflow.add_edge(START, "unstructured_data_node")

#         # Both feed into retrival_node (it will wait for both states to be ready)
#         workflow.add_edge("structured_retriever", "retrival_node")
#         workflow.add_edge("unstructured_data_node", "retrival_node")

#         workflow.add_edge("retrival_node", END)

#         return workflow.compile()
#     except Exception as e:
#         print(f"GRAPH CONSTRUCTION ERROR: {type(e).__name__} - {str(e)}")




