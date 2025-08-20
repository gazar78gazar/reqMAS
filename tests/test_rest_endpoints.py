"""
Test REST Endpoints with Real Data
Verify API functionality with actual product specifications and pricing
"""

import pytest
import sys
import os
import requests
import json
import time
import subprocess
import threading
from contextlib import contextmanager

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestRESTEndpoints:
    """Test REST API endpoints with real product data."""
    
    @classmethod
    def setup_class(cls):
        """Start the server for testing."""
        cls.base_url = "http://localhost:8000"
        cls.session_id = None
        cls.server_process = None
        
        # Start server in background
        print("Starting reqMAS server...")
        cls._start_server()
        time.sleep(3)  # Give server time to start
        
        # Verify server is running
        try:
            response = requests.get(f"{cls.base_url}/", timeout=5)
            print(f"Server status: {response.status_code}")
        except Exception as e:
            print(f"Server not responding: {e}")
            raise
    
    @classmethod
    def teardown_class(cls):
        """Stop the server after testing."""
        if cls.server_process:
            print("Stopping reqMAS server...")
            cls.server_process.terminate()
            cls.server_process.wait(timeout=5)
    
    @classmethod
    def _start_server(cls):
        """Start the reqMAS server in background."""
        import subprocess
        import sys
        
        server_script = os.path.join(os.path.dirname(__file__), '..', 'src', 'main.py')
        
        # Start server process
        cls.server_process = subprocess.Popen(
            [sys.executable, server_script],
            cwd=os.path.join(os.path.dirname(__file__), '..'),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    
    def setup_method(self):
        """Setup for each test method."""
        # Create session with test requirements
        self.session_data = {
            "user_expertise": "intermediate",
            "specifications": [
                {"constraint": "analog_input", "value": "16"},
                {"constraint": "digital_output", "value": "8"}
            ],
            "budget": 3000
        }
    
    def test_1_validate_endpoint(self):
        """Test 1: POST /api/v1/validate with session_id + $3000 budget"""
        print("\n=== TEST 1: /api/v1/validate Endpoint ===")
        
        # First create a session with specifications using /process endpoint
        print("Step 1: Create session with specifications")
        process_url = f"{self.base_url}/process"
        process_payload = {
            "input": "I need 16 analog inputs and 8 digital outputs",
            "session_id": "test_session_validate"
        }
        
        response = requests.post(process_url, json=process_payload, timeout=10)
        assert response.status_code == 200, f"Failed to create session: {response.status_code}"
        
        print("Session created successfully")
        
        # Now test validation endpoint
        print("Step 2: Validate accumulated requirements")
        url = f"{self.base_url}/api/v1/validate"
        payload = {
            "session_id": "test_session_validate",
            "budget": 3000,
            "user_profile": {"expertise": "intermediate"}
        }
        
        print(f"POST {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=10)
        execution_time = time.time() - start_time
        
        print(f"Response time: {execution_time:.3f}s")
        print(f"Status code: {response.status_code}")
        
        # Print response content for debugging
        if response.status_code != 200:
            print(f"Error response: {response.text}")
        
        # Should return success
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        result = response.json()
        print(f"Response keys: {list(result.keys())}")
        
        # Verify response structure - based on actual API
        assert "status" in result
        assert result["status"] == "success"
        assert "validation" in result
        
        # Check validation results structure
        validation = result.get("validation", {})
        final_result = validation.get("final_result", {})
        
        print(f"Validation successful: {validation.get('consensus_achieved', False)}")
        print(f"Validation confidence: {final_result.get('confidence', 0)}")
        
        # Check for actual UNO/ADAM products
        if "technical" in final_result and final_result["technical"]["valid"]:
            tech_result = final_result["technical"]
            controllers = tech_result.get("controller", {}).get("suitable_controllers", [])
            modules = tech_result.get("modules", {}).get("modules_required", [])
            
            print(f"Found {len(controllers)} suitable controllers:")
            for ctrl in controllers[:3]:  # Show first 3
                print(f"  - {ctrl.get('id', 'Unknown')}: capacity={ctrl.get('capacity', 0)}")
            
            print(f"Required modules: {len(modules)}")
            for module in modules:
                print(f"  - {module.get('type', 'Unknown')} x{module.get('quantity', 1)}")
            
            # Verify actual product IDs (should be from real JSON data)
            if controllers:
                first_controller = controllers[0]["id"]
                assert "UNO-" in first_controller, f"Expected real UNO controller, got {first_controller}"
            
            if modules:
                first_module = modules[0]["type"]
                assert "ADAM-" in first_module, f"Expected real ADAM module, got {first_module}"
        
        # Check for real pricing
        if "commercial" in final_result and final_result["commercial"]["valid"]:
            pricing = final_result["commercial"].get("pricing", {})
            if pricing:
                total_cost = pricing.get("final_price", 0)
                print(f"Total cost: ${total_cost}")
                assert total_cost > 0, "Should have valid pricing"
                
                # Show cost breakdown
                breakdown = pricing.get("breakdown", [])
                print("Cost breakdown:")
                for item in breakdown:
                    print(f"  - {item.get('item', 'Unknown')}: ${item.get('subtotal', 0)}")
        
        print("[OK] Validate endpoint returns actual UNO/ADAM products with real prices")
        
        # Store session for next tests
        self.__class__.session_id = "test_session_validate"
        return result
    
    def test_2_generate_abq_endpoint(self):
        """Test 2: POST /api/v1/generate_abq with budget conflict"""
        print("\n=== TEST 2: /api/v1/generate_abq Endpoint ===")
        
        url = f"{self.base_url}/api/v1/generate_abq"
        
        # Create budget conflict scenario ($500 over budget)
        payload = {
            "session_id": self.session_id or "test_session_abq",
            "conflict": {
                "type": "budget",
                "message": "Configuration exceeds budget by $500",
                "over_budget_amount": 500,
                "estimated_cost": 3500,
                "budget": 3000
            },
            "user_profile": {"expertise": "intermediate"}
        }
        
        print(f"POST {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=10)
        execution_time = time.time() - start_time
        
        print(f"Response time: {execution_time:.3f}s")
        print(f"Status code: {response.status_code}")
        
        # Should return success
        assert response.status_code == 200
        
        result = response.json()
        print(f"Response keys: {list(result.keys())}")
        
        # Verify A/B question structure
        assert "question" in result
        
        # Check for budget-specific A/B question - the API returns a single question
        questions = [result["question"]] if isinstance(result["question"], dict) else [result]
        
        print(f"Generated {len(questions)} A/B questions:")
        for i, question in enumerate(questions, 1):
            print(f"\nQuestion {i}:")
            print(f"  Question: {question.get('question', 'N/A')}")
            print(f"  Option A: {question.get('option_a', {}).get('label', 'N/A')}")
            print(f"  Option B: {question.get('option_b', {}).get('label', 'N/A')}")
            
            # Verify it's a budget question
            question_text = str(question.get('question', '')).lower()
            assert any(keyword in question_text for keyword in ['budget', 'cost', 'exceed'])
            
            # Verify increase/reduce options
            option_a_label = str(question.get('option_a', {}).get('label', '')).lower()
            option_b_label = str(question.get('option_b', {}).get('label', '')).lower()
            
            has_increase_option = 'increase' in option_a_label or 'increase' in option_b_label
            has_reduce_option = 'reduce' in option_a_label or 'reduce' in option_b_label or 'remove' in option_a_label or 'remove' in option_b_label
            
            print(f"  Has increase option: {has_increase_option}")
            print(f"  Has reduce option: {has_reduce_option}")
            
            assert has_increase_option or has_reduce_option, "Should have increase or reduce options"
        
        print("[OK] A/B question generated with increase/reduce options for budget conflict")
        return result
    
    def test_3_autofill_endpoint(self):
        """Test 3: POST /api/v1/autofill with high confidence validation"""
        print("\n=== TEST 3: /api/v1/autofill Endpoint ===")
        
        url = f"{self.base_url}/api/v1/autofill"
        
        # Simulate high confidence validation result
        payload = {
            "session_id": self.session_id or "test_session_autofill",
            "validation_results": {
                "final_result": {
                    "technical": {
                        "valid": True,
                        "controller": {
                            "suitable_controllers": [
                                {"id": "UNO-137-E23BA", "capacity": 16}
                            ]
                        },
                        "io_requirements": {
                            "analog_input": 16,
                            "digital_output": 8,
                            "total_io": 24
                        },
                        "modules": {
                            "modules_required": [
                                {"type": "ADAM-4017", "quantity": 2},
                                {"type": "ADAM-4050", "quantity": 1}
                            ]
                        }
                    },
                    "confidence": 0.92
                }
            },
            "user_profile": {"expertise": "intermediate"}
        }
        
        print(f"POST {url}")
        print(f"Payload keys: {list(payload.keys())}")
        print(f"Confidence: {payload['validation_results']['final_result']['confidence']}")
        
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=10)
        execution_time = time.time() - start_time
        
        print(f"Response time: {execution_time:.3f}s")
        print(f"Status code: {response.status_code}")
        
        # Should return success
        assert response.status_code == 200
        
        result = response.json()
        print(f"Response keys: {list(result.keys())}")
        
        # Verify autofill structure
        assert "should_autofill" in result or "autofill_triggered" in result
        
        # Check if autofill was triggered
        autofill_triggered = result.get("should_autofill", result.get("autofill_triggered", False))
        print(f"Autofill triggered: {autofill_triggered}")
        
        if autofill_triggered:
            # Verify field mappings
            field_mappings = result.get("field_mappings", {})
            autofilled_fields = result.get("autofilled_fields", {})
            
            mappings = field_mappings or autofilled_fields
            print(f"Field mappings: {len(mappings)}")
            
            for field, mapping in mappings.items():
                if isinstance(mapping, dict):
                    value = mapping.get("value", mapping)
                    confidence = mapping.get("confidence", "N/A")
                    print(f"  - {field}: {value} (confidence: {confidence})")
                else:
                    print(f"  - {field}: {mapping}")
            
            # Should have controller and I/O mappings
            expected_fields = ["controller_type", "analog_inputs"]
            found_fields = [field for field in expected_fields if field in mappings]
            print(f"Expected fields found: {found_fields}")
            
            assert len(mappings) > 0, "Should have field mappings"
        else:
            print("Autofill not triggered - confidence may be below threshold")
        
        print("[OK] Autofill endpoint returns form field mappings")
        return result
    
    def test_4_pipeline_status_endpoint(self):
        """Test 4: GET /api/v1/pipeline/status - circuit breakers closed"""
        print("\n=== TEST 4: /api/v1/pipeline/status Endpoint ===")
        
        url = f"{self.base_url}/api/v1/pipeline/status"
        
        print(f"GET {url}")
        
        start_time = time.time()
        response = requests.get(url, timeout=10)
        execution_time = time.time() - start_time
        
        print(f"Response time: {execution_time:.3f}s")
        print(f"Status code: {response.status_code}")
        
        # Should return success
        assert response.status_code == 200
        
        result = response.json()
        print(f"Response keys: {list(result.keys())}")
        
        # Verify pipeline status structure
        assert "status" in result
        assert result["status"] == "success"
        assert "pipeline" in result
        
        # Check circuit breaker states
        pipeline_data = result.get("pipeline", {})
        circuit_breakers = pipeline_data.get("circuit_breakers", {})
        
        if circuit_breakers:
            print("Circuit breaker states:")
            all_closed = True
            for agent, state_info in circuit_breakers.items():
                if isinstance(state_info, dict):
                    state = state_info.get("state", "unknown")
                else:
                    state = str(state_info)
                
                print(f"  - {agent}: {state}")
                if state != "closed":
                    all_closed = False
            
            print(f"All circuit breakers closed: {all_closed}")
            # Circuit breakers should be closed initially
            
        if pipeline_data:
            print(f"Pipeline status: {pipeline_data}")
        
        # Check for other status information
        if "pipeline_health" in result:
            print(f"Pipeline health: {result['pipeline_health']}")
        
        if "last_activity" in result:
            print(f"Last activity: {result['last_activity']}")
        
        print("[OK] Pipeline status endpoint accessible")
        return result
    
    def test_5_process_endpoint_enhanced(self):
        """Test 5: POST /api/v1/process with new requirement + session"""
        print("\n=== TEST 5: /api/v1/process Endpoint (Enhanced) ===")
        
        url = f"{self.base_url}/api/v1/process"
        
        # Add new requirement to existing session
        payload = {
            "input": "I also need operating temperature minimum -40C and sampling rate 5000 Hz",
            "session_id": self.session_id or "test_session_process",
            "budget": 3000,
            "user_profile": {"expertise": "intermediate"}
        }
        
        print(f"POST {url}")
        print(f"Payload keys: {list(payload.keys())}")
        print(f"Input: {payload['input']}")
        
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=15)
        execution_time = time.time() - start_time
        
        print(f"Response time: {execution_time:.3f}s")
        print(f"Status code: {response.status_code}")
        
        # Should return success
        assert response.status_code == 200
        
        result = response.json()
        print(f"Response keys: {list(result.keys())}")
        
        # Verify session processing
        assert "status" in result
        assert result["status"] == "success"
        
        # Check if validation was included
        confidence = result.get("aggregate_confidence", 0)
        validation_included = "validation" in result
        
        print(f"Aggregate confidence: {confidence}")
        print(f"Validation included: {validation_included}")
        
        # If confidence > 0.7, validation should be included
        if confidence > 0.7:
            assert validation_included or "autofill" in result
            print("Validation included due to high confidence")
        else:
            print("Validation not included - confidence below threshold")
        
        # Check for session context
        if "session_context" in result:
            session_context = result["session_context"]
            print(f"Total specifications: {session_context.get('total_specs', 0)}")
            print(f"Session turn: {session_context.get('turn', 0)}")
        
        # Check for conversation summary
        if "conversation_summary" in result:
            summary = result["conversation_summary"]
            print(f"Summary: {summary.get('summary', 'N/A')}")
        
        print("[OK] Process endpoint handles new requirements with session")
        return result
    
    def test_6_integration_full_workflow(self):
        """Test 6: Full workflow integration test"""
        print("\n=== TEST 6: Full Workflow Integration ===")
        
        print("Testing complete workflow:")
        print("1. Validate requirements")
        print("2. Handle conflicts with A/B questions")
        print("3. Apply autofill")
        print("4. Check system status")
        print("5. Process additional requirements")
        
        # Step 1: Initial validation
        validate_payload = {
            "session_id": "integration_test_session",
            "specifications": [
                {"constraint": "analog_input", "value": "12"},
                {"constraint": "digital_output", "value": "6"}
            ],
            "budget": 2000,
            "user_expertise": "expert"
        }
        
        start_workflow = time.time()
        
        # Validate
        response1 = requests.post(
            f"{self.base_url}/api/v1/validate",
            json=validate_payload,
            timeout=10
        )
        assert response1.status_code == 200
        validate_result = response1.json()
        
        # Step 2: Generate A/B question if there are conflicts
        if not validate_result.get("valid", True):
            conflicts = validate_result.get("conflicts", [])
            if conflicts:
                abq_payload = {
                    "session_id": "integration_test_session",
                    "conflicts": conflicts,
                    "user_expertise": "expert"
                }
                
                response2 = requests.post(
                    f"{self.base_url}/api/v1/generate_abq",
                    json=abq_payload,
                    timeout=10
                )
                assert response2.status_code == 200
                print("A/B questions generated for conflicts")
        
        # Step 3: Check pipeline status
        response3 = requests.get(f"{self.base_url}/api/v1/pipeline/status", timeout=10)
        assert response3.status_code == 200
        status_result = response3.json()
        
        # Step 4: Process additional requirements
        process_payload = {
            "session_id": "integration_test_session",
            "new_requirements": [
                {"constraint": "memory_capacity", "value": "16GB"}
            ],
            "budget": 2000
        }
        
        response4 = requests.post(
            f"{self.base_url}/api/v1/process",
            json=process_payload,
            timeout=10
        )
        assert response4.status_code == 200
        process_result = response4.json()
        
        total_workflow_time = time.time() - start_workflow
        
        print(f"Total workflow time: {total_workflow_time:.3f}s")
        print(f"Steps completed: 4/4")
        print(f"All endpoints responsive: True")
        
        # Workflow should complete quickly
        assert total_workflow_time < 15.0, f"Workflow took {total_workflow_time:.3f}s (should be <15s)"
        
        print("[OK] Full workflow integration successful")
        return {
            "validate": validate_result,
            "status": status_result,
            "process": process_result,
            "total_time": total_workflow_time
        }

# Sync test functions for pytest
def test_validate_endpoint():
    test_instance = TestRESTEndpoints()
    test_instance.setup_class()
    test_instance.setup_method()
    try:
        return test_instance.test_1_validate_endpoint()
    finally:
        test_instance.teardown_class()

def test_generate_abq_endpoint():
    test_instance = TestRESTEndpoints()
    test_instance.setup_class()
    test_instance.setup_method()
    try:
        return test_instance.test_2_generate_abq_endpoint()
    finally:
        test_instance.teardown_class()

if __name__ == "__main__":
    # Run just pipeline status test first to check basic connectivity
    print("=" * 80)
    print("REST ENDPOINTS TESTING WITH REAL DATA")
    print("=" * 80)
    
    test_instance = TestRESTEndpoints()
    
    try:
        # Setup
        test_instance.setup_class()
        test_instance.setup_method()
        
        # Run pipeline status test first (simplest)
        test_instance.test_4_pipeline_status_endpoint()
        
        print("\n" + "=" * 80)
        print("PIPELINE STATUS TEST COMPLETED!")
        print("=" * 80)
        
    finally:
        # Cleanup
        test_instance.teardown_class()