"""
Conversation Memory - Track conversation history for context

Enables multi-turn conversations where agent remembers previous messages
"""

from typing import List, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ConversationMemory:
    """Manage conversation history and context"""

    def __init__(self, max_history: int = 10):
        """
        Initialize conversation memory

        Args:
            max_history: Maximum number of turns to remember
        """
        self.max_history = max_history
        self.messages: List[Dict] = []
        self.metadata: Dict = {
            'start_time': datetime.now().isoformat(),
            'turn_count': 0,
            'escalated': False,
            'intents': [],
            'sentiments': []
        }

    def add_message(self, role: str, content: str, metadata: Dict = None):
        """
        Add message to history

        Args:
            role: 'customer' or 'agent'
            content: Message content
            metadata: Optional metadata (intent, sentiment, etc.)
        """
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }

        self.messages.append(message)
        self.metadata['turn_count'] += 1

        # Track intents and sentiments
        if metadata:
            if 'intent' in metadata:
                self.metadata['intents'].append(metadata['intent'])
            if 'sentiment' in metadata:
                self.metadata['sentiments'].append(metadata['sentiment'])

        # Trim history if too long
        if len(self.messages) > self.max_history * 2:  # *2 for customer + agent
            self.messages = self.messages[-self.max_history * 2:]

        logger.info(f"Added {role} message (turn {self.metadata['turn_count']})")

    def get_history(self, last_n: int = None) -> List[Dict]:
        """
        Get conversation history

        Args:
            last_n: Get last N messages (None = all)

        Returns:
            List of message dictionaries
        """
        if last_n:
            return self.messages[-last_n:]
        return self.messages

    def get_context_for_agent(self) -> str:
        """
        Format conversation history for agent context

        Returns:
            Formatted string with conversation history
        """
        if not self.messages:
            return "No previous conversation."

        context_parts = ["## Conversation History\n"]

        for msg in self.messages:
            role = "Customer" if msg['role'] == 'customer' else "Agent"
            context_parts.append(f"**{role}:** {msg['content']}\n")

        return "\n".join(context_parts)

    def mark_escalated(self, reason: str):
        """Mark conversation as escalated"""
        self.metadata['escalated'] = True
        self.metadata['escalation_reason'] = reason
        self.metadata['escalation_time'] = datetime.now().isoformat()
        logger.info(f"Conversation escalated: {reason}")

    def get_summary(self) -> Dict:
        """Get conversation summary"""
        return {
            'turn_count': self.metadata['turn_count'],
            'duration_minutes': self._calculate_duration(),
            'escalated': self.metadata['escalated'],
            'primary_intent': self._get_primary_intent(),
            'avg_sentiment': self._get_avg_sentiment()
        }

    def _calculate_duration(self) -> float:
        """Calculate conversation duration in minutes"""
        if not self.messages:
            return 0.0

        start = datetime.fromisoformat(self.metadata['start_time'])
        end = datetime.now()
        duration = (end - start).total_seconds() / 60
        return round(duration, 2)

    def _get_primary_intent(self) -> str:
        """Get most common intent"""
        if not self.metadata['intents']:
            return 'unknown'

        from collections import Counter
        intent_counts = Counter(self.metadata['intents'])
        return intent_counts.most_common(1)[0][0]

    def _get_avg_sentiment(self) -> float:
        """Get average sentiment score"""
        sentiments = self.metadata['sentiments']
        if not sentiments:
            return 0.5

        return round(sum(sentiments) / len(sentiments), 2)
