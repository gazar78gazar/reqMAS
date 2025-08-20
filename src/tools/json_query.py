"""
JSON Query Tool for reqMAS Phase 1
JSON data access utility with path-based querying
"""

from typing import Dict, List, Any, Optional, Union
import json
import os
import re

class JSONQueryTool:
    """
    JSON data access utility with path-based querying.
    Allows structured access to JSON data files.
    """
    
    def __init__(self, data_dir: str = None):
        """
        Initialize with optional data directory.
        If not provided, will use '../data/' relative to this file.
        """
        if data_dir is None:
            # Default to ../data/ relative to this file
            self.data_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), '..', '..', 'data')
            )
        else:
            self.data_dir = data_dir
        
        # Cache for loaded JSON files
        self.cache = {}
    
    def load_file(self, filename: str) -> Dict:
        """
        Load a JSON file from the data directory.
        Returns the parsed JSON data.
        """
        if filename in self.cache:
            return self.cache[filename]
        
        # Ensure .json extension
        if not filename.endswith('.json'):
            filename += '.json'
        
        file_path = os.path.join(self.data_dir, filename)
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                self.cache[filename] = data
                return data
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return {}
        except json.JSONDecodeError:
            print(f"Invalid JSON in file: {file_path}")
            return {}
    
    def query(self, filename: str, path: str) -> Any:
        """
        Query JSON data using a path expression.
        Path format: key1.key2[0].key3
        Returns the value at the specified path.
        """
        data = self.load_file(filename)
        
        if not path:
            return data
        
        return self._resolve_path(data, path)
    
    def _resolve_path(self, data: Any, path: str) -> Any:
        """
        Resolve a path expression against the data.
        Supports dot notation and array indexing.
        """
        if not path:
            return data
        
        # Parse the path into components
        components = self._parse_path(path)
        
        # Traverse the data
        current = data
        for component in components:
            # Handle array indexing
            if isinstance(component, int):
                if isinstance(current, list) and 0 <= component < len(current):
                    current = current[component]
                else:
                    return None
            # Handle dictionary keys
            elif isinstance(component, str):
                if isinstance(current, dict) and component in current:
                    current = current[component]
                else:
                    return None
        
        return current
    
    def _parse_path(self, path: str) -> List[Union[str, int]]:
        """
        Parse a path expression into components.
        Returns a list of string keys and integer indices.
        """
        if not path:
            return []
        
        components = []
        
        # Split by dots, but handle array indices
        parts = re.findall(r'([^\.\[\]]+)|\[(\d+)\]', path)
        
        for key, index in parts:
            if key:
                components.append(key)
            if index:
                components.append(int(index))
        
        return components
    
    def filter(self, filename: str, filter_expr: Dict[str, Any]) -> List[Any]:
        """
        Filter JSON data based on a filter expression.
        Returns items that match all filter criteria.
        """
        data = self.load_file(filename)
        
        if not isinstance(data, list):
            # If root is not a list, can't filter
            return []
        
        results = []
        
        for item in data:
            if self._matches_filter(item, filter_expr):
                results.append(item)
        
        return results
    
    def _matches_filter(self, item: Any, filter_expr: Dict[str, Any]) -> bool:
        """
        Check if an item matches the filter expression.
        """
        if not isinstance(item, dict):
            return False
        
        for key, value in filter_expr.items():
            # Handle nested paths with dot notation
            if '.' in key:
                item_value = self._resolve_path(item, key)
            else:
                item_value = item.get(key)
            
            # Check equality
            if item_value != value:
                return False
        
        return True
    
    def save(self, filename: str, data: Any) -> bool:
        """
        Save data to a JSON file in the data directory.
        Returns True if successful, False otherwise.
        """
        # Ensure .json extension
        if not filename.endswith('.json'):
            filename += '.json'
        
        file_path = os.path.join(self.data_dir, filename)
        
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
                # Update cache
                self.cache[filename] = data
                return True
        except Exception as e:
            print(f"Error saving to {file_path}: {e}")
            return False

if __name__ == "__main__":
    # Test the JSON query tool
    query_tool = JSONQueryTool()
    
    # Example data for testing
    test_data = {
        "requirements": [
            {
                "id": "REQ-001",
                "type": "SR",
                "description": "System must have 16 digital I/O points",
                "category": "io",
                "priority": "high"
            },
            {
                "id": "REQ-002",
                "type": "SR",
                "description": "System must support Modbus RTU",
                "category": "communication",
                "priority": "medium"
            }
        ],
        "metadata": {
            "version": "1.0",
            "last_updated": "2025-08-11"
        }
    }
    
    # Save test data
    query_tool.save("test_requirements", test_data)
    
    # Test queries
    print("Full data:", query_tool.query("test_requirements", ""))
    print("First requirement:", query_tool.query("test_requirements", "requirements[0]"))
    print("Metadata version:", query_tool.query("test_requirements", "metadata.version"))
    
    # Test filtering
    filter_result = query_tool.filter("test_requirements.requirements", {"category": "io"})
    print("Filtered I/O requirements:", filter_result)
