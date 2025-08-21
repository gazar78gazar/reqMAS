"""
Validation Pipeline - Orchestrates multi-phase validation
Technical → Commercial → Consensus
"""

from typing import Dict, List, Any, Optional
from agents.technical_validator import TechnicalValidator
from agents.commercial_validator import CommercialValidator
from validation.csp_validator import CSPValidator
from resilience.circuit_breaker import CircuitBreaker
from resilience.fallback_handler import FallbackHandler
import asyncio

class ValidationPipeline:
    """
    Orchestrates validation phases with circuit breaker protection.
    Implements 3-round consensus with early termination.
    """
    
    def __init__(self, blackboard=None, message_bus=None):
        self.technical_validator = TechnicalValidator(blackboard, message_bus)
        self.commercial_validator = CommercialValidator(blackboard, message_bus)
        self.csp_validator = CSPValidator()
        self.fallback_handler = FallbackHandler()
        
        # Circuit breakers for each validator
        self.breakers = {
            "technical": CircuitBreaker("technical_validator"),
            "commercial": CircuitBreaker("commercial_validator"),
            "csp": CircuitBreaker("csp_validator")
        }
        
        self.max_rounds = 3
        self.consensus_threshold = 0.85
    
    async def validate(self, specifications: List[Dict], context: Dict) -> Dict:
        """
        Run complete validation pipeline.
        """
        validation_results = {
            "rounds": [],
            "final_result": None,
            "consensus_achieved": False,
            "circuit_breaker_status": {},
            "fallback_used": False
        }
        
        for round_num in range(1, self.max_rounds + 1):
            round_result = await self._validation_round(specifications, context, round_num)
            validation_results["rounds"].append(round_result)
            
            # Check for early termination
            if round_result["confidence"] >= self.consensus_threshold:
                validation_results["consensus_achieved"] = True
                break
            
            # Refine specifications based on feedback
            specifications = self._refine_specifications(specifications, round_result)
        
        # Set final result
        validation_results["final_result"] = validation_results["rounds"][-1]
        
        # Get circuit breaker status
        for name, breaker in self.breakers.items():
            validation_results["circuit_breaker_status"][name] = breaker.get_status()
        
        # Check if any fallbacks were used
        validation_results["fallback_used"] = any(
            round_result.get("fallback_used", False) for round_result in validation_results["rounds"]
        )
        
        return validation_results
    
    async def _validation_round(self, specifications: List[Dict], context: Dict, round_num: int) -> Dict:
        """
        Single validation round.
        """
        round_result = {
            "round": round_num,
            "technical": None,
            "commercial": None,
            "csp": None,
            "valid": False,
            "confidence": 0.0,
            "fallback_used": False
        }
        
        # Phase 1: Technical Validation
        try:
            tech_result = await self.breakers["technical"].call(
                self.technical_validator.process,
                {"specifications": specifications},
                context
            )
            round_result["technical"] = tech_result
        except Exception as e:
            # Use fallback
            tech_result = self.fallback_handler.get_fallback_response(
                "technical_validator", 
                {"specifications": specifications}
            )
            round_result["technical"] = tech_result
            round_result["fallback_used"] = True
        
        # Only proceed if technical validation passes or we have fallback
        if not tech_result.get("valid", False) and not round_result["fallback_used"]:
            return round_result
        
        # Phase 2: Commercial Validation
        try:
            comm_result = await self.breakers["commercial"].call(
                self.commercial_validator.process,
                {
                    "technical_validation": tech_result,
                    "budget": context.get("budget")
                },
                context
            )
            round_result["commercial"] = comm_result
        except Exception as e:
            # Use fallback
            comm_result = self.fallback_handler.get_fallback_response(
                "commercial_validator",
                {"technical_validation": tech_result}
            )
            round_result["commercial"] = comm_result
            round_result["fallback_used"] = True
        
        # Phase 3: CSP Validation
        try:
            csp_result = await self.breakers["csp"].call(
                self._run_csp_validation,
                specifications
            )
            round_result["csp"] = csp_result
        except Exception as e:
            # CSP fallback - assume valid if other phases pass
            csp_result = {
                "valid": True,
                "confidence": 0.6,
                "violations": [],
                "fallback": True,
                "message": "CSP validation unavailable"
            }
            round_result["csp"] = csp_result
            round_result["fallback_used"] = True
        
        # Calculate overall result
        round_result["valid"] = all([
            round_result.get("technical", {}).get("valid", False),
            round_result.get("commercial", {}).get("valid", False),
            round_result.get("csp", {}).get("valid", False)
        ])
        
        # Calculate weighted confidence
        round_result["confidence"] = self._calculate_confidence(round_result)
        
        return round_result
    
    async def _run_csp_validation(self, specifications: List[Dict]) -> Dict:
        """Wrapper for CSP validation to work with async."""
        return self.csp_validator.validate_constraints(specifications)
    
    def _calculate_confidence(self, round_result: Dict) -> float:
        """Calculate weighted confidence score."""
        weights = {
            "technical": 0.4,
            "commercial": 0.3,
            "csp": 0.3
        }
        
        total_confidence = 0.0
        total_weight = 0.0
        
        for component, weight in weights.items():
            if round_result.get(component) and "confidence" in round_result[component]:
                confidence = round_result[component]["confidence"]
                # Reduce confidence if fallback was used
                if round_result[component].get("fallback", False):
                    confidence *= 0.7
                
                total_confidence += confidence * weight
                total_weight += weight
        
        return total_confidence / total_weight if total_weight > 0 else 0.0
    
    def _refine_specifications(self, specifications: List[Dict], round_result: Dict) -> List[Dict]:
        """Refine specifications based on validation feedback."""
        refined = specifications.copy()
        
        # Apply refinements based on CSP violations
        csp_result = round_result.get("csp")
        if not csp_result:
            return refined
        violations = csp_result.get("violations", [])
        
        for violation in violations:
            constraint_name = violation.get("constraint", "")
            
            # Find and adjust specifications that caused violations
            for spec in refined:
                if spec.get("constraint") == constraint_name:
                    if violation.get("violation") == "exceeds_maximum":
                        # Reduce value to maximum allowed
                        spec["value"] = str(violation.get("max_allowed", spec["value"]))
                    elif violation.get("violation") == "below_minimum":
                        # Increase value to minimum required
                        spec["value"] = str(violation.get("min_required", spec["value"]))
        
        # Apply technical constraint adjustments
        tech_result = round_result.get("technical", {})
        tech_violations = tech_result.get("constraints", {}).get("violations", [])
        
        for violation in tech_violations:
            # Add logic to adjust specifications based on technical violations
            pass
        
        return refined
    
    def get_pipeline_status(self) -> Dict:
        """Get overall pipeline status."""
        return {
            "circuit_breakers": {name: breaker.get_status() for name, breaker in self.breakers.items()},
            "cache_stats": self.fallback_handler.get_cache_stats(),
            "last_validation": self.csp_validator.last_validation.isoformat() if self.csp_validator.last_validation else None
        }
    
    def reset_circuit_breakers(self):
        """Reset all circuit breakers."""
        for breaker in self.breakers.values():
            breaker.reset()
    
    def clear_caches(self):
        """Clear all caches."""
        self.fallback_handler.clear_cache()
    
    async def validate_complete_solution(self, session_data: Dict) -> Dict:
        """
        Validate complete solution from session data.
        Wrapper for validate() method that extracts specifications and context.
        """
        specifications = session_data.get("specifications", [])
        
        # Extract context from session data
        context = {
            "budget": session_data.get("budget"),
            "user_expertise": session_data.get("user_expertise"),
            "session_id": session_data.get("session_id")
        }
        
        # Remove None values
        context = {k: v for k, v in context.items() if v is not None}
        
        # Run validation
        result = await self.validate(specifications, context)
        
        # Transform result to match expected format
        return {
            "valid": result["final_result"]["valid"],
            "confidence": result["final_result"]["confidence"],
            "rounds_completed": len(result["rounds"]),
            "consensus_achieved": result["consensus_achieved"],
            "fallback_used": result["fallback_used"],
            "technical": result["final_result"].get("technical", {}),
            "commercial": result["final_result"].get("commercial", {}),
            "csp": result["final_result"].get("csp", {}),
            "overall_confidence": result["final_result"]["confidence"],
            "conflicts": self._extract_conflicts(result["final_result"])
        }
    
    def _extract_conflicts(self, final_result: Dict) -> List[Dict]:
        """Extract conflicts from validation results."""
        conflicts = []
        
        # Check for technical conflicts
        tech_result = final_result.get("technical", {})
        if not tech_result.get("valid", True):
            conflicts.append({
                "type": "technical",
                "message": "Technical validation failed",
                "details": tech_result.get("violations", [])
            })
        
        # Check for commercial conflicts (budget)
        comm_result = final_result.get("commercial", {})
        if not comm_result.get("valid", True):
            pricing = comm_result.get("pricing", {})
            if pricing.get("exceeds_budget", False):
                conflicts.append({
                    "type": "budget",
                    "message": f"Configuration exceeds budget",
                    "estimated_cost": pricing.get("final_price", 0),
                    "budget": pricing.get("budget", 0),
                    "over_budget_amount": pricing.get("over_budget_amount", 0)
                })
        
        # Check for CSP conflicts
        csp_result = final_result.get("csp", {})
        violations = csp_result.get("violations", [])
        for violation in violations:
            conflicts.append({
                "type": "constraint",
                "message": f"Constraint violation: {violation.get('constraint', 'unknown')}",
                "details": violation
            })
        
        return conflicts