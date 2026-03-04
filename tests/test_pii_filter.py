"""CRITICAL PII Filter Tests - MUST PASS before production!"""

from src.pii_filter import PIIFilter

def test_email_detection():
    """Test email detection"""
    filter = PIIFilter(use_ner=False)
    text = "Contact: john@example.com"
    safe, meta = filter.safe_for_llm(text)

    assert meta['pii_detected'] == True
    assert 'EMAIL' in meta['entity_types']
    assert '@' not in safe
    print("  Email detection works")

def test_phone_detection():
    """Test phone number detection"""
    filter = PIIFilter(use_ner=False)
    phones = ["555-123-4567", "(555) 123-4567", "555.123.4567"]

    for phone in phones:
        safe, meta = filter.safe_for_llm(f"Call {phone}")
        assert meta['pii_detected'] == True
        print(f"    Detected: {phone}")
    print("  Phone detection works")

def test_ssn_detection():
    """Test SSN detection - CRITICAL!"""
    filter = PIIFilter(use_ner=False)
    text = "My SSN is 123-45-6789"
    safe, meta = filter.safe_for_llm(text)

    assert meta['pii_detected'] == True
    assert '123-45-6789' not in safe
    assert 'SSN' in meta['entity_types']
    print("  SSN detection - CRITICAL TEST PASSED")

def test_credit_card_detection():
    """Test credit card detection - CRITICAL!"""
    filter = PIIFilter(use_ner=False)
    text = "Card: 4532-1234-5678-9010"
    safe, meta = filter.safe_for_llm(text)

    assert meta['pii_detected'] == True
    assert '4532' not in safe
    print("  Credit card detection - CRITICAL TEST PASSED")

def test_multiple_pii():
    """Test complex message"""
    filter = PIIFilter(use_ner=False)
    message = """
    Order #AB123CD issue.
    Email: john@example.com
    Phone: (555) 123-4567
    """
    safe, meta = filter.safe_for_llm(message)

    print(f"\n  Original:\n{message}")
    print(f"  Redacted:\n{safe}")
    print(f"  PII: {meta['entity_types']}")

    assert meta['entity_count'] >= 2
    assert 'john@example.com' not in safe
    print("  Multiple PII types handled")

if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING CRITICAL PII TESTS")
    print("=" * 60)
    test_email_detection()
    test_phone_detection()
    test_ssn_detection()
    test_credit_card_detection()
    test_multiple_pii()
    print("\n" + "=" * 60)
    print("ALL CRITICAL TESTS PASSED!")
    print("=" * 60)
