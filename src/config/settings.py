"""
Configuration Settings for reqMAS Phase 1
Central configuration for the system
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys and Model Configuration
API_KEYS = {
    "openai": os.getenv("OPENAI_API_KEY", ""),
    "anthropic": os.getenv("ANTHROPIC_API_KEY", ""),
    "azure_openai": os.getenv("AZURE_OPENAI_API_KEY", "")
}

# Model Assignments
MODEL_CONFIG = {
    "io_expert": os.getenv("IO_EXPERT_MODEL", "claude-3-opus-20240229"),
    "system_expert": os.getenv("SYSTEM_EXPERT_MODEL", "gpt-4"),
    "communication_expert": os.getenv("COMMUNICATION_EXPERT_MODEL", "gpt-4o-mini"),
    "orchestrator": os.getenv("ORCHESTRATOR_MODEL", "gpt-4-turbo")
}

# Agent Priorities (higher number = higher priority)
AGENT_PRIORITIES = {
    "io_expert": 1000,
    "system_expert": 100,
    "communication_expert": 100,
    "orchestrator": 10
}

# Blackboard Configuration
BLACKBOARD_CONFIG = {
    "knowledge_spaces": [
        "raw",
        "processed",
        "validated",
        "consolidated"
    ],
    "conflict_threshold": 0.7,  # Similarity threshold for conflict detection
    "max_history_length": 100,  # Maximum message history length
    "vector_clock_enabled": True  # Enable vector clock CRDT
}

# Message Bus Configuration
MESSAGE_BUS_CONFIG = {
    "max_retries": 3,  # Maximum retries for failed message delivery
    "retry_delay": 1.0,  # Delay between retries in seconds
    "circuit_breaker_threshold": 5,  # Failures before circuit breaker trips
    "circuit_breaker_reset_time": 30.0  # Time to reset circuit breaker in seconds
}

# Agent Configuration
AGENT_CONFIG = {
    "timeout": 30.0,  # Default timeout for agent processing in seconds
    "confidence_threshold": 0.7,  # Minimum confidence for agent results
    "max_parallel_agents": 3,  # Maximum number of agents to run in parallel
    "fallback_enabled": True  # Enable fallback processing on failure
}

# Server Configuration
SERVER_CONFIG = {
    "host": os.getenv("HOST", "0.0.0.0"),
    "port": int(os.getenv("PORT", "8000")),
    "debug": os.getenv("DEBUG", "False").lower() == "true",
    "workers": int(os.getenv("WORKERS", "1")),
    "log_level": os.getenv("LOG_LEVEL", "info")
}

# Path Configuration
PATH_CONFIG = {
    "data_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data')),
    "log_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'logs'))
}

# Ensure directories exist
for directory in PATH_CONFIG.values():
    os.makedirs(directory, exist_ok=True)

def get_config() -> Dict[str, Any]:
    """Get the complete configuration as a dictionary."""
    return {
        "api_keys": API_KEYS,
        "model_config": MODEL_CONFIG,
        "agent_priorities": AGENT_PRIORITIES,
        "blackboard_config": BLACKBOARD_CONFIG,
        "message_bus_config": MESSAGE_BUS_CONFIG,
        "agent_config": AGENT_CONFIG,
        "server_config": SERVER_CONFIG,
        "path_config": PATH_CONFIG
    }

def get_model_for_agent(agent_id: str) -> str:
    """Get the model assigned to a specific agent."""
    return MODEL_CONFIG.get(agent_id, MODEL_CONFIG.get("orchestrator"))

def get_agent_priority(agent_id: str) -> int:
    """Get the priority for a specific agent."""
    return AGENT_PRIORITIES.get(agent_id, 1)  # Default priority is lowest

if __name__ == "__main__":
    # Print configuration for debugging
    import json
    
    # Hide API keys when printing
    config = get_config()
    config["api_keys"] = {k: "***" for k in config["api_keys"]}
    
    print(json.dumps(config, indent=2))
