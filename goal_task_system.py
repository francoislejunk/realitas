"""
Goal and Task System for Realitas Neo

This module provides a hierarchical goal/task system that distinguishes between:
- GOALS: Long-term, life-defining objectives that require substantial events to change
- TASKS: Short-term, immediate needs that update dynamically based on user actions

Goals represent the character's core motivations and life direction.
Tasks represent immediate priorities and everyday needs.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import json


class GoalImportance(Enum):
    """Importance level of a goal - determines resistance to change"""
    LIFE_DEFINING = "life_defining"  # Requires major life event to change
    MAJOR = "major"  # Requires significant event to change
    MODERATE = "moderate"  # Can change with meaningful events


class TaskPriority(Enum):
    """Priority level of a task"""
    CRITICAL = "critical"  # Survival needs, immediate danger
    HIGH = "high"  # Important but not life-threatening
    MODERATE = "moderate"  # Should be addressed soon
    LOW = "low"  # Can be deferred


class TaskCategory(Enum):
    """Categories of tasks for organization"""
    SURVIVAL = "survival"  # Food, water, sleep, shelter
    COMBAT = "combat"  # Fighting, defense
    EXPLORATION = "exploration"  # Investigation, discovery
    SOCIAL = "social"  # Relationship maintenance, social obligations
    ACQUISITION = "acquisition"  # Getting items, money
    PERSONAL = "personal"  # Character development
    GOAL_RELATED = "goal_related"  # Directly advances a goal
    MAINTENANCE = "maintenance"  # Equipment, health, resources
    REACTIVE = "reactive"  # Response to immediate events


@dataclass
class Goal:
    """Represents a long-term, life-defining goal"""
    description: str
    importance: GoalImportance
    progress: float = 0.0  # 0.0 to 1.0
    sub_goals: List[str] = field(default_factory=list)
    created_turn: int = 0
    last_modified_turn: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "description": self.description,
            "importance": self.importance.value,
            "progress": self.progress,
            "sub_goals": self.sub_goals,
            "created_turn": self.created_turn,
            "last_modified_turn": self.last_modified_turn
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Goal':
        return cls(
            description=data["description"],
            importance=GoalImportance(data["importance"]),
            progress=data.get("progress", 0.0),
            sub_goals=data.get("sub_goals", []),
            created_turn=data.get("created_turn", 0),
            last_modified_turn=data.get("last_modified_turn", 0)
        )


@dataclass
class Task:
    """Represents a short-term, dynamic task"""
    description: str
    priority: TaskPriority
    category: TaskCategory
    related_goal: Optional[str] = None  # Description of related goal if any
    created_turn: int = 0
    completed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "description": self.description,
            "priority": self.priority.value,
            "category": self.category.value,
            "related_goal": self.related_goal,
            "created_turn": self.created_turn,
            "completed": self.completed
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        return cls(
            description=data["description"],
            priority=TaskPriority(data["priority"]),
            category=TaskCategory(data["category"]),
            related_goal=data.get("related_goal"),
            created_turn=data.get("created_turn", 0),
            completed=data.get("completed", False)
        )


class GoalTaskManager:
    """Manages goals and tasks for an actor"""
    
    def __init__(self):
        self.goals: List[Goal] = []
        self.tasks: List[Task] = []
        self.current_task: Optional[Task] = None
        self.current_turn: int = 0
    
    def add_goal(self, description: str, importance: GoalImportance, sub_goals: List[str] = None) -> Goal:
        """Add a new goal"""
        goal = Goal(
            description=description,
            importance=importance,
            sub_goals=sub_goals or [],
            created_turn=self.current_turn,
            last_modified_turn=self.current_turn
        )
        self.goals.append(goal)
        return goal
    
    def update_goal(self, goal_index: int, new_description: str = None, 
                   new_progress: float = None, new_sub_goals: List[str] = None) -> bool:
        """Update an existing goal - requires justification for life-defining goals"""
        if goal_index >= len(self.goals):
            return False
        
        goal = self.goals[goal_index]
        
        if new_description:
            goal.description = new_description
        if new_progress is not None:
            goal.progress = max(0.0, min(1.0, new_progress))
        if new_sub_goals is not None:
            goal.sub_goals = new_sub_goals
        
        goal.last_modified_turn = self.current_turn
        return True
    
    def add_task(self, description: str, priority: TaskPriority, 
                category: TaskCategory, related_goal: str = None) -> Task:
        """Add a new task"""
        task = Task(
            description=description,
            priority=priority,
            category=category,
            related_goal=related_goal,
            created_turn=self.current_turn
        )
        self.tasks.append(task)
        return task
    
    def set_current_task(self, task: Task):
        """Set the current active task"""
        self.current_task = task
    
    def complete_task(self, task: Task):
        """Mark a task as completed"""
        task.completed = True
        if self.current_task == task:
            self.current_task = None
    
    def remove_task(self, task: Task):
        """Remove a task from the list"""
        if task in self.tasks:
            self.tasks.remove(task)
        if self.current_task == task:
            self.current_task = None
    
    def get_active_tasks(self) -> List[Task]:
        """Get all non-completed tasks"""
        return [t for t in self.tasks if not t.completed]
    
    def get_tasks_by_priority(self, priority: TaskPriority) -> List[Task]:
        """Get all active tasks of a specific priority"""
        return [t for t in self.get_active_tasks() if t.priority == priority]
    
    def get_tasks_by_category(self, category: TaskCategory) -> List[Task]:
        """Get all active tasks of a specific category"""
        return [t for t in self.get_active_tasks() if t.category == category]
    
    def get_highest_priority_task(self) -> Optional[Task]:
        """Get the highest priority active task"""
        active_tasks = self.get_active_tasks()
        if not active_tasks:
            return None
        
        priority_order = [TaskPriority.CRITICAL, TaskPriority.HIGH, 
                         TaskPriority.MODERATE, TaskPriority.LOW]
        
        for priority in priority_order:
            tasks = [t for t in active_tasks if t.priority == priority]
            if tasks:
                return tasks[0]
        
        return None
    
    def increment_turn(self):
        """Increment the turn counter"""
        self.current_turn += 1
    
    def display_current_task(self) -> str:
        """Get formatted string of current task for display"""
        if not self.current_task:
            return "No current task"
        
        task = self.current_task
        priority_emoji = {
            TaskPriority.CRITICAL: "🔴",
            TaskPriority.HIGH: "🟠",
            TaskPriority.MODERATE: "🟡",
            TaskPriority.LOW: "🟢"
        }
        
        category_emoji = {
            TaskCategory.SURVIVAL: "🍖",
            TaskCategory.COMBAT: "⚔️",
            TaskCategory.EXPLORATION: "🔍",
            TaskCategory.SOCIAL: "💬",
            TaskCategory.ACQUISITION: "💰",
            TaskCategory.PERSONAL: "👤"
        }
        
        emoji = priority_emoji.get(task.priority, "⚪")
        cat_emoji = category_emoji.get(task.category, "📋")
        
        return f"{emoji} {cat_emoji} {task.description}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "goals": [g.to_dict() for g in self.goals],
            "tasks": [t.to_dict() for t in self.tasks],
            "current_task": self.current_task.to_dict() if self.current_task else None,
            "current_turn": self.current_turn
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GoalTaskManager':
        """Deserialize from dictionary"""
        manager = cls()
        manager.goals = [Goal.from_dict(g) for g in data.get("goals", [])]
        manager.tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
        
        current_task_data = data.get("current_task")
        if current_task_data:
            manager.current_task = Task.from_dict(current_task_data)
        
        manager.current_turn = data.get("current_turn", 0)
        return manager
    
    def get_summary(self) -> str:
        """Get a human-readable summary of goals and tasks"""
        lines = []
        
        lines.append("=== GOALS ===")
        for i, goal in enumerate(self.goals):
            progress_bar = "█" * int(goal.progress * 10) + "░" * (10 - int(goal.progress * 10))
            lines.append(f"{i+1}. [{goal.importance.value}] {goal.description}")
            lines.append(f"   Progress: [{progress_bar}] {int(goal.progress * 100)}%")
            if goal.sub_goals:
                lines.append(f"   Sub-goals: {', '.join(goal.sub_goals)}")
        
        lines.append("\n=== ACTIVE TASKS ===")
        active_tasks = self.get_active_tasks()
        if not active_tasks:
            lines.append("No active tasks")
        else:
            for task in active_tasks:
                marker = "→" if task == self.current_task else " "
                lines.append(f"{marker} [{task.priority.value}] {task.description}")
                if task.related_goal:
                    lines.append(f"   Related to: {task.related_goal}")
        
        return "\n".join(lines)


class GoalTaskInterpreter:
    """
    Lightweight helper that works WITH the existing Interpreter Agent.
    Uses the Interpreter's action analysis to update tasks.
    """
    
    def __init__(self, client=None, model: str = None):
        """
        Initialize the interpreter
        
        Args:
            client: OpenRouter client for LLM calls (optional, uses existing if None)
            model: Model name to use for interpretation (optional, uses existing if None)
        """
        self.client = client
        self.model = model
    
    def interpret_action_for_tasks(self, user_action: str, current_context: str,
                                   goal_task_manager: GoalTaskManager, 
                                   action_interpretation: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze user action to determine task updates.
        Can use existing action_interpretation from Interpreter Agent if provided,
        or make its own LLM call if needed.
        
        Returns:
            {
                "inferred_intent": str,
                "current_task_should_change": bool,
                "new_current_task": Optional[dict],
                "new_tasks_to_add": List[dict],
                "tasks_to_complete": List[str],
                "reasoning": str
            }
        """
        # If we have existing interpretation, use rule-based inference
        if action_interpretation:
            return self._infer_tasks_from_interpretation(
                user_action, action_interpretation, goal_task_manager
            )
        
        # Otherwise, make LLM call (fallback)
        return self._llm_task_interpretation(user_action, current_context, goal_task_manager)
    
    def _infer_tasks_from_interpretation(self, user_action: str, 
                                        action_interpretation: Dict[str, Any],
                                        goal_task_manager: GoalTaskManager) -> Dict[str, Any]:
        """
        Use rule-based inference from existing action interpretation.
        This leverages the Interpreter Agent's analysis without extra LLM calls.
        """
        action_desc = action_interpretation.get('action_description', user_action).lower()
        action_noun = action_interpretation.get('action_noun', '').lower()
        
        # DEBUG: Show what we're analyzing
        print(f"[TASK DEBUG] User action: '{user_action}'")
        print(f"[TASK DEBUG] Action desc: '{action_desc}'")
        print(f"[TASK DEBUG] Action noun: '{action_noun}'")
        
        # Infer intent from action description
        inferred_intent = action_interpretation.get('action_description', user_action)
        
        # Rule-based task inference
        new_current_task = None
        new_tasks = []
        completed_tasks = []
        should_change = False
        
        # Check if current task is completed
        current_task = goal_task_manager.current_task
        if current_task:
            # Task completion detection
            task_desc_lower = current_task.description.lower()
            
            # If task was "investigate X" and action is investigating X, mark complete
            if 'investigate' in task_desc_lower:
                # Extract what we're investigating from task
                import re
                match = re.search(r'investigate:?\s+(.+)', task_desc_lower)
                if match:
                    investigation_target = match.group(1).strip()
                    # Check if user action mentions this target
                    if investigation_target in action_desc or investigation_target in user_action.lower():
                        print(f"[TASK DEBUG] Completing task: {current_task.description}")
                        completed_tasks.append(current_task.description)
                        goal_task_manager.complete_task(current_task)
                        should_change = True  # Need new task after completion
            
            # If task was "find X" and action is finding/taking X, mark complete
            elif 'find' in task_desc_lower:
                match = re.search(r'find\s+(.+)', task_desc_lower)
                if match:
                    search_target = match.group(1).strip()
                    # Check if action involves acquiring/finding this
                    if any(verb in action_desc for verb in ['take', 'grab', 'pick up', 'acquire', 'find', 'get']):
                        if search_target in action_desc or search_target in user_action.lower():
                            print(f"[TASK DEBUG] Completing task: {current_task.description}")
                            completed_tasks.append(current_task.description)
                            goal_task_manager.complete_task(current_task)
                            should_change = True
            
            # If task was "deal with threat" and action is combat/escape, mark complete
            elif 'threat' in task_desc_lower or 'danger' in task_desc_lower:
                if any(verb in action_desc for verb in ['defeat', 'escape', 'flee', 'kill', 'subdue']):
                    print(f"[TASK DEBUG] Completing task: {current_task.description}")
                    completed_tasks.append(current_task.description)
                    goal_task_manager.complete_task(current_task)
                    should_change = True
        
        # Survival keywords
        survival_keywords = {
            'eat': ('Find food', TaskPriority.HIGH, TaskCategory.SURVIVAL),
            'food': ('Find food', TaskPriority.HIGH, TaskCategory.SURVIVAL),
            'drink': ('Find water', TaskPriority.CRITICAL, TaskCategory.SURVIVAL),
            'water': ('Find water', TaskPriority.CRITICAL, TaskCategory.SURVIVAL),
            'sleep': ('Get rest', TaskPriority.HIGH, TaskCategory.SURVIVAL),
            'rest': ('Get rest', TaskPriority.HIGH, TaskCategory.SURVIVAL),
            'shelter': ('Find shelter', TaskPriority.HIGH, TaskCategory.SURVIVAL),
        }
        
        # Check for survival needs (use word boundaries to avoid false matches)
        import re
        for keyword, (task_desc, priority, category) in survival_keywords.items():
            # Use word boundaries to match whole words only
            if re.search(r'\b' + re.escape(keyword) + r'\b', action_desc):
                print(f"[TASK DEBUG] Found keyword '{keyword}' in action_desc")
                # Additional check: keyword should be in the USER action, not just context
                if keyword in user_action.lower():
                    print(f"[TASK DEBUG] Keyword '{keyword}' also in user_action - creating task: {task_desc}")
                    should_change = True
                    new_current_task = {
                        'description': task_desc,
                        'priority': priority.value,
                        'category': category.value,
                        'related_goal': None
                    }
                    break
                else:
                    print(f"[TASK DEBUG] Keyword '{keyword}' NOT in user_action - skipping")
        
        # Exploration/investigation keywords
        # Only create new investigation task if we didn't just complete one
        if any(word in action_desc for word in ['search', 'investigate', 'explore', 'look for', 'examine']):
            if not should_change:  # Don't override survival tasks or completed tasks
                # Don't create investigation task if we just completed an investigation
                if not (completed_tasks and any('investigate' in t.lower() for t in completed_tasks)):
                    should_change = True
                    new_current_task = {
                        'description': f"Investigate: {action_noun or 'the area'}",
                        'priority': TaskPriority.MODERATE.value,
                        'category': TaskCategory.EXPLORATION.value,
                        'related_goal': None
                    }
        
        # Combat/danger keywords
        if any(word in action_desc for word in ['attack', 'fight', 'defend', 'flee', 'escape']):
            if not should_change:
                should_change = True
                new_current_task = {
                    'description': f"Deal with immediate threat",
                    'priority': TaskPriority.CRITICAL.value,
                    'category': TaskCategory.REACTIVE.value,
                    'related_goal': None
                }
        
        return {
            'inferred_intent': inferred_intent,
            'current_task_should_change': should_change,
            'new_current_task': new_current_task,
            'new_tasks_to_add': new_tasks,
            'tasks_to_complete': completed_tasks,
            'reasoning': 'Rule-based inference from action interpretation'
        }
    
    def _llm_task_interpretation(self, user_action: str, current_context: str,
                                goal_task_manager: GoalTaskManager) -> Dict[str, Any]:
        """
        Fallback LLM-based task interpretation when no existing interpretation is available.
        """
        if not self.client or not self.model:
            # No LLM available, return minimal update
            return {
                'inferred_intent': user_action,
                'current_task_should_change': False,
                'new_current_task': None,
                'new_tasks_to_add': [],
                'tasks_to_complete': [],
                'reasoning': 'No LLM client available for task interpretation'
            }
        
        goals_summary = "\n".join([f"- {g.description} (Progress: {int(g.progress * 100)}%)" 
                                  for g in goal_task_manager.goals])
        tasks_summary = "\n".join([f"- [{t.priority.value}] {t.description}" 
                                  for t in goal_task_manager.get_active_tasks()])
        current_task_desc = goal_task_manager.current_task.description if goal_task_manager.current_task else "None"
        
        prompt = f"""You are analyzing a user's action to interpret their current intent and update their task list.

**Current Context:**
{current_context}

**User's Long-Term Goals:**
{goals_summary if goals_summary else "No goals defined"}

**Current Active Tasks:**
{tasks_summary if tasks_summary else "No active tasks"}

**Current Task:** {current_task_desc}

**User Action:** "{user_action}"

**Your Task:**
Analyze this action to determine:
1. What is the user's immediate intent? (What are they trying to accomplish RIGHT NOW?)
2. Should the current task be updated based on this action?
3. Are there new tasks that should be added based on this action?
4. Are any existing tasks now completed or obsolete?

**Task Categories:**
- survival: Food, water, sleep, shelter needs
- goal_related: Actions that advance a long-term goal
- social: Relationship maintenance, social obligations
- exploration: Investigation, discovery, learning
- maintenance: Equipment care, health management, resource management
- reactive: Immediate responses to events

**Task Priorities:**
- critical: Survival needs, immediate danger
- high: Important but not life-threatening
- moderate: Should be addressed soon
- low: Can be deferred

**Response Format:**
Return ONLY valid JSON:
{{
    "inferred_intent": "Brief description of what the user is trying to accomplish",
    "current_task_should_change": true/false,
    "new_current_task": {{
        "description": "Task description",
        "priority": "critical/high/moderate/low",
        "category": "survival/goal_related/social/exploration/maintenance/reactive",
        "related_goal": "Related goal description or null"
    }} or null,
    "new_tasks_to_add": [
        {{
            "description": "Task description",
            "priority": "critical/high/moderate/low",
            "category": "survival/goal_related/social/exploration/maintenance/reactive",
            "related_goal": "Related goal description or null"
        }}
    ],
    "tasks_to_complete": ["Task description 1", "Task description 2"],
    "reasoning": "Brief explanation of your interpretation"
}}

**Guidelines:**
- Be conservative with task updates - only change when user intent clearly shifts
- Survival tasks (eating, sleeping, etc.) should be inferred from actions like "I eat" or "I rest"
- Goal-related tasks should connect to the user's long-term goals
- Don't create duplicate tasks
- Mark tasks complete when the action clearly accomplishes them
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"Error in task interpretation: {e}")
            return {
                "inferred_intent": "Unknown",
                "current_task_should_change": False,
                "new_current_task": None,
                "new_tasks_to_add": [],
                "tasks_to_complete": [],
                "reasoning": f"Error: {e}"
            }
    
    def assess_goal_change(self, event_description: str, goal: Goal, 
                          current_context: str) -> Dict[str, Any]:
        """
        Assess whether a significant event warrants changing a goal
        
        Returns:
            {
                "should_change": bool,
                "change_type": "modify/abandon/complete",
                "new_description": Optional[str],
                "justification": str,
                "confidence": float  # 0.0 to 1.0
            }
        """
        prompt = f"""You are assessing whether a significant event should change a character's long-term goal.

**Current Context:**
{current_context}

**Current Goal:**
Description: {goal.description}
Importance: {goal.importance.value}
Progress: {int(goal.progress * 100)}%

**Significant Event:**
{event_description}

**Assessment Criteria:**
For LIFE_DEFINING goals (like finding a kidnapped loved one):
- Only change if: loved one is found, loved one is confirmed dead, or character definitively abandons the search
- Requires EXTREME circumstances to change

For MAJOR goals:
- Only change if: goal is achieved, goal becomes impossible, or character has strong reason to abandon

For MODERATE goals:
- Can change with meaningful events that make the goal irrelevant or impossible

**Your Task:**
Determine if this event warrants changing the goal.

**Response Format:**
Return ONLY valid JSON:
{{
    "should_change": true/false,
    "change_type": "modify/abandon/complete/none",
    "new_description": "New goal description if modifying, or null",
    "new_progress": 0.0-1.0 or null,
    "justification": "Detailed explanation of why this change is or isn't warranted",
    "confidence": 0.0-1.0
}}

**Guidelines:**
- Be VERY conservative with LIFE_DEFINING goals - they should rarely change
- Only suggest changes when the event directly and significantly impacts the goal
- "complete" means the goal is fully achieved
- "abandon" means the character gives up or the goal becomes impossible
- "modify" means the goal's description changes but the core intent remains
- confidence should reflect how certain you are about the assessment
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5  # Lower temperature for more conservative assessments
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"Error in goal assessment: {e}")
            return {
                "should_change": False,
                "change_type": "none",
                "new_description": None,
                "new_progress": None,
                "justification": f"Error: {e}",
                "confidence": 0.0
            }
