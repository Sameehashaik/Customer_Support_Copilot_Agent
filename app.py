"""
Agent Dashboard - Streamlit UI for customer support

Human-in-the-loop: AI suggests, human decides
"""

import streamlit as st
from datetime import datetime
import json

from src.agent_core import SupportAgent
from tools.knowledge_base import KnowledgeBaseTool
from tools.order_lookup import OrderLookupTool
from tools.escalation import EscalationTool

# Page config
st.set_page_config(
    page_title="Customer Support Copilot",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = SupportAgent()

    # Register tools
    tools = {
        'knowledge_base': KnowledgeBaseTool(),
        'order_lookup': OrderLookupTool(),
        'escalation': EscalationTool()
    }
    st.session_state.agent.register_tools(tools)

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

if 'total_cost' not in st.session_state:
    st.session_state.total_cost = 0.0

# Sidebar
with st.sidebar:
    st.title("🤖 Support Copilot")
    st.caption("AI-powered customer support assistant")

    st.divider()

    st.subheader("Session Stats")
    st.metric("Conversations", len(st.session_state.conversation_history))
    st.metric("Total Cost", f"${st.session_state.total_cost:.4f}")

    if st.session_state.agent.memory.metadata['turn_count'] > 0:
        summary = st.session_state.agent.memory.get_summary()
        st.metric("Current Turns", summary['turn_count'])
        st.metric("Avg Sentiment", f"{summary['avg_sentiment']:.2f}")

    st.divider()

    if st.button("🔄 New Conversation"):
        st.session_state.agent.reset_conversation()
        st.rerun()

    st.divider()

    with st.expander("💡 How to Use"):
        st.markdown("""
        **This is a human-in-the-loop system:**

        1. Customer message appears
        2. AI analyzes and suggests response
        3. **You decide:**
           - Send AI response as-is
           - Edit before sending
           - Write your own
           - Escalate to specialist

        **AI provides:**
        - Intent detection
        - Sentiment analysis
        - PII filtering
        - Suggested response
        - Safety checks
        """)

# Main area
st.title("Customer Support Dashboard")

# Create two columns
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📥 Customer Message")

    customer_message = st.text_area(
        "Customer Message",
        placeholder="Enter customer message here...",
        height=150,
        label_visibility="collapsed"
    )

    analyze_button = st.button("🔍 Analyze & Suggest Response", type="primary", disabled=not customer_message)

with col2:
    st.subheader("🤖 AI Analysis")

    analysis_placeholder = st.empty()

# Process message
if analyze_button and customer_message:
    with st.spinner("Analyzing message and generating response..."):
        # Get AI response
        result = st.session_state.agent.handle_message(customer_message)

        # Update cost
        st.session_state.total_cost += result['cost']

        # Store in history
        st.session_state.conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            'customer_message': customer_message,
            'ai_response': result['response'],
            'intent': result['intent'],
            'sentiment': result['sentiment'],
            'sentiment_score': result['sentiment_score'],
            'escalated': result['escalated'],
            'cost': result['cost']
        })

        # Display analysis
        with analysis_placeholder.container():
            # Intent
            intent_color = {
                'order_status': '🔍',
                'refund_request': '💰',
                'product_question': '📦',
                'complaint': '⚠️',
                'general_inquiry': '💬'
            }

            st.metric(
                "Intent",
                result['intent'].replace('_', ' ').title(),
                delta=f"{result['intent_confidence']:.0%} confidence"
            )

            # Sentiment
            sentiment_emoji = {
                'very_positive': '😊',
                'positive': '🙂',
                'neutral': '😐',
                'negative': '😟',
                'very_negative': '😡'
            }

            sentiment_color = 'normal' if result['sentiment_score'] > 0.4 else 'inverse'

            st.metric(
                "Sentiment",
                f"{sentiment_emoji.get(result['sentiment'], '😐')} {result['sentiment'].replace('_', ' ').title()}",
                delta=f"Score: {result['sentiment_score']:.2f}",
                delta_color=sentiment_color
            )

            # Escalation
            if result['escalated']:
                st.error("⚠️ **AUTO-ESCALATED** - Customer needs immediate human attention")
            elif result['sentiment_score'] < 0.4:
                st.warning("⚡ Consider escalating - Customer seems frustrated")

            # PII detected
            if result.get('pii_detected'):
                st.info("🔒 PII detected and filtered")

            # Safety
            if result['safe']:
                st.success("✅ Response passed safety checks")
            else:
                st.error("❌ Response failed safety checks")

# Response section
if st.session_state.conversation_history:
    latest = st.session_state.conversation_history[-1]

    st.divider()
    st.subheader("💬 Suggested Response")

    # Show AI suggestion
    with st.container():
        st.markdown("**AI Suggested Response:**")
        suggested_response = st.text_area(
            "suggested",
            value=latest['ai_response'],
            height=150,
            label_visibility="collapsed"
        )

    # Action buttons
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("✅ Send As-Is", type="primary"):
            st.success("✅ Response sent to customer!")
            st.balloons()

    with col2:
        if st.button("✏️ Edit & Send"):
            st.info("Edit the response above, then click 'Send Edited'")

    with col3:
        if st.button("🚀 Escalate to Human"):
            st.warning("Escalating to human agent...")

    with col4:
        if st.button("❌ Reject"):
            st.error("Response rejected. Write your own below.")

# Conversation history
if st.session_state.conversation_history:
    st.divider()
    st.subheader("📜 Conversation History")

    for i, conv in enumerate(reversed(st.session_state.conversation_history[-5:]), 1):
        with st.expander(f"Conversation {len(st.session_state.conversation_history) - i + 1} - {conv['intent'].replace('_', ' ').title()}"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Customer:**")
                st.text(conv['customer_message'])

            with col2:
                st.markdown("**AI Response:**")
                st.text(conv['ai_response'])

            st.caption(f"Intent: {conv['intent']} | Sentiment: {conv['sentiment']} ({conv['sentiment_score']:.2f}) | Cost: ${conv['cost']:.4f}")

# Footer
st.divider()
st.caption("Customer Support Copilot | Powered by AWS Bedrock (Claude 3.5 Haiku) | PII-Protected | GDPR/CCPA Compliant")
