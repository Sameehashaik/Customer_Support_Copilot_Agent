"""
Support Agent Core - Main customer support agent

Combines everything:
- PII filtering
- Intent classification
- Sentiment analysis
- Safety guardrails
- Instruction-based behavior
- Tool usage
- Conversation memory
"""

from typing import Dict, List, Optional
import logging
from pathlib import Path

from src.pii_filter import PIIFilter
from src.intent_classifier import IntentClassifier
from src.sentiment_analyzer import SentimentAnalyzer
from src.guardrails import ResponseGuardrails
from src.conversation_memory import ConversationMemory
from src.bedrock_client import BedrockClient
from src.cost_tracker import BedrockCostTracker

logger = logging.getLogger(__name__)

class SupportAgent:
    """
    Main customer support agent

    Uses instruction-based design - behavior from .md files!
    """

    def __init__(self, instructions_dir: str = 'instructions'):
        """Initialize support agent"""

        # Load instructions
        self.instructions = self._load_instructions(instructions_dir)

        # Initialize components
        self.pii_filter = PIIFilter()
        self.intent_classifier = IntentClassifier()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.guardrails = ResponseGuardrails()
        self.memory = ConversationMemory()

        # Bedrock client
        self.bedrock = BedrockClient()
        self.tracker = BedrockCostTracker()

        # Tools (will be set in Phase 6)
        self.tools = {}

        logger.info("Support Agent initialized")

    def _load_instructions(self, instructions_dir: str) -> str:
        """Load base + support agent instructions"""
        instructions_path = Path(instructions_dir)

        # Load base instructions
        base_path = instructions_path / 'base_instructions.md'
        if not base_path.exists():
            raise FileNotFoundError(f"Base instructions not found: {base_path}")

        with open(base_path, 'r') as f:
            base = f.read()

        # Load support agent instructions
        agent_path = instructions_path / 'support_agent_instructions.md'
        if not agent_path.exists():
            raise FileNotFoundError(f"Agent instructions not found: {agent_path}")

        with open(agent_path, 'r') as f:
            agent = f.read()

        # Combine
        combined = f"""{base}

---

# SUPPORT AGENT SPECIALIZED INSTRUCTIONS

{agent}"""

        logger.info(f"Loaded instructions: {len(combined)} characters")
        return combined

    def handle_message(self, customer_message: str) -> Dict:
        """
        Main entry point - handle customer message

        Process:
        1. Filter PII
        2. Classify intent
        3. Analyze sentiment
        4. Generate response
        5. Check guardrails
        6. Return safe response

        Returns:
            {
                'response': str,
                'intent': str,
                'sentiment': float,
                'escalated': bool,
                'cost': float,
                'safe': bool
            }
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing customer message...")

        # Step 1: Filter PII
        safe_message, pii_meta = self.pii_filter.safe_for_llm(customer_message)
        logger.info(f"PII detected: {pii_meta['pii_detected']}")

        # Step 2: Classify intent
        intent_result = self.intent_classifier.classify(safe_message)
        intent = intent_result['intent']
        logger.info(f"Intent: {intent} ({intent_result['confidence']:.2f})")

        # Step 3: Analyze sentiment
        sentiment_result = self.sentiment_analyzer.analyze(safe_message, intent)
        sentiment = sentiment_result['sentiment']
        sentiment_score = sentiment_result['score']
        should_escalate = sentiment_result['should_escalate']
        logger.info(f"Sentiment: {sentiment} ({sentiment_score:.2f})")

        # Step 4: Check if should escalate immediately
        if should_escalate:
            logger.info("Escalating due to sentiment")
            self.memory.mark_escalated(f"Negative sentiment ({sentiment_score:.2f})")
            return self._create_escalation_response(intent, sentiment_score)

        # Step 5: Add to conversation memory
        self.memory.add_message(
            'customer',
            customer_message,
            {
                'intent': intent,
                'sentiment': sentiment_score,
                'pii_detected': pii_meta['pii_detected']
            }
        )

        # Step 6: Generate response
        response = self._generate_response(safe_message, intent, sentiment_score)

        # Step 7: Check guardrails
        guardrail_result = self.guardrails.check_response(
            response=response,
            customer_message=safe_message,
            sentiment_score=sentiment_score,
            intent=intent
        )

        if not guardrail_result['safe']:
            logger.warning(f"Guardrails blocked response: {guardrail_result['issues']}")
            response = guardrail_result.get('modified_response', response)
            guardrail_result = self.guardrails.check_response(response)
            if not guardrail_result['safe']:
                response = self._create_safe_fallback_response()
                guardrail_result = {'safe': True}  # Fallback is always safe

        # Step 8: Add agent response to memory
        self.memory.add_message('agent', response, {})

        logger.info(f"{'='*60}\n")

        result = {
            'response': response,
            'intent': intent,
            'intent_confidence': intent_result['confidence'],
            'sentiment': sentiment,
            'sentiment_score': sentiment_score,
            'escalated': False,
            'pii_detected': pii_meta['pii_detected'],
            'safe': guardrail_result['safe'],
            'cost': self._calculate_session_cost()
        }
        result['needs_human_review'] = self._needs_review(result)
        return result

    def _generate_response(self, message: str, intent: str, sentiment: float) -> str:
        """Generate response using Claude"""

        # Build context
        conversation_context = self.memory.get_context_for_agent()

        user_message = f"""## Current Message
{message}

## Context
- Intent: {intent}
- Sentiment: {sentiment:.2f}

{conversation_context}

## Your Task
Write a direct response to the customer. Output ONLY the message that will be sent to the customer - nothing else. No reasoning, no strategy notes, no bullet points, no meta-commentary, no "Key considerations", no explanations of your approach. Just the customer-facing message.
"""

        try:
            result = self.bedrock.invoke(
                messages=[{"role": "user", "content": user_message}],
                system=self.instructions,
                max_tokens=500,
                temperature=0.7
            )

            self.tracker.track_call(
                agent_name="support_agent",
                input_tokens=result['usage']['input_tokens'],
                output_tokens=result['usage']['output_tokens'],
                description=f"Intent: {intent}"
            )

            return result['content']

        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return self._create_safe_fallback_response()

    def _create_escalation_response(self, intent: str, sentiment: float) -> Dict:
        """Create response for escalated conversation"""
        response = "I understand this is important to you. Let me connect you with one of our specialists who can help you right away. Please hold for just a moment."

        result = {
            'response': response,
            'intent': intent,
            'intent_confidence': 1.0,
            'sentiment': 'negative',
            'sentiment_score': sentiment,
            'escalated': True,
            'pii_detected': False,
            'safe': True,
            'cost': 0.0
        }
        result['needs_human_review'] = True  # Always review escalations
        return result

    def _needs_review(self, result: Dict) -> bool:
        """Determine if response needs human review before sending"""
        # Auto-escalated
        if result['escalated']:
            return True
        # Risky intents always need review
        if result['intent'] in ('refund_request', 'complaint'):
            return True
        # Negative sentiment
        if result['sentiment_score'] < 0.4:
            return True
        # Safety check failed
        if not result['safe']:
            return True
        # Low confidence only matters for non-trivial intents
        safe_intents = ('greeting', 'general_inquiry', 'order_status',
                        'shipping_question', 'product_question')
        if result['intent'] not in safe_intents and result['intent_confidence'] < 0.7:
            return True
        return False

    def _create_safe_fallback_response(self) -> str:
        """Safe fallback response if generation fails"""
        return "I apologize, but I'm having trouble processing your request. Let me connect you with a specialist who can help you better. Please hold for a moment."

    def _calculate_session_cost(self) -> float:
        """Calculate total session cost"""
        if self.tracker.session_costs:
            return sum(c['total_cost'] for c in self.tracker.session_costs)
        return 0.0

    def register_tools(self, tools: Dict):
        """Register tools for the agent to use"""
        self.tools = tools
        logger.info(f"Registered {len(tools)} tools: {list(tools.keys())}")

    def reset_conversation(self):
        """Reset conversation memory"""
        self.memory = ConversationMemory()
        logger.info("Conversation reset")
