"""
Intent Classification - Determine what customer wants

Intents:
- order_status: "Where's my order?"
- refund_request: "I want my money back"
- product_question: "Does this come in blue?"
- shipping_question: "How long to ship?"
- account_help: "I forgot my password"
- complaint: "This is terrible service"
- technical_issue: "The app keeps crashing"
- general_inquiry: Everything else
"""

from typing import Dict
import json
import logging
from src.cost_tracker import BedrockCostTracker

try:
    from src.bedrock_client import BedrockClient
except ImportError:
    from bedrock_client import BedrockClient

logger = logging.getLogger(__name__)

class IntentClassifier:
    """Classify customer intent using few-shot prompting"""

    INTENTS = [
        "order_status",
        "refund_request",
        "product_question",
        "shipping_question",
        "account_help",
        "technical_issue",
        "complaint",
        "general_inquiry"
    ]

    def __init__(self):
        self.bedrock = BedrockClient()
        self.tracker = BedrockCostTracker()

    def classify(self, message: str) -> Dict:
        """
        Classify customer message intent

        Returns:
            {
                'intent': str,
                'confidence': float,
                'reasoning': str
            }
        """
        system_prompt = self._build_system_prompt()
        user_message = f"Classify this message:\n\n{message}"

        try:
            result = self.bedrock.invoke(
                messages=[{"role": "user", "content": user_message}],
                system=system_prompt,
                max_tokens=200,
                temperature=0.0  # Deterministic for classification
            )

            # Track cost
            self.tracker.track_call(
                agent_name="intent_classifier",
                input_tokens=result['usage']['input_tokens'],
                output_tokens=result['usage']['output_tokens'],
                description="Intent classification"
            )

            # Parse response
            classification = self._parse_response(result['content'])

            logger.info(f"Intent: {classification['intent']} ({classification['confidence']:.2f})")
            return classification

        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            return {
                'intent': 'general_inquiry',
                'confidence': 0.0,
                'reasoning': f"Classification failed: {str(e)}"
            }

    def _build_system_prompt(self) -> str:
        """Build few-shot system prompt"""
        return f"""You are an intent classification system for customer support.

Available intents: {', '.join(self.INTENTS)}

Examples:

Message: "Where is my order #12345?"
Intent: order_status
Confidence: 0.95
Reasoning: Customer asking about order location

Message: "I want a refund!"
Intent: refund_request
Confidence: 0.98
Reasoning: Explicit refund request

Message: "Does this come in blue?"
Intent: product_question
Confidence: 0.90
Reasoning: Question about product features

Message: "How long does shipping take?"
Intent: shipping_question
Confidence: 0.95
Reasoning: Question about shipping timeframe

Message: "I can't log in"
Intent: account_help
Confidence: 0.92
Reasoning: Account access issue

Message: "Your service is terrible!"
Intent: complaint
Confidence: 0.88
Reasoning: Expressing dissatisfaction

Respond ONLY with JSON:
{{
  "intent": "...",
  "confidence": 0.XX,
  "reasoning": "..."
}}"""

    def _parse_response(self, response: str) -> Dict:
        """Parse LLM response to extract intent"""
        try:
            # Try to parse as JSON
            response = response.strip()
            if response.startswith('```'):
                response = response.split('```')[1]
                if response.startswith('json'):
                    response = response[4:]

            data = json.loads(response)

            return {
                'intent': data.get('intent', 'general_inquiry'),
                'confidence': float(data.get('confidence', 0.5)),
                'reasoning': data.get('reasoning', '')
            }
        except Exception as e:
            logger.error(f"Failed to parse intent response: {e}")
            return {
                'intent': 'general_inquiry',
                'confidence': 0.5,
                'reasoning': 'Parse error'
            }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    classifier = IntentClassifier()

    test_messages = [
        "Where's my order?",
        "I want a refund",
        "Does this come in red?",
        "This is the worst service ever!",
    ]

    for msg in test_messages:
        result = classifier.classify(msg)
        print(f"\nMessage: {msg}")
        print(f"Intent: {result['intent']} ({result['confidence']:.2f})")
        print(f"Reasoning: {result['reasoning']}")
