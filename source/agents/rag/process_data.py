import os
import pickle
from llama_cpp import Llama
import json
import json_repair
from langchain_community.chat_models import ChatOllama
from typing import Any,List
from pydantic import BaseModel
from langchain_core.documents import Document
from unstructured.partition.pdf import partition_pdf
from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_experimental.graph_transformers.llm import UnstructuredRelation
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, PromptTemplate
from langchain_community.graphs.graph_document import GraphDocument, Node, Relationship
from langchain_community.graphs import Neo4jGraph
import logging, json
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
# Initialize graph and LLM
os.environ["NEO4J_URI"] = "bolt://localhost:7687"
os.environ["NEO4J_USERNAME"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "legal_tech"

graph = Neo4jGraph()

# llm = ChatOllama(model="interstellarninja/hermes-2-pro-llama-3-8b",
#                  temperature=0.0,
#                  num_ctx=2048,
#                  stop=["<|im_end|>"])
llm = ChatOllama(
    model="interstellarninja/hermes-2-pro-llama-3-8b",
    temperature=0.0,
    top_p=0.3,  # Lower than default (0.9)
    repeat_penalty=1.5,  # Stronger than default (1.1)
    num_ctx=2048,
    stop=["<|im_end|>"],
    top_k=20  # Lower than default (40)
)


class Element(BaseModel):
    type: str
    text: Any

def exterat_elements_from_pdf(file_path: str, 
                              metadata: dict,
                              images: bool = False, 
                              max_char: int = 1000, 
                              new_after_n_chars: int = 800,
                              combine: int = 200,) -> List[Document]:
    # Define parameters for Unstructured's library
    strategy = "hi_res" # Strategy for analyzing PDFs and extracting table structure
    model_name = "yolox" # Best model for table extraction. Other options are detectron2_onnx and chipper depending on file layout
    # Extract images, tables, and chunk text
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
    print("*****The type of result of partition:",type(raw_pdf_elements))
    print("*****Result of partition:",raw_pdf_elements)

    # Create a dictionary to store counts of each type
    category_counts = {}

    for element in raw_pdf_elements:
        category = str(type(element))
        if category in category_counts:
            category_counts[category] += 1
        else:
            category_counts[category] = 1
    print("*******Store counts of each type:",category_counts)

    # Unique_categories will have unique elements
    # TableChunk if Table > max chars set above
    #unique_categories = set(category_counts.keys())


    # Categorize by type
    categorized_elements = []
    for element in raw_pdf_elements:
        if "unstructured.documents.elements.Table" in str(type(element)):
            categorized_elements.append(Element(type="table", text=str(element.metadata.text_as_html)))
        elif "unstructured.documents.elements.CompositeElement" in str(type(element)):
            categorized_elements.append(Element(type="text", text=str(element)))
    
    print("******** Categorize by type:",categorized_elements)

    # Tables
    table_elements = [e for e in categorized_elements if e.type == "table"]
    table_elements = [Document(page_content=i.text, metadata=metadata) for i in table_elements if i.text != ""]

    print("******Table elements:",table_elements)
    # Text
    text_elements = [e for e in categorized_elements if e.type == "text"]
    print("********* TEXT elements:",text_elements)
    documents = [Document(page_content=i.text, metadata=metadata) for i in text_elements if i.text != ""]
    
    documents.extend(table_elements)
    metaDoct = Document(page_content=json.dumps(metadata),metadata=metadata)
    print("******* META DOCT:",metaDoct)
    documents.append(metaDoct)
    print("******** FINAL Documents:",documents)
    return documents


examples = [
    # Example 1: Contract Parties (More precise entity types)
    {
        "text": "This Sub-Reseller Agreement is made between Salesforce.com, Inc. (‘SFDC’) and Acme Solutions LLC (‘Reseller’).",
        "head": "Salesforce.com, Inc.",
        "head_type": "Company",
        "relation": "IS_PARTY_TO",
        "tail": "Sub-Reseller Agreement",
        "tail_type": "Contract"
    },
    {
        "head": "Acme Solutions LLC",
        "head_type": "Company",
        "relation": "IS_PARTY_TO",
        "tail": "Sub-Reseller Agreement",
        "tail_type": "Contract"
    },

    # Example 2: Termination Clause (Clearer relationship)
    {
        "text": "Either Party may terminate this Agreement for cause upon thirty (30) days’ written notice.",
        "head": "Termination Clause",
        "head_type": "Clause",
        "relation": "ALLOWS_TERMINATION_BY",
        "tail": "Either Party",
        "tail_type": "Company"  # More accurate than "Party"
    },
    {
        "head": "Termination Clause",
        "head_type": "Clause",
        "relation": "REQUIRES_NOTICE_PERIOD",
        "tail": "30 days",
        "tail_type": "Duration"
    },

    # Example 3: Governing Law (Standardized jurisdiction)
    {
        "text": "This Agreement shall be governed by the laws of the State of Delaware.",
        "head": "Sub-Reseller Agreement",
        "head_type": "Contract",
        "relation": "GOVERNED_BY",
        "tail": "Delaware law",
        "tail_type": "Jurisdiction"  # Better than "Governing_Law"
    },

    # --- NEW EXAMPLES TO ADD ---
    # Example 4: Amendment Reference
    {
        "text": "This Agreement amends the Reseller Agreement dated August 1, 2015.",
        "head": "Sub-Reseller Agreement",
        "head_type": "Contract",
        "relation": "AMENDS",
        "tail": "Reseller Agreement",
        "tail_type": "Contract"
    },

    # Example 5: Conditional Clause
    {
        "text": "If either Party breaches this Agreement, the non-breaching Party may terminate immediately.",
        "head": "Termination Clause",
        "head_type": "Clause",
        "relation": "HAS_CONDITION",
        "tail": "Material breach by either Party",
        "tail_type": "Condition"
    },

    # Example 6: Definitions
    {
        "text": "‘Confidential Information’ means any non-public business information disclosed hereunder.",
        "head": "Sub-Reseller Agreement",
        "head_type": "Contract",
        "relation": "DEFINES_TERM",
        "tail": "Confidential Information",
        "tail_type": "Definition"
    }
]

# Create Prompt
def create_prompt():
    # base_string_parts = [
    #     "You are a top-tier algorithm designed for extracting information in "
    #     "structured formats to build a knowledge graph. Your task is to identify "
    #     "the entities and relations requested with the user prompt from a given "
    #     "text. You must generate the output in a JSON format containing a list "
    #     'with JSON objects. Each object should have the keys: "head", '
    #     '"head_type", "relation", "tail", and "tail_type". The "head" '
    #     "key must contain the text of the extracted entity with one type.",
    #     "Attempt to extract as many entities and relations as you can. Maintain "
    #     "Entity Consistency: When extracting entities, it's vital to ensure "
    #     'consistency. If an entity, such as "John Doe", is mentioned multiple '
    #     "times in the text but is referred to by different names or pronouns "
    #     '(e.g., "Joe", "he"), always use the most complete identifier for '
    #     "that entity. The knowledge graph should be coherent and easily "
    #     "understandable, so maintaining consistency in entity references is "
    #     "crucial.",
    #     "IMPORTANT NOTES:\n- Don't add any explanation and text.",
    # ]
    base_string_parts = [
    # Role and Objective
    "You are a legal contract analysis AI specialized in extracting structured entities and relationships from legal documents.",
    "Your task is to identify ONLY legal/commercial entities and their relationships, outputting JSON with strict schema compliance.",
    
    # Output Format
    'Generate JSON objects with these exact keys: "head", "head_type", "relation", "tail", "tail_type"',
    "Never include null values - omit any incomplete relationships instead.",
    
    # Entity Type Constraints
    "STRICTLY USE THESE ENTITY TYPES:",
    "- Organization/Company/LegalEntity (for all parties, signatories, etc.)",
    "- Contract/Agreement/Amendment (for legal documents)",
    "- Clause/Section/Provision (for contract clauses)",
    "- Jurisdiction/GoverningLaw",
    "- Duration/TimePeriod",
    "- Obligation/Restriction",
    "- Definition/Term",
    "- Condition/Trigger",
    "NEVER use 'Person' type - legal parties are always organizations.",
    
    # Relationship Guidelines
    "Common relationship types to extract:",
    "- IS_PARTY_TO, GOVERNS, AMENDS, CONTAINS_CLAUSE",
    "- DEFINES_TERM, SPECIFIES_JURISDICTION, HAS_CONDITION",
    "- REQUIRES_NOTICE, GRANTS_RIGHT, IMPOSES_OBLIGATION",
    
    # Quality Control
    "Entity Consistency Rules:",
    "1. Always use the full formal name (e.g., 'Salesforce.com, Inc.' not 'Salesforce')",
    "2. Maintain case sensitivity from original document",
    "3. Never infer pronouns - only extract explicitly named entities",
    
    # Anti-Hallucination Measures
    "STRICT PROHIBITIONS:",
    "- No hypothetical relationships",
    "- No interpretation beyond literal text",
    "- No 'Person' entities under any circumstances",
    "- No relationships without direct textual evidence",
    
    # Technical Requirements
    "Output exactly one valid JSON array per request.",
    "Never include explanatory text or markdown formatting.",
    "If no valid relationships exist, return empty array []."
    ]
    system_prompt = "\n".join(filter(None, base_string_parts))
    system_message = SystemMessage(content=system_prompt)
    parser = JsonOutputParser(pydantic_object=UnstructuredRelation)
    human_prompt = PromptTemplate(
        template="""Based on the following example, extract entities and 
relations from the provided text. Attempt to extract as many entities and relations as you can.\n\n

Below are a number of examples of text and their extracted entities and relationships.
{examples}

For the following text or table, extract entities and relations as in the provided example. Table is in HTML format.
{format_instructions}\nText: {input}
IMPORTANT NOTES:\n- Each key must have a valid value, 'null' is not allowed. \n- Don't add any explanation and text. \n- Extract information as much as possible""",
        input_variables=["input"],
        partial_variables={
            "format_instructions": parser.get_format_instructions(),
            "examples": examples,
        },
    )

    human_message_prompt = HumanMessagePromptTemplate(prompt=human_prompt)
    chat_prompt = ChatPromptTemplate.from_messages([system_message, human_message_prompt])
    return chat_prompt


prompt = create_prompt()
#llm_transformer = LLMGraphTransformer(llm=llm, prompt=prompt)
#json_repair = json_repair
chain = prompt | llm 

def process_response(document,i,j,metadata) -> GraphDocument:


    print("*****DOCUMENT :",document)
    print(f"processing document {i} out of {j}")

    print(f"\n▶ processing document {i+1}/{j}  "
          f"(size={len(document.page_content)} chars)")
    
    print("*****Document en cours :",document.page_content)
    
    raw_schema=chain.invoke({"input": document.page_content})
    parsed_json = json_repair.loads(raw_schema.content)

    print("*******THE OUTPUT OF LLM in json:",parsed_json)
    nodes_set = set()
    relationships = []
    # print(type(metadata))
    for rel in parsed_json:
        try:
            # Nodes need to be deduplicated using a set
            rel["head_type"] = rel["head_type"] if rel["head_type"] else "Unknown"
            rel["tail_type"] = rel["tail_type"] if rel["tail_type"] else "Unknown"
            nodes_set.add((rel["head"], rel["head_type"]))
            nodes_set.add((rel["tail"], rel["tail_type"]))
            source_node = Node(
                id=rel["head"],
                type=rel["head_type"]
            )
            target_node = Node(
                id=rel["tail"],
                type=rel["tail_type"]
            )
            relationships.append(
                Relationship(
                    source=source_node,
                    target=target_node,
                    type=rel["relation"]
                )
            )
        except:
            print(f"Error processing relation: {rel}")
    # Create nodes list
    print("******************FINAL RESULT:")
    nodes = [Node(id=el[0], type=el[1]) for el in list(nodes_set)]
    print("NODES :",nodes)
    print("RELATIONSHIPS :",relationships)
    return GraphDocument(nodes=nodes, relationships=relationships, source=document)


def flatten_json(y):
    out = {}

    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + '_')
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + '_')
                i += 1
        else:
            out[name[:-1]] = x

    flatten(y)
    return out

def process_document(file_path: str, 
                     meta: dict,
                    images: bool = False, 
                    max_char: int = 1000, 
                    new_after_n_chars: int = 800,
                    combine: int = 200) -> None:
    # metadata = json.dumps(meta)
    metadata = flatten_json(meta)
    pickle_file = f"output_{os.path.basename(file_path)}.pkl"  # Unique name per file
    if os.path.exists(pickle_file):
        with open(pickle_file, "rb") as f:
            text_summaries = pickle.load(f)#problem
    else:
        documents = exterat_elements_from_pdf(file_path,metadata,images,max_char,new_after_n_chars,combine)
        #problem
        text_summaries = [process_response(document,i,len(documents),metadata) for i,document in enumerate(documents)]
        with open(pickle_file, "wb") as f:
            pickle.dump(text_summaries, f)
        
    graph.add_graph_documents(text_summaries,
    baseEntityLabel=True, 
    include_source=True)


# CLI interaction
def cli():
    while True:
        action = input("\nEnter a PDF path or 'quit' to exit: ")
        if os.path.exists(action):
            _, ext = os.path.splitext(action)
            if ext == '.pdf':
                print("Processing document %s" % action)
                process_document(
                    action, 
                    {"source": action}, 
                    images=False,
                    max_char=1000,
                    new_after_n_chars=800,
                    combine=200,
                )
            else:
                try:
                    for file in os.listdir(action):
                        if file.endswith(".pdf"):
                            print("Processing document %s" % file)
                            process_document(
                                action + '/' + file, 
                                {"source": action}, 
                                images=False,
                                max_char=1000,
                                new_after_n_chars=800,
                                combine=200,
                            )
                except:
                    print("Invalid input.")
        elif action == 'quit':
            break

# def cli():
#     while True:
#         action = input("\nEnter a PDF path or 'quit' to exit: ").strip()
#         print("THE ACTION IS:",action)
#         metadata = {"source": action}

#         if action.lower() in {"quit", "exit"}:
#             break

#         if os.path.exists(action):
#             _, ext = os.path.splitext(action)
#             if ext.lower() == ".pdf":
#                 print(f"Processing document {action}")
#                 documents=exterat_elements_from_pdf(
#                     action,
#                     {"source": action},
#                     images=False,
#                     max_char=1000,
#                     new_after_n_chars=800,
#                     combine=200,
#                 )
#                 print(f"SECOND STEP:Processing response {action}")
#                 total = len(documents)
#                 graph_docs = []                # optional: collect results

#                 for idx, doc in enumerate(documents):
#                     gdoc = process_response(doc, idx, total, metadata)
#                     graph_docs.append(gdoc)    # keep if you need them later

#                 print(f"✓ Finished PDF ({total} chunks processed)\n")
#             else:
#                 print("The path exists but is not a PDF file.")
#         else:
#             print("File does not exist. Please enter a valid PDF path.")


if __name__ == "__main__":
     cli()


