"""
Confidence Aggregator - Aggregates confidence scores from multiple validators
"""

from typing import Dict, List, Any
import statistics

class ConfidenceAggregator:
    """
    Aggregates confidence scores from multiple validation sources.
    Uses weighted averages and consensus algorithms.
    """
    
    def __init__(self):
        self.default_weights = {
            "technical": 0.4,
            "commercial": 0.3,
            "csp": 0.25,
            "user_feedback": 0.05
        }
    
    def aggregate_confidence(self, validation_results: Dict, weights: Dict = None) -> Dict:
        """
        Aggregate confidence scores from validation results.
        """
        if weights is None:
            weights = self.default_weights
        
        scores = []
        weighted_scores = []
        component_scores = {}
        
        # Extract confidence scores from each component
        for component, weight in weights.items():
            if component in validation_results:
                confidence = validation_results[component].get("confidence", 0.0)
                scores.append(confidence)
                weighted_scores.append(confidence * weight)
                component_scores[component] = confidence
        
        if not scores:
            return {
                "aggregate_confidence": 0.0,
                "method": "no_data",
                "component_scores": {},
                "consensus_level": "none"
            }
        
        # Calculate different aggregation methods
        weighted_average = sum(weighted_scores) / sum(weights.values()) if weights else 0.0
        simple_average = statistics.mean(scores)
        median_score = statistics.median(scores)
        min_score = min(scores)
        max_score = max(scores)
        
        # Calculate consensus level
        consensus_level = self._calculate_consensus(scores)
        
        # Determine primary method based on consensus
        if consensus_level == "high":
            primary_score = weighted_average
            method = "weighted_average"
        elif consensus_level == "medium":
            primary_score = median_score
            method = "median"
        else:
            primary_score = min_score
            method = "conservative_min"
        
        return {
            "aggregate_confidence": round(primary_score, 3),
            "method": method,
            "component_scores": component_scores,
            "consensus_level": consensus_level,
            "statistics": {
                "weighted_average": round(weighted_average, 3),
                "simple_average": round(simple_average, 3),
                "median": round(median_score, 3),
                "min": round(min_score, 3),
                "max": round(max_score, 3),
                "std_dev": round(statistics.stdev(scores) if len(scores) > 1 else 0.0, 3)
            }
        }
    
    def _calculate_consensus(self, scores: List[float]) -> str:
        """Calculate consensus level among confidence scores."""
        if len(scores) < 2:
            return "single_source"
        
        std_dev = statistics.stdev(scores)
        mean_score = statistics.mean(scores)
        
        # Calculate coefficient of variation
        cv = std_dev / mean_score if mean_score > 0 else float('inf')
        
        if cv < 0.1:  # Very low variation
            return "high"
        elif cv < 0.25:  # Moderate variation
            return "medium"
        else:  # High variation
            return "low"
    
    def calculate_temporal_confidence(self, historical_results: List[Dict]) -> Dict:
        """
        Calculate confidence trend over time.
        """
        if not historical_results:
            return {"trend": "no_data", "current_confidence": 0.0}
        
        # Extract confidence scores over time
        confidence_series = []
        for result in historical_results:
            if "aggregate_confidence" in result:
                confidence_series.append(result["aggregate_confidence"])
        
        if len(confidence_series) < 2:
            return {
                "trend": "insufficient_data",
                "current_confidence": confidence_series[0] if confidence_series else 0.0
            }
        
        # Calculate trend
        recent_scores = confidence_series[-3:]  # Last 3 measurements
        earlier_scores = confidence_series[:-3] if len(confidence_series) > 3 else confidence_series[:-1]
        
        recent_avg = statistics.mean(recent_scores)
        earlier_avg = statistics.mean(earlier_scores) if earlier_scores else recent_avg
        
        trend_direction = "stable"
        if recent_avg > earlier_avg + 0.05:
            trend_direction = "improving"
        elif recent_avg < earlier_avg - 0.05:
            trend_direction = "declining"
        
        return {
            "trend": trend_direction,
            "current_confidence": confidence_series[-1],
            "trend_magnitude": abs(recent_avg - earlier_avg),
            "series_length": len(confidence_series)
        }