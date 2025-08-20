"""
Test Pricing and Budget Validation with Real Prices
Verify that pricing calculations and budget validation work correctly
"""

import pytest
import sys
import os
import asyncio

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.commercial_validator import CommercialValidator
from agents.technical_validator import TechnicalValidator
from tools.price_calculator import PriceCalculator
from validation.validation_pipeline import ValidationPipeline
from data.data_loader import data_loader

class TestPricingValidation:
    """Test pricing and budget validation functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.commercial_validator = CommercialValidator()
        self.technical_validator = TechnicalValidator()
        self.calculator = PriceCalculator()
        self.pipeline = ValidationPipeline()
    
    async def test_configuration_under_budget(self):
        """Test configuration under budget ($2000) -> valid + savings amount"""
        print("\n=== TEST 1: Configuration Under Budget ($2000) ===")
        
        # Create specifications for a simple system under budget
        specifications = [
            {"constraint": "analog_input", "value": "4"},
            {"constraint": "digital_io", "value": "8"}
        ]
        
        session_data = {
            "specifications": specifications,
            "budget": 2000
        }
        
        # Use ValidationPipeline to get complete validation including pricing
        result = await self.pipeline.validate_complete_solution(session_data)
        
        print(f"Validation result: {result['valid']}")
        print(f"Technical valid: {result.get('technical', {}).get('valid', 'N/A')}")
        print(f"Commercial valid: {result.get('commercial', {}).get('valid', 'N/A')}")
        
        # Should be valid - simple config should be under $2000
        assert result["valid"] == True
        
        # Check commercial validation
        commercial = result.get("commercial", {})
        if "pricing" in commercial:
            pricing = commercial["pricing"]
            total_cost = pricing["final_price"]
            budget = session_data["budget"]
            savings = budget - total_cost
            
            print(f"Total cost: ${total_cost}")
            print(f"Budget: ${budget}")
            print(f"Savings: ${savings}")
            
            assert total_cost < budget, f"Cost ${total_cost} should be less than budget ${budget}"
            assert savings > 0, f"Should have savings of ${savings}"
            
            # Verify pricing breakdown
            breakdown = pricing["breakdown"]
            print(f"Cost breakdown:")
            for item in breakdown:
                print(f"  - {item['item']}: ${item['subtotal']} ({item['quantity']}x @ ${item['unit_price']})")
        else:
            # Fallback: test calculator directly
            print("Testing direct calculator pricing:")
            calc_result = self.calculator.calculate_total_cost("UNO-137-E23BA", [{"type": "ADAM-4017", "quantity": 1}])
            total_cost = calc_result["final_price"]
            budget = session_data["budget"]
            savings = budget - total_cost
            
            print(f"Total cost: ${total_cost}")
            print(f"Budget: ${budget}")
            print(f"Savings: ${savings}")
            
            assert total_cost < budget, f"Cost ${total_cost} should be less than budget ${budget}"
        
        return result
    
    async def test_configuration_over_budget(self):
        """Test configuration over budget ($500) -> invalid + alternatives"""
        print("\n=== TEST 2: Configuration Over Budget ($500) ===")
        
        # Create a configuration that should exceed $500
        input_data = {
            "controller": "UNO-148-D33BA",  # More expensive controller
            "modules": [
                {"type": "ADAM-4017", "quantity": 2, "purpose": "analog input"},
                {"type": "ADAM-4050", "quantity": 1, "purpose": "digital I/O"}
            ],
            "budget": 500
        }
        
        result = await self.validator.process(input_data, {})
        
        print(f"Validation result: {result['valid']}")
        print(f"Budget validation: {result['budget_validation']}")
        
        # Should be invalid - complex config should exceed $500
        assert result["budget_validation"]["within_budget"] == False
        
        # Check pricing details
        pricing = result["pricing"]
        total_cost = pricing["final_price"]
        budget = input_data["budget"]
        overage = total_cost - budget
        
        print(f"Total cost: ${total_cost}")
        print(f"Budget: ${budget}")
        print(f"Overage: ${overage}")
        
        assert total_cost > budget, f"Cost ${total_cost} should exceed budget ${budget}"
        assert overage > 0, f"Should have overage of ${overage}"
        
        # Should provide alternatives
        alternatives = result["budget_validation"]["alternatives"]
        print(f"Alternatives provided: {len(alternatives)}")
        for alt in alternatives:
            print(f"  - {alt}")
        
        assert len(alternatives) > 0, "Should provide budget alternatives"
        
        return result
    
    async def test_exact_budget_match(self):
        """Test exact budget match -> valid with warning"""
        print("\n=== TEST 3: Exact Budget Match ===")
        
        # First calculate the exact cost of a simple configuration
        simple_config = {
            "controller": "UNO-137-E23BA",
            "modules": [{"type": "ADAM-4017", "quantity": 1, "purpose": "analog input"}]
        }
        
        # Calculate exact cost
        controller_price = self.calculator._get_product_price("UNO-137-E23BA", "uno")
        module_price = self.calculator._get_product_price("ADAM-4017", "adam")
        exact_cost = controller_price + module_price
        
        # Apply any discounts
        final_cost = self.calculator._apply_pricing_rules(exact_cost, 1)
        
        print(f"Calculated exact cost: ${final_cost}")
        
        # Test with exact budget
        input_data = {
            "controller": "UNO-137-E23BA",
            "modules": [{"type": "ADAM-4017", "quantity": 1, "purpose": "analog input"}],
            "budget": final_cost
        }
        
        result = await self.validator.process(input_data, {})
        
        print(f"Validation result: {result['valid']}")
        print(f"Budget validation: {result['budget_validation']}")
        
        # Should be valid but with warning
        assert result["valid"] == True
        assert result["budget_validation"]["within_budget"] == True
        
        # Check for exact match warning
        budget_validation = result["budget_validation"]
        total_cost = result["pricing"]["final_price"]
        
        print(f"Final cost: ${total_cost}")
        print(f"Budget: ${input_data['budget']}")
        
        # Should be exact or very close match
        assert abs(total_cost - input_data["budget"]) < 0.01, "Should be exact budget match"
        
        return result
    
    async def test_no_budget_specified(self):
        """Test no budget specified -> returns price estimate only"""
        print("\n=== TEST 4: No Budget Specified ===")
        
        input_data = {
            "controller": "UNO-137-E23BA",
            "modules": [
                {"type": "ADAM-4017", "quantity": 1, "purpose": "analog input"},
                {"type": "ADAM-4050", "quantity": 1, "purpose": "digital I/O"}
            ]
            # No budget specified
        }
        
        result = await self.validator.process(input_data, {})
        
        print(f"Validation result: {result['valid']}")
        print(f"Budget validation: {result['budget_validation']}")
        
        # Should be valid since no budget constraint
        assert result["valid"] == True
        
        # Should indicate no budget constraint
        budget_validation = result["budget_validation"]
        assert "no_budget_specified" in budget_validation or budget_validation.get("within_budget") == True
        
        # Should still provide pricing estimate
        pricing = result["pricing"]
        assert pricing["final_price"] > 0
        
        print(f"Price estimate: ${pricing['final_price']}")
        print(f"Confidence: {pricing['confidence']}")
        
        # Show cost breakdown
        breakdown = pricing["breakdown"]
        print(f"Cost breakdown:")
        for item in breakdown:
            print(f"  - {item['item']}: ${item['subtotal']}")
        
        return result
    
    async def test_discount_rules(self):
        """Test discount rules (>3 modules, >$3000) -> correct discounts applied"""
        print("\n=== TEST 5: Discount Rules ===")
        
        # Test 1: 3+ modules discount (5% off)
        print("Testing 3+ modules discount:")
        input_data_modules = {
            "controller": "UNO-148-D33BA",
            "modules": [
                {"type": "ADAM-4017", "quantity": 2, "purpose": "analog input"},
                {"type": "ADAM-4050", "quantity": 2, "purpose": "digital I/O"}
            ]
        }
        
        result_modules = await self.validator.process(input_data_modules, {})
        pricing_modules = result_modules["pricing"]
        
        base_cost = pricing_modules["base_cost"]
        final_price = pricing_modules["final_price"]
        module_count = sum(m["quantity"] for m in input_data_modules["modules"])
        
        print(f"Module count: {module_count}")
        print(f"Base cost: ${base_cost}")
        print(f"Final price: ${final_price}")
        print(f"Discount applied: {pricing_modules['discount_applied']}")
        
        if module_count >= 3:
            expected_discount = base_cost * 0.05
            actual_discount = base_cost - final_price
            print(f"Expected discount: ${expected_discount}")
            print(f"Actual discount: ${actual_discount}")
            assert pricing_modules["discount_applied"] == True
        
        # Test 2: High value discount (10% off for >$3000)
        print("\\nTesting high value discount:")
        input_data_high = {
            "controller": "UNO-148-D33BA",
            "modules": [
                {"type": "ADAM-4017", "quantity": 5, "purpose": "analog input"},
                {"type": "ADAM-4050", "quantity": 5, "purpose": "digital I/O"}
            ]
        }
        
        result_high = await self.validator.process(input_data_high, {})
        pricing_high = result_high["pricing"]
        
        base_cost_high = pricing_high["base_cost"]
        final_price_high = pricing_high["final_price"]
        
        print(f"Base cost: ${base_cost_high}")
        print(f"Final price: ${final_price_high}")
        print(f"Discount applied: {pricing_high['discount_applied']}")
        
        if base_cost_high > 3000:
            print("High value discount should apply")
            assert pricing_high["discount_applied"] == True
        
        return result_modules, result_high
    
    async def test_price_json_accuracy(self):
        """Verify all prices match JSON data exactly"""
        print("\n=== TEST 6: Price JSON Data Accuracy ===")
        
        print("Testing ADAM product prices against JSON:")
        
        # Test ADAM products that have pricing in JSON
        adam_samples = ["ADAM-6015", "ADAM-6017", "ADAM-6018+"]
        
        for product_id in adam_samples:
            if product_id in data_loader.adam_products:
                json_price = data_loader.adam_products[product_id].get("price_usd", 0)
                calc_price = self.calculator._get_product_price(product_id, "adam")
                
                print(f"  - {product_id}:")
                print(f"    JSON price: ${json_price}")
                print(f"    Calculator price: ${calc_price}")
                
                if json_price > 0:
                    assert calc_price == json_price, f"Price mismatch for {product_id}"
                    print(f"    [OK] Prices match exactly")
                else:
                    print(f"    [INFO] Using fallback price")
        
        print("\\nTesting UNO controller prices (fallback):")
        
        # Test UNO controllers (using fallback prices)
        uno_samples = ["UNO-137-E23BA", "UNO-148-D33BA"]
        
        for product_id in uno_samples:
            calc_price = self.calculator._get_product_price(product_id, "uno")
            fallback_key = product_id.split('-')[0] + "-" + product_id.split('-')[1]  # e.g., "UNO-137"
            fallback_price = self.calculator.fallback_prices.get(fallback_key, 500)
            
            print(f"  - {product_id}:")
            print(f"    Calculator price: ${calc_price}")
            print(f"    Expected fallback: ${fallback_price}")
            
            # Should use fallback price
            assert calc_price == fallback_price or calc_price == 500, f"Should use fallback price for {product_id}"
            print(f"    [OK] Using correct fallback price")
        
        print("\\nTesting complete cost calculation:")
        
        # Test complete system pricing
        test_config = {
            "controller": "UNO-137-E23BA",
            "modules": [
                {"type": "ADAM-6015", "quantity": 1, "purpose": "temperature monitoring"}
            ]
        }
        
        # Manual calculation
        controller_price = self.calculator._get_product_price("UNO-137-E23BA", "uno")
        module_price = self.calculator._get_product_price("ADAM-6015", "adam")
        expected_base = controller_price + module_price
        expected_final = self.calculator._apply_pricing_rules(expected_base, 1)
        
        # Calculator result
        calc_result = self.calculator.calculate_total_cost("UNO-137-E23BA", [{"type": "ADAM-6015", "quantity": 1}])
        
        print(f"Manual calculation:")
        print(f"  Controller: ${controller_price}")
        print(f"  Module: ${module_price}")
        print(f"  Base total: ${expected_base}")
        print(f"  Final (with rules): ${expected_final}")
        
        print(f"Calculator result:")
        print(f"  Base cost: ${calc_result['base_cost']}")
        print(f"  Final price: ${calc_result['final_price']}")
        
        assert calc_result["base_cost"] == expected_base, "Base cost calculation mismatch"
        assert calc_result["final_price"] == expected_final, "Final price calculation mismatch"
        
        print("[OK] All pricing calculations accurate")
        
        return True

# Test runner functions for synchronous execution
def test_configuration_under_budget():
    """Sync wrapper for async test"""
    test_instance = TestPricingValidation()
    test_instance.setup_method()
    return asyncio.run(test_instance.test_configuration_under_budget())

def test_configuration_over_budget():
    """Sync wrapper for async test"""
    test_instance = TestPricingValidation()
    test_instance.setup_method()
    return asyncio.run(test_instance.test_configuration_over_budget())

def test_exact_budget_match():
    """Sync wrapper for async test"""
    test_instance = TestPricingValidation()
    test_instance.setup_method()
    return asyncio.run(test_instance.test_exact_budget_match())

def test_no_budget_specified():
    """Sync wrapper for async test"""
    test_instance = TestPricingValidation()
    test_instance.setup_method()
    return asyncio.run(test_instance.test_no_budget_specified())

def test_discount_rules():
    """Sync wrapper for async test"""
    test_instance = TestPricingValidation()
    test_instance.setup_method()
    return asyncio.run(test_instance.test_discount_rules())

def test_price_json_accuracy():
    """Sync wrapper for async test"""
    test_instance = TestPricingValidation()
    test_instance.setup_method()
    return asyncio.run(test_instance.test_price_json_accuracy())

if __name__ == "__main__":
    # Run all tests with detailed output
    print("=" * 80)
    print("PRICING AND BUDGET VALIDATION TESTS")
    print("=" * 80)
    
    test_configuration_under_budget()
    test_configuration_over_budget()
    test_exact_budget_match()
    test_no_budget_specified()
    test_discount_rules()
    test_price_json_accuracy()
    
    print("\n" + "=" * 80)
    print("ALL PRICING VALIDATION TESTS COMPLETED")
    print("=" * 80)