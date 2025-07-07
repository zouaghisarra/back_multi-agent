from source.agents.orchestrator.schema import AgentState
#from pydantic import BaseModel

from typing import Optional,List

# Main state for the summarizer agent
class RagState(AgentState):
    full_text_query:Optional[str]=None
    #retrieval_results :Optional[str]=None
    structured_data: Optional[str]=None
    unstructured_data: Optional[List[str]]=None
