"""
Phase 2 Code Audit Script
Finds common Python/async issues and data flow problems
"""

import ast
import os
from pathlib import Path
import re

class Phase2Auditor:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.info = []
        
    def audit_file(self, filepath: Path) -> dict:
        """Audit a single Python file for common issues"""
        issues = []
        
        if not filepath.exists():
            return {"error": f"File not found: {filepath}"}
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check 1: ainvoke usage (should be invoke)
        if 'ainvoke' in content:
            lines = [i+1 for i, line in enumerate(content.split('\n')) if 'ainvoke' in line]
            issues.append({
                'type': 'CRITICAL',
                'issue': 'Uses ainvoke instead of invoke',
                'lines': lines
            })
        
        # Check 2: Forgotten await
        async_patterns = re.findall(r'(\w+)\s*=\s*(\w+\.process|validate|execute)\(', content)
        for var, method in async_patterns:
            if 'await' not in content.split(f'{var} =')[0][-50:]:
                issues.append({
                    'type': 'WARNING',
                    'issue': f'Possible missing await for {method}',
                    'pattern': f'{var} = {method}('
                })
        
        # Check 3: Mutable default arguments
        if re.search(r'def \w+\([^)]*=\s*\[\]', content):
            issues.append({
                'type': 'WARNING',
                'issue': 'Mutable default argument (=[])',
                'pattern': 'def function(param=[])'
            })
        
        if re.search(r'def \w+\([^)]*=\s*\{\}', content):
            issues.append({
                'type': 'WARNING',
                'issue': 'Mutable default argument (={})',
                'pattern': 'def function(param={})'
            })
        
        # Check 4: Unsafe dict access
        unsafe_patterns = re.findall(r'(\w+)\[[\'"]\w+[\'"]]\[[\'"]\w+[\'"]]', content)
        if unsafe_patterns:
            issues.append({
                'type': 'INFO',
                'issue': 'Unsafe nested dict access (use .get() instead)',
                'count': len(unsafe_patterns)
            })
        
        # Check 5: Specifications handling
        spec_access = content.count("['specifications']") + content.count('["specifications"]')
        spec_get = content.count(".get('specifications'") + content.count('.get("specifications"')
        spec_pass = content.count("specifications=") + content.count("specifications:")
        spec_in_params = content.count("specifications,") + content.count("all_specs")
        
        if 'specifications' in content:
            issues.append({
                'type': 'METRICS',
                'spec_access': spec_access,
                'spec_get': spec_get,
                'spec_pass': spec_pass,
                'spec_in_params': spec_in_params
            })
        
        # Check 6: Lost data - specs assigned but not used
        if 'all_specs = ' in content:
            # Check if all_specs is used after assignment
            parts = content.split('all_specs = ')
            for i, part in enumerate(parts[1:], 1):
                next_section = part[:500]  # Check next 500 chars
                if 'all_specs' not in next_section and 'return' in next_section[:100]:
                    issues.append({
                        'type': 'WARNING',
                        'issue': 'all_specs assigned but possibly not used',
                        'context': next_section[:50]
                    })
        
        # Check 7: Dict mutation issues
        if re.search(r'(\w+)\s*=\s*(\w+)\s*\n.*\1\.clear\(\)', content):
            issues.append({
                'type': 'WARNING',
                'issue': 'Possible dict mutation issue (assignment then clear)'
            })
        
        return issues
    
    def audit_data_flow(self):
        """Audit the specific data flow for specifications"""
        print("\n" + "="*60)
        print("DATA FLOW AUDIT")
        print("="*60)
        
        # Critical path for specifications
        critical_path = [
            {
                'file': 'src/main.py',
                'function': 'process_with_orchestrator',
                'checks': [
                    'all_specs is created',
                    'all_specs is passed to validation_pipeline',
                    'all_specs is passed to decision_coordinator'
                ]
            },
            {
                'file': 'src/validation/validation_pipeline.py',
                'function': 'validate',
                'checks': [
                    'receives specifications parameter',
                    'returns specifications in result',
                    'does not filter/clear specs'
                ]
            },
            {
                'file': 'src/agents/decision_coordinator.py',
                'function': 'process',
                'checks': [
                    'receives all_specs in input_data',
                    'passes all_specs to formatting methods',
                    'formatting methods use all_specs'
                ]
            }
        ]
        
        for step in critical_path:
            filepath = Path(step['file'])
            print(f"\n[CHECKING] {step['file']} :: {step['function']}")
            
            if not filepath.exists():
                print(f"  [FAIL] File not found")
                continue
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find the function
            func_pattern = f"def {step['function']}" if not step['function'].startswith('async') else f"async def {step['function']}"
            if func_pattern in content or f"async {func_pattern}" in content:
                print(f"  [OK] Function found")
                
                # Extract function content (simple approach)
                start_idx = content.find(func_pattern)
                if start_idx != -1:
                    func_content = content[start_idx:start_idx+2000]  # Get next 2000 chars
                    
                    for check in step['checks']:
                        if 'all_specs' in check:
                            if 'all_specs' in func_content:
                                print(f"  [OK] {check}")
                            else:
                                print(f"  [FAIL] {check}")
                        elif 'specifications' in check:
                            if 'specifications' in func_content:
                                print(f"  [OK] {check}")
                            else:
                                print(f"  [WARN]  {check}")
            else:
                print(f"  [FAIL] Function not found")
    
    def check_async_await_consistency(self):
        """Check for async/await consistency"""
        print("\n" + "="*60)
        print("ASYNC/AWAIT CONSISTENCY CHECK")
        print("="*60)
        
        files_to_check = [
            'src/main.py',
            'src/agents/decision_coordinator.py',
            'src/validation/validation_pipeline.py'
        ]
        
        for filepath in files_to_check:
            path = Path(filepath)
            if not path.exists():
                continue
            
            print(f"\n[FILE] {filepath}")
            
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find async functions
            async_funcs = re.findall(r'async def (\w+)', content)
            print(f"  Async functions: {len(async_funcs)}")
            
            # Check for calls without await
            for func in async_funcs:
                # Simple pattern - might have false positives
                pattern = f"[^await ]({func}\\()"
                matches = re.findall(pattern, content)
                if matches:
                    print(f"  [WARN]  {func} might be called without await ({len(matches)} instances)")
    
    def generate_debug_instrumentation(self):
        """Generate debug instrumentation code"""
        print("\n" + "="*60)
        print("DEBUG INSTRUMENTATION CODE")
        print("="*60)
        
        template = '''
def method_with_debug(self, param1, param2):
    """Example method with full debug instrumentation"""
    # ENTRY
    method_name = "method_with_debug"
    print(f"[{self.__class__.__name__}] ENTER {method_name}")
    print(f"  Params: {list(locals().keys())}")
    
    # Check for specifications in params
    for param_name, param_value in locals().items():
        if param_name not in ['self', 'method_name']:
            if isinstance(param_value, dict):
                has_specs = 'specifications' in param_value or 'all_specs' in param_value
                print(f"  {param_name}: type={type(param_value).__name__}, has_specs={has_specs}")
                if has_specs:
                    spec_count = len(param_value.get('specifications', param_value.get('all_specs', [])))
                    print(f"    -> Contains {spec_count} specifications")
            elif isinstance(param_value, list):
                print(f"  {param_name}: list with {len(param_value)} items")
    
    try:
        # === METHOD LOGIC HERE ===
        result = {"example": "result"}
        
        # EXIT - Success
        print(f"[{self.__class__.__name__}] EXIT {method_name} - SUCCESS")
        if isinstance(result, dict):
            print(f"  Return keys: {list(result.keys())}")
            has_specs = 'specifications' in result or 'all_specs' in result
            print(f"  Has specs: {has_specs}")
        else:
            print(f"  Return type: {type(result).__name__}")
        
        return result
        
    except Exception as e:
        # EXIT - Error
        print(f"[{self.__class__.__name__}] EXIT {method_name} - ERROR")
        print(f"  Exception: {e}")
        raise
'''
        print(template)
        
        print("\n[TODO] Add this instrumentation to:")
        print("1. validation_pipeline.validate()")
        print("2. decision_coordinator.process()")
        print("3. decision_coordinator._format_chat_response()")
        print("4. decision_coordinator._format_intermediate_response()")

def main():
    auditor = Phase2Auditor()
    
    print("="*60)
    print("PHASE 2 COMPREHENSIVE AUDIT")
    print("="*60)
    
    # Audit critical files
    files_to_audit = [
        'src/main.py',
        'src/validation/validation_pipeline.py',
        'src/agents/decision_coordinator.py',
        'src/validation/confidence_aggregator.py'
    ]
    
    print("\n[INDIVIDUAL FILE AUDIT]")
    all_issues = {}
    
    for filepath in files_to_audit:
        path = Path(filepath)
        print(f"\n[FILE] {filepath}")
        
        issues = auditor.audit_file(path)
        all_issues[filepath] = issues
        
        if issues:
            for issue in issues:
                if isinstance(issue, dict):
                    issue_type = issue.get('type', 'INFO')
                    if issue_type == 'CRITICAL':
                        print(f"  [FAIL] CRITICAL: {issue.get('issue')}")
                        if 'lines' in issue:
                            print(f"     Lines: {issue['lines']}")
                    elif issue_type == 'WARNING':
                        print(f"  [WARN]  WARNING: {issue.get('issue')}")
                    elif issue_type == 'METRICS':
                        print(f"  [METRICS]:")
                        print(f"     - Spec access: {issue.get('spec_access', 0)}")
                        print(f"     - Spec get: {issue.get('spec_get', 0)}")
                        print(f"     - Spec pass: {issue.get('spec_pass', 0)}")
                        print(f"     - Spec in params: {issue.get('spec_in_params', 0)}")
    
    # Run specialized audits
    auditor.audit_data_flow()
    auditor.check_async_await_consistency()
    
    # Generate debug code
    print("\n" + "="*60)
    print("RECOMMENDED ACTIONS")
    print("="*60)
    
    critical_count = sum(1 for issues in all_issues.values() 
                        for issue in issues 
                        if isinstance(issue, dict) and issue.get('type') == 'CRITICAL')
    
    warning_count = sum(1 for issues in all_issues.values() 
                       for issue in issues 
                       if isinstance(issue, dict) and issue.get('type') == 'WARNING')
    
    print(f"\n[SUMMARY]:")
    print(f"  - Critical Issues: {critical_count}")
    print(f"  - Warnings: {warning_count}")
    
    print("\n[IMMEDIATE ACTIONS]:")
    if critical_count > 0:
        print("1. Fix all 'ainvoke' calls - replace with 'invoke'")
    print("2. Add debug instrumentation to trace specification flow")
    print("3. Check all async function calls have 'await'")
    print("4. Verify all_specs is passed through the entire Phase 2 chain")
    
    # Generate instrumentation code
    print("\n[TIP] To add debug instrumentation, see the template above")
    print("   Copy and adapt it for each critical method")

if __name__ == "__main__":
    main()