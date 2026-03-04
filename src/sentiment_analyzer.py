"""
Sentiment Analysis - Detect customer emotion

Sentiments:
- very_positive (0.8-1.0): "Thank you so much!"
- positive (0.6-0.8): "Good service"
- neutral (0.4-0.6): "Where is my order?"
- negative (0.2-0.4): "This is frustrating"
- very_negative (0.0-0.2): "Worst service ever!"

Escalation triggers:
- very_negative -> Immediate escalation
- negative + refund_request -> Escalate
"""

from typing import Dict
import json
import logging
from src.bedrock_client import BedrockClient
from src.cost_tracker import BedrockCostTracker

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """Analyze customer sentiment for escalation decisions"""

    def __init__(self):
        self.bedrock = BedrockClient()
        self.tracker = BedrockCostTracker()

    def analyze(self, message: str, intent: str = None) -> Dict:
        """
        Analyze sentiment

        Returns:
            {
                'sentiment': str,
                'score': float,
                'should_escalate': bool,
                'escalation_reason': str
            }
        """
        system_prompt = self._build_system_prompt()
        user_message = f"Analyze sentiment:\n\n{message}"

        try:
            result = self.bedrock.invoke(
                messages=[{"role": "user", "content": user_message}],
                system=system_prompt,
                max_tokens=200,
                temperature=0.0
            )

            self.tracker.track_call(
                agent_name="sentiment_analyzer",
                input_tokens=result['usage']['input_tokens'],
                output_tokens=result['usage']['output_tokens'],
                description="Sentiment analysis"
            )

            analysis = self._parse_response(result['content'])

            # Add escalation logic
            analysis['should_escalate'] = self._should_escalate(
                analysis['score'],
                analysis['sentiment'],
                intent
            )

            logger.info(f"Sentiment: {analysis['sentiment']} ({analysis['score']:.2f}), Escalate: {analysis['should_escalate']}")
            return analysis

        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {
                'sentiment': 'neutral',
                'score': 0.5,
                'should_escalate': False,
                'escalation_reason': ''
            }

    def _build_system_prompt(self) -> str:
        """Build sentiment analysis prompt"""
        return """You are a sentiment analysis system for customer support.

Analyze the emotional tone of customer messages.

Sentiment scale:
- very_positive (0.8-1.0): Happy, grateful, satisfied
- positive (0.6-0.8): Pleased, content
- neutral (0.4-0.6): Matter-of-fact, informational
- negative (0.2-0.4): Frustrated, disappointed
- very_negative (0.0-0.2): Angry, upset, threatening

Examples:

Message: "Thank you so much for the help!"
Sentiment: very_positive
Score: 0.95

Message: "Where is my order?"
Sentiment: neutral
Score: 0.5

Message: "This is getting frustrating"
Sentiment: negative
Score: 0.3

Message: "Worst service ever! I'm done!"
Sentiment: very_negative
Score: 0.1

Respond ONLY with JSON:
{
  "sentiment": "...",
  "score": 0.XX
}"""

    def _parse_response(self, response: str) -> Dict:
        """Parse sentiment response"""
        try:
            response = response.strip()
            if response.startswith('```'):
                response = response.split('```')[1]
                if response.startswith('json'):
                    response = response[4:]

            data = json.loads(response)

            return {
                'sentiment': data.get('sentiment', 'neutral'),
                'score': float(data.get('score', 0.5)),
                'should_escalate': False,
                'escalation_reason': ''
            }
        except Exception as e:
            logger.error(f"Failed to parse sentiment: {e}")
            return {
                'sentiment': 'neutral',
                'score': 0.5,
                'should_escalate': False,
                'escalation_reason': ''
            }

    def _should_escalate(self, score: float, sentiment: str, intent: str = None) -> bool:
        """Determine if should escalate to human"""
        reasons = []

        # Very negative sentiment -> always escalate
        if score < 0.3:
            reasons.append("Very negative sentiment detected")

        # Negative + refund request -> escalate
        if score < 0.5 and intent == 'refund_request':
            reasons.append("Negative sentiment with refund request")

        # Complaint with negative sentiment -> escalate
        if intent == 'complaint' and score < 0.5:
            reasons.append("Complaint with negative sentiment")

        return len(reasons) > 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    analyzer = SentimentAnalyzer()

    test_messages = [
        "Thank you so much!",
        "Where is my order?",
        "This is getting frustrating",
        "Worst service ever! I want a refund!",
    ]

    for msg in test_messages:
        result = analyzer.analyze(msg)
        print(f"\nMessage: {msg}")
        print(f"Sentiment: {result['sentiment']} ({result['score']:.2f})")
        print(f"Escalate: {result['should_escalate']}")
