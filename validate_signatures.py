"""
Method Signature Validator for reqMAS
Checks for parameter mismatches between callers and callees
"""

import ast
import os
from pathlib import Path

class SignatureValidator:
    def __init__(self, project_root="src"):
        self.project_root = Path(project_root)
        self.issues = []
        
    def extract_function_signatures(self, filepath):
        """Extract all function/method signatures from a Python file"""
        signatures = {}
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    # Get function name
                    func_name = node.name
                    
                    # Get parameters
                    params = []
                    for arg in node.args.args:
                        params.append(arg.arg)
                    
                    # Check if async
                    is_async = isinstance(node, ast.AsyncFunctionDef)
                    
                    signatures[func_name] = {
                        'params': params,
                        'is_async': is_async,
                        'line': node.lineno
                    }
        except Exception as e:
            print(f"Error parsing {filepath}: {e}")
        
        return signatures
    
    def find_function_calls(self, filepath, target_function):
        """Find all calls to a specific function"""
        calls = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Handle different call types
                    call_name = None
                    
                    if isinstance(node.func, ast.Name):
                        call_name = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        call_name = node.func.attr
                    
                    if call_name == target_function:
                        # Count arguments
                        num_args = len(node.args)
                        num_kwargs = len(node.keywords)
                        
                        calls.append({
                            'line': node.lineno if hasattr(node, 'lineno') else 0,
                            'num_args': num_args,
                            'num_kwargs': num_kwargs,
                            'total_args': num_args + num_kwargs
                        })
        except Exception as e:
            print(f"Error analyzing calls in {filepath}: {e}")
        
        return calls
    
    def validate_critical_signatures(self):
        """Validate critical method signatures in reqMAS"""
        
        critical_checks = [
            {
                'file': 'agents/decision_coordinator.py',
                'method': '_format_intermediate_response',
                'expected_params': ['self', 'validation', 'all_specs'],
                'callers': [
                    {'file': 'agents/decision_coordinator.py', 'method': '_format_chat_response'}
                ]
            },
            {
                'file': 'agents/decision_coordinator.py',
                'method': 'process',
                'expected_params': ['self', 'input_data', 'context'],
                'callers': [
                    {'file': 'main.py', 'line_hint': 'decision_coordinator.process'}
                ]
            },
            {
                'file': 'validation/validation_pipeline.py',
                'method': 'validate',
                'expected_params': ['self', 'specifications', 'context'],
                'callers': [
                    {'file': 'main.py', 'line_hint': 'validation_pipeline.validate'}
                ]
            }
        ]
        
        print("="*60)
        print("METHOD SIGNATURE VALIDATION")
        print("="*60)
        
        for check in critical_checks:
            filepath = self.project_root / check['file']
            
            if not filepath.exists():
                print(f"\n❌ File not found: {filepath}")
                continue
            
            print(f"\n[CHECKING] {check['file']} :: {check['method']}")
            
            # Get actual signature
            signatures = self.extract_function_signatures(filepath)
            
            if check['method'] in signatures:
                actual = signatures[check['method']]
                print(f"  Actual params: {actual['params']}")
                print(f"  Expected params: {check['expected_params']}")
                
                # Check for mismatches
                if actual['params'] != check['expected_params']:
                    print(f"  ❌ MISMATCH! Actual has {len(actual['params'])} params, expected {len(check['expected_params'])}")
                    self.issues.append({
                        'file': check['file'],
                        'method': check['method'],
                        'issue': 'Parameter count mismatch',
                        'actual': actual['params'],
                        'expected': check['expected_params']
                    })
                else:
                    print(f"  ✅ Signature matches")
                
                # Check if async
                if actual['is_async']:
                    print(f"  ⚠️  Method is async - callers must use 'await'")
            else:
                print(f"  ❌ Method not found in file")
    
    def check_phase2_data_flow(self):
        """Specifically check Phase 2 data flow"""
        print("\n" + "="*60)
        print("PHASE 2 DATA FLOW CHECK")
        print("="*60)
        
        # Check main.py Phase 2 integration
        main_file = self.project_root / "main.py"
        
        if main_file.exists():
            with open(main_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if all_specs is passed to decision_coordinator
            if "all_specs" in content and "decision_coordinator.process" in content:
                print("\n✅ main.py appears to pass all_specs to decision_coordinator")
                
                # Find the specific line
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if "all_specs" in line and "decision_coordinator" in line:
                        print(f"  Line {i}: {line.strip()[:80]}...")
            else:
                print("\n❌ main.py may not be passing all_specs to decision_coordinator")
        
        # Check decision_coordinator receives specs
        dc_file = self.project_root / "agents/decision_coordinator.py"
        
        if dc_file.exists():
            with open(dc_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if all_specs is extracted from input_data
            if "all_specs = input_data.get" in content:
                print("\n✅ decision_coordinator extracts all_specs from input_data")
            else:
                print("\n⚠️  decision_coordinator may not be extracting all_specs")
            
            # Check if formatting methods use all_specs
            if "_format_intermediate_response(self, validation: Dict, all_specs: List)" in content:
                print("✅ _format_intermediate_response accepts all_specs parameter")
            else:
                print("❌ _format_intermediate_response may not accept all_specs")

def main():
    validator = SignatureValidator()
    
    # Run validation
    validator.validate_critical_signatures()
    validator.check_phase2_data_flow()
    
    # Summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    if validator.issues:
        print("\n❌ Issues Found:")
        for issue in validator.issues:
            print(f"\n  File: {issue['file']}")
            print(f"  Method: {issue['method']}")
            print(f"  Issue: {issue['issue']}")
            print(f"  Actual: {issue['actual']}")
            print(f"  Expected: {issue['expected']}")
    else:
        print("\n✅ No signature mismatches found")
    
    print("\n📋 Manual Checks Needed:")
    print("1. Verify async/await usage is correct")
    print("2. Check that all_specs is populated before Phase 2")
    print("3. Confirm validation_pipeline preserves specifications")
    print("4. Ensure decision_coordinator formats responses with specs")

if __name__ == "__main__":
    main()