"""
Commercial Validator - Validates commercial feasibility using actual pricing
Uses price calculator for deterministic calculations, optional LLM for explanations
"""

from typing import Dict, List, Any, Optional
from agents.base_agent import StatelessAgent
from tools.price_calculator import PriceCalculator
from data.data_loader import data_loader

class CommercialValidator(StatelessAgent):
    """
    Validates commercial feasibility: budget, availability, pricing.
    Uses calculator tool for math, optional LLM for explanations.
    """
    
    def __init__(self, blackboard=None, message_bus=None):
        super().__init__(
            agent_id="commercial_validator",
            model="gpt-4o-mini",  # For explanations only
            blackboard=blackboard,
            message_bus=message_bus
        )
        self.calculator = PriceCalculator()
    
    async def process(self, input_data: Dict, context: Dict) -> Dict:
        """
        Validate commercial feasibility.
        Technical validation must pass first.
        """
        tech_validation = input_data.get("technical_validation", {})
        budget = input_data.get("budget", None)
        
        if not tech_validation.get("valid", False):
            return {
                "valid": False,
                "confidence": 0.0,
                "message": "Technical validation must pass first"
            }
        
        # Get recommended configuration from technical validator
        suitable_controllers = tech_validation.get("controller", {}).get("suitable_controllers", [])
        if not suitable_controllers:
            return {
                "valid": False,
                "confidence": 0.0,
                "message": "No suitable controllers found"
            }
        
        controller = suitable_controllers[0]["id"]
        modules = tech_validation.get("modules", {}).get("modules_required", [])
        
        # Calculate actual costs using calculator tool
        pricing = self.calculator.calculate_total_cost(controller, modules)
        
        # Validate against budget if provided
        budget_validation = self._validate_budget(pricing, budget)
        
        # Generate alternatives if over budget
        alternatives = []
        if budget and not budget_validation["within_budget"]:
            alternatives = self._generate_alternatives(budget, tech_validation)
        
        return {
            "valid": budget_validation["within_budget"] if budget else True,
            "confidence": 0.95,
            "pricing": pricing,
            "budget_validation": budget_validation,
            "alternatives": alternatives,
            "recommendation": self._generate_recommendation(pricing, budget)
        }
    
    def _validate_budget(self, pricing: Dict, budget: Optional[float]) -> Dict:
        """Check if configuration fits within budget."""
        if not budget:
            return {
                "budget_specified": False,
                "within_budget": True,
                "message": "No budget constraint specified"
            }
        
        final_price = pricing["final_price"]
        within_budget = final_price <= budget
        
        return {
            "budget_specified": True,
            "budget": budget,
            "estimated_cost": final_price,
            "within_budget": within_budget,
            "over_budget_amount": max(0, final_price - budget),
            "under_budget_amount": max(0, budget - final_price),
            "message": f"Configuration {'fits within' if within_budget else 'exceeds'} budget"
        }
    
    def _generate_alternatives(self, budget: float, tech_validation: Dict) -> List[Dict]:
        """Generate alternative configurations within budget."""
        alternatives = []
        
        # Try smaller controller if possible
        io_requirements = tech_validation.get("io_requirements", {})
        if io_requirements.get("total_io", 0) <= 16:
            # Suggest UNO-137 instead of UNO-148
            smaller_config = self.calculator.estimate_from_requirements(io_requirements)
            if smaller_config["final_price"] <= budget:
                alternatives.append({
                    "description": "Use UNO-137 with minimal modules",
                    "estimated_cost": smaller_config["final_price"],
                    "savings": tech_validation.get("pricing", {}).get("final_price", 0) - smaller_config["final_price"]
                })
        
        return alternatives
    
    def _generate_recommendation(self, pricing: Dict, budget: Optional[float]) -> str:
        """Generate recommendation text."""
        if not budget:
            return f"Estimated system cost: ${pricing['final_price']}"
        
        if pricing["final_price"] <= budget:
            savings = budget - pricing["final_price"]
            return f"Configuration fits budget with ${savings:.2f} to spare"
        else:
            overage = pricing["final_price"] - budget
            return f"Configuration exceeds budget by ${overage:.2f}. Consider alternatives."
    
    def get_tools(self) -> List[str]:
        return ["price_calculator", "budget_analyzer"]