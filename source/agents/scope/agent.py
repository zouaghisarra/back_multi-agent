# agents/scope/agent.py
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END, START  # ✅ END et START importés
from langchain_ollama import ChatOllama
from source.agents.researcher.utils.utils import get_today_str
from rich.console import Console
from rich.panel import Panel

from source.agents.scope.test_scope import show_prompt
from .state import ScopeState, ClarifyWithUser, ResearchQuestion
from .prompts import clarify_with_user_prompt, transform_messages_prompt

# ===== CONFIGURATION DU MODÈLE =====
model = ChatOllama(model="mistral:latest", temperature=0.0)
console = Console()

# ===== NŒUD 1 : clarify_node =====
def clarify_node(state: ScopeState):
    """
    Décide s'il faut clarifier la demande utilisateur.
    Utilise la sortie structurée pour éviter l'hallucination.
    """
    structured_model = model.with_structured_output(ClarifyWithUser)

    # Format propre des messages
    formatted_messages = "\n".join([f"{m.type.upper()}: {m.content}" for m in state["messages"]])
    console.print("\n🔍 [bold]Étape 1 : clarify_node[/bold]")
    
    show_prompt(
        clarify_with_user_prompt.format(
            messages=formatted_messages,
            date=get_today_str()
        ),
        title="📄 Prompt pour clarifier"
    )
    response = structured_model.invoke([
        HumanMessage(content=clarify_with_user_prompt.format(
            messages=formatted_messages,
            date=get_today_str()
        ))
    ])
    console.print("\n💬 [green]Réponse de clarify_node :[/green]")
    console.print(Panel(str(response), title="🤖 Assistant", border_style="green"))

    if response.need_clarification:
        console.print(Panel(response.question, title="🤖 Assistant", border_style="green"))
        return {
            "messages": [AIMessage(content=response.question)]
        }
    else:
        console.print(Panel(response.verification, title="🤖 Assistant", border_style="green"))
        return {
            "messages": [AIMessage(content=response.verification)]
        }

# ===== NŒUD 2 : write_brief_node =====
def write_brief_node(state: ScopeState):
    """
    Génère un brief de recherche structuré à partir de la conversation.
    """
    structured_model = model.with_structured_output(ResearchQuestion)
    console.print("\n✅ [bold green]Pas de question → on passe à write_brief_node[/bold green]")

    formatted_messages = "\n".join([f"{m.type.upper()}: {m.content}" for m in state["messages"]])
    console.print("\n📝 [bold]Prompt de génération du brief[/bold]")
    show_prompt(
        transform_messages_prompt.format(
            messages=formatted_messages,
            date=get_today_str()
        ),
        title="📄 Prompt pour write_brief_node"
    )
    response = structured_model.invoke([
        HumanMessage(content=transform_messages_prompt.format(
            messages=formatted_messages,
            date=get_today_str()
        ))
    ])
     # Exécuter tout le graphe (déjà fait par invoke)
    console.print("\n📋 [bold blue]Résultat final[/bold blue]")
    console.print(f"📄 research_brief :\n{response.research_brief}")
   
    return {
        "research_brief": response.research_brief,
        "country": state.get("country", "France"),  # ✅ Garde la valeur existante
        "official_domains": state.get("official_domains", ["legifrance.gouv.fr"])
    }

# ===== GRAPHE : Construction du workflow =====
builder = StateGraph(ScopeState)

builder.add_node("clarify_node", clarify_node)
builder.add_node("write_brief_node", write_brief_node)

# Début du graphe
builder.add_edge(START, "clarify_node")

# === FLUX CONDITIONNEL CORRIGÉ ===
def route_after_clarify(state: ScopeState):
    """
    Décide où aller après clarify_node.
    - Si besoin de clarification → END (on envoie la question)
    - Sinon → write_brief_node
    """
    # On regarde le dernier message
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage):
        if "?" in last_message.content:
            console.print(Panel("besoin de clarification → END (on envoie la question)", title="🤖 Assistant", border_style="green"))
            return END  # C'est une question → on arrête
        else:
            console.print(Panel("write_brief_node", title="🤖 Assistant", border_style="green"))
            return "write_brief_node"
    return "write_brief_node"

# ✅ Utilisation correcte de add_conditional_edges
builder.add_conditional_edges(
    "clarify_node",
    route_after_clarify,
    {
        "write_brief_node": "write_brief_node",
        END: END
    }
)

# Après write_brief → fin
builder.add_edge("write_brief_node", END)

# Compilation
scope_agent = builder.compile()