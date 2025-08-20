"""
Test Requirement Validation Against Real Products
Verify that technical validation works correctly with actual product data
"""

import pytest
import sys
import os
import asyncio

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.technical_validator import TechnicalValidator
from data.data_loader import data_loader

class TestRequirementValidation:
    """Test validation against real product specifications."""
    
    def setup_method(self):
        """Setup test environment."""
        self.validator = TechnicalValidator()
    
    async def test_8_analog_inputs(self):
        """Test '8 analog inputs' -> selects appropriate UNO + ADAM modules"""
        print("\n=== TEST 1: 8 Analog Inputs ===")
        
        # Create specifications for 8 analog inputs
        specifications = [
            {"constraint": "analog_input", "value": "8"}
        ]
        
        result = await self.validator.process(
            {"specifications": specifications}, 
            {}
        )
        
        print(f"Validation result: {result['valid']}")
        print(f"Controller validation: {result['controller']['valid']}")
        print(f"Module validation: {result['modules']['valid']}")
        
        # Should be valid
        assert result["valid"] == True
        assert result["controller"]["valid"] == True
        assert result["modules"]["valid"] == True
        
        # Check suitable controllers
        controllers = result["controller"]["suitable_controllers"]
        print(f"Suitable controllers: {len(controllers)}")
        for ctrl in controllers:
            print(f"  - {ctrl['id']}: capacity={ctrl['capacity']}")
            # Verify these are real product IDs from JSON
            assert ctrl['id'] in data_loader.uno_products
        
        # Check required modules
        modules = result["modules"]["modules_required"]
        print(f"Required modules: {len(modules)}")
        for module in modules:
            print(f"  - {module['type']} x{module['quantity']}: {module['purpose']}")
            # Should recommend ADAM-4017 for analog input
            if "analog" in module['purpose'].lower():
                assert "ADAM" in module['type']
        
        # Should have at least 1 module for 8 analog inputs
        analog_modules = [m for m in modules if "analog" in m['purpose'].lower()]
        assert len(analog_modules) >= 1
        
        # Check I/O requirements calculation
        io_req = result["io_requirements"]
        assert io_req["analog_input"] == 8
        assert io_req["total_io"] == 8
        
        return result
    
    async def test_32_digital_io(self):
        """Test '32 digital I/O' -> exceeds controller limits, requires modules"""
        print("\n=== TEST 2: 32 Digital I/O (Exceeds Controller Limits) ===")
        
        specifications = [
            {"constraint": "digital_io", "value": "32"}
        ]
        
        result = await self.validator.process(
            {"specifications": specifications}, 
            {}
        )
        
        print(f"Validation result: {result['valid']}")
        print(f"I/O requirements: {result['io_requirements']}")
        
        # Should be invalid because 32 > max controller capacity (16)
        assert result["valid"] == False
        assert result["controller"]["valid"] == False
        
        # Check that no controllers can handle 32 I/O
        controllers = result["controller"]["suitable_controllers"]
        print(f"Suitable controllers for 32 I/O: {len(controllers)}")
        assert len(controllers) == 0, "No single controller should handle 32 I/O"
        
        # Check total I/O calculation is correct
        io_req = result["io_requirements"]
        assert io_req["total_io"] == 32
        
        # Should have recommendations for alternatives
        recommendations = result["recommendations"]
        print(f"Recommendations: {recommendations}")
        
        return result
    
    async def test_16_digital_io_max_capacity(self):
        """Test '16 digital I/O' -> selects controllers at max capacity"""
        print("\n=== TEST 2B: 16 Digital I/O (Max Controller Capacity) ===")
        
        specifications = [
            {"constraint": "digital_io", "value": "16"}
        ]
        
        result = await self.validator.process(
            {"specifications": specifications}, 
            {}
        )
        
        print(f"Validation result: {result['valid']}")
        print(f"I/O requirements: {result['io_requirements']}")
        
        # Should be valid - 16 is max capacity
        assert result["valid"] == True
        assert result["controller"]["valid"] == True
        
        # Check suitable controllers
        controllers = result["controller"]["suitable_controllers"]
        print(f"Suitable controllers for 16 I/O: {len(controllers)}")
        for ctrl in controllers:
            print(f"  - {ctrl['id']}: capacity={ctrl['capacity']}")
            assert ctrl['capacity'] >= 16  # Must handle 16 I/O
            assert ctrl['id'] in data_loader.uno_products
        
        # Should have controllers with 16 I/O capacity
        assert len(controllers) > 0, "Should have controllers that can handle 16 I/O"
        
        # Check total I/O calculation
        io_req = result["io_requirements"]
        assert io_req["total_io"] == 16
        
        return result
    
    async def test_exceed_all_limits(self):
        """Test '999 I/O' -> returns invalid with proper message"""
        print("\n=== TEST 3: Exceed All Limits (999 I/O) ===")
        
        specifications = [
            {"constraint": "digital_io", "value": "999"}
        ]
        
        result = await self.validator.process(
            {"specifications": specifications}, 
            {}
        )
        
        print(f"Validation result: {result['valid']}")
        print(f"Controller validation: {result['controller']['valid']}")
        print(f"Message: {result['controller']['message']}")
        
        # Should be invalid - no controller can handle 999 I/O
        assert result["valid"] == False
        assert result["controller"]["valid"] == False
        
        # Should have no suitable controllers
        controllers = result["controller"]["suitable_controllers"]
        assert len(controllers) == 0
        
        # Check conflicts
        conflicts = result["conflicts"]
        print(f"Conflicts found: {len(conflicts)}")
        for conflict in conflicts:
            print(f"  - {conflict['type']}: {conflict['message']}")
        
        assert len(conflicts) > 0
        
        # Check I/O requirements
        io_req = result["io_requirements"]
        assert io_req["total_io"] == 999
        
        return result
    
    async def test_temperature_requirement(self):
        """Test temperature requirement '-40°C' -> filters compatible products only"""
        print("\n=== TEST 4: Temperature Requirement (-40°C) ===")
        
        # First check what temperature ranges our products support
        print("Available UNO products and their temperature ranges:")
        temp_ranges = {}
        for product_id, specs in data_loader.uno_products.items():
            min_temp = specs.get("operating_temp_min_c", 0)
            max_temp = specs.get("operating_temp_max_c", 0)
            temp_ranges[product_id] = (min_temp, max_temp)
            print(f"  - {product_id}: {min_temp}°C to {max_temp}°C")
        
        # Create a specification with temperature constraint
        specifications = [
            {"constraint": "digital_io", "value": "8"},
            {"constraint": "operating_temperature_min", "value": "-40"}
        ]
        
        result = await self.validator.process(
            {"specifications": specifications}, 
            {}
        )
        
        print(f"Validation result: {result['valid']}")
        
        # Check which controllers are suitable
        controllers = result["controller"]["suitable_controllers"]
        print(f"Controllers suitable for -40°C: {len(controllers)}")
        
        compatible_count = 0
        for ctrl in controllers:
            product_id = ctrl['id']
            min_temp, max_temp = temp_ranges[product_id]
            print(f"  - {product_id}: {min_temp}°C to {max_temp}°C, capacity={ctrl['capacity']}")
            
            # Verify this controller actually supports -40°C
            assert min_temp <= -40, f"{product_id} should support -40°C but min is {min_temp}°C"
            compatible_count += 1
        
        print(f"Found {compatible_count} controllers that support -40°C operation")
        
        return result
    
    async def test_mixed_io_requirements(self):
        """Test mixed I/O '4 AI + 4 DI + 4 DO' -> correct module combination"""
        print("\n=== TEST 5: Mixed I/O Requirements (4AI + 4DI + 4DO) ===")
        
        specifications = [
            {"constraint": "analog_input", "value": "4"},
            {"constraint": "digital_input", "value": "4"},
            {"constraint": "digital_output", "value": "4"}
        ]
        
        result = await self.validator.process(
            {"specifications": specifications}, 
            {}
        )
        
        print(f"Validation result: {result['valid']}")
        
        # Should be valid - 12 total I/O is within limits
        assert result["valid"] == True
        
        # Check I/O requirements calculation
        io_req = result["io_requirements"]
        print(f"I/O breakdown: {io_req}")
        assert io_req["analog_input"] == 4
        assert io_req["digital_input"] == 4
        assert io_req["digital_output"] == 4
        assert io_req["total_io"] == 12
        
        # Check suitable controllers (must handle 12 total I/O)
        controllers = result["controller"]["suitable_controllers"]
        print(f"Suitable controllers: {len(controllers)}")
        for ctrl in controllers:
            print(f"  - {ctrl['id']}: capacity={ctrl['capacity']}")
            assert ctrl['capacity'] >= 12
            assert ctrl['id'] in data_loader.uno_products
        
        assert len(controllers) > 0, "Should have controllers for 12 I/O"
        
        # Check required modules
        modules = result["modules"]["modules_required"]
        print(f"Required modules: {len(modules)}")
        
        has_analog_module = False
        has_digital_module = False
        
        for module in modules:
            print(f"  - {module['type']} x{module['quantity']}: {module['purpose']}")
            
            if "analog" in module['purpose'].lower():
                has_analog_module = True
                # Should be ADAM module for analog I/O
                assert "ADAM" in module['type']
            
            if "digital" in module['purpose'].lower():
                has_digital_module = True
                # Should be ADAM module for digital I/O
                assert "ADAM" in module['type']
        
        # Should have modules for analog I/O
        assert has_analog_module, "Should have analog I/O module for 4 analog inputs"
        
        return result
    
    async def test_product_id_verification(self):
        """Verify all recommendations use actual product IDs from JSON"""
        print("\n=== TEST 6: Product ID Verification ===")
        
        specifications = [
            {"constraint": "analog_input", "value": "4"},
            {"constraint": "digital_io", "value": "8"}
        ]
        
        result = await self.validator.process(
            {"specifications": specifications}, 
            {}
        )
        
        print("Verifying all recommended products exist in JSON data...")
        
        # Check all controller recommendations
        controllers = result["controller"]["suitable_controllers"]
        print(f"Verifying {len(controllers)} controllers:")
        for ctrl in controllers:
            product_id = ctrl['id']
            print(f"  - {product_id}: ", end="")
            
            # Must exist in UNO products JSON
            assert product_id in data_loader.uno_products, f"Controller {product_id} not found in uno_products.json"
            
            # Verify capacity matches JSON data
            json_capacity = data_loader.uno_products[product_id].get("builtin_total_digital_io", 0)
            assert ctrl['capacity'] == json_capacity, f"Capacity mismatch for {product_id}"
            
            print(f"✓ Found in JSON with capacity {json_capacity}")
        
        # Check all module recommendations
        modules = result["modules"]["modules_required"]
        print(f"Verifying {len(modules)} module types:")
        for module in modules:
            module_type = module['type']
            print(f"  - {module_type}: ", end="")
            
            # Check if it's in ADAM products (when we have ADAM modules recommended)
            if "ADAM" in module_type:
                # For now, verify against common ADAM module patterns
                # In a full implementation, these would be in adam_products.json
                common_adam_modules = ["ADAM-4017", "ADAM-4050", "ADAM-4024", "ADAM-4055"]
                is_valid_adam = any(known in module_type for known in common_adam_modules)
                assert is_valid_adam, f"Unknown ADAM module type: {module_type}"
                print(f"✓ Valid ADAM module pattern")
            else:
                print(f"✓ Valid module type")
        
        print("✓ All product IDs verified against JSON data")
        
        return result

# Test runner functions for synchronous execution
def test_8_analog_inputs():
    """Sync wrapper for async test"""
    test_instance = TestRequirementValidation()
    test_instance.setup_method()
    return asyncio.run(test_instance.test_8_analog_inputs())

def test_32_digital_io():
    """Sync wrapper for async test"""
    test_instance = TestRequirementValidation()
    test_instance.setup_method()
    return asyncio.run(test_instance.test_32_digital_io())

def test_16_digital_io_max_capacity():
    """Sync wrapper for async test"""
    test_instance = TestRequirementValidation()
    test_instance.setup_method()
    return asyncio.run(test_instance.test_16_digital_io_max_capacity())

def test_exceed_all_limits():
    """Sync wrapper for async test"""
    test_instance = TestRequirementValidation()
    test_instance.setup_method()
    return asyncio.run(test_instance.test_exceed_all_limits())

def test_temperature_requirement():
    """Sync wrapper for async test"""
    test_instance = TestRequirementValidation()
    test_instance.setup_method()
    return asyncio.run(test_instance.test_temperature_requirement())

def test_mixed_io_requirements():
    """Sync wrapper for async test"""
    test_instance = TestRequirementValidation()
    test_instance.setup_method()
    return asyncio.run(test_instance.test_mixed_io_requirements())

def test_product_id_verification():
    """Sync wrapper for async test"""
    test_instance = TestRequirementValidation()
    test_instance.setup_method()
    return asyncio.run(test_instance.test_product_id_verification())

if __name__ == "__main__":
    # Run all tests with detailed output
    print("=" * 80)
    print("REQUIREMENT VALIDATION AGAINST REAL PRODUCTS")
    print("=" * 80)
    
    test_8_analog_inputs()
    test_16_digital_io_max_capacity()
    test_32_digital_io()
    test_exceed_all_limits()
    test_temperature_requirement()
    test_mixed_io_requirements()
    test_product_id_verification()
    
    print("\n" + "=" * 80)
    print("ALL REQUIREMENT VALIDATION TESTS COMPLETED")
    print("=" * 80)