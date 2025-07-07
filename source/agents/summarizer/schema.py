"""Schemas for the summarizer agent."""

from typing import Annotated,List, Optional
from typing import TypedDict
import operator
from pydantic import BaseModel, Field
from source.agents.orchestrator.schema import AgentState
from transformers import pipeline

# Main state for the summarizer agent
class SummarizerState(AgentState):
    """Main state for the summarizer agent."""

    # input_document_content: Optional[str] = Field(
    #     default=None,
    #     description="Pre-processed text content of the document to be summarized",
    # )
    # document: str = Field(
    #     default="",
    #     description="Original document processed by the node (can be same as input_document_content or derived)",
    # )
    chunks: List[str] = Field(
        default_factory=list, description="Document split into chunks"
    )
    summaries: Annotated[List[str], operator.add] = Field(
        default_factory=list,
        description="Individual chunk summaries (uses add reducer)",
    )
    final_summary: Optional[str] = Field(
        default=None, description="Final combined summary"
    )
    is_short_document: bool = False 





class ChunkSizeRecommendation(BaseModel):
    """Structured output for chunk size recommendation."""

    chunk_size: int = Field(
        description="Recommended chunk size in tokens", gt=99, lt=4001
    )
    chunk_overlap: int = Field(
        description="Recommended overlap size in tokens", gt=19, lt=501
    )
    reasoning: str = Field(description="Brief explanation for the recommendation")


class ChunkState(TypedDict):
    """State for processing individual document chunks."""

    chunk: str
    chunk_id: int


class Summarize_chunk_response(TypedDict):
    """Response schema for chunk summarization."""
    summaries: List[str]


# # Schema Definitions
# class SummarizerResponse(TypedDict):
#     """Response structure for summarization results."""
#     chunk_summaries: List[str]
#     final_summary: str
#     num_chunks: int
#     metadata: Dict[str, float | str | int]


class Final_Summary_Response:
    """Final summary response container."""
    final_summary: str

