import json
import os
from typing import Dict, List, Any
from pathlib import Path

class DataLoader:
    """Handles loading and accessing JSON data files for the requirements system."""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            # Phase 2: Look in both src/data and root data directories
            src_data_dir = Path(__file__).parent
            root_data_dir = Path(__file__).parent.parent.parent / "data"
            data_dir = root_data_dir if root_data_dir.exists() else src_data_dir
        self.data_dir = Path(data_dir)
        self._data_cache = {}
        
        # Phase 2: Load constraint and form data immediately
        self._load_phase2_data()
    
    def load_json(self, filename: str) -> Dict[str, Any]:
        """Load JSON data from file with caching."""
        if filename in self._data_cache:
            return self._data_cache[filename]
        
        file_path = self.data_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._data_cache[filename] = data
            return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {filename}: {e}")
    
    def get_requirements(self) -> List[Dict[str, Any]]:
        """Load requirements data."""
        return self.load_json('requirements.json')
    
    def get_projects(self) -> List[Dict[str, Any]]:
        """Load projects data."""
        return self.load_json('projects.json')
    
    def get_stakeholders(self) -> List[Dict[str, Any]]:
        """Load stakeholders data."""
        return self.load_json('stakeholders.json')
    
    def get_dependencies(self) -> List[Dict[str, Any]]:
        """Load dependencies data."""
        return self.load_json('dependencies.json')
    
    def get_change_requests(self) -> List[Dict[str, Any]]:
        """Load change requests data."""
        return self.load_json('change_requests.json')
    
    def reload_data(self):
        """Clear cache and reload all data."""
        self._data_cache.clear()
    
    def list_available_files(self) -> List[str]:
        """List all JSON files in the data directory."""
        return [f.name for f in self.data_dir.glob('*.json')]
    
    def _load_phase2_data(self):
        """Load Phase 2 constraint and form data."""
        try:
            # Load constraints.json
            self.constraints = self.load_json('constraints.json').get('constraints_pool', {})
        except (FileNotFoundError, KeyError, ValueError):
            self.constraints = {}
        
        try:
            # Load form_fields.json
            self.form_fields = self.load_json('form_fields.json').get('field_definitions', {})
        except (FileNotFoundError, KeyError, ValueError):
            self.form_fields = {}
        
        try:
            # Load useCase.json
            self.use_cases = self.load_json('useCase.json').get('use_cases', {})
        except (FileNotFoundError, KeyError, ValueError):
            print("Warning: Could not load useCase.json, using empty data")
            self.use_cases = {}
        
        # Optional product data - will be provided later
        try:
            uno_data = self.load_json('uno_products.json')
            self.uno_products = uno_data.get('controllers', {})
        except (FileNotFoundError, ValueError):
            self.uno_products = {}
        
        try:
            adam_data = self.load_json('adam_products.json')
            self.adam_products = adam_data.get('adam_modules', {})
        except (FileNotFoundError, ValueError):
            self.adam_products = {}

# Global instance for easy access
data_loader = DataLoader()