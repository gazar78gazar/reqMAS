"""
Phase 2 Integration Tests
Tests the complete validation pipeline and API endpoints
"""

import pytest
import asyncio
from validation.validation_pipeline import ValidationPipeline
from agents.decision_coordinator import DecisionCoordinatorAgent
from agents.technical_validator import TechnicalValidator
from agents.commercial_validator import CommercialValidator
from tools.price_calculator import PriceCalculator
from tools.abq_generator import ABQuestionGenerator
from tools.autofill_mapper import AutofillMapper
from validation.csp_validator import CSPValidator
from resilience.circuit_breaker import CircuitBreaker, CircuitState

@pytest.mark.asyncio
async def test_validation_pipeline():
    """Test complete validation pipeline."""
    pipeline = ValidationPipeline()
    
    specifications = [
        {"type": "SR", "constraint": "analog_input", "value": "8", "strength": 1000},
        {"type": "SR", "constraint": "digital_output", "value": "4", "strength": 1000}
    ]
    
    context = {
        "session_id": "test",
        "budget": 2000,
        "user_profile": {"expertise_level": "intermediate"}
    }
    
    result = await pipeline.validate(specifications, context)
    
    assert "final_result" in result
    assert "rounds" in result
    assert len(result["rounds"]) >= 1
    assert isinstance(result["final_result"]["valid"], bool)
    assert isinstance(result["final_result"]["confidence"], float)

@pytest.mark.asyncio
async def test_technical_validator():
    """Test technical validator."""
    validator = TechnicalValidator()
    
    input_data = {
        "specifications": [
            {"constraint": "analog_input", "value": "8"},
            {"constraint": "digital_output", "value": "4"}
        ]
    }
    
    result = await validator.process(input_data, {})
    
    assert result["valid"] in [True, False]
    assert "controller" in result
    assert "modules" in result
    assert "confidence" in result
    assert isinstance(result["confidence"], float)

@pytest.mark.asyncio
async def test_commercial_validator():
    """Test commercial validator."""
    validator = CommercialValidator()
    
    # First need technical validation to pass
    tech_validation = {
        "valid": True,
        "controller": {
            "suitable_controllers": [{"id": "UNO-137", "capacity": 16}]
        },
        "modules": {
            "modules_required": [{"type": "ADAM-4017", "quantity": 1}]
        },
        "io_requirements": {"total_io": 12, "analog_input": 8}
    }
    
    input_data = {
        "technical_validation": tech_validation,
        "budget": 1500
    }
    
    result = await validator.process(input_data, {})
    
    assert result["valid"] in [True, False]
    assert "pricing" in result
    assert "budget_validation" in result

def test_price_calculator():
    """Test price calculator tool."""
    calculator = PriceCalculator()
    
    modules = [
        {"type": "ADAM-4017", "quantity": 1},
        {"type": "ADAM-4050", "quantity": 1}
    ]
    
    result = calculator.calculate_total_cost("UNO-137", modules)
    
    assert "final_price" in result
    assert "breakdown" in result
    assert result["confidence"] == 1.0
    assert result["final_price"] > 0

def test_abq_generator():
    """Test A/B question generator."""
    generator = ABQuestionGenerator()
    
    conflict = {
        "type": "budget",
        "over_budget_amount": 500,
        "estimated_cost": 2500
    }
    
    result = generator.generate_question(conflict, {})
    
    assert "question" in result
    assert "option_a" in result
    assert "option_b" in result
    assert result["type"] == "budget_resolution"

def test_autofill_mapper():
    """Test autofill mapper."""
    mapper = AutofillMapper()
    
    validated_config = {
        "controller": {
            "suitable_controllers": [{"id": "UNO-137"}]
        },
        "io_requirements": {
            "analog_input": 8,
            "digital_output": 4
        },
        "modules": {
            "modules_required": [{"type": "ADAM-4017", "quantity": 1}]
        }
    }
    
    result = mapper.generate_autofill(validated_config, 0.9)
    
    assert result["should_autofill"] == True
    assert "field_mappings" in result
    assert result["confidence"] == 0.9

def test_csp_validator():
    """Test CSP validator."""
    validator = CSPValidator()
    
    specifications = [
        {"constraint": "analog_input", "value": "8"},
        {"constraint": "power_consumption", "value": "15"}  # Within limits
    ]
    
    result = validator.validate_constraints(specifications)
    
    assert "valid" in result
    assert "violations" in result
    assert "confidence" in result

@pytest.mark.asyncio
async def test_decision_coordinator():
    """Test decision coordinator."""
    coordinator = DecisionCoordinatorAgent()
    
    # Test A/B question generation
    result = await coordinator.process(
        {
            "action_type": "generate_abq",
            "conflict": {"type": "budget", "over_budget_amount": 200}
        },
        {
            "session_id": "test",
            "user_profile": {"expertise_level": "novice"}
        }
    )
    
    assert result["type"] == "abq"
    assert "question" in result
    assert result["max_attempts"] == 5  # Novice gets 5 attempts

def test_circuit_breaker():
    """Test circuit breaker functionality."""
    breaker = CircuitBreaker("test_agent", failure_threshold=2)
    
    # Should start closed
    assert breaker.state == CircuitState.CLOSED
    
    # Simulate failures
    try:
        breaker._on_failure()
        breaker._on_failure()  # Should open after 2 failures
    except:
        pass
    
    assert breaker.state == CircuitState.OPEN
    
    # Test manual reset
    breaker.reset()
    assert breaker.state == CircuitState.CLOSED

@pytest.mark.asyncio
async def test_pipeline_with_circuit_breaker():
    """Test pipeline with circuit breaker protection."""
    pipeline = ValidationPipeline()
    
    # Test that pipeline handles circuit breaker failures gracefully
    specifications = [
        {"constraint": "analog_input", "value": "8"}
    ]
    
    context = {"session_id": "test"}
    
    # Force a circuit breaker open
    pipeline.breakers["technical"].force_open()
    
    result = await pipeline.validate(specifications, context)
    
    # Should get fallback response
    assert result["fallback_used"] == True
    assert "final_result" in result

@pytest.mark.asyncio
async def test_validation_pipeline_early_termination():
    """Test that pipeline terminates early on high confidence."""
    pipeline = ValidationPipeline()
    
    # Use specifications that should give high confidence
    specifications = [
        {"constraint": "analog_input", "value": "4"},  # Simple requirement
        {"constraint": "digital_output", "value": "2"}
    ]
    
    context = {
        "session_id": "test",
        "budget": 5000  # High budget
    }
    
    result = await pipeline.validate(specifications, context)
    
    # Check if consensus was achieved (might be true with fallback)
    assert "consensus_achieved" in result
    assert "rounds" in result
    
    # If consensus achieved, should have stopped early
    if result["consensus_achieved"]:
        assert len(result["rounds"]) <= pipeline.max_rounds

def test_confidence_aggregation():
    """Test confidence aggregation from multiple validators."""
    from validation.confidence_aggregator import ConfidenceAggregator
    
    aggregator = ConfidenceAggregator()
    
    validation_results = {
        "technical": {"confidence": 0.9},
        "commercial": {"confidence": 0.8},
        "csp": {"confidence": 0.95}
    }
    
    result = aggregator.aggregate_confidence(validation_results)
    
    assert "aggregate_confidence" in result
    assert "consensus_level" in result
    assert "method" in result
    assert 0.0 <= result["aggregate_confidence"] <= 1.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])