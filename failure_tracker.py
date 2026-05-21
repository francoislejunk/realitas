"""
Failure Tracker System

Tracks repeated action attempts and failures to enable self-aware
internal voice commentary like "Are we really dumb enough to keep doing this?"
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any


class FailureTracker:
    """
    Tracks recent action attempts and failures for self-aware internal voice.
    
    Enables escalating frustration commentary:
    - 1st failure: "Damn. That didn't work."
    - 2nd failure: "Twice now. Maybe we need a different approach."
    - 3rd failure: "Are we really dumb enough to keep doing this?"
    - 4th+ failure: "This is insane. We're idiots."
    """
    
    def __init__(self, max_history: int = 10):
        """
        Initialize failure tracker.
        
        Args:
            max_history: Maximum number of attempts to track (default 10)
        """
        self.recent_attempts: List[Dict[str, Any]] = []
        self.max_history = max_history
    
    def record_attempt(self, action_description: str, success: bool):
        """
        Record an action attempt.
        
        Args:
            action_description: The action attempted
            success: Whether the action succeeded
        """
        self.recent_attempts.append({
            'action': self._normalize_action(action_description),
            'success': success,
            'timestamp': datetime.now()
        })
        
        # Keep only recent history
        if len(self.recent_attempts) > self.max_history:
            self.recent_attempts.pop(0)
    
    def _normalize_action(self, action: str) -> str:
        """
        Normalize action for comparison (remove minor variations).
        
        Args:
            action: The action description
            
        Returns:
            Normalized action string
        """
        # Extract core action (e.g., "climb ladder", "pick lock", "convince guard")
        # Simple keyword extraction - first 3 meaningful words
        stop_words = {'i', 'try', 'to', 'the', 'a', 'an', 'and', 'or'}
        words = action.lower().split()
        keywords = [w for w in words if w not in stop_words][:3]
        return " ".join(keywords)
    
    def get_failure_count(self, action_description: str, window_minutes: int = 30) -> int:
        """
        Get count of recent failures for similar action.
        
        Args:
            action_description: The action to check
            window_minutes: Time window to check (default 30 minutes)
            
        Returns:
            Number of failures in time window
        """
        normalized = self._normalize_action(action_description)
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        
        failures = [
            a for a in self.recent_attempts
            if a['action'] == normalized
            and not a['success']
            and a['timestamp'] > cutoff_time
        ]
        
        return len(failures)
    
    def get_consecutive_failures(self, action_description: str) -> int:
        """
        Get count of consecutive failures for this action.
        
        Counts backwards from most recent until hitting a success or different action.
        
        Args:
            action_description: The action to check
            
        Returns:
            Number of consecutive failures
        """
        normalized = self._normalize_action(action_description)
        
        # Count from most recent backwards
        consecutive = 0
        for attempt in reversed(self.recent_attempts):
            if attempt['action'] == normalized and not attempt['success']:
                consecutive += 1
            elif attempt['action'] == normalized:
                # Hit a success, stop counting
                break
            # Different action, keep looking backwards
        
        return consecutive
    
    def get_total_attempts(self, action_description: str, window_minutes: int = 30) -> int:
        """
        Get total number of attempts for this action.
        
        Args:
            action_description: The action to check
            window_minutes: Time window to check (default 30 minutes)
            
        Returns:
            Total number of attempts
        """
        normalized = self._normalize_action(action_description)
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        
        attempts = [
            a for a in self.recent_attempts
            if a['action'] == normalized
            and a['timestamp'] > cutoff_time
        ]
        
        return len(attempts)
    
    def should_show_failure_awareness(self, action_description: str) -> bool:
        """
        Determine if failure awareness should be shown.
        
        Args:
            action_description: The action to check
            
        Returns:
            True if 2+ consecutive failures (show awareness)
        """
        return self.get_consecutive_failures(action_description) >= 2
    
    def get_frustration_level(self, action_description: str) -> str:
        """
        Get frustration level based on consecutive failures.
        
        Args:
            action_description: The action to check
            
        Returns:
            Frustration level: "none", "moderate", "high", "extreme"
        """
        consecutive = self.get_consecutive_failures(action_description)
        
        if consecutive == 0:
            return "none"
        elif consecutive == 1:
            return "none"  # First failure, no frustration yet
        elif consecutive == 2:
            return "moderate"
        elif consecutive == 3:
            return "high"
        else:  # 4+
            return "extreme"
    
    def clear_history(self):
        """Clear all tracked attempts."""
        self.recent_attempts.clear()
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of tracked attempts.
        
        Returns:
            Dictionary with summary statistics
        """
        if not self.recent_attempts:
            return {
                'total_attempts': 0,
                'successes': 0,
                'failures': 0,
                'success_rate': 0.0
            }
        
        successes = sum(1 for a in self.recent_attempts if a['success'])
        failures = len(self.recent_attempts) - successes
        
        return {
            'total_attempts': len(self.recent_attempts),
            'successes': successes,
            'failures': failures,
            'success_rate': successes / len(self.recent_attempts) if self.recent_attempts else 0.0
        }
