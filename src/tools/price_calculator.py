"""
Price Calculator - Deterministic price calculations using product JSON data
No LLM for calculations - only direct computation
"""

from typing import Dict, List, Optional
from data.data_loader import data_loader

class PriceCalculator:
    """Calculate prices deterministically from product data."""
    
    def __init__(self):
        self.uno_products = data_loader.uno_products if hasattr(data_loader, 'uno_products') else {}
        self.adam_products = data_loader.adam_products if hasattr(data_loader, 'adam_products') else {}
        
        # Load pricing data from separate file
        try:
            self.pricing_data = data_loader.load_json('price_leadtime.json').get('components', {})
        except (FileNotFoundError, ValueError):
            self.pricing_data = {}
        
        # Fallback prices if JSON not available
        self.fallback_prices = {
            "UNO-137": 800,
            "UNO-148": 1200,
            "ADAM-4017": 250,
            "ADAM-4050": 200
        }
    
    def calculate_total_cost(self, controller_id: str, modules: List[Dict]) -> Dict:
        """
        Calculate total system cost.
        Returns detailed breakdown and total.
        """
        cost_breakdown = []
        total_cost = 0
        
        # Controller cost
        controller_price = self._get_product_price(controller_id, "uno")
        total_cost += controller_price
        cost_breakdown.append({
            "item": controller_id,
            "category": "controller",
            "quantity": 1,
            "unit_price": controller_price,
            "subtotal": controller_price
        })
        
        # Module costs
        for module in modules:
            module_type = module.get("type", "")
            quantity = module.get("quantity", 1)
            unit_price = self._get_product_price(module_type, "adam")
            subtotal = unit_price * quantity
            
            total_cost += subtotal
            cost_breakdown.append({
                "item": module_type,
                "category": "module",
                "quantity": quantity,
                "unit_price": unit_price,
                "subtotal": subtotal
            })
        
        # Apply pricing rules (future: discounts, bundles)
        total_modules = sum(module.get("quantity", 1) for module in modules)
        final_price = self._apply_pricing_rules(total_cost, total_modules)
        
        return {
            "base_cost": total_cost,
            "final_price": final_price,
            "currency": "USD",
            "breakdown": cost_breakdown,
            "discount_applied": final_price < total_cost,
            "confidence": 1.0  # Deterministic calculation
        }
    
    def _get_product_price(self, product_id: str, product_type: str) -> float:
        """Get product price from JSON or fallback."""
        # First try to get price from integrated product data
        if product_type == "uno" and product_id in self.uno_products:
            price = self.uno_products[product_id].get("price_usd", 0)
            if price > 0:
                return price
        elif product_type == "adam" and product_id in self.adam_products:
            price = self.adam_products[product_id].get("price_usd", 0)
            if price > 0:
                return price
        
        # Try pricing data file
        if product_id in self.pricing_data:
            price = self.pricing_data[product_id].get("price_usd", 0)
            if price > 0:
                return price
        
        # Use fallback price
        return self.fallback_prices.get(product_id, 500)
    
    def _apply_pricing_rules(self, base_cost: float, module_count: int) -> float:
        """Apply business rules like bulk discounts."""
        final_price = base_cost
        
        # Example: 5% discount for 3+ modules
        if module_count >= 3:
            final_price *= 0.95
        
        # Example: 10% discount for systems over $3000
        if base_cost > 3000:
            final_price *= 0.9
        
        return round(final_price, 2)
    
    def estimate_from_requirements(self, io_requirements: Dict) -> Dict:
        """Quick estimation based on I/O requirements."""
        # Select cheapest suitable controller
        if io_requirements.get("total_io", 0) <= 16:
            controller = "UNO-137"
        else:
            controller = "UNO-148"
        
        # Estimate modules needed
        modules = []
        if io_requirements.get("analog_input", 0) > 0:
            modules.append({
                "type": "ADAM-4017",
                "quantity": (io_requirements["analog_input"] + 7) // 8
            })
        
        return self.calculate_total_cost(controller, modules)