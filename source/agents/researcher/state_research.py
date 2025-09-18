
"""
State Definitions and Pydantic Schemas for Research Agent

This module defines the state objects and structured schemas used for
the research agent workflow, including researcher state management and output schemas.
"""

import operator
from typing_extensions import TypedDict, Annotated, List, Sequence
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
class Summary(BaseModel):
    """Schema for webpage content summarization."""
    summary: str = Field(
        description="Concise, factual summary of the webpage content, including key context such as document type, date, and legal relevance."
    )
    key_excerpts: List[str] = Field(
        description="List of exact quotes or excerpts from the legal text or error message. Max 5 items. Verbatim only."
    )
# ===== STATE DEFINITIONS =====

class ResearcherState(TypedDict):
    researcher_messages: Annotated[Sequence[BaseMessage], add_messages]
    tool_call_iterations: int
    research_brief: str
    country: str
    country_domain: str
    official_domains: List[str]  # ✅ Doit être une liste, pas une chaîne
    raw_notes: Annotated[List[Summary], operator.add]  # ✅ raw_notes contient des objets Summary, pas des str
    compressed_research: str  # Le rapport final structuré

class ResearcherOutputState(TypedDict):
    compressed_research: str
    raw_notes: Annotated[List[Summary], operator.add]

# ===== STRUCTURED OUTPUT SCHEMAS =====

class ClarifyWithUser(BaseModel):
    """Schema for user clarification decisions during scoping phase."""
    need_clarification: bool = Field(
        description="Whether the user needs to be asked a clarifying question.",
    )
    question: str = Field(
        description="A question to ask the user to clarify the report scope",
    )
    verification: str = Field(
        description="Verify message that we will start research after the user has provided the necessary information.",
    )

class ResearchQuestion(BaseModel):
    """Schema for research brief generation."""
    research_brief: str = Field(
        description="A research question that will be used to guide the research.",
    )

