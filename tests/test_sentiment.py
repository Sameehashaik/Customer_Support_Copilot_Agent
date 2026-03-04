"""Test sentiment analysis"""

from src.sentiment_analyzer import SentimentAnalyzer

def test_sentiment_analysis():
    """Test various sentiments"""
    analyzer = SentimentAnalyzer()

    test_cases = [
        ("Thank you so much!", "positive", False),
        ("Where is my order?", "neutral", False),
        ("This is frustrating", "negative", False),
        ("Worst service ever!", "very_negative", True),
    ]

    for message, expected_sentiment_type, should_escalate in test_cases:
        result = analyzer.analyze(message)
        print(f"\nMessage: {message}")
        print(f"Sentiment: {result['sentiment']} ({result['score']:.2f})")
        print(f"Should escalate: {result['should_escalate']}")

    print("\n  Sentiment analysis tested")

if __name__ == "__main__":
    test_sentiment_analysis()
