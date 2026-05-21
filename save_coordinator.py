"""
Save Coordinator - Single Source of Truth for All Save Operations

This system eliminates save conflicts by centralizing all save requests
through a single coordinator that manages deduplication and queuing.
"""

from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import time
import threading
from queue import Queue, Empty

from color_utils import Color


class SaveTriggerType(Enum):
    """Types of events that can trigger saves"""
    REGULAR_AUTO_SAVE = "regular_auto_save"
    ROUND_COMPLETION = "round_completion"
    SCENE_TRANSITION = "scene_transition"
    ENCOUNTER_END = "encounter_end"
    USER_QUIT = "user_quit"
    EMERGENCY_SAVE = "emergency_save"


@dataclass
class SaveRequest:
    """Request to perform a save operation with full context"""
    trigger_type: SaveTriggerType
    requester_system: str
    save_data: Dict[str, Any]
    priority: int = 1  # Lower number = higher priority
    timestamp: float = field(default_factory=time.time)
    description: str = ""
    
    def __post_init__(self):
        if not self.description:
            self.description = f"{self.trigger_type.value} by {self.requester_system}"


@dataclass
class SaveResult:
    """Result of save operation with status and timing"""
    success: bool
    trigger_types: List[SaveTriggerType]
    combined_data: Dict[str, Any]
    execution_time: float
    error_message: Optional[str] = None
    deduplication_count: int = 0


class SaveCoordinator:
    """
    Centralized save coordinator that manages all save operations.
    
    CRITICAL: This is the ONLY system allowed to perform saves.
    All other systems must request saves through this coordinator.
    """
    
    def __init__(self, tracker_instance):
        self.tracker = tracker_instance
        
        # Save request queue and processing
        self.save_queue: Queue = Queue()
        self.processing_lock = threading.Lock()
        self.is_processing = False
        
        # Deduplication tracking
        self.pending_triggers: Set[SaveTriggerType] = set()
        self.last_save_timestamp = time.time()
        self.save_history: List[SaveResult] = []
        
        # Configuration
        self.deduplication_window = 2.0  # 2 seconds to combine saves
        self.max_queue_size = 10
        
        print(f"{Color.SYSTEM}💾 Save Coordinator initialized - All save operations centralized{Color.RESET}")
    
    def request_save(self, request: SaveRequest) -> bool:
        """
        SINGLE POINT OF SAVE OPERATIONS
        
        All systems must use this method to perform saves.
        This prevents conflicts and ensures proper deduplication.
        """
        try:
            # Check if queue is full
            if self.save_queue.qsize() >= self.max_queue_size:
                print(f"⚠️ Save queue full, dropping save request: {request.description}")
                return False
            
            # Add to queue
            self.save_queue.put(request)
            
            # Process queue if not already processing
            self._process_save_queue()
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to queue save request: {e}")
            return False
    
    def _process_save_queue(self):
        """Process all pending save requests with deduplication"""
        with self.processing_lock:
            if self.is_processing:
                return  # Already processing
            
            self.is_processing = True
        
        try:
            # Collect all pending requests within deduplication window
            requests_to_process = []
            
            # Get first request (blocking)
            try:
                first_request = self.save_queue.get(timeout=0.1)
                requests_to_process.append(first_request)
            except Empty:
                return  # No requests to process
            
            # Collect additional requests within deduplication window
            start_time = time.time()
            while (time.time() - start_time) < self.deduplication_window:
                try:
                    additional_request = self.save_queue.get(timeout=0.1)
                    requests_to_process.append(additional_request)
                except Empty:
                    break  # No more requests
            
            # Process combined requests
            if requests_to_process:
                result = self._execute_combined_save(requests_to_process)
                self.save_history.append(result)
                
                # Keep only last 10 save results
                if len(self.save_history) > 10:
                    self.save_history.pop(0)
        
        finally:
            with self.processing_lock:
                self.is_processing = False
    
    def _execute_combined_save(self, requests: List[SaveRequest]) -> SaveResult:
        """Execute a combined save operation from multiple requests"""
        start_time = time.time()
        
        # Sort by priority (lower number = higher priority)
        requests.sort(key=lambda r: r.priority)
        
        # Combine save data from all requests
        combined_data = {}
        trigger_types = []
        
        for request in requests:
            trigger_types.append(request.trigger_type)
            
            # Merge save data (later requests override earlier ones for conflicts)
            combined_data.update(request.save_data)
            
            # Add trigger-specific metadata
            combined_data[f"{request.trigger_type.value}_metadata"] = {
                'requester': request.requester_system,
                'timestamp': request.timestamp,
                'description': request.description
            }
        
        # Add coordination metadata
        combined_data['save_coordination'] = {
            'combined_triggers': [t.value for t in trigger_types],
            'deduplication_count': len(requests) - 1,
            'execution_timestamp': time.time(),
            'processing_duration': 0  # Will be updated below
        }
        
        # Execute the save operation
        try:
            # Determine save method based on highest priority trigger
            primary_trigger = requests[0].trigger_type
            
            if primary_trigger == SaveTriggerType.SCENE_TRANSITION:
                self.tracker.save_scene_transition(combined_data)
            elif primary_trigger == SaveTriggerType.ROUND_COMPLETION:
                self.tracker.save_round_completion(combined_data)
            elif primary_trigger == SaveTriggerType.USER_QUIT:
                self.tracker.save_final_session_state(combined_data)
            else:
                # Default to session state save
                self.tracker.save_session_state(combined_data)
            
            execution_time = time.time() - start_time
            combined_data['save_coordination']['processing_duration'] = execution_time
            
            # Display consolidated save message
            trigger_names = [t.value.replace('_', ' ').title() for t in trigger_types]
            if len(trigger_names) > 1:
                print(f"{Color.SUCCESS}💾 Combined save completed: {', '.join(trigger_names)} ({execution_time:.2f}s){Color.RESET}")
            else:
                print(f"{Color.SUCCESS}💾 Save completed: {trigger_names[0]} ({execution_time:.2f}s){Color.RESET}")

            try:
                session_file = self.tracker.storage_directory / "sessions" / f"session_{self.tracker.session_id}.json"
                print(f"{Color.SUCCESS}💾 WORLD SAVED: {session_file}{Color.RESET}")
            except Exception:
                print(f"{Color.SUCCESS}💾 WORLD SAVED!{Color.RESET}")
            
            self.last_save_timestamp = time.time()
            
            return SaveResult(
                success=True,
                trigger_types=trigger_types,
                combined_data=combined_data,
                execution_time=execution_time,
                deduplication_count=len(requests) - 1
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            print(f"❌ Save operation failed: {error_msg}")
            
            return SaveResult(
                success=False,
                trigger_types=trigger_types,
                combined_data=combined_data,
                execution_time=execution_time,
                error_message=error_msg,
                deduplication_count=len(requests) - 1
            )
    
    def create_regular_auto_save_request(self, session_data: Dict[str, Any]) -> SaveRequest:
        """Helper to create regular auto-save requests"""
        return SaveRequest(
            trigger_type=SaveTriggerType.REGULAR_AUTO_SAVE,
            requester_system="main_simulation",
            save_data=session_data,
            priority=3,  # Lower priority
            description="Regular auto-save (every 5 actions)"
        )
    
    def create_round_completion_request(self, round_data: Dict[str, Any]) -> SaveRequest:
        """Helper to create round completion save requests"""
        return SaveRequest(
            trigger_type=SaveTriggerType.ROUND_COMPLETION,
            requester_system="encounter_system",
            save_data=round_data,
            priority=2,  # Medium priority
            description="Round completion save"
        )
    
    def create_scene_transition_request(self, scene_data: Dict[str, Any]) -> SaveRequest:
        """Helper to create scene transition save requests"""
        return SaveRequest(
            trigger_type=SaveTriggerType.SCENE_TRANSITION,
            requester_system="scene_manager",
            save_data=scene_data,
            priority=1,  # High priority
            description="Scene transition save"
        )
    
    def create_user_quit_request(self, final_data: Dict[str, Any]) -> SaveRequest:
        """Helper to create user quit save requests"""
        return SaveRequest(
            trigger_type=SaveTriggerType.USER_QUIT,
            requester_system="main_simulation",
            save_data=final_data,
            priority=0,  # Highest priority
            description="Final session save"
        )
    
    def get_save_status(self) -> Dict[str, Any]:
        """Get current save coordinator status"""
        return {
            'queue_size': self.save_queue.qsize(),
            'is_processing': self.is_processing,
            'last_save_timestamp': self.last_save_timestamp,
            'time_since_last_save': time.time() - self.last_save_timestamp,
            'total_saves_completed': len(self.save_history),
            'recent_saves': [
                {
                    'triggers': [t.value for t in result.trigger_types],
                    'success': result.success,
                    'deduplication_count': result.deduplication_count,
                    'execution_time': result.execution_time
                }
                for result in self.save_history[-3:]  # Last 3 saves
            ]
        }
    
    def force_immediate_save(self, emergency_data: Dict[str, Any]) -> SaveResult:
        """Force an immediate save, bypassing queue (emergency use only)"""
        print("🚨 Emergency save triggered - bypassing queue")
        
        emergency_request = SaveRequest(
            trigger_type=SaveTriggerType.EMERGENCY_SAVE,
            requester_system="emergency_system",
            save_data=emergency_data,
            priority=0,
            description="Emergency immediate save"
        )
        
        return self._execute_combined_save([emergency_request])
    
    def flush_pending_saves(self) -> List[SaveResult]:
        """Process all pending saves immediately and return results"""
        results = []
        
        print("🔄 Flushing all pending saves...")
        
        while not self.save_queue.empty():
            self._process_save_queue()
            if self.save_history:
                results.append(self.save_history[-1])
        
        return results


# Global instance - SINGLE SOURCE OF TRUTH
_save_coordinator: Optional[SaveCoordinator] = None

def get_save_coordinator() -> SaveCoordinator:
    """Get the global save coordinator instance"""
    global _save_coordinator
    if _save_coordinator is None:
        raise RuntimeError("Save coordinator not initialized. Call initialize_save_coordinator() first.")
    return _save_coordinator

def initialize_save_coordinator(tracker_instance) -> SaveCoordinator:
    """Initialize the global save coordinator"""
    global _save_coordinator
    _save_coordinator = SaveCoordinator(tracker_instance)
    return _save_coordinator
