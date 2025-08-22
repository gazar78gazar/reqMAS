"""
Main Entry Point for reqMAS Phase 1
Initializes core components and provides API endpoints
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Force load from project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Verify it loaded
print(f"OpenAI Key Loaded: {bool(os.getenv('OPENAI_API_KEY'))}")

import asyncio
from fastapi import FastAPI, WebSocket, HTTPException
from core.blackboard import ReflectiveBlackboard
from core.message_bus import EventDrivenMessageBus
from agents.orchestrator import OrchestratorAgent
from agents.io_expert import IOExpertAgent
from agents.system_expert import SystemExpertAgent
from agents.communication_expert import CommunicationExpertAgent
# Phase 2 imports
from validation.validation_pipeline import ValidationPipeline
from agents.decision_coordinator import DecisionCoordinatorAgent
from validation.confidence_aggregator import ConfidenceAggregator
import json
import uvicorn
from datetime import datetime

# Initialize FastAPI
app = FastAPI(title="reqMAS Phase 1")

# Initialize core components
blackboard = ReflectiveBlackboard()
message_bus = EventDrivenMessageBus()

# Initialize agents
orchestrator = OrchestratorAgent(blackboard, message_bus)
io_expert = IOExpertAgent(blackboard, message_bus)
system_expert = SystemExpertAgent(blackboard, message_bus)  # Phase 1
comm_expert = CommunicationExpertAgent(blackboard, message_bus)  # Phase 1

# Phase 2 components
validation_pipeline = ValidationPipeline(blackboard=blackboard, message_bus=message_bus)
decision_coordinator = DecisionCoordinatorAgent(blackboard=blackboard, message_bus=message_bus)
confidence_aggregator = ConfidenceAggregator()

print("\n=== PHASE 2 COMPONENT STATUS ===")
print(f"1. ValidationPipeline: {'✓ Initialized' if validation_pipeline else '✗ Not initialized'}")
print(f"2. DecisionCoordinator: {'✓ Initialized' if decision_coordinator else '✗ Not initialized'}")
print(f"3. ConfidenceAggregator: {'✓ Initialized' if confidence_aggregator else '✗ Not initialized'}")

# Check if they have required methods
if validation_pipeline:
    print(f"   - Has validate(): {hasattr(validation_pipeline, 'validate')}")
    print(f"   - Has detect_conflicts(): {hasattr(validation_pipeline, 'detect_conflicts')}")
    
if decision_coordinator:
    print(f"   - Has process(): {hasattr(decision_coordinator, 'process')}")
    print(f"   - Has ABQ generator: {hasattr(decision_coordinator, 'abq_generator')}")
    
print("=== END COMPONENT STATUS ===\n")

# Agent registry
agent_registry = {
    "orchestrator": orchestrator,
    "io_expert": io_expert,
    "system_expert": system_expert,
    "communication_expert": comm_expert
}

@app.on_event("startup")
async def startup():
    """Initialize message bus on startup."""
    await message_bus.start()
    print("reqMAS Phase 1 initialized")

@app.on_event("shutdown")
async def shutdown():
    """Clean shutdown."""
    await message_bus.stop()
    print("reqMAS Phase 1 shutdown")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication."""
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Process through orchestrator
            result = await process_with_orchestrator({
                "user_input": message.get("input", ""),
                "source": "websocket",
                "session_id": message.get("session_id") or "default"
            })
            
            # Send response
            await websocket.send_json({
                "type": "response",
                "data": result
            })
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

@app.post("/process")
async def process_requirement(data: dict):
    """Process requirement through MAS."""
    if not data or "input" not in data:
        raise HTTPException(status_code=400, detail="Invalid request data")
    
    result = await process_with_orchestrator({
        "user_input": data.get("input", ""),
        "source": "api",
        "session_id": data.get("session_id") or "default"
    })
    
    print("\n" + "="*30)
    print("API ENDPOINT DIAGNOSTIC")
    print("="*30)
    print(f"Returning to Postman:")
    print(f"  - Status: {result.get('status', 'MISSING')}")
    print(f"  - Has conversational_response: {'conversational_response' in result}")
    print(f"  - Response preview: {result.get('conversational_response', 'MISSING')[:100] if 'conversational_response' in result else 'MISSING'}")
    print("="*30 + "\n")
    
    return {
        "status": "success",
        "result": result,
        "blackboard_state": blackboard.get_state_snapshot()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agents": list(agent_registry.keys()),
        "blackboard": "active",
        "message_bus": "active"
    }

@app.get("/session/{session_id}")
async def get_session_state(session_id: str):
    """Get session state for debugging/monitoring."""
    session_key = f"session_{session_id}"
    session_state = await blackboard.read("orchestrator", "consolidated", session_key)
    
    if not session_state:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    return {
        "session_id": session_id,
        "state": session_state,
        "summary": generate_conversation_summary(
            session_state.get("messages", []),
            session_state.get("accumulated_specs", [])
        )
    }

@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Clear session state."""
    session_key = f"session_{session_id}"
    # For now, we'll just try to read it to see if it exists
    existing = await blackboard.read("orchestrator", "consolidated", session_key)
    
    if not existing:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    # Clear by writing empty state
    await blackboard.write("orchestrator", "consolidated", session_key, None)
    
    return {
        "status": "success",
        "message": f"Session {session_id} cleared",
        "previous_turns": existing.get("conversation_turn", 0)
    }

async def process_with_orchestrator(input_data: dict):
    """Process input through orchestrator with session persistence and requirement accumulation."""
    import time
    import json
    
    print("\n" + "="*50)
    print("DIAGNOSTIC TRACE START")
    print("="*50)
    
    checkpoint_times = {}
    checkpoint_times['start'] = time.time()
    
    session_id = input_data.get("session_id") or "default"
    user_input = input_data.get("user_input", "")
    
    print(f"1. Input received: {user_input[:50]}...")
    print(f"   Session ID: {session_id}")
    
    # RETRIEVE previous session state from blackboard
    session_key = f"session_{session_id}"
    previous_state = await blackboard.read("orchestrator", "consolidated", session_key)
    
    # Initialize if new session
    if not previous_state:
        previous_state = {
            "conversation_turn": 0,
            "messages": [],
            "accumulated_specs": [],
            "requirements": {},
            "context": {}
        }
    
    # Increment conversation turn
    current_turn = previous_state["conversation_turn"] + 1
    
    # Prepare context with conversation history for agents
    context = {
        "session_id": session_id,
        "conversation_turn": current_turn,
        "previous_messages": previous_state["messages"],
        "accumulated_specs": previous_state["accumulated_specs"],
        "previous_requirements": previous_state["requirements"]
    }
    
    # First, let orchestrator analyze and route with context
    routing_result = await orchestrator.process(input_data, context)
    
    # Extract agents to activate
    agents_to_activate = routing_result.get("activated_agents", [])
    
    checkpoint_times['before_agents'] = time.time()
    print(f"2. Starting agent execution at {checkpoint_times['before_agents'] - checkpoint_times['start']:.2f}s")
    print(f"   Agents to activate: {agents_to_activate}")
    
    # Process with selected agents
    agent_results = {}
    for agent_id in agents_to_activate:
        if agent_id in agent_registry:
            agent = agent_registry[agent_id]
            try:
                # Pass full context to each agent
                agent_result = await agent.execute(input_data)
                agent_results[agent_id] = agent_result
            except Exception as e:
                agent_results[agent_id] = {
                    "status": "error",
                    "error": str(e),
                    "confidence": 0.0
                }
    
    checkpoint_times['after_agents'] = time.time()
    print(f"3. Agents completed in {checkpoint_times['after_agents'] - checkpoint_times['before_agents']:.2f}s")
    print(f"   Agent results keys: {list(agent_results.keys())}")
    
    # Merge results
    merged = blackboard.merge_parallel_outputs(agent_results) if agent_results else {}
    
    # Get current turn's specifications FIRST
    current_specs = merged.get("primary", {}).get("specifications", [])
    
    # ACCUMULATE specifications (not replace!)
    all_specs = list(previous_state["accumulated_specs"])
    if current_specs:
        all_specs.extend(current_specs)
    
    # UPDATE conversation history
    previous_state["messages"].append({
        "turn": current_turn,
        "user": user_input,
        "system": merged,
        "timestamp": datetime.now().isoformat(),
        "agents_activated": agents_to_activate
    })
    
    # SAVE complete state back to blackboard
    updated_state = {
        "conversation_turn": current_turn,
        "messages": previous_state["messages"],
        "accumulated_specs": all_specs,
        "requirements": merged.get("primary", {}),
        "context": merged,
        "session_id": session_id,
        "last_updated": datetime.now().isoformat()
    }
    
    await blackboard.write("orchestrator", "consolidated", session_key, updated_state)
    
    checkpoint_times['before_response'] = time.time()
    print(f"4. Generating conversational response...")
    
    # Use Phase 2 intelligent response generation
    # Run Phase 2 if we have accumulated specs OR new specs this turn
    if len(all_specs) > 0 or len(current_specs) > 0:
        # Run validation
        validation_result = await validation_pipeline.validate(all_specs, context)
        
        # Detect conflicts
        conflicts = []
        if hasattr(validation_pipeline, 'detect_conflicts'):
            conflicts = validation_pipeline.detect_conflicts(validation_result)
        
        # Generate intelligent response
        decision_result = await decision_coordinator.process({
            "action_type": "format_response",
            "validation_results": validation_result,
            "conflicts": conflicts,
            "specs_count": len(all_specs),
            "turn": current_turn
        }, context)
        
        conversational_response = decision_result.get("message", "")
        
        # If conflicts exist, add A/B question
        if conflicts:
            abq_result = await decision_coordinator.process({
                "action_type": "generate_abq",
                "conflict": conflicts[0]
            }, context)
            conversational_response += f"\n\n{abq_result.get('question', '')}"
    else:
        # Fallback to basic response
        conversational_response = generate_conversational_response(
            user_input, all_specs, current_turn, previous_state
        )
    
    checkpoint_times['after_response'] = time.time()
    print(f"   Response generated: '{conversational_response[:100]}...'")
    print(f"   Generation took: {checkpoint_times['after_response'] - checkpoint_times['before_response']:.2f}s")
    
    aggregate_confidence = calculate_aggregate_confidence(all_specs)
    
    response = {
        "routing": routing_result,
        "merged_results": merged,
        "conversational_response": conversational_response,
        "aggregate_confidence": aggregate_confidence,
        "session_context": {
            "turn": current_turn,
            "total_specs": len(all_specs),
            "session_id": session_id,
            "accumulated_specifications": all_specs
        },
        "conversation_summary": generate_conversation_summary(previous_state["messages"], all_specs)
    }
    
    print(f"5. Final response structure:")
    print(f"   - Keys in response: {list(response.keys())}")
    print(f"   - conversational_response present: {'conversational_response' in response}")
    print(f"   - conversational_response value: '{response.get('conversational_response', 'MISSING')}'")
    
    checkpoint_times['end'] = time.time()
    total_time = checkpoint_times['end'] - checkpoint_times['start']
    print(f"6. Total processing time: {total_time:.2f}s")
    
    if total_time > 3.0:
        print("WARNING: Processing exceeded 3 second timeout!")
        print(f"   Exceeded by: {total_time - 3.0:.2f}s")
    
    print("="*50)
    print("DIAGNOSTIC TRACE END")
    print("="*50 + "\n")
    
    return response


def generate_conversational_response(user_input: str, all_specs: list, turn: int, previous_state: dict) -> str:
    """Generate context-aware response"""
    
    print(f"   [ConvResp] Generating response for turn {turn}")
    print(f"   [ConvResp] Specs count: {len(all_specs)}")
    print(f"   [ConvResp] User input preview: {user_input[:50]}...")
    
    # Check if asking about accumulated requirements
    if any(word in user_input.lower() for word in ["total", "what are my", "summary", "all"]):
        if all_specs:
            spec_summary = []
            for spec in all_specs:
                spec_summary.append(f"- {spec.get('constraint')}: {spec.get('value')}")
            response = f"Your total requirements (Turn {turn}):\n" + "\n".join(spec_summary)
            print(f"   [ConvResp] Returning: '{response[:100]}...'")
            return response
        else:
            response = "No requirements captured yet. Please describe what you need."
            print(f"   [ConvResp] Returning: '{response[:100]}...'")
            return response
    
    # Check if adding to previous
    if "also" in user_input.lower() or "addition" in user_input.lower():
        response = f"I've added that to your requirements. You now have {len(all_specs)} specifications."
        print(f"   [ConvResp] Returning: '{response[:100]}...'")
        return response
    
    # Default response showing accumulation
    if all_specs:
        response = f"Captured {len(all_specs)} requirements so far. What else do you need?"
        print(f"   [ConvResp] Returning: '{response[:100]}...'")
        return response
    else:
        response = "I'm ready to help with your IoT requirements. What do you need?"
        print(f"   [ConvResp] Returning: '{response[:100]}...'")
        return response


def calculate_aggregate_confidence(specs: list) -> float:
    """Calculate overall confidence from accumulated specs"""
    if not specs:
        return 0.0
    # More specs = higher confidence
    return min(0.95, len(specs) * 0.15)


def generate_conversation_summary(messages: list, accumulated_specs: list) -> dict:
    """Generate a summary of the conversation for user feedback."""
    if not messages:
        return {
            "summary": "New session started",
            "total_turns": 0,
            "total_specs": len(accumulated_specs)
        }
    
    last_message = messages[-1] if messages else {}
    
    return {
        "summary": f"Session with {len(messages)} turns, {len(accumulated_specs)} total specifications",
        "total_turns": len(messages),
        "total_specs": len(accumulated_specs),
        "last_interaction": last_message.get("timestamp", ""),
        "recent_specs": accumulated_specs[-3:] if accumulated_specs else []  # Show last 3 specs
    }


# Phase 2 API Endpoints

@app.post("/api/v1/validate")
async def validate_requirements(data: dict):
    """
    Validate accumulated requirements.
    """
    session_id = data.get("session_id") or "default"
    
    # Get accumulated specifications from blackboard
    session_key = f"session_{session_id}"
    session_state = await blackboard.read("orchestrator", "consolidated", session_key)
    
    if not session_state:
        return {
            "status": "error",
            "message": "No session found"
        }
    
    specifications = session_state.get("accumulated_specs", [])
    context = {
        "session_id": session_id,
        "budget": data.get("budget"),
        "user_profile": data.get("user_profile", {})
    }
    
    # Run validation pipeline
    validation_result = await validation_pipeline.validate(specifications, context)
    
    return {
        "status": "success",
        "validation": validation_result,
        "specifications_validated": len(specifications)
    }

@app.post("/api/v1/generate_abq")
async def generate_ab_question(data: dict):
    """
    Generate A/B clarification question.
    """
    result = await decision_coordinator.process(
        {
            "action_type": "generate_abq",
            "conflict": data.get("conflict", {})
        },
        {
            "session_id": data.get("session_id") or "default",
            "user_profile": data.get("user_profile", {})
        }
    )
    
    return result

@app.post("/api/v1/autofill")
async def check_autofill(data: dict):
    """
    Check if autofill should trigger.
    """
    session_id = data.get("session_id") or "default"
    
    # Get validation results
    validation = data.get("validation_results", {})
    confidence = validation.get("final_result", {}).get("confidence", 0.0)
    
    result = await decision_coordinator.process(
        {
            "action_type": "check_autofill",
            "validated_config": validation.get("final_result", {}),
            "confidence": confidence
        },
        {
            "session_id": session_id,
            "user_profile": data.get("user_profile", {})
        }
    )
    
    return result

@app.post("/api/v1/process")
async def enhanced_process(data: dict):
    """
    Enhanced process endpoint with validation.
    """
    # First run existing process
    process_result = await process_requirement(data)
    
    # If confidence is high enough, run validation
    if process_result.get("aggregate_confidence", 0) >= 0.7:
        validation_result = await validate_requirements({
            "session_id": data.get("session_id") or "default",
            "budget": data.get("budget")
        })
        
        process_result["validation"] = validation_result.get("validation")
        
        # Check for autofill
        if validation_result.get("validation", {}).get("final_result", {}).get("valid"):
            autofill_result = await check_autofill({
                "session_id": data.get("session_id") or "default",
                "validation_results": validation_result.get("validation"),
                "user_profile": data.get("user_profile", {})
            })
            
            process_result["autofill"] = autofill_result
    
    return process_result

@app.get("/api/v1/pipeline/status")
async def get_pipeline_status():
    """
    Get validation pipeline status.
    """
    return {
        "status": "success",
        "pipeline": validation_pipeline.get_pipeline_status(),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/pipeline/reset")
async def reset_pipeline():
    """
    Reset validation pipeline circuit breakers.
    """
    validation_pipeline.reset_circuit_breakers()
    validation_pipeline.clear_caches()
    
    return {
        "status": "success",
        "message": "Pipeline reset completed"
    }


if __name__ == "__main__":
    print("Starting reqMAS Phase 1...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
