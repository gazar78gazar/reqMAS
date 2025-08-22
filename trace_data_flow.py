"""
Systematic Data Flow Tracer for reqMAS
Traces specifications through the entire system to identify where they get lost
"""

import requests
import json
import time
from typing import Dict, List, Any

class DataFlowTracer:
    def __init__(self):
        self.checkpoints = {
            "1_input": "User input received",
            "2_orchestrator": "Orchestrator processes",
            "3_agents": "Agents extract specs",
            "4_accumulation": "Specs accumulated", 
            "5_phase2_input": "Phase 2 receives specs",
            "6_validation": "Validation processes specs",
            "7_response_gen": "Response generator receives specs",
            "8_output": "Final response includes spec info"
        }
        self.trace_log = []
    
    def validate_structure(self, data: Any, expected_structure: Dict, checkpoint: str):
        """Validate data structure at checkpoint"""
        print(f"\n[VALIDATION] {checkpoint}")
        
        if data is None:
            print(f"  ❌ Data is None!")
            self.trace_log.append((checkpoint, "NULL_DATA", None))
            return False
        
        if isinstance(expected_structure, dict):
            if not isinstance(data, dict):
                print(f"  ❌ Expected dict, got {type(data)}")
                self.trace_log.append((checkpoint, "TYPE_MISMATCH", type(data)))
                return False
            
            # Check expected keys
            for key, expected_type in expected_structure.items():
                if key not in data:
                    print(f"  ❌ Missing key: {key}")
                    self.trace_log.append((checkpoint, f"MISSING_KEY_{key}", None))
                elif not isinstance(data[key], expected_type):
                    print(f"  ❌ {key} is {type(data[key])}, expected {expected_type}")
                    self.trace_log.append((checkpoint, f"TYPE_ERROR_{key}", type(data[key])))
                else:
                    print(f"  ✅ {key}: {type(data[key])} ({len(data[key]) if hasattr(data[key], '__len__') else 'N/A'} items)")
        
        return True
    
    def trace_single_request(self, input_text: str):
        """Trace a single request through the system"""
        print("\n" + "="*60)
        print("TRACING DATA FLOW")
        print("="*60)
        print(f"Input: {input_text}")
        
        # Make API call
        response = requests.post(
            "http://localhost:8000/process",
            json={
                "user_input": input_text,
                "session_id": f"trace_{int(time.time())}"
            },
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            return None
        
        data = response.json()
        
        # Checkpoint 1: API Response Structure
        print("\n[CHECKPOINT 1] API Response Structure")
        print(f"Top-level keys: {list(data.keys())}")
        
        # Check if response is nested or direct
        if 'result' in data:
            print("  → Response is NESTED (has 'result' key)")
            result = data['result']
        else:
            print("  → Response is DIRECT (no 'result' key)")
            result = data
        
        # Checkpoint 2: Routing Information
        print("\n[CHECKPOINT 2] Routing Information")
        expected_routing = {
            "has_io_content": bool,
            "has_system_content": bool,
            "has_comm_content": bool
        }
        routing = result.get('routing', {})
        self.validate_structure(routing, expected_routing, "Routing")
        
        # Checkpoint 3: Agent Results
        print("\n[CHECKPOINT 3] Agent Results")
        activated_agents = result.get('activated_agents', [])
        print(f"Activated agents: {activated_agents}")
        
        merged_results = result.get('merged_results', {})
        if merged_results:
            print(f"Merged results keys: {list(merged_results.keys())}")
            if 'primary' in merged_results:
                primary = merged_results['primary']
                if 'specifications' in primary:
                    specs = primary['specifications']
                    print(f"  → Found {len(specs)} specifications in primary")
                    for i, spec in enumerate(specs[:3]):
                        print(f"    Spec {i+1}: {spec.get('constraint', 'N/A')} = {spec.get('value', 'N/A')}")
        
        # Checkpoint 4: Session Context
        print("\n[CHECKPOINT 4] Session Context")
        session_context = result.get('session_context', {})
        if session_context:
            print(f"Session context keys: {list(session_context.keys())}")
            accumulated_specs = session_context.get('accumulated_specifications', [])
            print(f"  → Accumulated specs: {len(accumulated_specs)}")
            total_specs = session_context.get('total_specs', 0)
            print(f"  → Total specs count: {total_specs}")
        
        # Checkpoint 5: Conversational Response
        print("\n[CHECKPOINT 5] Conversational Response")
        conv_response = result.get('conversational_response', '')
        print(f"Response length: {len(conv_response)}")
        print(f"Response preview: {conv_response[:150]}...")
        
        # Check if response is generic or contextual
        if "I'm ready to help" in conv_response:
            print("  ❌ GENERIC RESPONSE - Phase 2 not working!")
        elif "Based on your requirements" in conv_response:
            print("  ✅ CONTEXTUAL RESPONSE - Phase 2 working!")
        else:
            print("  🔍 UNKNOWN RESPONSE TYPE")
        
        # Analyze Phase 2 data flow
        print("\n[CHECKPOINT 6] Phase 2 Data Flow Analysis")
        if len(accumulated_specs if 'accumulated_specs' in locals() else []) > 0:
            print("  ✅ Specs accumulated")
            print("  → CHECK: Are specs passed to validation_pipeline?")
            print("  → CHECK: Does validation_result contain specs?")
            print("  → CHECK: Are specs passed to decision_coordinator?")
        else:
            print("  ❌ No specs accumulated - Phase 2 has nothing to work with!")
        
        return result
    
    def trace_conversation_flow(self):
        """Trace a multi-turn conversation"""
        print("\n" + "="*60)
        print("CONVERSATION FLOW TRACE")
        print("="*60)
        
        session_id = f"conversation_trace_{int(time.time())}"
        
        messages = [
            "I need 8 analog inputs",
            "Also 4 digital outputs",
            "What are my requirements?"
        ]
        
        accumulated_specs = []
        
        for i, message in enumerate(messages, 1):
            print(f"\n--- Turn {i}: {message} ---")
            
            response = requests.post(
                "http://localhost:8000/process",
                json={
                    "user_input": message,
                    "session_id": session_id
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('result', data)
                
                # Track specification accumulation
                session_context = result.get('session_context', {})
                current_specs = session_context.get('accumulated_specifications', [])
                new_specs = len(current_specs) - len(accumulated_specs)
                
                print(f"  New specs this turn: {new_specs}")
                print(f"  Total accumulated: {len(current_specs)}")
                
                conv_response = result.get('conversational_response', '')
                print(f"  Response type: {'CONTEXTUAL' if 'Based on' in conv_response else 'GENERIC'}")
                
                accumulated_specs = current_specs
    
    def analyze_method_signatures(self):
        """Analyze potential method signature mismatches"""
        print("\n" + "="*60)
        print("METHOD SIGNATURE ANALYSIS")
        print("="*60)
        
        checks = [
            {
                "file": "main.py",
                "caller": "decision_coordinator.process()",
                "expected_params": ["input_data", "context"],
                "actual_call": "Check if all_specs is in input_data"
            },
            {
                "file": "decision_coordinator.py", 
                "method": "_format_intermediate_response()",
                "expected_params": ["validation", "all_specs"],
                "check": "Are both params passed?"
            },
            {
                "file": "validation_pipeline.py",
                "method": "validate()",
                "expected_params": ["specifications", "context"],
                "check": "What structure does it expect?"
            }
        ]
        
        for check in checks:
            print(f"\n[CHECK] {check.get('file', 'Unknown')}")
            if 'method' in check:
                print(f"  Method: {check['method']}")
            if 'caller' in check:
                print(f"  Caller: {check['caller']}")
            print(f"  Check: {check.get('check', 'N/A')}")

def main():
    tracer = DataFlowTracer()
    
    # Test 1: Single request with specifications
    print("\n🔍 TEST 1: Single Request Trace")
    result1 = tracer.trace_single_request("I need 16 digital inputs and 8 analog outputs")
    
    # Test 2: Conversation flow
    print("\n🔍 TEST 2: Conversation Flow")
    tracer.trace_conversation_flow()
    
    # Test 3: Method signature analysis
    print("\n🔍 TEST 3: Method Signatures")
    tracer.analyze_method_signatures()
    
    # Summary
    print("\n" + "="*60)
    print("TRACE SUMMARY")
    print("="*60)
    
    if tracer.trace_log:
        print("\n❌ Issues Found:")
        for checkpoint, issue, detail in tracer.trace_log:
            print(f"  - {checkpoint}: {issue} {f'({detail})' if detail else ''}")
    else:
        print("✅ No structural issues found in trace log")
    
    print("\n📋 Next Steps:")
    print("1. Check server logs for [SPECS], [PHASE2], and [DecisionCoord] messages")
    print("2. Verify validation_pipeline.validate() receives specifications")
    print("3. Confirm decision_coordinator gets specs in input_data")
    print("4. Check if _format_intermediate_response receives all_specs parameter")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Tracer failed: {e}")
        print("Make sure the server is running on http://localhost:8000")