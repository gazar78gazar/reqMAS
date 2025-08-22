"""
Decision Coordinator - Manages A/B questions, autofill, and chat responses
Uses form_fields.json and useCase.json for context-aware decisions
"""

from typing import Dict, List, Any, Optional
from agents.base_agent import StatelessAgent
from tools.abq_generator import ABQuestionGenerator
from tools.autofill_mapper import AutofillMapper

class DecisionCoordinatorAgent(StatelessAgent):
    """
    Coordinates decisions: A/B questions, autofill triggers, chat responses.
    Central point for user interaction decisions.
    """
    
    def __init__(self, blackboard=None, message_bus=None):
        super().__init__(
            agent_id="decision_coordinator",
            model="gpt-4o-mini",
            blackboard=blackboard,
            message_bus=message_bus
        )
        self.abq_generator = ABQuestionGenerator()
        self.autofill_mapper = AutofillMapper()
        
        # Attempt tracking for expertise adaptation
        self.max_attempts = {
            "expert": 2,
            "intermediate": 3,
            "novice": 5
        }
        self.current_attempts = {}
    
    async def process(self, input_data: Dict, context: Dict) -> Dict:
        """
        Process decision request: generate A/B, trigger autofill, or format response.
        """
        action_type = input_data.get("action_type", "evaluate")
        
        if action_type == "generate_abq":
            return await self._generate_abq(input_data, context)
        elif action_type == "check_autofill":
            return await self._check_autofill(input_data, context)
        elif action_type == "format_response":
            return await self._format_chat_response(input_data, context)
        else:
            return await self._evaluate_next_action(input_data, context)
    
    async def _generate_abq(self, input_data: Dict, context: Dict) -> Dict:
        """Generate A/B clarification question."""
        conflict = input_data.get("conflict", {})
        session_id = context.get("session_id", "default")
        user_profile = context.get("user_profile", {})
        expertise_level = user_profile.get("expertise_level", "intermediate")
        
        # Check attempt limit
        attempts = self.current_attempts.get(session_id, 0)
        max_attempts = self.max_attempts[expertise_level]
        
        if attempts >= max_attempts:
            return {
                "type": "max_attempts_reached",
                "message": "Maximum clarification attempts reached. Using defaults.",
                "should_use_defaults": True
            }
        
        # Generate A/B question
        abq = self.abq_generator.generate_question(conflict, context)
        
        # Track attempt
        self.current_attempts[session_id] = attempts + 1
        
        return {
            "type": "abq",
            "question": abq,
            "attempt_number": attempts + 1,
            "max_attempts": max_attempts,
            "expertise_level": expertise_level
        }
    
    async def _check_autofill(self, input_data: Dict, context: Dict) -> Dict:
        """Check if autofill should trigger."""
        validated_config = input_data.get("validated_config", {})
        confidence = input_data.get("confidence", 0.0)
        user_profile = context.get("user_profile", {})
        expertise_level = user_profile.get("expertise_level", "intermediate")
        
        # Expertise-based thresholds
        autofill_thresholds = {
            "expert": 0.80,
            "intermediate": 0.85,
            "novice": 0.90
        }
        
        threshold = autofill_thresholds[expertise_level]
        
        if confidence >= threshold:
            autofill_data = self.autofill_mapper.generate_autofill(validated_config, confidence)
            return {
                "type": "autofill",
                "triggered": autofill_data["should_autofill"],
                "data": autofill_data,
                "expertise_level": expertise_level,
                "threshold": threshold
            }
        
        return {
            "type": "autofill",
            "triggered": False,
            "confidence": confidence,
            "threshold": threshold,
            "message": f"Confidence {confidence:.2%} below threshold {threshold:.2%}"
        }
    
    async def _format_chat_response(self, input_data: Dict, context: Dict) -> Dict:
        """Format a chat response based on validation results."""
        validation_results = input_data.get("validation_results", {})
        user_profile = context.get("user_profile", {})
        expertise_level = user_profile.get("expertise_level", "intermediate")
        
        # Format response based on expertise
        if expertise_level == "expert":
            # Technical details
            response = self._format_expert_response(validation_results)
        elif expertise_level == "novice":
            # Simplified explanation
            response = self._format_novice_response(validation_results)
        else:
            # Balanced response
            response = self._format_intermediate_response(validation_results)
        
        return {
            "type": "chat_response",
            "message": response,
            "expertise_level": expertise_level
        }
    
    async def _evaluate_next_action(self, input_data: Dict, context: Dict) -> Dict:
        """Evaluate what action to take next based on current state."""
        confidence = input_data.get("confidence", 0.0)
        conflicts = input_data.get("conflicts", [])
        completeness = input_data.get("completeness", 0.0)
        
        # Decision logic
        if conflicts:
            return {
                "next_action": "generate_abq",
                "reason": "Conflicts need resolution",
                "conflicts": conflicts
            }
        elif confidence >= 0.85 and completeness >= 0.80:
            return {
                "next_action": "trigger_autofill",
                "reason": "High confidence and completeness"
            }
        elif confidence < 0.60:
            return {
                "next_action": "request_clarification",
                "reason": "Low confidence requires more information"
            }
        else:
            return {
                "next_action": "continue_conversation",
                "reason": "Gathering more requirements"
            }
    
    def _format_expert_response(self, validation: Dict) -> str:
        """Format technical response for experts."""
        controllers = validation.get('controller', {}).get('suitable_controllers', [])
        modules = validation.get('modules', {}).get('modules_required', [])
        violations = validation.get('constraints', {}).get('violations', [])
        price = validation.get('pricing', {}).get('final_price', 0)
        confidence = validation.get('confidence', 0)
        
        return f"""Technical Validation Results:
- Controller: {[c['id'] for c in controllers]}
- I/O Modules: {[f"{m['quantity']}x {m['type']}" for m in modules]}
- Constraint Violations: {len(violations)}
- Total Cost: ${price:.2f}
- Confidence: {confidence:.2%}"""
    
    def _format_novice_response(self, validation: Dict) -> str:
        """Format simple response for novices."""
        if validation.get('valid', False):
            return "✓ Your configuration looks good! Everything is compatible."
        else:
            return "There are some issues with your configuration. Let me help you fix them."
    
    def _format_intermediate_response(self, validation: Dict) -> str:
        """Format balanced response for intermediate users."""
        print(f"   [DecisionCoord] _format_intermediate_response called with: {list(validation.keys()) if validation else 'None'}")
        
        # Check if validation is empty or has no specs
        if not validation or not validation.get('specifications'):
            print(f"   [DecisionCoord] No specifications found, returning generic response")
            return "I'm ready to help with your IoT requirements. Please describe what you need."
        
        valid = validation.get('valid', False)
        price = validation.get('pricing', {}).get('final_price', 0)
        
        if valid:
            return f"Your configuration is valid. Estimated cost: ${price:.2f}"
        else:
            conflicts = validation.get('conflicts', [])
            if conflicts:
                return f"Found {len(conflicts)} issues to resolve. Let's work through them."
            else:
                return "Analyzing your requirements. Please provide more details about your needs."
    
    def reset_attempts(self, session_id: str):
        """Reset attempt counter for session."""
        self.current_attempts[session_id] = 0
    
    def get_tools(self) -> List[str]:
        return ["abq_generator", "autofill_mapper", "response_formatter"]