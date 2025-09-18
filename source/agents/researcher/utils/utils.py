
"""Research Utilities and Tools.

This module provides search and content processing utilities for the research agent,
including web search capabilities and content summarization tools.
"""

import os
from pathlib import Path
from datetime import datetime
from typing_extensions import Annotated, List, Literal

from langchain.chat_models import init_chat_model 
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool, InjectedToolArg
from tavily import TavilyClient

from source.agents.researcher.state_research import Summary
from source.agents.researcher.prompts import summarize_webpage_prompt
from llama_cpp import Llama

# ===== UTILITY FUNCTIONS =====
from dotenv import load_dotenv
load_dotenv()  # Charge .env
from langchain_ollama import ChatOllama



def get_today_str() -> str:
    """Get current date in a human-readable format."""
    now = datetime.now()
    formatted = now.strftime("%a %b %d, %Y")
    print(formatted)
    return formatted.replace(" 0", " ")  # "May 05" → "May 5", "May 15" → "May 15"

def get_current_dir() -> Path:
    """Get the current directory of the module.

    This function is compatible with Jupyter notebooks and regular Python scripts.

    Returns:
        Path object representing the current directory
    """
    try:
        return Path(__file__).resolve().parent
    except NameError:  # __file__ is not defined
        return Path.cwd()

# ===== CONFIGURATION =====

# summarization_model = init_chat_model(model="openai:gpt-4.1-mini")

# ✅ Modèle rapide pour résumer des pages web
# summarization_model = ChatGoogleGenerativeAI(
#     model="gemini-1.5-flash",
#     temperature=0.3,
#     max_tokens=8192,
#     api_key=os.getenv("GOOGLE_API_KEY")  # Doit être dans ton .env
# )
summarization_model = ChatOllama(
    model="mistral:latest" ,
    temperature=0.3,
    num_ctx=8192,
    base_url="http://localhost:11434"

)

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# ===== SEARCH FUNCTIONS =====

def tavily_search_multiple(
    search_queries: List[str], 
    max_results: int = 3, 
    topic: Literal["general", "news", "finance" , "legal"] = "general", 
    include_raw_content: bool = True, 
) -> List[dict]:
    """Perform search using Tavily API for multiple queries.

    Args:
        search_queries: List of search queries to execute
        max_results: Maximum number of results per query
        topic: Topic filter for search results
        include_raw_content: Whether to include raw webpage content

    Returns:
        List of search result dictionaries
    """

    # Execute searches sequentially. Note: yon can use AsyncTavilyClient to parallelize this step.
    search_docs = []
    for query in search_queries:
        result = tavily_client.search(
            query,
            max_results=max_results,
            include_raw_content=include_raw_content,
            topic=topic
        )
        search_docs.append(result)

    return search_docs

def summarize_webpage_content(webpage_content: str) -> str:
    """Summarize webpage content with legal precision."""
    try:
        structured_model = summarization_model.with_structured_output(Summary)
        summary = structured_model.invoke([
            HumanMessage(content=summarize_webpage_prompt.format(
                webpage_content=webpage_content,
                date=get_today_str()
            ))
        ])

        # Format avec balises claires
        return (
            f"<summary>{summary.summary}</summary>\n"
            f"<excerpts>{summary.key_excerpts}</excerpts>"
        )
    except Exception as e:
        print(f"Failed to summarize webpage: {str(e)}")
        return f"<summary>{webpage_content[:1000]}...</summary>"

def deduplicate_search_results(search_results: List[dict]) -> dict:
    """Remove duplicate results by URL."""
    unique_results = {}
    for response in search_results:
        for result in response.get('results', []):
            url = result['url']
            if url not in unique_results:
                unique_results[url] = {
                    'title': result['title'],
                    'url': url,
                    'content': result.get('content', ''),
                    'raw_content': result.get('raw_content', '')
                }
    return unique_results

def process_search_results(unique_results: dict) -> dict:
    """Process results: use raw content if available, summarize it."""
    summarized_results = {}
    for url, result in unique_results.items():
        content = result['raw_content'] or result['content']
        if result['raw_content']:
            content = summarize_webpage_content(result['raw_content'])
        
        summarized_results[url] = {
            'title': result['title'],
            'url': url,
            'content': content
        }
    return summarized_results

def format_search_output(summarized_results: dict) -> str:
    """Format results with clear source attribution and URLs."""
    if not summarized_results:
        return "No valid search results found."

    output = "🔍 SEARCH RESULTS WITH SOURCES:\n\n"
    for i, (url, result) in enumerate(summarized_results.items(), 1):
        output += f"📄 [{i}] {result['title']}\n"
        output += f"🔗 {url}\n"
        output += f"📝 {result['content']}\n"
        output += "\n" + "-" * 80 + "\n"
    return output

# ===== RESEARCH TOOLS =====

@tool(parse_docstring=True)
def tavily_search(
    query: str,
    max_results: Annotated[int, InjectedToolArg] = 3,
    topic: Annotated[Literal["general", "news", "finance"  , "legal"], InjectedToolArg] = "general",
) -> str:
    """Fetch results from Tavily search API with content summarization.

    Args:
        query: A single search query to execute
        max_results: Maximum number of results to return
        topic: Topic to filter results by ('general', 'news', 'finance')

    Returns:
        Formatted string of search results with summaries
    """
    # Execute search for single query
    search_results = tavily_search_multiple(
        [query],  # Convert single query to list for the internal function
        max_results=max_results,
        topic=topic,
        include_raw_content=True,
    )

    # Deduplicate results by URL to avoid processing duplicate content
    unique_results = deduplicate_search_results(search_results)

    # Process results with summarization
    summarized_results = process_search_results(unique_results)

    # Format output for consumption
    return format_search_output(summarized_results)

@tool(parse_docstring=True)
def think_tool(reflection: str) -> str:
    """Tool for strategic reflection on research progress and decision-making.

    Use this tool after each search to analyze results and plan next steps systematically.
    This creates a deliberate pause in the research workflow for quality decision-making.

    When to use:
    - After receiving search results: What key information did I find?
    - Before deciding next steps: Do I have enough to answer comprehensively?
    - When assessing research gaps: What specific information am I still missing?
    - Before concluding research: Can I provide a complete answer now?

    Reflection should address:
    1. Analysis of current findings - What concrete information have I gathered?
    2. Gap assessment - What crucial information is still missing?
    3. Quality evaluation - Do I have sufficient evidence/examples for a good answer?
    4. Strategic decision - Should I continue searching or provide my answer?

    Args:
        reflection: Your detailed reflection on research progress, findings, gaps, and next steps

    Returns:
        Confirmation that reflection was recorded for decision-making
    """
    return f"Reflection recorded: {reflection}"