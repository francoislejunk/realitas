"""
Goal Progress Tracker - Dynamic LLM-based progress evaluation

Evaluates whether actions/events advance actor goals and updates progress accordingly.
Progress reaches 100% ONLY when goal is fully accomplished.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import json
from openrouter_config import OpenRouterConfig
from goal_task_system import Goal, GoalImportance


@dataclass
class ProgressEvaluation:
    """Result of evaluating goal progress"""
    goal_advanced: bool
    progress_increment: float  # 0.0 to 1.0
    reasoning: str
    goal_completed: bool  # True only if goal is 100% accomplished
    completion_narrative: Optional[str] = None  # Special narrative for completion


class GoalProgressTracker:
    """
    Tracks and updates goal progress based on actions and events.
    Uses LLM to determine if actions advance goals.
    """
    
    def __init__(self):
        self.client = OpenRouterConfig.create_role_client("coordination")  # Use coordination role
        self.model = OpenRouterConfig.get_model_for_role("coordination")
        
    def evaluate_progress(
        self,
        goal: Goal,
        current_progress: float,
        action_description: str,
        action_result: str,
        narrative_context: str = ""
    ) -> ProgressEvaluation:
        """
        Evaluate if an action/event advances a goal.
        
        Args:
            goal: The goal to evaluate
            current_progress: Current progress (0.0 to 1.0)
            action_description: What the actor did
            action_result: Outcome of the action
            narrative_context: Recent narrative for context
            
        Returns:
            ProgressEvaluation with increment and reasoning
        """
        
        prompt = f"""You are evaluating whether an action advances an actor's goal.

GOAL: {goal.description}
IMPORTANCE: {goal.importance.value}
CURRENT PROGRESS: {int(current_progress * 100)}%

ACTION TAKEN: {action_description}
ACTION RESULT: {action_result}

RECENT CONTEXT:
{narrative_context[:500] if narrative_context else "No recent context"}

EVALUATION RULES:
1. Progress increments should be SMALL (typically 0.01 to 0.05, or 1% to 5%)
2. DIRECT advancement → 0.02 to 0.05 (2% to 5%)
3. INDIRECT/preparatory advancement → 0.005 to 0.01 (0.5% to 1%)
4. NO advancement (completely unrelated) → 0.0 (0%)
5. Goal is COMPLETE (100%) ONLY when fully accomplished, not just "close"
6. If action is even SLIGHTLY relevant, give at least 0.005 (0.5%)

CRITICAL: If goal_advanced is TRUE, progress_increment MUST be > 0!

RESPOND IN JSON:
{{
    "goal_advanced": true/false,
    "progress_increment": 0.0 to 0.05,
    "reasoning": "brief explanation",
    "goal_completed": true/false,
    "completion_narrative": "special narrative if goal completed, else null"
}}

Examples:
- Found a clue for fraud case → {{"goal_advanced": true, "progress_increment": 0.02}}
- Interviewed key witness → {{"goal_advanced": true, "progress_increment": 0.05}}
- Met someone who might help later → {{"goal_advanced": true, "progress_increment": 0.005}}
- Bought coffee (unrelated) → {{"goal_advanced": false, "progress_increment": 0.0}}
- Presented case and won → {{"goal_advanced": true, "goal_completed": true}}

Evaluate now:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=500,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            result = json.loads(content)
            
            # Validate and clamp values
            goal_advanced = bool(result.get("goal_advanced", False))
            progress_increment = float(result.get("progress_increment", 0.0))
            progress_increment = max(0.0, min(0.05, progress_increment))  # Clamp to 0-5%
            
            reasoning = str(result.get("reasoning", "No reasoning provided"))
            goal_completed = bool(result.get("goal_completed", False))
            completion_narrative = result.get("completion_narrative")
            
            # If goal completed, set progress to exactly 1.0
            if goal_completed:
                progress_increment = 1.0 - current_progress
            
            # Don't allow progress beyond 1.0
            if current_progress + progress_increment > 1.0:
                progress_increment = 1.0 - current_progress
                goal_completed = True
            
            return ProgressEvaluation(
                goal_advanced=goal_advanced,
                progress_increment=progress_increment,
                reasoning=reasoning,
                goal_completed=goal_completed,
                completion_narrative=completion_narrative
            )
            
        except Exception as e:
            # Graceful fallback - no progress
            return ProgressEvaluation(
                goal_advanced=False,
                progress_increment=0.0,
                reasoning=f"Evaluation failed: {e}",
                goal_completed=False,
                completion_narrative=None
            )
    
    def should_evaluate_progress(
        self,
        action_description: str,
        success_level: int
    ) -> bool:
        """
        Determine if this action is significant enough to evaluate for progress.
        
        Args:
            action_description: What the actor did
            success_level: 1-5 success level
            
        Returns:
            True if action should be evaluated
        """
        # Skip trivial actions
        trivial_keywords = [
            'look', 'examine', 'observe', 'wait', 'stand', 'sit',
            'walk around', 'do nothing', 'rest', 'think'
        ]
        
        action_lower = action_description.lower()
        if any(keyword in action_lower for keyword in trivial_keywords):
            return False
        
        # Skip failed actions (success level 1)
        if success_level <= 1:
            return False
        
        # Evaluate all other actions
        return True


def process_goal_progress(
    tracker: GoalProgressTracker,
    actor,
    action_description: str,
    action_result: str,
    success_level: int,
    narrative_context: str = ""
) -> Optional[Dict[str, Any]]:
    """
    Process goal progress for an actor after an action.
    
    Args:
        tracker: GoalProgressTracker instance
        actor: Actor with goal_task_manager
        action_description: What the actor did
        action_result: Outcome narrative
        success_level: 1-5 success level
        narrative_context: Recent narrative
        
    Returns:
        Dict with progress update info, or None if no progress
    """
    # Check if actor has goals
    if not hasattr(actor.sheet, 'goal_task_manager'):
        return None
    
    if not actor.sheet.goal_task_manager.goals:
        return None
    
    # Check if action is significant enough
    if not tracker.should_evaluate_progress(action_description, success_level):
        return None
    
    # Evaluate progress for primary goal (index 0)
    goal = actor.sheet.goal_task_manager.goals[0]
    current_progress = goal.progress
    
    # Don't evaluate if goal already complete
    if current_progress >= 1.0:
        return None
    
    # Evaluate with LLM
    evaluation = tracker.evaluate_progress(
        goal=goal,
        current_progress=current_progress,
        action_description=action_description,
        action_result=action_result,
        narrative_context=narrative_context
    )
    
    # Update progress if advanced
    # CRITICAL: Both conditions must be true - goal_advanced AND increment > 0
    # If LLM says goal_advanced=True but gives 0 increment, that's a contradiction - ignore it
    if evaluation.goal_advanced and evaluation.progress_increment > 0.0:
        new_progress = current_progress + evaluation.progress_increment
        actor.sheet.update_goal_progress(0, new_progress)
        
        return {
            "goal_advanced": True,
            "old_progress": current_progress,
            "new_progress": new_progress,
            "increment": evaluation.progress_increment,
            "reasoning": evaluation.reasoning,
            "goal_completed": evaluation.goal_completed,
            "completion_narrative": evaluation.completion_narrative
        }
    
    # If goal_advanced=True but increment=0, log the contradiction
    if evaluation.goal_advanced and evaluation.progress_increment == 0.0:
        import logging
        logging.warning(f"LLM contradiction: goal_advanced=True but progress_increment=0.0. Reasoning: {evaluation.reasoning}")
    
    return None


def display_goal_progress_update(progress_info: Dict[str, Any], actor_name: str):
    """Display goal progress update to user"""
    from color_utils import Color
    
    old_pct = int(progress_info["old_progress"] * 100)
    new_pct = int(progress_info["new_progress"] * 100)
    increment_pct = int(progress_info["increment"] * 100)
    
    if progress_info["goal_completed"]:
        print(f"\n{Color.SUCCESS}{'='*60}{Color.RESET}")
        print(f"{Color.SUCCESS}🎉 GOAL COMPLETED! 🎉{Color.RESET}")
        print(f"{Color.SUCCESS}{'='*60}{Color.RESET}")
        
        if progress_info["completion_narrative"]:
            print(f"\n{Color.NARRATIVE}{progress_info['completion_narrative']}{Color.RESET}")
        
        print(f"\n{Color.INFO}✓ {actor_name}'s goal has been accomplished!{Color.RESET}")
        print(f"{Color.INFO}Progress: {old_pct}% → 100%{Color.RESET}")
        print(f"{Color.SUCCESS}{'='*60}{Color.RESET}\n")
    else:
        print(f"\n{Color.INFO}📈 Goal Progress: {old_pct}% → {new_pct}% (+{increment_pct}%){Color.RESET}")
        print(f"{Color.SYSTEM}Reason: {progress_info['reasoning']}{Color.RESET}")
