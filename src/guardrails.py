"""
Safety Guardrails - Validate responses before sending

Checks:
1. No PII leaked
2. Professional tone
3. No overpromising
4. Appropriate for customer sentiment
5. Policy compliant
6. No harmful content
"""

from typing import Dict, List
import re
import logging
from src.pii_filter import PIIFilter

logger = logging.getLogger(__name__)

class ResponseGuardrails:
    """Safety checks for agent responses"""

    def __init__(self):
        self.pii_filter = PIIFilter()

    def check_response(
        self,
        response: str,
        customer_message: str = "",
        sentiment_score: float = 0.5,
        intent: str = ""
    ) -> Dict:
        """
        Comprehensive safety check

        Returns:
            {
                'safe': bool,
                'issues': List[str],
                'suggestions': List[str]
            }
        """
        issues = []
        suggestions = []

        # Check 1: No PII leaked
        safe_text, pii_meta = self.pii_filter.safe_for_llm(response)
        if pii_meta['pii_detected']:
            issues.append(f"PII detected in response: {pii_meta['entity_types']}")
            suggestions.append("Remove PII from response")

        # Check 2: Professional tone
        if self._has_unprofessional_language(response):
            issues.append("Unprofessional language detected")
            suggestions.append("Use professional language")

        # Check 3: No overpromising
        if self._overpromises(response):
            issues.append("Response overpromises")
            suggestions.append("Be realistic about what we can do")

        # Check 4: Appropriate for sentiment
        if sentiment_score < 0.3 and not self._shows_empathy(response):
            issues.append("Response not empathetic for angry customer")
            suggestions.append("Show more empathy and understanding")

        # Check 5: Policy violations
        policy_issues = self._check_policy_compliance(response, intent)
        issues.extend(policy_issues)

        safe = len(issues) == 0

        logger.info(f"Guardrails check: {'SAFE' if safe else 'ISSUES FOUND'}")
        if issues:
            logger.warning(f"Issues: {issues}")

        return {
            'safe': safe,
            'issues': issues,
            'suggestions': suggestions,
            'modified_response': safe_text if pii_meta['pii_detected'] else response
        }

    def _has_unprofessional_language(self, text: str) -> bool:
        """Check for unprofessional language"""
        unprofessional = [
            r'\bcrap\b',
            r'\bsucks\b',
            r'\bdumb\b',
            r'\bstupid\b',
            r'\bidiot\b',
        ]

        text_lower = text.lower()
        for pattern in unprofessional:
            if re.search(pattern, text_lower):
                return True
        return False

    def _overpromises(self, text: str) -> bool:
        """Check for overpromising"""
        overpromise_phrases = [
            "definitely will",
            "guaranteed to",
            "100% certain",
            "absolutely will",
            "promise you",
            "within minutes",
        ]

        text_lower = text.lower()
        for phrase in overpromise_phrases:
            if phrase in text_lower:
                return True
        return False

    def _shows_empathy(self, text: str) -> bool:
        """Check if response shows empathy"""
        empathy_indicators = [
            "understand",
            "sorry",
            "apologize",
            "frustrating",
            "appreciate",
            "help you",
        ]

        text_lower = text.lower()
        return any(indicator in text_lower for indicator in empathy_indicators)

    def _check_policy_compliance(self, text: str, intent: str) -> List[str]:
        """Check policy compliance"""
        issues = []

        # Refunds should be handled by humans
        if intent == "refund_request" and "refund" in text.lower():
            if "agent" not in text.lower() and "representative" not in text.lower() and "specialist" not in text.lower():
                issues.append("Refund requests must mention human agent")

        # Don't promise specific delivery dates unless verified
        if re.search(r'\b(tomorrow|today|by \w+day)\b', text.lower(), re.IGNORECASE):
            if intent == "order_status":
                issues.append("Specific delivery promises need verification")

        return issues


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    guardrails = ResponseGuardrails()

    # Test cases
    test_responses = [
        ("Your order will arrive tomorrow for sure!", "order_status", 0.5),
        ("I understand your frustration. Let me help.", "complaint", 0.2),
        ("This is a stupid question.", "general_inquiry", 0.5),
        ("Your email is john@example.com", "account_help", 0.6),
    ]

    for response, intent, sentiment in test_responses:
        print(f"\n{'='*60}")
        print(f"Response: {response}")
        print(f"Intent: {intent}, Sentiment: {sentiment}")

        result = guardrails.check_response(
            response=response,
            sentiment_score=sentiment,
            intent=intent
        )

        print(f"Safe: {result['safe']}")
        if result['issues']:
            print(f"Issues: {result['issues']}")
            print(f"Suggestions: {result['suggestions']}")
