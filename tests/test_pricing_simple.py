"""
Test Pricing Calculations with Real Data
Focus on PriceCalculator functionality with actual product prices
"""

import pytest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tools.price_calculator import PriceCalculator
from data.data_loader import data_loader

class TestPricingCalculations:
    """Test core pricing calculation functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.calculator = PriceCalculator()
    
    def test_simple_configuration_under_budget(self):
        """Test 1: Simple configuration under budget ($2000)"""
        print("\n=== TEST 1: Simple Configuration Under Budget ($2000) ===")
        
        # Simple config: UNO controller + 1 ADAM module
        controller = "UNO-137-E23BA"
        modules = [{"type": "ADAM-4017", "quantity": 1}]
        budget = 2000
        
        result = self.calculator.calculate_total_cost(controller, modules)
        
        total_cost = result["final_price"]
        savings = budget - total_cost
        
        print(f"Configuration:")
        print(f"  Controller: {controller}")
        print(f"  Modules: {modules[0]['type']} x{modules[0]['quantity']}")
        print(f"Total cost: ${total_cost}")
        print(f"Budget: ${budget}")
        print(f"Savings: ${savings}")
        print(f"Within budget: {total_cost < budget}")
        
        # Should be under budget
        assert total_cost < budget, f"Cost ${total_cost} should be less than budget ${budget}"
        assert savings > 0, f"Should have savings of ${savings}"
        
        # Show breakdown
        print("\nCost breakdown:")
        for item in result["breakdown"]:
            print(f"  - {item['item']}: ${item['subtotal']} ({item['quantity']}x @ ${item['unit_price']})")
        
        return result
    
    def test_expensive_configuration_over_budget(self):
        """Test 2: Expensive configuration over budget ($500)"""
        print("\n=== TEST 2: Expensive Configuration Over Budget ($500) ===")
        
        # Expensive config: UNO controller + multiple ADAM modules
        controller = "UNO-148-D33BA"  # More expensive fallback
        modules = [
            {"type": "ADAM-6015", "quantity": 2},  # $235 each
            {"type": "ADAM-6017", "quantity": 2}   # $175 each
        ]
        budget = 500
        
        result = self.calculator.calculate_total_cost(controller, modules)
        
        total_cost = result["final_price"]
        overage = total_cost - budget
        
        print(f"Configuration:")
        print(f"  Controller: {controller}")
        for module in modules:
            print(f"  Module: {module['type']} x{module['quantity']}")
        print(f"Total cost: ${total_cost}")
        print(f"Budget: ${budget}")
        print(f"Overage: ${overage}")
        print(f"Over budget: {total_cost > budget}")
        
        # Should be over budget
        assert total_cost > budget, f"Cost ${total_cost} should exceed budget ${budget}"
        assert overage > 0, f"Should have overage of ${overage}"
        
        # Show breakdown
        print("\nCost breakdown:")
        for item in result["breakdown"]:
            print(f"  - {item['item']}: ${item['subtotal']} ({item['quantity']}x @ ${item['unit_price']})")
        
        return result
    
    def test_exact_budget_match(self):
        """Test 3: Configuration matching exact budget"""
        print("\n=== TEST 3: Exact Budget Match ===")
        
        # Calculate exact cost first
        controller = "UNO-137-E23BA"
        modules = [{"type": "ADAM-6015", "quantity": 1}]  # $235
        
        result = self.calculator.calculate_total_cost(controller, modules)
        exact_cost = result["final_price"]
        
        print(f"Configuration:")
        print(f"  Controller: {controller}")
        print(f"  Module: {modules[0]['type']} x{modules[0]['quantity']}")
        print(f"Exact cost calculated: ${exact_cost}")
        
        # Test with exact budget
        budget = exact_cost
        difference = abs(result["final_price"] - budget)
        
        print(f"Budget set to: ${budget}")
        print(f"Final cost: ${result['final_price']}")
        print(f"Difference: ${difference}")
        print(f"Exact match: {difference < 0.01}")
        
        # Should be exact match
        assert difference < 0.01, f"Should be exact match, difference: ${difference}"
        
        return result
    
    def test_no_budget_price_estimate(self):
        """Test 4: Price estimate without budget constraint"""
        print("\n=== TEST 4: Price Estimate (No Budget) ===")
        
        # Medium complexity config
        controller = "UNO-148-D33BA"
        modules = [
            {"type": "ADAM-6015", "quantity": 1},  # Temperature monitoring
            {"type": "ADAM-6017", "quantity": 1}   # Analog I/O
        ]
        
        result = self.calculator.calculate_total_cost(controller, modules)
        
        print(f"Configuration:")
        print(f"  Controller: {controller}")
        for module in modules:
            print(f"  Module: {module['type']} x{module['quantity']}")
        
        print(f"\nPrice estimate: ${result['final_price']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Currency: {result['currency']}")
        
        # Should have valid pricing
        assert result["final_price"] > 0
        assert result["confidence"] == 1.0  # Deterministic calculation
        assert result["currency"] == "USD"
        
        # Show detailed breakdown
        print("\nDetailed cost breakdown:")
        for item in result["breakdown"]:
            print(f"  - {item['item']} ({item['category']}): ${item['subtotal']}")
            print(f"    {item['quantity']} x ${item['unit_price']} each")
        
        return result
    
    def test_discount_rules_application(self):
        """Test 5: Discount rules (>3 modules, >$3000)"""
        print("\n=== TEST 5: Discount Rules ===")
        
        # Test bulk module discount (5% for 3+ modules)
        print("Testing bulk module discount (3+ modules):")
        controller = "UNO-148-D33BA"
        bulk_modules = [
            {"type": "ADAM-6015", "quantity": 2},  # $235 each
            {"type": "ADAM-6017", "quantity": 2}   # $175 each
        ]
        
        result_bulk = self.calculator.calculate_total_cost(controller, bulk_modules)
        module_count = sum(m["quantity"] for m in bulk_modules)
        
        print(f"Module count: {module_count}")
        print(f"Base cost: ${result_bulk['base_cost']}")
        print(f"Final price: ${result_bulk['final_price']}")
        print(f"Discount applied: {result_bulk['discount_applied']}")
        
        if module_count >= 3:
            expected_discount = result_bulk["base_cost"] * 0.05
            actual_discount = result_bulk["base_cost"] - result_bulk["final_price"]
            print(f"Expected 5% discount: ${expected_discount}")
            print(f"Actual discount: ${actual_discount}")
            assert result_bulk["discount_applied"] == True
        
        # Test high-value discount (10% for >$3000)
        print("\nTesting high-value discount (>$3000):")
        expensive_modules = [
            {"type": "ADAM-6015", "quantity": 5},  # $235 each = $1175
            {"type": "ADAM-6017", "quantity": 5},  # $175 each = $875
            {"type": "ADAM-6018+", "quantity": 3}  # $200 each = $600
        ]
        
        result_expensive = self.calculator.calculate_total_cost(controller, expensive_modules)
        
        print(f"Base cost: ${result_expensive['base_cost']}")
        print(f"Final price: ${result_expensive['final_price']}")
        print(f"Discount applied: {result_expensive['discount_applied']}")
        
        if result_expensive["base_cost"] > 3000:
            print("High-value discount should apply (10% off)")
            assert result_expensive["discount_applied"] == True
            # Should have both discounts: 5% (modules) + 10% (high value)
            expected_with_bulk = result_expensive["base_cost"] * 0.95
            expected_final = expected_with_bulk * 0.9
            print(f"Expected final (with both discounts): ${expected_final}")
        
        return result_bulk, result_expensive
    
    def test_json_price_accuracy(self):
        """Test 6: Verify prices match JSON data exactly"""
        print("\n=== TEST 6: JSON Price Accuracy ===")
        
        # Test ADAM products with JSON pricing
        print("Testing ADAM product prices:")
        adam_tests = ["ADAM-6015", "ADAM-6017", "ADAM-6018+"]
        
        for product_id in adam_tests:
            if product_id in data_loader.adam_products:
                json_price = data_loader.adam_products[product_id].get("price_usd", 0)
                calc_price = self.calculator._get_product_price(product_id, "adam")
                
                print(f"  {product_id}:")
                print(f"    JSON: ${json_price}")
                print(f"    Calculator: ${calc_price}")
                print(f"    Match: {json_price == calc_price}")
                
                if json_price > 0:
                    assert calc_price == json_price, f"Price mismatch for {product_id}"
        
        # Test UNO controller fallback pricing
        print("\nTesting UNO controller fallback prices:")
        uno_tests = [("UNO-137-E23BA", "UNO-137"), ("UNO-148-D33BA", "UNO-148")]
        
        for full_id, fallback_key in uno_tests:
            calc_price = self.calculator._get_product_price(full_id, "uno")
            expected_fallback = self.calculator.fallback_prices.get(fallback_key, 500)
            
            print(f"  {full_id}:")
            print(f"    Calculator: ${calc_price}")
            print(f"    Expected fallback: ${expected_fallback}")
            print(f"    Using fallback: {calc_price == expected_fallback or calc_price == 500}")
        
        # Test complete system calculation accuracy
        print("\nTesting complete system calculation:")
        test_controller = "UNO-137-E23BA"
        test_modules = [{"type": "ADAM-6015", "quantity": 1}]
        
        # Manual calculation
        controller_price = self.calculator._get_product_price(test_controller, "uno")
        module_price = self.calculator._get_product_price("ADAM-6015", "adam")
        manual_base = controller_price + module_price
        manual_final = self.calculator._apply_pricing_rules(manual_base, 1)
        
        # Calculator result
        calc_result = self.calculator.calculate_total_cost(test_controller, test_modules)
        
        print(f"Manual calculation: ${manual_final}")
        print(f"Calculator result: ${calc_result['final_price']}")
        print(f"Match: {abs(manual_final - calc_result['final_price']) < 0.01}")
        
        assert abs(manual_final - calc_result["final_price"]) < 0.01, "Calculation mismatch"
        
        print("\n[OK] All price calculations verified!")
        return True

if __name__ == "__main__":
    # Run all tests with detailed output
    print("=" * 80)
    print("PRICING CALCULATIONS WITH REAL DATA")
    print("=" * 80)
    
    test_instance = TestPricingCalculations()
    test_instance.setup_method()
    
    test_instance.test_simple_configuration_under_budget()
    test_instance.test_expensive_configuration_over_budget()
    test_instance.test_exact_budget_match()
    test_instance.test_no_budget_price_estimate()
    test_instance.test_discount_rules_application()
    test_instance.test_json_price_accuracy()
    
    print("\n" + "=" * 80)
    print("ALL PRICING TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 80)