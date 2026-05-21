"""
Dialogue Context System for UTAS Simulation

Prevents fake signals where NPCs forget conversations, lose topic continuity,
or don't reference previous statements.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from color_utils import Color


class DialogueContext:
    """Tracks a single conversation between two actors."""
    
    def __init__(self, actor1_name: str, actor2_name: str):
        self.actor1_name = actor1_name
        self.actor2_name = actor2_name
        self.conversation_history = []
        self.current_topic = None
        self.topics_discussed = []
        self.promises_made = []
        self.threats_made = []
        self.questions_asked = []
        self.information_shared = []
        self.emotional_tone = "neutral"
        self.started_at = datetime.now()
        self.last_exchange_at = datetime.now()
        self.turn_count = 0
    
    def add_exchange(
        self,
        speaker: str,
        statement: str,
        statement_type: str = "statement",
        topic: str = None,
        emotional_tone: str = None
    ):
        """Add a dialogue exchange to the conversation history."""
        exchange = {
            'speaker': speaker,
            'statement': statement,
            'type': statement_type,  # statement, question, threat, promise, etc.
            'topic': topic or self.current_topic,
            'emotional_tone': emotional_tone or self.emotional_tone,
            'timestamp': datetime.now(),
            'turn': self.turn_count
        }
        
        self.conversation_history.append(exchange)
        self.last_exchange_at = datetime.now()
        self.turn_count += 1
        
        # Update current topic if provided
        if topic and topic != self.current_topic:
            self.current_topic = topic
            if topic not in self.topics_discussed:
                self.topics_discussed.append(topic)
        
        # Track special statement types
        if statement_type == "promise":
            self.promises_made.append({
                'speaker': speaker,
                'promise': statement,
                'turn': self.turn_count
            })
        elif statement_type == "threat":
            self.threats_made.append({
                'speaker': speaker,
                'threat': statement,
                'turn': self.turn_count
            })
        elif statement_type == "question":
            self.questions_asked.append({
                'speaker': speaker,
                'question': statement,
                'turn': self.turn_count,
                'answered': False
            })
        elif statement_type == "information":
            self.information_shared.append({
                'speaker': speaker,
                'information': statement,
                'turn': self.turn_count
            })
        
        # Update emotional tone
        if emotional_tone:
            self.emotional_tone = emotional_tone
    
    def mark_question_answered(self, question_index: int):
        """Mark a question as answered."""
        if 0 <= question_index < len(self.questions_asked):
            self.questions_asked[question_index]['answered'] = True
    
    def get_unanswered_questions(self) -> List[Dict]:
        """Get list of unanswered questions."""
        return [q for q in self.questions_asked if not q['answered']]
    
    def get_recent_exchanges(self, count: int = 5) -> List[Dict]:
        """Get the most recent exchanges."""
        return self.conversation_history[-count:]
    
    def get_context_summary(self) -> str:
        """Get a summary of the conversation for LLM context."""
        if not self.conversation_history:
            return "No previous conversation."
        
        summary_parts = []
        
        # Recent exchanges
        recent = self.get_recent_exchanges(3)
        if recent:
            summary_parts.append("RECENT CONVERSATION:")
            for exchange in recent:
                summary_parts.append(f"  {exchange['speaker']}: {exchange['statement']}")
        
        # Current topic
        if self.current_topic:
            summary_parts.append(f"\nCURRENT TOPIC: {self.current_topic}")
        
        # Unanswered questions
        unanswered = self.get_unanswered_questions()
        if unanswered:
            summary_parts.append("\nUNANSWERED QUESTIONS:")
            for q in unanswered:
                summary_parts.append(f"  {q['speaker']} asked: {q['question']}")
        
        # Promises/threats
        if self.promises_made:
            summary_parts.append("\nPROMISES MADE:")
            for p in self.promises_made[-2:]:  # Last 2 promises
                summary_parts.append(f"  {p['speaker']}: {p['promise']}")
        
        if self.threats_made:
            summary_parts.append("\nTHREATS MADE:")
            for t in self.threats_made[-2:]:  # Last 2 threats
                summary_parts.append(f"  {t['speaker']}: {t['threat']}")
        
        # Emotional tone
        summary_parts.append(f"\nCONVERSATION TONE: {self.emotional_tone}")
        
        return "\n".join(summary_parts)


class DialogueContextSystem:
    """
    Manages dialogue contexts between all actor pairs.
    
    Features:
    - Tracks conversation history per actor pair
    - Maintains topic continuity
    - Tracks promises, threats, questions
    - Provides context for LLM prompts
    - Prevents NPCs from forgetting conversations
    """
    
    def __init__(self):
        self.conversations: Dict[str, DialogueContext] = {}
        self.global_dialogue_count = 0
    
    def _get_conversation_key(self, actor1_name: str, actor2_name: str) -> str:
        """Get unique key for conversation between two actors."""
        # Sort names to ensure same key regardless of order
        names = sorted([actor1_name, actor2_name])
        return f"{names[0]}_{names[1]}"
    
    def get_or_create_context(self, actor1_name: str, actor2_name: str) -> DialogueContext:
        """Get existing conversation context or create new one."""
        key = self._get_conversation_key(actor1_name, actor2_name)
        
        if key not in self.conversations:
            self.conversations[key] = DialogueContext(actor1_name, actor2_name)
        
        return self.conversations[key]
    
    def add_dialogue(
        self,
        speaker_name: str,
        listener_name: str,
        statement: str,
        statement_type: str = "statement",
        topic: str = None,
        emotional_tone: str = None
    ):
        """Add a dialogue exchange to the conversation."""
        context = self.get_or_create_context(speaker_name, listener_name)
        context.add_exchange(speaker_name, statement, statement_type, topic, emotional_tone)
        self.global_dialogue_count += 1
        
        # Display dialogue tracking
        print(f"{Color.INFO}💬 Dialogue tracked: {speaker_name} → {listener_name}{Color.RESET}")
        if topic:
            print(f"{Color.INFO}   Topic: {topic}{Color.RESET}")
    
    def get_dialogue_context(self, actor1_name: str, actor2_name: str) -> str:
        """Get dialogue context summary for LLM prompts."""
        context = self.get_or_create_context(actor1_name, actor2_name)
        return context.get_context_summary()
    
    def detect_statement_type(self, statement: str) -> str:
        """Detect the type of statement using heuristics."""
        statement_lower = statement.lower()
        
        # Detect questions
        if '?' in statement or any(word in statement_lower for word in ['what', 'where', 'when', 'why', 'who', 'how']):
            return "question"
        
        # Detect promises
        if any(word in statement_lower for word in ['promise', 'will', "i'll", 'swear', 'guarantee']):
            return "promise"
        
        # Detect threats
        if any(word in statement_lower for word in ['or else', 'better', 'regret', 'kill', 'hurt', 'destroy']):
            return "threat"
        
        # Detect information sharing
        if any(word in statement_lower for word in ['know', 'tell', 'inform', 'explain', 'because', 'saw', 'heard']):
            return "information"
        
        return "statement"
    
    def detect_topic(self, statement: str, current_topic: str = None) -> str:
        """Detect the topic of conversation using heuristics."""
        statement_lower = statement.lower()
        
        # Common topics
        topics = {
            'money': ['money', 'cash', 'dollars', 'pay', 'cost', 'price', 'buy', 'sell'],
            'violence': ['fight', 'kill', 'shoot', 'attack', 'hurt', 'weapon', 'gun'],
            'location': ['where', 'place', 'here', 'there', 'go', 'leave', 'stay'],
            'identity': ['who', 'name', 'you are', 'i am', 'called'],
            'help': ['help', 'assist', 'aid', 'support', 'save'],
            'information': ['know', 'tell', 'explain', 'information', 'secret'],
            'threat': ['or else', 'better', 'regret', 'warning'],
            'negotiation': ['deal', 'offer', 'trade', 'exchange', 'bargain']
        }
        
        for topic, keywords in topics.items():
            if any(keyword in statement_lower for keyword in keywords):
                return topic
        
        # If no topic detected, keep current topic
        return current_topic or "general"
    
    def detect_emotional_tone(self, statement: str) -> str:
        """Detect emotional tone of statement."""
        statement_lower = statement.lower()
        
        # Aggressive
        if any(word in statement_lower for word in ['kill', 'die', 'hate', 'damn', 'hell', '!']):
            return "aggressive"
        
        # Fearful
        if any(word in statement_lower for word in ['please', 'mercy', 'scared', 'afraid', 'help']):
            return "fearful"
        
        # Friendly
        if any(word in statement_lower for word in ['friend', 'thanks', 'appreciate', 'glad', 'happy']):
            return "friendly"
        
        # Suspicious
        if any(word in statement_lower for word in ['why', 'suspicious', 'trust', 'believe', 'liar']):
            return "suspicious"
        
        return "neutral"
    
    def process_user_dialogue(
        self,
        user_input: str,
        speaker_name: str,
        listener_name: str
    ) -> Dict[str, Any]:
        """
        Process user dialogue input and extract metadata.
        
        Returns:
            Dict with statement_type, topic, emotional_tone, and context
        """
        # Get current context
        context = self.get_or_create_context(speaker_name, listener_name)
        
        # Detect metadata
        statement_type = self.detect_statement_type(user_input)
        topic = self.detect_topic(user_input, context.current_topic)
        emotional_tone = self.detect_emotional_tone(user_input)
        
        # Add to conversation
        self.add_dialogue(
            speaker_name=speaker_name,
            listener_name=listener_name,
            statement=user_input,
            statement_type=statement_type,
            topic=topic,
            emotional_tone=emotional_tone
        )
        
        return {
            'statement_type': statement_type,
            'topic': topic,
            'emotional_tone': emotional_tone,
            'context_summary': context.get_context_summary(),
            'unanswered_questions': context.get_unanswered_questions(),
            'promises_made': context.promises_made,
            'threats_made': context.threats_made
        }
    
    def has_conversation_history(self, actor1_name: str, actor2_name: str) -> bool:
        """Check if two actors have conversation history."""
        key = self._get_conversation_key(actor1_name, actor2_name)
        return key in self.conversations and len(self.conversations[key].conversation_history) > 0
    
    def get_conversation_stats(self, actor1_name: str, actor2_name: str) -> Dict[str, Any]:
        """Get statistics about a conversation."""
        if not self.has_conversation_history(actor1_name, actor2_name):
            return {
                'exists': False,
                'exchange_count': 0
            }
        
        context = self.get_or_create_context(actor1_name, actor2_name)
        
        return {
            'exists': True,
            'exchange_count': len(context.conversation_history),
            'topics_discussed': context.topics_discussed,
            'current_topic': context.current_topic,
            'promises_count': len(context.promises_made),
            'threats_count': len(context.threats_made),
            'unanswered_questions': len(context.get_unanswered_questions()),
            'emotional_tone': context.emotional_tone,
            'duration_minutes': (datetime.now() - context.started_at).total_seconds() / 60
        }
    
    def display_conversation_summary(self, actor1_name: str, actor2_name: str):
        """Display a summary of the conversation."""
        if not self.has_conversation_history(actor1_name, actor2_name):
            print(f"{Color.INFO}No conversation history between {actor1_name} and {actor2_name}{Color.RESET}")
            return
        
        context = self.get_or_create_context(actor1_name, actor2_name)
        stats = self.get_conversation_stats(actor1_name, actor2_name)
        
        print(f"\n{Color.INFO}{'='*80}{Color.RESET}")
        print(f"{Color.INFO}💬 CONVERSATION SUMMARY: {actor1_name} ↔ {actor2_name}{Color.RESET}")
        print(f"{Color.INFO}{'='*80}{Color.RESET}")
        print(f"{Color.SYSTEM}Exchanges: {stats['exchange_count']}{Color.RESET}")
        print(f"{Color.SYSTEM}Current Topic: {stats['current_topic']}{Color.RESET}")
        print(f"{Color.SYSTEM}Emotional Tone: {stats['emotional_tone']}{Color.RESET}")
        
        if stats['unanswered_questions'] > 0:
            print(f"{Color.WARNING}Unanswered Questions: {stats['unanswered_questions']}{Color.RESET}")
        
        if stats['promises_count'] > 0:
            print(f"{Color.SUCCESS}Promises Made: {stats['promises_count']}{Color.RESET}")
        
        if stats['threats_count'] > 0:
            print(f"{Color.ERROR}Threats Made: {stats['threats_count']}{Color.RESET}")
        
        print(f"\n{Color.NARRATIVE}Recent Exchanges:{Color.RESET}")
        for exchange in context.get_recent_exchanges(3):
            print(f"{Color.NARRATIVE}  {exchange['speaker']}: {exchange['statement'][:80]}...{Color.RESET}")
        
        print(f"{Color.INFO}{'='*80}{Color.RESET}\n")
    
    def clear_conversation(self, actor1_name: str, actor2_name: str):
        """Clear conversation history between two actors."""
        key = self._get_conversation_key(actor1_name, actor2_name)
        if key in self.conversations:
            del self.conversations[key]
            print(f"{Color.WARNING}Cleared conversation between {actor1_name} and {actor2_name}{Color.RESET}")


# Global instance
dialogue_context_system = DialogueContextSystem()
