# reqMAS - Requirements Multi-Agent System

## Overview

reqMAS is a reflective blackboard architecture for requirements engineering, utilizing multiple expert agents operating in parallel with I/O priority coordination. The system is designed to process, validate, and consolidate requirements for industrial control systems.

## Phase 1 Architecture

Phase 1 implements the core foundation with:

- Reflective blackboard with knowledge spaces and agent spaces
- Event-driven message bus with circuit breaker pattern
- Vector clock CRDT for conflict detection
- Three expert agents (I/O, System, Communication)
- Orchestrator for agent coordination
- FastAPI main entry point with WebSocket and REST endpoints

## Directory Structure

```
reqmas/
├── src/
│   ├── core/
│   │   ├── blackboard.py       # Reflective blackboard implementation
│   │   ├── message_bus.py      # Event-driven message bus
│   │   ├── state_management.py # State management with LangGraph
│   │   └── vector_clock.py     # Vector clock CRDT
│   ├── agents/
│   │   ├── base_agent.py       # Abstract base agent class
│   │   ├── io_expert.py        # I/O expert with primary authority
│   │   ├── system_expert.py    # System/performance expert
│   │   ├── communication_expert.py # Communication protocols expert
│   │   └── orchestrator.py     # Agent coordinator
│   ├── tools/
│   │   ├── requirement_parser.py # NL to constraint mapping
│   │   ├── json_query.py       # JSON data access utility
│   │   └── compatibility_checker.py # Constraint compatibility validation
│   ├── config/
│   │   └── settings.py         # Central configuration
│   └── main.py                 # FastAPI application entry point
├── data/                       # Data storage directory
├── tests/
│   └── test_integration.py     # Integration tests
├── .env.example                # Example environment configuration
└── README.md                   # This file
```

## Key Components

### Reflective Blackboard

The blackboard provides shared memory spaces for agents to read and write, with:
- Knowledge spaces for different stages of processing
- Agent spaces for agent-specific data
- Vector clocks for conflict detection
- Permission checking and conflict resolution
- Event-driven updates

### Message Bus

The asynchronous event-driven message bus enables:
- Agent communication with publish/subscribe pattern
- Circuit breaker pattern for resilience
- Message prioritization
- Asynchronous processing

### Agents

- **I/O Expert**: Primary authority with veto power, focuses on I/O requirements
- **System Expert**: Secondary authority for system/performance requirements
- **Communication Expert**: Secondary authority for communication protocols
- **Orchestrator**: Routes inputs, selects agents, and merges results

### Tools

- **Requirement Parser**: Maps natural language to structured constraints
- **JSON Query Tool**: Provides structured access to JSON data
- **Compatibility Checker**: Validates constraint compatibility

## Setup and Usage

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the environment: 
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and add your API keys
6. Run the application: `python -m src.main`

## API Endpoints

- `GET /health`: Health check endpoint
- `POST /process`: Process requirements via REST API
- `WebSocket /ws`: Real-time communication

## Testing

Run integration tests:
```
pytest tests/test_integration.py -v
```

## License

Copyright © 2025
