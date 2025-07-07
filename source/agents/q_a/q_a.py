from .prompt import QA_PROMPT
from .schema import QARequest, QAResponse
from source.config.config import get_model
from source.agents.orchestrator.schema import AgentState
import ast

llm = get_model()
from typing import Optional
from pydantic import BaseModel

# class QARequest(AgentState):
#     question: str
#     max_length: Optional[int] = 400
#     temperature: Optional[float] = 0.3
#     #language: str = "fr"
#     q_a_result: Optional[str] = None  # ajout optionnel pour stocker la réponse

# class QAResponse(BaseModel):
#     answer: str
#     status: str = "success"

async def generate_answer(state: AgentState) -> AgentState:  # ← Return AgentState instead of dict
    print("HELLO Q_A agent")
    
    try:
        question = state.messages[-1].content if state.messages else ""
        prompt = QA_PROMPT.get_qa_prompt(question)

        response = llm(
            prompt,
            max_tokens=400,
            temperature=0.3,
            stream=False
        )
        print("LLM ANSWER RESPONSE ",response)

        answer = ""
        # ... (keep your existing response processing logic)
          # 💡 Supposons que `response` est un dictionnaire avec une clé "text" ou similaire
        if isinstance(response, str):
            answer = response
        elif isinstance(response, dict) and "text" in response:
            answer = response["text"]
        elif hasattr(response, "choices") and len(response.choices) > 0:
            answer = response.choices[0].text
        else:
            answer = str(response)  # fallback

        # Nettoyage facultatif
        if "Réponse :" in answer:
            answer = answer.split("Réponse :")[1].strip()
        print("ANSWER TYPE::",type(answer))

       

        # Convertir le string en dictionnaire Python
        data = ast.literal_eval(answer)

        # Extraire le texte
        text = data['choices'][0]['text']

        print("THIS IS THE ANSWER")
        print(text)
        # Update the state instead of returning dict
        state.q_a_result = text
        return state  # ← Critical change

    except Exception as e:
        print(f"❌ Error generating answer: {str(e)}")
        state.q_a_result = f"Error: {str(e)}"
        return state