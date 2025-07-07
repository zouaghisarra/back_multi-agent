from .prompt import Generator_PROMPT
from source.config.config import get_model
from source.agents.orchestrator.schema import AgentState
llm = get_model()

def generate_legal_clause(state:AgentState)->AgentState:
    print("HI generator")
    try:
        question = state.messages[-1].content if state.messages else ""
        prompt = Generator_PROMPT.get_prompt(question)
    except Exception as e:
        print(f"❌ PROMT PROBLEM: {str(e)}")
    try:
        response = llm(
                prompt,
                max_tokens=400,
                temperature=0.3,
                stream=False
            )
        print("LLM RESPONSE STRUCTURE:", type(response), response)
    except Exception as e:
        print(f"❌ LLM PROBLEM: {str(e)}")

    try:
        
        response = llm(
            prompt,
            max_tokens=400,
            temperature=0.3,
            stream=False
        )
        print("LLM RESPONSE STRUCTURE:", type(response), response)
        # for chunk in response:
        #     if 'choices' in chunk:
        #         text = chunk["choices"][0]["text"]
        #         yield text  # This makes it a generator function
        

        answer = ""
        # # ... (keep your existing response processing logic)
        #   # 💡 Supposons que `response` est un dictionnaire avec une clé "text" ou similaire
        # if isinstance(response, str):
        #     answer = response
        # elif isinstance(response, dict) and "text" in response:
        #     answer = response["text"]
        # elif hasattr(response, "choices") and len(response.choices) > 0:
        #     answer = response.choices[0].text
        # else:
        #     answer = str(response)  # fallback

        # Extraction spécifique des choices
        if isinstance(response, dict):
            if 'choices' in response and len(response['choices']) > 0:
                answer = response['choices'][0]['text']
            else:
                answer = "No valid choices in response"
        else:
            answer = "Unexpected response format"
        

        # Nettoyage facultatif
        if "Réponse :" in answer:
            answer = answer.split("Réponse :")[1].strip()
        print("ANSWER TYPE::",type(answer))

        # Update the state instead of returning dict
        state.generator_result = answer
        print("THIS IS THE GENERATOR CLAUSE",answer)
        return state  # ← Critical change
        
    except Exception as e:
        print(f"❌ Error generating clause: {str(e)}")
        state.generator_result = f"Error: {str(e)}"
        return state