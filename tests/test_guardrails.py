"""Test safety guardrails"""

from src.guardrails import ResponseGuardrails

def test_pii_leakage():
    """Test PII detection in responses"""
    guardrails = ResponseGuardrails()

    response = "Your email is john@example.com"
    result = guardrails.check_response(response)

    assert result['safe'] == False
    assert any('PII' in issue for issue in result['issues'])
    print("  PII leakage detected correctly")

def test_unprofessional_language():
    """Test unprofessional language detection"""
    guardrails = ResponseGuardrails()

    response = "That's a stupid question"
    result = guardrails.check_response(response)

    assert result['safe'] == False
    assert any('Unprofessional' in issue for issue in result['issues'])
    print("  Unprofessional language detected")

def test_empathy_for_angry_customer():
    """Test empathy check for negative sentiment"""
    guardrails = ResponseGuardrails()

    # No empathy with angry customer
    response = "Your order will arrive when it arrives"
    result = guardrails.check_response(
        response=response,
        sentiment_score=0.2  # Very negative
    )

    assert result['safe'] == False
    print("  Lack of empathy detected for angry customer")

    # Good empathetic response
    response = "I understand your frustration. Let me help you track that order."
    result = guardrails.check_response(
        response=response,
        sentiment_score=0.2
    )

    assert result['safe'] == True
    print("  Empathetic response approved")

def test_safe_response():
    """Test completely safe response"""
    guardrails = ResponseGuardrails()

    response = "I can help you track your order. Could you provide your order number?"
    result = guardrails.check_response(response)

    assert result['safe'] == True
    assert len(result['issues']) == 0
    print("  Safe response approved")

if __name__ == "__main__":
    print("=" * 60)
    print("TESTING SAFETY GUARDRAILS")
    print("=" * 60)
    test_pii_leakage()
    test_unprofessional_language()
    test_empathy_for_angry_customer()
    test_safe_response()
    print("\n" + "=" * 60)
    print("ALL GUARDRAIL TESTS PASSED")
    print("=" * 60)
