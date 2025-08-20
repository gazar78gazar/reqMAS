"""
Circuit Breaker - Implements circuit breaker pattern for agent resilience
"""

from typing import Dict, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import asyncio

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    """
    Circuit breaker for individual agents.
    Prevents cascading failures.
    """
    
    def __init__(self, 
                 agent_id: str,
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 half_open_requests: int = 3):
        self.agent_id = agent_id
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout  # seconds
        self.half_open_requests = half_open_requests
        self.half_open_successes = 0
        self.last_failure_time = None
        self.last_state_change = datetime.now()
    
    async def call(self, func: Callable, *args, **kwargs):
        """
        Execute function through circuit breaker.
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.half_open_successes = 0
                self.last_state_change = datetime.now()
            else:
                raise Exception(f"Circuit breaker OPEN for {self.agent_id}")
        
        try:
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_successes += 1
            if self.half_open_successes >= self.half_open_requests:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.last_state_change = datetime.now()
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.last_state_change = datetime.now()
        elif self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.last_state_change = datetime.now()
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if not self.last_failure_time:
            return True
        
        time_since_failure = datetime.now() - self.last_failure_time
        return time_since_failure.total_seconds() >= self.recovery_timeout
    
    def get_status(self) -> Dict:
        """Get circuit breaker status."""
        return {
            "agent_id": self.agent_id,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_state_change": self.last_state_change.isoformat(),
            "recovery_timeout": self.recovery_timeout,
            "half_open_successes": self.half_open_successes
        }
    
    def reset(self):
        """Manually reset circuit breaker."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.half_open_successes = 0
        self.last_state_change = datetime.now()
        self.last_failure_time = None
    
    def force_open(self):
        """Manually open circuit breaker."""
        self.state = CircuitState.OPEN
        self.last_state_change = datetime.now()
    
    def is_available(self) -> bool:
        """Check if circuit breaker allows requests."""
        if self.state == CircuitState.OPEN:
            return self._should_attempt_reset()
        return True