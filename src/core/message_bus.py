"""
Event-Driven Message Bus for reqMAS Phase 1
Asynchronous message bus for agent communication
"""

import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import uuid
from collections import defaultdict
from dataclasses import dataclass
import json

@dataclass
class Message:
    """Typed message for inter-agent communication"""
    id: str
    sender: str
    message_type: str
    payload: Any
    timestamp: datetime
    correlation_id: Optional[str] = None
    vector_clock: Optional[Dict[str, int]] = None

class EventDrivenMessageBus:
    """
    Asynchronous message bus for agent communication.
    Implements circuit breaker pattern for resilience.
    """
    
    def __init__(self):
        self.subscribers = defaultdict(list)
        self.message_queue = asyncio.Queue()
        self.circuit_breakers = {}
        self.message_history = []
        self.running = False
        
    async def start(self):
        """Start the message bus processor."""
        self.running = True
        asyncio.create_task(self._process_messages())
    
    async def stop(self):
        """Stop the message bus."""
        self.running = False
    
    async def publish(self, sender: str, message_type: str, payload: Any, 
                     correlation_id: Optional[str] = None) -> str:
        """
        Publish a message to the bus.
        """
        message_id = str(uuid.uuid4())
        
        message = Message(
            id=message_id,
            sender=sender,
            message_type=message_type,
            payload=payload,
            timestamp=datetime.now(),
            correlation_id=correlation_id or message_id,
            vector_clock={}  # Will be set by blackboard
        )
        
        # Check circuit breaker
        if self._is_circuit_open(sender):
            raise Exception(f"Circuit breaker open for {sender}")
        
        await self.message_queue.put(message)
        return message_id
    
    def subscribe(self, message_type: str, callback: Callable):
        """Subscribe to a message type."""
        self.subscribers[message_type].append(callback)
    
    async def _process_messages(self):
        """Process messages from the queue."""
        while self.running:
            try:
                message = await asyncio.wait_for(
                    self.message_queue.get(), 
                    timeout=1.0
                )
                
                # Store in history
                self.message_history.append(message)
                
                # Notify subscribers
                for callback in self.subscribers.get(message.message_type, []):
                    try:
                        await callback(message)
                        self._reset_circuit_breaker(message.sender)
                    except Exception as e:
                        self._record_failure(message.sender)
                        print(f"Error processing message: {e}")
                        
            except asyncio.TimeoutError:
                continue
    
    def _is_circuit_open(self, sender: str) -> bool:
        """Check if circuit breaker is open for sender."""
        breaker = self.circuit_breakers.get(sender, {"failures": 0, "state": "closed"})
        return breaker["state"] == "open"
    
    def _record_failure(self, sender: str):
        """Record a failure for circuit breaker."""
        if sender not in self.circuit_breakers:
            self.circuit_breakers[sender] = {"failures": 0, "state": "closed"}
        
        self.circuit_breakers[sender]["failures"] += 1
        
        # Open circuit after 5 failures
        if self.circuit_breakers[sender]["failures"] >= 5:
            self.circuit_breakers[sender]["state"] = "open"
            # Schedule circuit reset after 10 seconds
            asyncio.create_task(self._reset_circuit_after_delay(sender, 10))
    
    def _reset_circuit_breaker(self, sender: str):
        """Reset circuit breaker on success."""
        if sender in self.circuit_breakers:
            self.circuit_breakers[sender] = {"failures": 0, "state": "closed"}
    
    async def _reset_circuit_after_delay(self, sender: str, delay: int):
        """Reset circuit breaker after delay."""
        await asyncio.sleep(delay)
        if sender in self.circuit_breakers:
            self.circuit_breakers[sender]["state"] = "half-open"

if __name__ == "__main__":
    print("Event-Driven Message Bus loaded successfully!")
    
    # Test message bus
    async def test_message_bus():
        bus = EventDrivenMessageBus()
        await bus.start()
        
        # Test subscriber
        async def test_callback(message):
            print(f"Received message: {message.message_type} - {message.payload}")
        
        bus.subscribe("test_message", test_callback)
        
        # Publish test message
        message_id = await bus.publish(
            sender="test_sender",
            message_type="test_message",
            payload={"data": "test_value"}
        )
        
        print(f"Published message with ID: {message_id}")
        
        # Wait for processing
        await asyncio.sleep(1)
        await bus.stop()
    
    # Run test
    asyncio.run(test_message_bus())
