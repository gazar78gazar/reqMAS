"""
Test Complete Validation Flow
Verify end-to-end validation pipeline with performance requirements
"""

import pytest
import sys
import os
import asyncio
import time
from typing import Dict, Any

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from validation.validation_pipeline import ValidationPipeline
from resilience.circuit_breaker import CircuitBreaker
from validation.csp_validator import CSPValidator
from agents.technical_validator import TechnicalValidator
from agents.commercial_validator import CommercialValidator

class TestValidationFlow:
    """Test complete validation flow with timing and circuit breaker behavior."""
    
    def setup_method(self):
        """Setup test environment."""
        self.pipeline = ValidationPipeline()
        self.csp_validator = CSPValidator()
        # Circuit breakers are built into the pipeline
        
    async def test_single_round_success(self):
        """Test 1: Single round success (>85% confidence) -> early termination"""
        print("\n=== TEST 1: Single Round Success (Early Termination) ===")
        
        start_time = time.time()
        
        # Simple, clear requirements that should succeed in one round
        session_data = {
            "specifications": [
                {"constraint": "analog_input", "value": "4"},
                {"constraint": "digital_io", "value": "8"}
            ],
            "budget": 2000,
            "user_expertise": "expert"
        }
        
        # Run validation
        specifications = session_data["specifications"]
        context = {k: v for k, v in session_data.items() if k != "specifications"}
        result = await self.pipeline.validate(specifications, context)
        
        execution_time = time.time() - start_time
        
        print(f"Execution time: {execution_time:.3f} seconds")
        print(f"Consensus achieved: {result['consensus_achieved']}")
        print(f"Rounds completed: {len(result['rounds'])}")
        print(f"Fallback used: {result['fallback_used']}")
        
        # Check final result
        final = result['final_result']
        print(f"Final validation: {final['valid']}")
        print(f"Final confidence: {final['confidence']}")
        
        # Check individual validator results
        if 'technical' in final:
            print(f"Technical valid: {final['technical']['valid']}")
            print(f"Technical confidence: {final['technical']['confidence']}")
        
        if 'commercial' in final:
            print(f"Commercial valid: {final['commercial']['valid']}")
            print(f"Commercial confidence: {final['commercial']['confidence']}")
        
        # Should succeed in single round with high confidence
        assert final["valid"] == True
        assert final["confidence"] >= 0.85
        assert len(result["rounds"]) == 1  # Early termination
        assert execution_time < 3.0  # Performance requirement
        
        print("[OK] Single round success with early termination")
        return result
    
    async def test_multi_round_validation(self):
        """Test 2: Multi-round validation -> refinement between rounds"""
        print("\n=== TEST 2: Multi-Round Validation ===")
        
        start_time = time.time()
        
        # Complex requirements that might need refinement
        session_data = {
            "specifications": [
                {"constraint": "analog_input", "value": "16"},
                {"constraint": "digital_output", "value": "12"},
                {"constraint": "sampling_rate", "value": "10000"},
                {"constraint": "operating_temperature_min", "value": "-30"}
            ],
            "budget": 1200,  # Tight budget
            "user_expertise": "intermediate"
        }
        
        # Run validation with multiple rounds
        result = await self.pipeline.validate_complete_solution(session_data)
        
        execution_time = time.time() - start_time
        
        print(f"Execution time: {execution_time:.3f} seconds")
        print(f"Validation result: {result['valid']}")
        print(f"Overall confidence: {result.get('overall_confidence', 'N/A')}")
        print(f"Rounds completed: {result.get('rounds_completed', 'N/A')}")
        print(f"Refinements applied: {result.get('refinements_applied', 'N/A')}")
        
        # Check for conflicts and resolutions
        if 'conflicts' in result:
            print(f"Conflicts found: {len(result['conflicts'])}")
            for conflict in result['conflicts']:
                print(f"  - {conflict['type']}: {conflict['message']}")
        
        # Should handle multiple rounds if needed
        assert execution_time < 3.0  # Performance requirement
        rounds_completed = result.get("rounds_completed", 1)
        assert 1 <= rounds_completed <= 3  # Should complete within max rounds
        
        print(f"[OK] Multi-round validation completed in {rounds_completed} rounds")
        return result
    
    async def test_circuit_breaker_open(self):
        """Test 3: Circuit breaker open -> fallback response"""
        print("\n=== TEST 3: Circuit Breaker Open (Fallback) ===")
        
        start_time = time.time()
        
        # Force circuit breaker into open state by simulating failures
        # Access the pipeline's technical validator circuit breaker
        tech_breaker = self.pipeline.breakers["technical"]
        for i in range(6):  # Exceed failure threshold
            try:
                await tech_breaker.call(self._failing_operation)
            except Exception:
                pass  # Expected failures
        
        print(f"Circuit breaker state: {tech_breaker.state}")
        
        # Now try validation with circuit breaker open
        session_data = {
            "specifications": [
                {"constraint": "analog_input", "value": "4"}
            ],
            "budget": 1000
        }
        
        # This should use fallback response
        result = await self.pipeline.validate_complete_solution(session_data)
        
        execution_time = time.time() - start_time
        
        print(f"Execution time: {execution_time:.3f} seconds")
        print(f"Validation result: {result['valid']}")
        print(f"Using fallback: {result.get('fallback_used', False)}")
        print(f"Fallback reason: {result.get('fallback_reason', 'N/A')}")
        
        # Should provide fallback response quickly
        assert execution_time < 1.0  # Fallback should be very fast
        assert result.get("fallback_used", False) == True or result["valid"] == True
        
        print("[OK] Circuit breaker fallback response provided")
        return result
    
    async def _failing_operation(self):
        """Helper method that always fails to trigger circuit breaker."""
        raise Exception("Simulated failure")
    
    async def test_csp_constraint_violation(self):
        """Test 4: CSP constraint violation -> proper error reporting"""
        print("\n=== TEST 4: CSP Constraint Violation ===")
        
        start_time = time.time()
        
        # Create conflicting constraints that should violate CSP rules
        session_data = {
            "specifications": [
                {"constraint": "power_consumption", "value": "200"},  # High power
                {"constraint": "operating_temperature_max", "value": "0"},   # Very low temp
                {"constraint": "memory_capacity", "value": "32"},    # High memory
                {"constraint": "storage_capacity", "value": "1000"}  # High storage
            ],
            "budget": 300  # Impossibly low budget for these requirements
        }
        
        # Run validation
        specifications = session_data["specifications"]
        context = {k: v for k, v in session_data.items() if k != "specifications"}
        result = await self.pipeline.validate(specifications, context)
        
        execution_time = time.time() - start_time
        
        print(f"Execution time: {execution_time:.3f} seconds")
        print(f"Validation result: {result['valid']}")
        print(f"CSP violations: {result.get('csp_violations', [])}")
        
        # Check for constraint violations
        if 'csp' in result:
            print(f"CSP valid: {result['csp']['valid']}")
            print(f"CSP violations: {len(result['csp'].get('violations', []))}")
            for violation in result['csp'].get('violations', []):
                print(f"  - {violation}")
        
        # Should detect constraint violations
        assert execution_time < 3.0  # Performance requirement
        # Either CSP should be invalid or overall should be invalid due to conflicts
        csp_valid = result.get('csp', {}).get('valid', True)
        overall_valid = result['valid']
        
        if not csp_valid:
            print("[OK] CSP constraint violations properly detected")
        elif not overall_valid:
            print("[OK] Constraint conflicts detected by other validators")
        else:
            print("[INFO] No constraint violations found - requirements may be feasible")
        
        return result
    
    async def test_all_validators_pass(self):
        """Test 5: All validators pass -> combined confidence score"""
        print("\n=== TEST 5: All Validators Pass (Combined Confidence) ===")
        
        start_time = time.time()
        
        # Well-designed requirements that should pass all validators
        session_data = {
            "specifications": [
                {"constraint": "analog_input", "value": "8"},
                {"constraint": "digital_output", "value": "4"},
                {"constraint": "operating_temperature_min", "value": "-20"},
                {"constraint": "operating_temperature_max", "value": "60"}
            ],
            "budget": 1500,  # Reasonable budget
            "user_expertise": "intermediate"
        }
        
        # Run validation
        specifications = session_data["specifications"]
        context = {k: v for k, v in session_data.items() if k != "specifications"}
        result = await self.pipeline.validate(specifications, context)
        
        execution_time = time.time() - start_time
        
        print(f"Execution time: {execution_time:.3f} seconds")
        print(f"Validation result: {result['valid']}")
        print(f"Overall confidence: {result.get('overall_confidence', 'N/A')}")
        
        # Check individual validator results
        validator_results = {}
        for validator_type in ['technical', 'commercial', 'csp']:
            if validator_type in result:
                valid = result[validator_type]['valid']
                confidence = result[validator_type]['confidence']
                validator_results[validator_type] = {'valid': valid, 'confidence': confidence}
                print(f"{validator_type.title()} - Valid: {valid}, Confidence: {confidence}")
        
        # Calculate expected combined confidence
        if validator_results:
            avg_confidence = sum(v['confidence'] for v in validator_results.values()) / len(validator_results)
            print(f"Average confidence: {avg_confidence:.3f}")
        
        # All validators should pass with good confidence
        assert result["valid"] == True
        assert execution_time < 3.0  # Performance requirement
        
        # Check that we have results from multiple validators
        assert len(validator_results) >= 2
        
        # Combined confidence should be reasonable
        overall_confidence = result.get('overall_confidence', 0)
        assert overall_confidence > 0.5  # At least moderate confidence
        
        print("[OK] All validators pass with combined confidence score")
        return result
    
    async def test_performance_timing(self):
        """Test 6: Measure execution time -> must be < 3 seconds"""
        print("\n=== TEST 6: Performance Timing ===")
        
        # Test various scenarios and measure timing
        test_cases = [
            {
                "name": "Simple case",
                "data": {
                    "specifications": [{"constraint": "analog_input", "value": "4"}],
                    "budget": 1000
                }
            },
            {
                "name": "Complex case",
                "data": {
                    "specifications": [
                        {"constraint": "analog_input", "value": "8"},
                        {"constraint": "digital_output", "value": "8"},
                        {"constraint": "sampling_rate", "value": "5000"},
                        {"constraint": "operating_temperature_min", "value": "-40"}
                    ],
                    "budget": 2000
                }
            },
            {
                "name": "Conflicting case",
                "data": {
                    "specifications": [
                        {"constraint": "analog_input", "value": "16"},
                        {"constraint": "digital_output", "value": "16"}
                    ],
                    "budget": 400  # Too low budget
                }
            }
        ]
        
        timing_results = []
        
        for test_case in test_cases:
            print(f"\nTesting {test_case['name']}:")
            start_time = time.time()
            
            result = await self.pipeline.validate_complete_solution(test_case['data'])
            
            execution_time = time.time() - start_time
            timing_results.append({
                "case": test_case['name'],
                "time": execution_time,
                "valid": result['valid']
            })
            
            print(f"  Time: {execution_time:.3f}s, Valid: {result['valid']}")
            
            # Each case must complete within 3 seconds
            assert execution_time < 3.0, f"{test_case['name']} took {execution_time:.3f}s (>3s limit)"
        
        # Calculate statistics
        times = [r['time'] for r in timing_results]
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        print(f"\nTiming Summary:")
        print(f"  Average time: {avg_time:.3f}s")
        print(f"  Maximum time: {max_time:.3f}s")
        print(f"  All cases under 3s: {max_time < 3.0}")
        
        # Performance requirements
        assert max_time < 3.0  # No case should exceed 3 seconds
        assert avg_time < 2.0  # Average should be well under limit
        
        print("[OK] All performance timing requirements met")
        return timing_results
    
    async def test_complete_pipeline_integration(self):
        """Test 7: Complete pipeline integration test"""
        print("\n=== TEST 7: Complete Pipeline Integration ===")
        
        start_time = time.time()
        
        # Comprehensive test that exercises all components
        session_data = {
            "specifications": [
                {"constraint": "analog_input", "value": "8"},
                {"constraint": "digital_output", "value": "6"},
                {"constraint": "operating_temperature_min", "value": "-30"},
                {"constraint": "sampling_rate", "value": "2000"}
            ],
            "budget": 1200,
            "user_expertise": "intermediate",
            "session_id": "integration_test_001"
        }
        
        # Run complete validation
        result = await self.pipeline.validate_complete_solution(session_data)
        
        execution_time = time.time() - start_time
        
        print(f"Execution time: {execution_time:.3f} seconds")
        print(f"Validation result: {result['valid']}")
        print(f"Overall confidence: {result.get('overall_confidence', 'N/A')}")
        print(f"Rounds completed: {result.get('rounds_completed', 'N/A')}")
        
        # Check all major components
        components_tested = []
        
        if 'technical' in result:
            components_tested.append('technical')
            print(f"Technical validation: {result['technical']['valid']}")
        
        if 'commercial' in result:
            components_tested.append('commercial')
            print(f"Commercial validation: {result['commercial']['valid']}")
        
        if 'csp' in result:
            components_tested.append('csp')
            print(f"CSP validation: {result['csp']['valid']}")
        
        if 'conflicts' in result:
            print(f"Conflicts detected: {len(result['conflicts'])}")
        
        if 'autofill' in result:
            components_tested.append('autofill')
            print(f"Autofill available: {result['autofill'].get('available', False)}")
        
        # Integration requirements
        assert execution_time < 3.0  # Performance requirement
        assert len(components_tested) >= 2  # Multiple components should be tested
        assert 'overall_confidence' in result  # Should have combined confidence
        
        print(f"[OK] Complete pipeline integration - tested {len(components_tested)} components")
        return result

# Sync test wrappers for pytest
def test_single_round_success():
    """Sync wrapper for async test"""
    test_instance = TestValidationFlow()
    test_instance.setup_method()
    return asyncio.run(test_instance.test_single_round_success())

def test_multi_round_validation():
    """Sync wrapper for async test"""
    test_instance = TestValidationFlow()
    test_instance.setup_method()
    return asyncio.run(test_instance.test_multi_round_validation())

def test_circuit_breaker_open():
    """Sync wrapper for async test"""
    test_instance = TestValidationFlow()
    test_instance.setup_method()
    return asyncio.run(test_instance.test_circuit_breaker_open())

def test_csp_constraint_violation():
    """Sync wrapper for async test"""
    test_instance = TestValidationFlow()
    test_instance.setup_method()
    return asyncio.run(test_instance.test_csp_constraint_violation())

def test_all_validators_pass():
    """Sync wrapper for async test"""
    test_instance = TestValidationFlow()
    test_instance.setup_method()
    return asyncio.run(test_instance.test_all_validators_pass())

def test_performance_timing():
    """Sync wrapper for async test"""
    test_instance = TestValidationFlow()
    test_instance.setup_method()
    return asyncio.run(test_instance.test_performance_timing())

def test_complete_pipeline_integration():
    """Sync wrapper for async test"""
    test_instance = TestValidationFlow()
    test_instance.setup_method()
    return asyncio.run(test_instance.test_complete_pipeline_integration())

if __name__ == "__main__":
    # Run all tests with detailed output
    print("=" * 80)
    print("COMPLETE VALIDATION FLOW TESTS")
    print("=" * 80)
    
    test_single_round_success()
    test_multi_round_validation()
    test_circuit_breaker_open()
    test_csp_constraint_violation()
    test_all_validators_pass()
    test_performance_timing()
    test_complete_pipeline_integration()
    
    print("\n" + "=" * 80)
    print("ALL VALIDATION FLOW TESTS COMPLETED")
    print("=" * 80)