"""
Escalation Tool - Transfer to human agent

In production, integrates with ticketing system (Zendesk, Intercom, etc.)
"""

from typing import Dict
from datetime import datetime
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class EscalationTool:
    """Escalate conversation to human agent"""

    PRIORITY_LEVELS = ['low', 'medium', 'high', 'urgent']

    def __init__(self, escalation_log: str = 'escalations.json'):
        """Initialize escalation tool"""
        self.escalation_log = Path(escalation_log)
        self.escalations = []

        if self.escalation_log.exists():
            with open(self.escalation_log, 'r') as f:
                self.escalations = json.load(f)

    def create_escalation(
        self,
        reason: str,
        priority: str = 'medium',
        customer_message: str = '',
        intent: str = '',
        sentiment_score: float = 0.5,
        conversation_summary: Dict = None
    ) -> Dict:
        """
        Create escalation to human agent

        Args:
            reason: Why escalating
            priority: low/medium/high/urgent
            customer_message: Latest customer message
            intent: Detected intent
            sentiment_score: Sentiment score
            conversation_summary: Full conversation context

        Returns:
            Escalation ticket details
        """
        if priority not in self.PRIORITY_LEVELS:
            priority = 'medium'

        escalation = {
            'escalation_id': f'ESC{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'timestamp': datetime.now().isoformat(),
            'reason': reason,
            'priority': priority,
            'customer_message': customer_message,
            'intent': intent,
            'sentiment_score': sentiment_score,
            'conversation_summary': conversation_summary or {},
            'status': 'pending',
            'assigned_agent': None
        }

        self.escalations.append(escalation)
        self._save_escalations()

        logger.info(f"Created escalation: {escalation['escalation_id']} (Priority: {priority})")

        return escalation

    def _save_escalations(self):
        """Save escalations to file"""
        with open(self.escalation_log, 'w') as f:
            json.dump(self.escalations, f, indent=2)

    def get_escalation_message(self, escalation: Dict) -> str:
        """Generate message to show customer"""
        priority_messages = {
            'urgent': "I'm connecting you with a senior specialist right away. They'll be with you in under 5 minutes.",
            'high': "Let me connect you with a specialist. They'll be with you shortly - typically within 15 minutes.",
            'medium': "I'm going to connect you with one of our specialists who can help you better. They'll reach out within the hour.",
            'low': "I'll create a ticket for our specialist team. They'll follow up with you within 4 hours."
        }

        return priority_messages.get(escalation['priority'], priority_messages['medium'])

    def get_pending_escalations(self, priority: str = None) -> list:
        """Get pending escalations, optionally filtered by priority"""
        pending = [e for e in self.escalations if e['status'] == 'pending']

        if priority:
            pending = [e for e in pending if e['priority'] == priority]

        return sorted(pending, key=lambda x: x['timestamp'], reverse=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    tool = EscalationTool()

    # Test escalation
    escalation = tool.create_escalation(
        reason="Very negative sentiment",
        priority="high",
        customer_message="This is terrible service!",
        intent="complaint",
        sentiment_score=0.15
    )

    print("\nEscalation Created:")
    print(json.dumps(escalation, indent=2))

    print("\nCustomer Message:")
    print(tool.get_escalation_message(escalation))
