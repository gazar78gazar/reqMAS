"""
Basic Phase 2 Tests
Simple tests to verify Phase 2 components work
"""

import pytest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tools.price_calculator import PriceCalculator
from tools.abq_generator import ABQuestionGenerator
from validation.csp_validator import CSPValidator

def test_price_calculator_basic():
    """Test basic price calculation."""
    calculator = PriceCalculator()
    
    # Test with empty modules
    result = calculator.calculate_total_cost("UNO-137", [])
    
    assert result["final_price"] > 0
    assert result["currency"] == "USD"
    assert result["confidence"] == 1.0

def test_abq_generator_basic():
    """Test basic A/B question generation."""
    generator = ABQuestionGenerator()
    
    # Test with default conflict
    conflict = {"type": "unknown"}
    result = generator.generate_question(conflict, {})
    
    assert "question" in result
    assert "option_a" in result
    assert "option_b" in result

def test_csp_validator_basic():
    """Test basic CSP validation."""
    validator = CSPValidator()
    
    # Test with empty specifications
    result = validator.validate_constraints([])
    
    assert "valid" in result
    assert "violations" in result
    assert result["valid"] == True  # No specs = no violations

def test_data_loader_access():
    """Test that data loader can access Phase 2 data."""
    from data.data_loader import data_loader
    
    # Should have loaded the Phase 2 data
    assert hasattr(data_loader, 'constraints')
    assert hasattr(data_loader, 'form_fields')
    assert hasattr(data_loader, 'use_cases')
    
    # Constraints should be loaded (even if empty)
    assert isinstance(data_loader.constraints, dict)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])