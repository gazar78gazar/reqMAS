"""
A/B Question Generator - Creates contextual binary questions using useCase.json
"""

from typing import Dict, List, Optional
from data.data_loader import data_loader

class ABQuestionGenerator:
    """Generate A/B questions based on conflicts and use cases."""
    
    def __init__(self):
        self.use_cases = data_loader.use_cases if hasattr(data_loader, 'use_cases') else {}
        self.form_fields = data_loader.form_fields if hasattr(data_loader, 'form_fields') else {}
    
    def generate_question(self, conflict: Dict, context: Dict) -> Dict:
        """
        Generate A/B question for conflict resolution.
        Uses useCase.json for context-aware questions.
        """
        conflict_type = conflict.get("type", "")
        
        if conflict_type == "budget":
            return self._generate_budget_question(conflict, context)
        elif conflict_type == "technical":
            return self._generate_technical_question(conflict, context)
        elif conflict_type == "ambiguous":
            return self._generate_clarification_question(conflict, context)
        
        # Default question
        return {
            "question": "Which option better fits your needs?",
            "option_a": {
                "label": "Option A",
                "description": "First alternative",
                "impact": "Default impact"
            },
            "option_b": {
                "label": "Option B", 
                "description": "Second alternative",
                "impact": "Alternative impact"
            },
            "context": "Please select the option that best matches your requirements"
        }
    
    def _generate_budget_question(self, conflict: Dict, context: Dict) -> Dict:
        """Generate budget-related A/B question."""
        over_budget = conflict.get("over_budget_amount", 0)
        current_cost = conflict.get("estimated_cost", 0)
        
        return {
            "question": f"Your configuration exceeds budget by ${over_budget:.2f}. What would you prefer?",
            "option_a": {
                "label": "Increase Budget",
                "description": f"Increase budget to ${current_cost:.2f} for full functionality",
                "impact": "Get all requested features with higher cost"
            },
            "option_b": {
                "label": "Reduce Features",
                "description": "Remove some features to stay within budget",
                "impact": "Stay within budget with reduced functionality"
            },
            "context": "Budget constraint detected",
            "type": "budget_resolution"
        }
    
    def _generate_technical_question(self, conflict: Dict, context: Dict) -> Dict:
        """Generate technical conflict A/B question."""
        return {
            "question": "Technical limitation detected. How should we proceed?",
            "option_a": {
                "label": "Upgrade Components",
                "description": "Use higher-capacity components",
                "impact": "Higher cost but meets all requirements"
            },
            "option_b": {
                "label": "Adjust Requirements",
                "description": "Modify requirements to fit current components",
                "impact": "Lower cost but some limitations"
            },
            "context": "Technical constraint detected",
            "type": "technical_resolution"
        }
    
    def _generate_clarification_question(self, conflict: Dict, context: Dict) -> Dict:
        """Generate clarification A/B question for ambiguous input."""
        ambiguous_term = conflict.get("term", "requirement")
        
        # Check use cases for context
        relevant_use_case = self._find_relevant_use_case(context)
        
        if relevant_use_case:
            # Use case-specific question
            return self._generate_use_case_question(relevant_use_case, ambiguous_term)
        
        # Generic clarification
        return {
            "question": f"When you say '{ambiguous_term}', which do you mean?",
            "option_a": {
                "label": "Industrial Grade",
                "description": "Heavy-duty, high-reliability components",
                "impact": "Higher cost, better durability"
            },
            "option_b": {
                "label": "Standard Grade",
                "description": "Cost-effective standard components",
                "impact": "Lower cost, standard reliability"
            },
            "context": "Clarification needed",
            "type": "clarification"
        }
    
    def _find_relevant_use_case(self, context: Dict) -> Optional[Dict]:
        """Find relevant use case from context."""
        # Match context keywords with use cases
        user_input = context.get("user_input", "").lower()
        
        for use_case_id, use_case in self.use_cases.items():
            keywords = use_case.get("keywords", [])
            if any(keyword in user_input for keyword in keywords):
                return use_case
        
        return None
    
    def _generate_use_case_question(self, use_case: Dict, term: str) -> Dict:
        """Generate question based on specific use case."""
        return {
            "question": use_case.get("clarification_question", f"Please clarify '{term}'"),
            "option_a": use_case.get("option_a", {}),
            "option_b": use_case.get("option_b", {}),
            "context": use_case.get("context", ""),
            "type": "use_case_specific"
        }