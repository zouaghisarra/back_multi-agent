class QA_PROMPT:
    def get_qa_prompt(question: str) -> str:
        """
        Generates the prompt for legal QA
        Args:
            question: The legal question to be answered
        Returns:
            Formatted prompt string
        """
        return f"Question juridique : {question}\nRéponse :"