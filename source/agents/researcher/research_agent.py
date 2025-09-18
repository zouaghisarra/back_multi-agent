"""Research Agent Implementation (Juridique, Paramétrable)."""

import os
from datetime import datetime
from typing_extensions import Literal
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, filter_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

from source.agents.researcher.state_research import ResearcherState, ResearcherOutputState
from source.agents.researcher.utils.utils import get_today_str
from source.agents.researcher.prompts import (
    research_agent_prompt,
    compress_research_system_prompt,
    compress_research_human_message
)
from source.agents.researcher.utils.utils import tavily_search, think_tool

# ===== CONFIGURATION =====
tools = [tavily_search , think_tool ]
tools_by_name = {tool.name: tool for tool in tools}

model = ChatOllama(
    model="mistral:latest" ,
    # model="mistral-nemo:latest" ,
    temperature=0.3,
    num_ctx=8192,
    base_url="http://localhost:11434"
)


# model = ChatGoogleGenerativeAI(
#     model="gemini-1.5-flash",
#     temperature=0.3,
#     max_tokens=8192,
#     api_key=os.getenv("GOOGLE_API_KEY")
# )

model_with_tools = model.bind_tools(tools)

# compress_model = ChatGoogleGenerativeAI(
#     model="gemini-1.5-flash",
#     temperature=0.2,
#     max_tokens=4096,
#     api_key=os.getenv("GOOGLE_API_KEY")
# )

compress_model = ChatOllama(
    # model="phi3:medium" ,
    model="mistral:latest" ,
    temperature=0.3,
    num_ctx=8192,
    base_url="http://localhost:11434"
)

# ===== NOEUDS =====
def llm_call(state: ResearcherState):
    country = state["country"]
    country_domain = state["country_domain"]
    official_domains = state["official_domains"]
    date_str = get_today_str()

    filled_prompt = research_agent_prompt.format(
        country=country,
        country_domain=country_domain,
        official_domains=official_domains,
        date=date_str
    )

    return {
        "researcher_messages": [
            model_with_tools.invoke([
                SystemMessage(content=filled_prompt)
            ] + state["researcher_messages"])
        ]
    }

def tool_node(state: ResearcherState):
    tool_calls = state["researcher_messages"][-1].tool_calls
    if not tool_calls:
        return {"researcher_messages": []}

    observations = []
    for tool_call in tool_calls:
        tool_name = tool_call.get("name")
        if not isinstance(tool_name, str) or tool_name not in tools_by_name:
            print(f"⚠️ Outil inconnu ou invalide : {tool_name}")
            continue
        tool = tools_by_name[tool_name]
        try:
            result = tool.invoke(tool_call["args"])
            observations.append(result)
        except Exception as e:
            print(f"❌ Échec invocation : {e}")
            observations.append(f"Erreur : {str(e)}")

    tool_messages = [
        ToolMessage(
            content=obs,
            name=tc["name"],
            tool_call_id=tc["id"]
        ) for obs, tc in zip(observations, tool_calls)
    ]

    return {"researcher_messages": tool_messages}

def compress_research(state: ResearcherState) -> dict:
    research_brief = state["research_brief"]
    date_str = get_today_str()

    try:
        system_filled = compress_research_system_prompt.format(
            research_brief=research_brief,
            date=date_str
        )
        human_filled = compress_research_human_message.format(
            research_brief=research_brief
        )
    except KeyError as e:
        raise ValueError(f"Variable manquante dans le prompt : {e}")

    messages = [
        SystemMessage(content=system_filled)
    ] + state.get("researcher_messages", []) + [
        HumanMessage(content=human_filled)
    ]

    response = compress_model.invoke(messages)

    raw_notes = [
        str(m.content) for m in filter_messages(
            state["researcher_messages"],
            include_types=["tool", "ai"]
        )
    ]

    return {
        "compressed_research": str(response.content),
        "raw_notes": ["\n".join(raw_notes)]
    }

def should_continue(state: ResearcherState) -> Literal["tool_node", "compress_research"]:
    last_message = state["researcher_messages"][-1]
    return "tool_node" if last_message.tool_calls else "compress_research"

# ===== GRAPHE =====
agent_builder = StateGraph(ResearcherState, output_schema=ResearcherOutputState)
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)
agent_builder.add_node("compress_research", compress_research)
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    {
        "tool_node": "tool_node",
        "compress_research": "compress_research",
    },
)
agent_builder.add_edge("tool_node", "llm_call")
agent_builder.add_edge("compress_research", END)

researcher_agent = agent_builder.compile()