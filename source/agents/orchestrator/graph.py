from .schema import AgentState,AnswerReturn

from langgraph.graph import StateGraph, START, END
from source.agents.generator_clauses.generator import generate_legal_clause
from source.agents.q_a.q_a import generate_answer
from langchain_community.chat_models import ChatOllama
from source.agents.summarizer.graph import create_summarizer_graph
from source.agents.rag.graphrag import create_graph_rag
# from langchain_core.runnables.base import RunnableLambda
# import asyncio 
from langchain_core.messages import AIMessage

from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
)

llm = ChatOllama(
    model="interstellarninja/hermes-2-pro-llama-3-8b",  # Note: "llama3.1" might not exist—try "llama3" or "llama2"
    temperature=0,
)
"""Main graph builder that compiles all sub-graphs."""

ROUTER_PROMPT = """
You are a routing assistant.

Decide if the user's message is a:
- question → respond: q_a
- generation task → respond: generator
- summary → respond: summary
- rag request -> respond: rag

Context:
{context}

Respond with only one word: q_a or generator.
"""


async def route_message(state: AgentState) -> AgentState:
    """Route les messages vers le bon agent en retournant le nom de la route sous forme de string."""
    print("ROUTER MESSAGE FUNCTION EXECUTING")
    
    # Vérification initiale robuste
    if not hasattr(state, 'messages') or not state.messages:
        return {"routing_decision": "q_a"}

    try:
        last_msg = state.messages[-1].content
        
        # Règle de routage directe
        if isinstance(last_msg, str) and last_msg.startswith("GENERATE:"):
            return {"routing_decision": "generator"}
        if isinstance(last_msg, str) and last_msg.startswith("SUMMARY:"):
            return {"routing_decision": "summary"}
        if isinstance(last_msg, str) and last_msg.startswith("RETREIVE:"):
            return {"routing_decision": "rag"}

        # Préparation du contexte avec vérification
        context_msgs = [msg for msg in state.messages[-3:] if hasattr(msg, 'content')]
        context = "\n".join(
            f"{getattr(msg, '__class__', type(msg)).__name__}: {msg.content}" 
            for msg in context_msgs
        )

        # Appel LLM avec gestion d'erreur
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(ROUTER_PROMPT)
        ])
        chain = prompt | llm
        try:
            response = await chain.ainvoke({"context": context})
            print("LLM RESPONSE:", response)

            raw = response.content.strip().lower()
            print("RAW:",raw)

        except Exception as e:
            print(f"LLM ROUTING ERROR: {type(e).__name__} - {str(e)}")
        # Parsing robuste de la réponse
        if raw not in {"q_a", "generator","summary","rag"}:
            raise ValueError(f"Invalid route: {raw}")
        else :return {"routing_decision": raw}

    except Exception as e:
        print(f"ROUTING ERROR: {type(e).__name__} - {str(e)}")
        return {"routing_decision": "q_a"}  # Fallback toujours sous forme de string


async def synthesize_response(state: AgentState) -> AnswerReturn:
    #routing_decision = state.get("routing_decision", "")
    parts = []
    if state.generator_result:
        parts.append(f"✍️ **Generated Text**:\n{state.generator_result}")
    if state.q_a_result:
        parts.append(f"❓ **Answer**:\n{state.q_a_result}")
    if state.summarizer_response:
        parts.append(f"✍️ **SUMMARIZED Text**:\n{state.summarizer_response}")
    if state.graphrag_response:
        parts.append(f"✍️ **RAG Text**:\n{state.graphrag_response}")
    

    print(parts)
    if not parts:
        #return {"messages": [AIMessage(content="No results available.")]}
        AnswerReturn(messages=[AIMessage(content="No results available.")])
    
    final_response = "\n\n".join(parts)
    print("FINAL RESPONSE IN SYNTHETIZE :",final_response)
    #return {"messages": [AIMessage(content=final_response)]}

    return AnswerReturn(messages=[AIMessage(content=final_response)])

def create_graph():
    
    try:
        print("WEYYYYYY GRAPH ROUTER")
        graph = StateGraph(AgentState)
        summarizer_graph=create_summarizer_graph()
        rag_graph=create_graph_rag()

        graph.add_node("router", route_message)
        graph.add_node("q_a", generate_answer)
        graph.add_node("generator", generate_legal_clause)
        graph.add_node("synthesize_response", synthesize_response)
        graph.add_node("rag", rag_graph)
        graph.add_node("summary",summarizer_graph)

        graph.add_edge(START, "router")

        graph.add_conditional_edges(
        "router",
        lambda x: x.routing_decision,  # Properly extracts the route
        {"q_a": "q_a", "generator": "generator","summary":"summary","rag":"rag"}
       )


        graph.add_edge("q_a", "synthesize_response")
        graph.add_edge("generator", "synthesize_response")
        graph.add_edge("rag", "synthesize_response")
        graph.add_edge("summary", "synthesize_response")
        graph.add_edge("synthesize_response", END)

        return graph.compile()
    except Exception as e:
        print(f"GRAPH ROUTER ERROR: {type(e).__name__} - {str(e)}")


# async def main():
#     # Test 1: Call with empty messages
#     empty_state = AgentState(messages=[])
#     result = await route_message(empty_state)
#     print(f"Empty state result: {result}")  # Should print "q_a"

#     # Test 2: Call with GENERATE command
#     generate_state = AgentState(messages=[HumanMessage(content="GENERATE: contract clause")])
#     result = await route_message(generate_state)
#     print(f"GENERATE command result: {result}")  # Should print "generator"

#     # Test 3: Call with normal question (requires mock LLM)
#     question_state = AgentState(messages=[HumanMessage(content="What is contract law?")])
#     result = await route_message(question_state)
#     print(f"Question result: {result}")  # Depends on your LLM response

# if __name__ == "__main__":
#     asyncio.run(main())