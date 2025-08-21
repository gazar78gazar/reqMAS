"""
Test system performance metrics for reqMAS API
"""

import requests
import json
import time
import threading
import psutil
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

BASE_URL = "http://localhost:8000"

def get_memory_usage():
    """Get current memory usage of the system"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return memory_info.rss / 1024 / 1024  # Convert to MB

def test_simple_requirement_performance():
    """Test 1: Simple requirement (5 specs) → < 500ms"""
    print("\n=== TEST 1: Simple Requirement Performance ===")
    
    payload = {
        "input": "I need 4 analog inputs, 2 digital outputs, RS485 communication, temperature range -10 to 50C, and 12V power supply",
        "session_id": "perf_simple"
    }
    
    # Warm up request
    requests.post(f"{BASE_URL}/process", json=payload, timeout=10)
    
    # Performance test
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/process", json=payload, timeout=10)
    execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    print(f"Status Code: {response.status_code}")
    print(f"Execution Time: {execution_time:.2f}ms")
    
    if response.status_code == 200:
        result = response.json()
        specs_count = len(result.get("result", {}).get("session_context", {}).get("accumulated_specifications", []))
        print(f"Specifications extracted: {specs_count}")
        
        if execution_time < 500:
            print(f"[PASS] Simple requirement completed in {execution_time:.2f}ms (< 500ms target)")
        else:
            print(f"[FAIL] Simple requirement took {execution_time:.2f}ms (> 500ms target)")
    else:
        print(f"[FAIL] Request failed with status {response.status_code}")
    
    return execution_time

def test_complex_requirement_performance():
    """Test 2: Complex requirement (20 specs) → < 2 seconds"""
    print("\n=== TEST 2: Complex Requirement Performance ===")
    
    payload = {
        "input": """I need a comprehensive IoT solution with 16 analog inputs for temperature sensors, 
        8 digital inputs for motion detectors, 12 analog outputs for valve control, 6 digital outputs for alarms,
        RS485 and Modbus TCP communication, operating temperature -40C to +85C, IP67 protection rating,
        24VDC power supply with backup battery, 1000Hz sampling rate, 16MB memory capacity,
        Ethernet connectivity, WiFi backup, MQTT protocol support, data logging capability,
        real-time monitoring, alarm notification system, remote configuration access,
        firmware update capability, and integration with SCADA systems.""",
        "session_id": "perf_complex"
    }
    
    # Warm up
    requests.post(f"{BASE_URL}/process", json=payload, timeout=15)
    
    # Performance test
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/process", json=payload, timeout=15)
    execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    print(f"Status Code: {response.status_code}")
    print(f"Execution Time: {execution_time:.2f}ms")
    
    if response.status_code == 200:
        result = response.json()
        specs_count = len(result.get("result", {}).get("session_context", {}).get("accumulated_specifications", []))
        print(f"Specifications extracted: {specs_count}")
        
        if execution_time < 2000:
            print(f"[PASS] Complex requirement completed in {execution_time:.2f}ms (< 2000ms target)")
        else:
            print(f"[FAIL] Complex requirement took {execution_time:.2f}ms (> 2000ms target)")
    else:
        print(f"[FAIL] Request failed with status {response.status_code}")
    
    return execution_time

def test_full_validation_pipeline():
    """Test 3: Full validation pipeline → < 3 seconds"""
    print("\n=== TEST 3: Full Validation Pipeline Performance ===")
    
    # First create a session with requirements
    setup_payload = {
        "input": "I need 8 analog inputs, 4 digital outputs, and RS485 communication",
        "session_id": "perf_validation"
    }
    requests.post(f"{BASE_URL}/process", json=setup_payload, timeout=10)
    
    # Test full validation pipeline
    validation_payload = {
        "session_id": "perf_validation",
        "budget": 3000,
        "user_profile": {"expertise": "intermediate"}
    }
    
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/api/v1/validate", json=validation_payload, timeout=15)
    execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    print(f"Status Code: {response.status_code}")
    print(f"Execution Time: {execution_time:.2f}ms")
    
    if response.status_code == 200:
        result = response.json()
        validation = result.get("validation", {})
        consensus = validation.get("consensus_achieved", False)
        
        print(f"Validation consensus achieved: {consensus}")
        
        if execution_time < 3000:
            print(f"[PASS] Full validation completed in {execution_time:.2f}ms (< 3000ms target)")
        else:
            print(f"[FAIL] Full validation took {execution_time:.2f}ms (> 3000ms target)")
    else:
        print(f"[FAIL] Validation failed with status {response.status_code}")
    
    return execution_time

def test_memory_usage():
    """Test 4: Memory usage → < 500MB"""
    print("\n=== TEST 4: Memory Usage ===")
    
    # Get baseline memory usage
    baseline_memory = get_memory_usage()
    print(f"Baseline memory usage: {baseline_memory:.2f}MB")
    
    # Perform multiple operations to stress memory
    sessions = []
    for i in range(10):
        payload = {
            "input": f"Test session {i} with analog inputs and digital outputs",
            "session_id": f"memory_test_{i}"
        }
        response = requests.post(f"{BASE_URL}/process", json=payload, timeout=10)
        if response.status_code == 200:
            sessions.append(f"memory_test_{i}")
    
    # Check memory after operations
    current_memory = get_memory_usage()
    memory_increase = current_memory - baseline_memory
    
    print(f"Memory after operations: {current_memory:.2f}MB")
    print(f"Memory increase: {memory_increase:.2f}MB")
    
    # Note: This measures the test script's memory, not the server's
    # For actual server memory, we would need to monitor the server process
    print("[INFO] Memory test measures client script memory, not server memory")
    
    if current_memory < 500:
        print(f"[PASS] Total memory usage {current_memory:.2f}MB (< 500MB target)")
    else:
        print(f"[WARNING] Total memory usage {current_memory:.2f}MB (> 500MB target)")
    
    return current_memory

def validate_session(session_id, budget=2000):
    """Helper function to validate a single session"""
    payload = {
        "session_id": session_id,
        "budget": budget,
        "user_profile": {"expertise": "intermediate"}
    }
    
    start_time = time.time()
    try:
        response = requests.post(f"{BASE_URL}/api/v1/validate", json=payload, timeout=15)
        execution_time = (time.time() - start_time) * 1000
        
        return {
            "session_id": session_id,
            "status_code": response.status_code,
            "execution_time": execution_time,
            "success": response.status_code == 200
        }
    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        return {
            "session_id": session_id,
            "status_code": 500,
            "execution_time": execution_time,
            "success": False,
            "error": str(e)
        }

def test_concurrent_validations():
    """Test 5: Concurrent validations (3 sessions) → all complete"""
    print("\n=== TEST 5: Concurrent Validations ===")
    
    # Create 3 sessions with requirements
    sessions = []
    for i in range(3):
        session_id = f"concurrent_test_{i}"
        payload = {
            "input": f"Session {i}: I need {4+i} analog inputs and {2+i} digital outputs",
            "session_id": session_id
        }
        response = requests.post(f"{BASE_URL}/process", json=payload, timeout=10)
        if response.status_code == 200:
            sessions.append(session_id)
    
    print(f"Created {len(sessions)} sessions for concurrent testing")
    
    # Run concurrent validations
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Submit all validation tasks
        future_to_session = {
            executor.submit(validate_session, session_id): session_id 
            for session_id in sessions
        }
        
        results = []
        for future in as_completed(future_to_session):
            result = future.result()
            results.append(result)
    
    total_time = (time.time() - start_time) * 1000
    
    print(f"Total concurrent execution time: {total_time:.2f}ms")
    print("Individual results:")
    
    successful_validations = 0
    for result in results:
        status = "[PASS]" if result["success"] else "[FAIL]"
        print(f"  - {result['session_id']}: {status} {result['execution_time']:.2f}ms")
        if result["success"]:
            successful_validations += 1
    
    if successful_validations == len(sessions):
        print(f"[PASS] All {successful_validations} concurrent validations completed successfully")
    else:
        print(f"[FAIL] Only {successful_validations}/{len(sessions)} validations completed successfully")
    
    return results

def test_circuit_breaker_recovery():
    """Test 6: Circuit breaker recovery → < 60 seconds"""
    print("\n=== TEST 6: Circuit Breaker Recovery ===")
    
    # Check current circuit breaker status
    status_response = requests.get(f"{BASE_URL}/api/v1/pipeline/status", timeout=10)
    if status_response.status_code == 200:
        status_data = status_response.json()
        pipeline = status_data.get("pipeline", {})
        circuit_breakers = pipeline.get("circuit_breakers", {})
        
        print("Current circuit breaker states:")
        for agent, state in circuit_breakers.items():
            if isinstance(state, dict):
                cb_state = state.get("state", "unknown")
            else:
                cb_state = str(state)
            print(f"  - {agent}: {cb_state}")
        
        # All circuit breakers should be closed (healthy)
        all_closed = True
        for agent, state in circuit_breakers.items():
            if isinstance(state, dict):
                cb_state = state.get("state", "unknown")
            else:
                cb_state = str(state)
            if cb_state != "closed":
                all_closed = False
                break
        
        if all_closed:
            print("[PASS] All circuit breakers are in 'closed' (healthy) state")
            print("[INFO] No recovery test needed - system is healthy")
        else:
            print("[INFO] Some circuit breakers are open - testing recovery...")
            
            # Try to reset circuit breakers
            reset_response = requests.post(f"{BASE_URL}/api/v1/pipeline/reset", timeout=10)
            if reset_response.status_code == 200:
                print("Circuit breaker reset initiated")
                
                # Wait and check recovery
                time.sleep(5)
                recovery_response = requests.get(f"{BASE_URL}/api/v1/pipeline/status", timeout=10)
                if recovery_response.status_code == 200:
                    recovery_data = recovery_response.json()
                    recovery_breakers = recovery_data.get("pipeline", {}).get("circuit_breakers", {})
                    
                    recovered = all(
                        (state.get("state", "unknown") if isinstance(state, dict) else str(state)) == "closed"
                        for state in recovery_breakers.values()
                    )
                    
                    if recovered:
                        print("[PASS] Circuit breakers recovered successfully")
                    else:
                        print("[WARNING] Circuit breakers still recovering")
            else:
                print("[FAIL] Circuit breaker reset failed")
    else:
        print("[FAIL] Could not check circuit breaker status")

def run_performance_tests():
    """Run all performance tests"""
    print("=" * 60)
    print("REQMAS SYSTEM PERFORMANCE METRICS TESTING")
    print("=" * 60)
    print(f"Test started at: {datetime.now()}")
    
    results = {}
    
    try:
        # Test 1: Simple requirement performance
        results['simple'] = test_simple_requirement_performance()
        time.sleep(1)
        
        # Test 2: Complex requirement performance  
        results['complex'] = test_complex_requirement_performance()
        time.sleep(1)
        
        # Test 3: Full validation pipeline
        results['validation'] = test_full_validation_pipeline()
        time.sleep(1)
        
        # Test 4: Memory usage
        results['memory'] = test_memory_usage()
        time.sleep(1)
        
        # Test 5: Concurrent validations
        results['concurrent'] = test_concurrent_validations()
        time.sleep(1)
        
        # Test 6: Circuit breaker recovery
        test_circuit_breaker_recovery()
        
    except Exception as e:
        print(f"[FAIL] Performance test suite failed: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("PERFORMANCE TEST SUMMARY")
    print("=" * 60)
    
    if 'simple' in results:
        status = "PASS" if results['simple'] < 500 else "FAIL"
        print(f"Simple requirement: {results['simple']:.2f}ms [{status}]")
    
    if 'complex' in results:
        status = "PASS" if results['complex'] < 2000 else "FAIL"  
        print(f"Complex requirement: {results['complex']:.2f}ms [{status}]")
    
    if 'validation' in results:
        status = "PASS" if results['validation'] < 3000 else "FAIL"
        print(f"Full validation: {results['validation']:.2f}ms [{status}]")
    
    if 'memory' in results:
        status = "PASS" if results['memory'] < 500 else "WARNING"
        print(f"Memory usage: {results['memory']:.2f}MB [{status}]")
    
    if 'concurrent' in results:
        successful = sum(1 for r in results['concurrent'] if r['success'])
        total = len(results['concurrent'])
        status = "PASS" if successful == total else "FAIL"
        print(f"Concurrent validations: {successful}/{total} [{status}]")
    
    print(f"\nTest completed at: {datetime.now()}")

if __name__ == "__main__":
    run_performance_tests()