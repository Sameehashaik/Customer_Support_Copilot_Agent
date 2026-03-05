"""Test support agent"""

from src.agent_core import SupportAgent
import logging

logging.basicConfig(level=logging.INFO)

def test_agent_initialization():
    """Test agent can be created"""
    agent = SupportAgent()
    assert agent.instructions is not None
    assert len(agent.instructions) > 0
    print("  Agent initialized successfully")

def test_handle_simple_message():
    """Test handling simple message"""
    agent = SupportAgent()

    message = "Where is my order?"
    result = agent.handle_message(message)

    assert result['response'] is not None
    assert len(result['response']) > 0
    assert result['intent'] is not None
    assert result['safe'] == True

    print(f"\n  Simple message handled")
    print(f"   Response: {result['response'][:100]}...")
    print(f"   Intent: {result['intent']}")
    print(f"   Sentiment: {result['sentiment']}")

def test_angry_customer_escalation():
    """Test angry customer gets escalated"""
    agent = SupportAgent()

    message = "This is the worst service ever! I want a refund NOW!"
    result = agent.handle_message(message)

    print(f"\n  Angry customer test")
    print(f"   Message: {message}")
    print(f"   Escalated: {result['escalated']}")
    print(f"   Sentiment: {result['sentiment']} ({result['sentiment_score']:.2f})")
    print(f"   Response: {result['response']}")

def test_multi_turn_conversation():
    """Test conversation memory"""
    agent = SupportAgent()

    # Turn 1
    result1 = agent.handle_message("Hi, I need help")
    print(f"\n  Multi-turn conversation")
    print(f"\n   Turn 1:")
    print(f"   Customer: Hi, I need help")
    print(f"   Agent: {result1['response'][:80]}...")

    # Turn 2
    result2 = agent.handle_message("Where is my order #12345?")
    print(f"\n   Turn 2:")
    print(f"   Customer: Where is my order #12345?")
    print(f"   Agent: {result2['response'][:80]}...")

    # Check memory
    summary = agent.memory.get_summary()
    print(f"\n   Conversation summary:")
    print(f"   - Turns: {summary['turn_count']}")
    print(f"   - Primary intent: {summary['primary_intent']}")

if __name__ == "__main__":
    print("=" * 60)
    print("TESTING SUPPORT AGENT")
    print("=" * 60)

    test_agent_initialization()
    test_handle_simple_message()
    test_angry_customer_escalation()
    test_multi_turn_conversation()

    print("\n" + "=" * 60)
    print("ALL AGENT TESTS COMPLETED")
    print("=" * 60)
