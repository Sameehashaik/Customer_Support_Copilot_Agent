"""
End-to-end integration tests

Test the complete pipeline with real scenarios
"""

from src.agent_core import SupportAgent
from tools.knowledge_base import KnowledgeBaseTool
from tools.order_lookup import OrderLookupTool
from tools.escalation import EscalationTool
from src.sre_monitor import SREMonitor
import logging
import time

logging.basicConfig(level=logging.INFO)

def test_happy_path_order_status():
    """Test happy path - customer checks order"""
    print("\n" + "=" * 60)
    print("TEST: Happy Path - Order Status")
    print("=" * 60)

    agent = SupportAgent()
    tools = {
        'knowledge_base': KnowledgeBaseTool(),
        'order_lookup': OrderLookupTool(),
        'escalation': EscalationTool()
    }
    agent.register_tools(tools)

    message = "Hi! Can you check on my order #ORDER12345?"

    start = time.time()
    result = agent.handle_message(message)
    duration = time.time() - start

    print(f"\nCustomer: {message}")
    print(f"Agent: {result['response']}")
    print(f"\nIntent: {result['intent']}")
    print(f"Sentiment: {result['sentiment']} ({result['sentiment_score']:.2f})")
    print(f"Escalated: {result['escalated']}")
    print(f"Duration: {duration:.2f}s")
    print(f"Cost: ${result['cost']:.4f}")

    assert result['safe'] == True
    assert result['escalated'] == False
    print("\n  Happy path test passed")

def test_angry_customer_escalation():
    """Test angry customer gets escalated"""
    print("\n" + "=" * 60)
    print("TEST: Angry Customer Escalation")
    print("=" * 60)

    agent = SupportAgent()
    tools = {
        'knowledge_base': KnowledgeBaseTool(),
        'order_lookup': OrderLookupTool(),
        'escalation': EscalationTool()
    }
    agent.register_tools(tools)

    message = "This is RIDICULOUS! My order is 2 weeks late and I want a FULL refund NOW!"

    result = agent.handle_message(message)

    print(f"\nCustomer: {message}")
    print(f"Agent: {result['response']}")
    print(f"\nIntent: {result['intent']}")
    print(f"Sentiment: {result['sentiment']} ({result['sentiment_score']:.2f})")
    print(f"Escalated: {result['escalated']}")

    assert result['escalated'] == True, "Angry customer should be escalated!"
    print("\n  Escalation test passed")

def test_pii_protection():
    """Test PII is filtered"""
    print("\n" + "=" * 60)
    print("TEST: PII Protection")
    print("=" * 60)

    agent = SupportAgent()

    message = "My email is john.doe@example.com and my SSN is 123-45-6789. Can you help?"

    result = agent.handle_message(message)

    print(f"\nCustomer: {message}")
    print(f"Agent: {result['response']}")
    print(f"PII Detected: {result['pii_detected']}")

    # Response should NOT contain PII
    assert 'john.doe@example.com' not in result['response']
    assert '123-45-6789' not in result['response']
    print("\n  PII protection test passed")

def test_multi_turn_conversation():
    """Test conversation memory works"""
    print("\n" + "=" * 60)
    print("TEST: Multi-Turn Conversation")
    print("=" * 60)

    agent = SupportAgent()
    tools = {
        'knowledge_base': KnowledgeBaseTool(),
        'order_lookup': OrderLookupTool(),
        'escalation': EscalationTool()
    }
    agent.register_tools(tools)

    # Turn 1
    result1 = agent.handle_message("Hi, I need help with an order")
    print(f"\nTurn 1:")
    print(f"Customer: Hi, I need help with an order")
    print(f"Agent: {result1['response'][:100]}...")

    # Turn 2
    result2 = agent.handle_message("Order number ORDER12345")
    print(f"\nTurn 2:")
    print(f"Customer: Order number ORDER12345")
    print(f"Agent: {result2['response'][:100]}...")

    # Check memory
    summary = agent.memory.get_summary()
    print(f"\nConversation Summary:")
    print(f"  Turns: {summary['turn_count']}")
    print(f"  Primary Intent: {summary['primary_intent']}")

    assert summary['turn_count'] >= 2
    print("\n  Multi-turn conversation test passed")

def test_sre_monitoring():
    """Test SRE monitoring"""
    print("\n" + "=" * 60)
    print("TEST: SRE Monitoring")
    print("=" * 60)

    monitor = SREMonitor()

    # Simulate normal operations
    for i in range(10):
        monitor.track_interaction({
            'pii_filter_success': True,
            'escalated': False,
            'sentiment_score': 0.6,
            'response_time_ms': 2000,
            'cost': 0.008
        })

    # Simulate PII failure (should trigger alert)
    monitor.track_interaction({
        'pii_filter_success': False,
        'escalated': False,
        'sentiment_score': 0.5,
        'response_time_ms': 2000,
        'cost': 0.008
    })

    # Check metrics
    metrics = monitor.get_dashboard_metrics()
    print(f"\nMetrics:")
    print(f"  Total Interactions: {metrics['total_interactions']}")
    print(f"  PII Success Rate: {metrics['pii_success_rate']:.1%}")
    print(f"  Escalation Rate: {metrics['escalation_rate']:.1%}")

    # Should have critical alert for PII failure
    critical_alerts = [a for a in monitor.alerts if a['severity'] == 'CRITICAL']
    assert len(critical_alerts) > 0, "Should have critical alert for PII failure"

    print(f"\n  Alerts: {len(monitor.alerts)}")
    for alert in monitor.alerts:
        print(f"  [{alert['severity']}] {alert['title']}")

    print("\n  SRE monitoring test passed")

if __name__ == "__main__":
    print("=" * 60)
    print("END-TO-END INTEGRATION TESTS")
    print("=" * 60)

    test_happy_path_order_status()
    test_angry_customer_escalation()
    test_pii_protection()
    test_multi_turn_conversation()
    test_sre_monitoring()

    print("\n" + "=" * 60)
    print("ALL END-TO-END TESTS PASSED!")
    print("=" * 60)
    print("\n  System is production-ready!")
