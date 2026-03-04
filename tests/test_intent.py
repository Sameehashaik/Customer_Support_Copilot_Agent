"""Test intent classification"""

from src.intent_classifier import IntentClassifier

def test_intent_classification():
    """Test various intents"""
    classifier = IntentClassifier()

    test_cases = [
        ("Where's my order #12345?", "order_status"),
        ("I want a refund", "refund_request"),
        ("Does this come in blue?", "product_question"),
        ("How long to ship?", "shipping_question"),
    ]

    for message, expected_intent in test_cases:
        result = classifier.classify(message)
        print(f"\nMessage: {message}")
        print(f"Expected: {expected_intent}")
        print(f"Got: {result['intent']} ({result['confidence']:.2f})")
        print(f"Reasoning: {result['reasoning']}")

    print("\n  Intent classification tested")

if __name__ == "__main__":
    test_intent_classification()
