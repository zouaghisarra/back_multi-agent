class Generator_PROMPT:
    @staticmethod
    def get_prompt(description: str) -> str:
        """
        Generates a legal clause prompt in either French or English.
        Returns a clean string (never a list or dict) to prevent concatenation errors.
        
        Args:
            description: The clause description from user input
            
        Returns:
            str: Formatted prompt string
        """
        # Detect language from description (simple check for French words)
        language = "fr" if any(fr_word in description.lower() 
                             for fr_word in ["données", "confidentialité", "personnelles"]) else "en"
        
        template = f"""Rédigez une clause juridique professionnelle qui:
1. Description: {description}
2. Exigences:
   - Précision juridique
   - Structure claire
   - Conformité au droit {'français' if language == 'fr' else 'common law'}
3. Format:
   - Titre explicite
   - Définitions si nécessaire
   - Portée claire
   - Durée si applicable
   - Sanctions en cas de violation

Clause:""" if language == "fr" else f"""Draft a professional legal clause that:
1. Description: {description}
2. Requirements:
   - Legally precise
   - Clear structure
   - Compliant with {'French law' if language == 'fr' else 'common law'}
3. Format:
   - Explicit title
   - Definitions if needed
   - Clear scope
   - Duration if applicable
   - Remedies for violation

Clause:"""

        # Ensure we return a clean string
        return str(template)