import sys,torch
from pathlib import Path
import tempfile
import os
from typing import Any,List
from pydantic import BaseModel
from langchain_core.documents import Document
from unstructured.partition.pdf import partition_pdf
# Ajoute la racine du projet à sys.path (2 ou 3 niveaux au-dessus)
sys.path.append(str(Path(__file__).resolve().parents[3]))
from typing import List, Dict, TypedDict
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langchain.text_splitter import RecursiveCharacterTextSplitter
from genaipy.extractors.pdf import extract_pages_text
# from genaipy.openai_apis.chat import get_chat_response
# from genaipy.prompts.build_prompt import build_prompt
import asyncio ,time
import base64
import logging
from langchain_community.chat_models import ChatOllama
from source.agents.summarizer.schema import (
    SummarizerState
)
# from source.agents.summarizer.prompt import (
#     CHUNK_SIZE_PROMPT,
#     CHUNK_SUMMARY_PROMPT,
#     FINAL_SUMMARY_PROMPT,
# )
from source.config.config import get_model

#PDF_PATH = "file/contrat.pdf"
model = get_model()
#model=ChatOllama(model="C:/Users/HP/legal-bart-summarizer/model.safetensors")

import torch
from source.config.config import get_model_summarizer
#tokenizer, mode, device = get_model_summarizer()

# Load model and tokenizer
import tiktoken

from io import BytesIO
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
llm=get_model()

class Element(BaseModel):
    type: str
    text: Any
def exterat_elements_from_pdf(file_path: str,
                              images: bool = False,
                              max_char: int = 1000,
                              new_after_n_chars: int = 800,
                              combine: int = 200) -> List[Document]:
    # Define parameters for Unstructured's library
    strategy = "hi_res"  # Strategy for analyzing PDFs and extracting table structure
    model_name = "yolox"  # Best model for table extraction

    raw_pdf_elements = partition_pdf(
        filename=file_path,
        extract_images_in_pdf=images,
        infer_table_structure=True,
        chunking_strategy="by_title",
        max_characters=max_char,
        new_after_n_chars=new_after_n_chars,
        combine_text_under_n_chars=combine,
        image_output_dir_path="./",
        strategy=strategy,
        model_name=model_name
    )

    logging.info("  ↳ %d elements extracted", len(raw_pdf_elements))

    category_counts = {}
    for element in raw_pdf_elements:
        category = str(type(element))
        if category in category_counts:
            category_counts[category] += 1
        else:
            category_counts[category] = 1

    categorized_elements = []
    for element in raw_pdf_elements:
        if "unstructured.documents.elements.Table" in str(type(element)):
            categorized_elements.append(Element(type="table", text=str(element.metadata.text_as_html)))
        elif "unstructured.documents.elements.CompositeElement" in str(type(element)):
            categorized_elements.append(Element(type="text", text=str(element)))

    # Tables
    table_elements = [e for e in categorized_elements if e.type == "table"]
    table_elements = [Document(page_content=i.text) for i in table_elements if i.text != ""]

    # Text
    text_elements = [e for e in categorized_elements if e.type == "text"]
    documents = [Document(page_content=i.text) for i in text_elements if i.text != ""]

    documents.extend(table_elements)

    return documents

def extract_pages_text(pdf_stream: BytesIO):
    pages_dict = {}
    pdf_stream.seek(0)  # Remet au début du stream
    for i, page_layout in enumerate(extract_pages(pdf_stream)):
        texts = []
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                texts.append(element.get_text())
        page_text = "".join(texts).strip()
        pages_dict[i] = {"content": page_text}
    return pages_dict

def pdf_bytes_to_temp_file(pdf_bytes: bytes) -> str:
    """
    Convertit des bytes PDF en fichier temporaire.
    Retourne le chemin du fichier temporaire.
    Ce fichier est supprimé automatiquement après utilisation.
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            tmpfile.write(pdf_bytes)
            tmpfile_path = tmpfile.name
        return tmpfile_path
    except Exception as e:
        raise RuntimeError(f"❌ Échec de la création du fichier temporaire : {e}")

def process_pdf_node_test(pdf_bytes: bytes) -> str:
    try:
        pdf_stream = BytesIO(pdf_bytes)
        pages = extract_pages_text(pdf_stream)
        logging.info(f"✅ Chargement réussi de {len(pages)} pages.")

        # Concatène uniquement les pages ayant du texte
        full_text = "\n".join(
            page["content"] for page in pages.values() if page["content"]
        )
        logging.info(f"✅ Texte extrait (500 premiers caractères) :\n{full_text}...")
        return full_text

    except Exception as e:
        logging.error(f"❌ Erreur lors du traitement du PDF : {e}")
        raise

def process_pdf_node(full_path: str) -> str:  # ← Changement du type de retour
    try:
        if not full_path:
            raise ValueError("❌ Le chemin ou contenu du document est vide (NoneType)")
        logging.info(f"✅ Successfully ****************** {full_path} .")

        # Décoder le base64 en bytes
        pdf_bytes = base64.b64decode(full_path)
        # Extraire le texte

        path=pdf_bytes_to_temp_file(pdf_bytes)
        pdf_text = exterat_elements_from_pdf(path)

        # pages = extract_pages_text(pdf_path=full_path)
        # logging.info(f"✅ Successfully loaded text from {len(pages)} PDF pages.")
        print("****************PDF EXTRACT PROCESS PDF NODE",pdf_text)
        # Concaténer toutes les pages en une seule chaîne
        # full_text = "\n".join(page["content"] for page in pages.values())
        return pdf_text
        
    except Exception as e:
        logging.error(f"❌ Error processing PDF: {e}")
        raise

   

MAX_TOKENS = 900  # Limite que ton modèle peut gérer (souvent 1024, 2048 ou plus)



def chunk_document_node(state: SummarizerState) -> SummarizerState:
    print("HELLO SUMMARY:")
    
    # Extraction
    docs = process_pdf_node(state.input_document)

    # Concatenate all Document contents into one string
    full_text = "\n".join(doc.page_content for doc in docs)
    # Encodage pour vérifier le nombre de tokens
    state.extracted_document = full_text

    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(state.extracted_document)
    #print("********LENGTH OF TOKENS:",len(tokens))

    if len(tokens) <= MAX_TOKENS:
        # Document court : un seul chunk avec un id
        state.chunks = [{"chunk_id": 0, "chunk": state.extracted_document}]
        state.is_short_document = True
    else:
        # Document trop long : découpage
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=MAX_TOKENS,
            length_function=lambda text: len(encoding.encode(text)),
            chunk_overlap=100
        )
        chunks = text_splitter.split_text(state.extracted_document)
        
        # Ajout d'un chunk_id unique à chaque morceau
        state.chunks = [
            {"chunk_id": i, "chunk": chunk_text}
            for i, chunk_text in enumerate(chunks)
        ]
        state.is_short_document = False
    print("********************THE CHUNKS",state.chunks)
    return state


async def summarize_chunks_node(state: SummarizerState) -> SummarizerState:
    summaries = []
    for chunk in state.chunks:
        chunk_id = chunk["chunk_id"]
        raw_chunk_text = chunk["chunk"].strip()
        try:
            chunk_text = clean_text(raw_chunk_text)
            prompt = (
                "Summarize the following contract clause in 3–5 clear and concise sentences. "
                "Focus on key parties and terms, main obligations, compensation and duration, "
                "and important legal conditions or limitations.\n\n"
                f"Clause:\n{chunk_text.strip()}"
            )

            # inputs = tokenizer(chunk_text, return_tensors="pt", truncation=True, max_length=512)
            # print("*********INPUTS:",inputs)
            #         # Passez les inputs tokenisés au modèle
            # response = mode.generate(
            #             input_ids=inputs["input_ids"],
            #             attention_mask=inputs["attention_mask"],
            #             temperature=0.3,
            #             max_length=300,
            #             top_p=0.9,
            #             num_beams=4,
            #             early_stopping=True
            #         )
            #   # Détokenisez la réponse
            # summary = tokenizer.decode(response[0], skip_special_tokens=True)
            # print("*********** SUMMARY OF RESPONSE",summary)       

   
            response = llm(
            prompt,
            max_tokens=400,
            temperature=0.3,
            stream=False
        )   
            print("***************LLM RESPONSE:",response)
            # Extract summary from the OpenAI-style response
            if isinstance(response, dict) and "choices" in response:
                summary = response["choices"][0]["text"].strip()
            else:
                summary = str(response)  # Fallback if format is unexpected

            #Clean up the summary (remove trailing headers if present)
            summary = summary.split("<|end_header_id|>")[-1].strip()

            # Add warning if summary ends abruptly
            if summary and summary[-1] not in (".", "!", "?"):
                summary += " [⚠️ Incomplete]"
            summaries.append(summary)
            print(f"✅ Chunk {chunk_id} summarized: {summary}...")
        except Exception as e:
            summaries.append(f"[❌ Error summarizing chunk {chunk_id}: {str(e)}]")
    state.summaries = summaries
    print("**********Summarized text",state.summaries)
    return state

def clean_text(text: str) -> str:
    """Nettoie les textes d'entrée pour supprimer les caractères indésirables."""
    if not isinstance(text, str):
        return ""
    return (
        text.replace("", "")
        .replace("\xa0", " ")
        .replace("ÃÂ", "")
        .replace("¯¯¯¯¯¯¯¯", "")
        .strip()
    )


async def summarize_final_result_node(state: SummarizerState) -> SummarizerState:
    """
    Generate a final summary by summarizing the list of chunk summaries.
    """
    try:
        if state.is_short_document and len(state.summaries) == 1:
            print("⚠️ Short document detected: skipping final summary generation.")
            state.summarizer_response = state.summaries[0]
            return state
        # Combiner les résumés
        combined_summaries = "\n".join(f"- {s}" for s in state.summaries if s.strip())
        print("*********************** COMBINED IN THE PROMPT ",combined_summaries)
        # Créer le prompt
        prompt = f"""You are a legal assistant. Based on the following summaries of an employment contract, write a complete and concise final summary in 3–5 sentences. Focus on:
        - Key terms and obligations
        - Roles of each party
        - Compensation and duration
        - Important legal conditions

        Summaries:
        {combined_summaries}

        Respond ONLY with the final summary. Be clear and professional."""

        try:
            response = llm(
                prompt,
                max_tokens=400,
                temperature=0.3,
                stop=None,
                stream=False
            ) 
            print("**********LLM FINAL RESPONSE:",response)
        except Exception as e:
            print("ERROR IN LLM FINAL RESPONSE:",e)
        if isinstance(response, dict) and "choices" in response:
                final_summary=response["choices"][0]["text"].strip()
        else:

                final_summary= str(response)
        
        print("*****************************Final summary generated.", type(final_summary), final_summary)
        state.summarizer_response = final_summary

        return state

    except Exception as e:
        print(f"❌ Error generating final summary: {e}")
        state.summarizer_response = "[Error generating final summary]"
        return state
    

# Build the workflow
def create_summarizer_graph():
    workflow = StateGraph(SummarizerState)
    #workflow.add_edge(START, "process_pdf")
   

    # Add nodes (converted to state-aware functions)
    workflow.add_node("chunk_document", chunk_document_node)
    workflow.add_node("summarize_chunks", summarize_chunks_node)
    workflow.add_node("generate_final_summary", summarize_final_result_node)

    # Define flow
    workflow.add_edge("chunk_document", "summarize_chunks")
    workflow.add_edge("summarize_chunks", "generate_final_summary")
    workflow.add_edge("generate_final_summary", END)
    workflow.add_edge(START, "chunk_document")
    workflow.add_edge("summarize_chunks", END)


    return workflow.compile()