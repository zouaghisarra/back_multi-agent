"""Core schemas for agent system."""

from typing import Annotated, List, Optional, Union

from langchain_core.messages import BaseMessage
from langgraph.prebuilt.chat_agent_executor import AgentStatePydantic
from pydantic import BaseModel, Field
from typing import List, Union,Literal
from langchain_core.messages import HumanMessage, AIMessage


# Agent State
class AgentState(AgentStatePydantic):
    """Base state for all agents."""

    # Common state
    try:
        #messages: Annotated[List[HumanMessage], "accumulate"]
        messages:List[HumanMessage]          
        input_document: Optional[str] = None
        extracted_document: Optional[str] = None
        summarizer_response: Optional[str] = None
        routing_decision: Optional[Literal["q_a", "generator","summary","rag"]]=None  
        # Agent-specific state - only one will be populated based on routing
        graphrag_response: Optional[str] = None
        #summarizer_response: Optional[Union[Dict[str, Any], Any]] = None
        #document_content: Optional[str] = None
        generator_result: Optional[str] = None
        q_a_result: Optional[str] = None
    except Exception as e:
        print(f"SCHEMA ERROR: {type(e).__name__} - {str(e)}")



# Node Return Types


class SummaryReturn(BaseModel):
    """Return type for summary node."""

    summary: str
    messages: List[BaseMessage] = Field(default_factory=list)


class AnswerReturn(BaseModel):
    """Return type for answer node."""

    messages: List[BaseMessage] = Field(default_factory=list)
