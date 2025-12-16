"""
Execution time profiling utility.
Provides context managers and decorators for tracking execution time of code blocks.
"""

import time
import logging
import contextlib
from typing import Dict, Any, Optional, List
from threading import local

logger = logging.getLogger(__name__)

# Thread-local storage for managing nested profiling contexts
_thread_local = local()

def get_current_profiler() -> Optional['Profiler']:
    """Get the active profiler for the current thread/context."""
    if not hasattr(_thread_local, 'active_profiler'):
        _thread_local.active_profiler = None
    return _thread_local.active_profiler

class Profiler:
    """
    Hierarchical execution time profiler.
    
    Usage:
        with Profiler("process_name") as p:
            # do work
            with p.step("sub_task"):
                 # do sub work
            
            # Or use global helper if passed around
            with profile_step("another_task"):
                 # do work
    """
    
    def __init__(self, name: str = "root"):
        self.name = name
        self.timings: Dict[str, float] = {}
        self.start_times: Dict[str, float] = {}
        
        # Stack to track nested steps: [(name, start_time), ...]
        self._stack: List[str] = []
        
    def start(self, step_name: str):
        """Start measuring a step."""
        full_name = self._get_full_name(step_name)
        self.start_times[full_name] = time.perf_counter()
        self._stack.append(step_name)
        
    def stop(self, step_name: str, log_level: int = logging.DEBUG):
        """Stop measuring a step and record the time."""
        if not self._stack or self._stack[-1] != step_name:
            logger.warning(f"Profiler stack mismatch: stopping {step_name} but top is {self._stack[-1] if self._stack else 'empty'}")
            return

        self._stack.pop()
        full_name = self._get_full_name(step_name)
        start_time = self.start_times.pop(full_name, None)
        
        if start_time is not None:
            duration = time.perf_counter() - start_time
            self.timings[full_name] = duration
            logger.log(log_level, f"PROFILE: {full_name} completed in {duration:.4f}s")
            
    def _get_full_name(self, step_name: str) -> str:
        """Construct hierarchical name."""
        # Note: self._stack already contains the current step when called from start(), 
        # but we want the prefix of *active* parents.
        # Actually, for flat dictionary keys, we can just use dot notation.
        # When _get_full_name is called from start(), step_name is not yet in stack (or just added).
        # Let's simplify: keys are just "step_name". Hierarchy is implied by usage or we can build it.
        # To support flat simple keys for the report, let's just use the step_name provided.
        # If conflicts are possible, user should namespace them.
        return step_name

    @contextlib.contextmanager
    def step(self, name: str, log_level: int = logging.DEBUG):
        """Context manager for a single profiling step."""
        self.start(name)
        try:
            yield
        finally:
            self.stop(name, log_level)
            
    def get_timings(self) -> Dict[str, float]:
        """Return a copy of the recorded timings."""
        return self.timings.copy()

    # Make the profiler itself a context manager for the root block
    def __enter__(self):
        # Set as thread-local active profiler
        self._prev_profiler = get_current_profiler()
        _thread_local.active_profiler = self
        
        self.start(self.name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop(self.name, logging.INFO) # Log root at INFO
        
        # Restore previous profiler
        _thread_local.active_profiler = self._prev_profiler


@contextlib.contextmanager
def profile_step(name: str, log_level: int = logging.DEBUG):
    """
    Global helper to profile a step using the current thread's active Profiler.
    If no profiler is active, it just logs the time locally without storing it.
    """
    profiler = get_current_profiler()
    if profiler:
        with profiler.step(name, log_level):
            yield
    else:
        # Fallback if no profiler context exists
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            logger.log(log_level, f"PROFILE (detached): {name} completed in {duration:.4f}s")
