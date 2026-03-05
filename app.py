"""
Customer Support Chatbot - Smart auto-respond with human review on risk

Auto-handles simple messages (greetings, order status, FAQ).
Pauses for human review on risky messages (angry, refunds, PII, low confidence).
"""

import streamlit as st
from datetime import datetime

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

# Custom CSS
st.markdown("""
<style>
    .block-container {
        max-width: 900px;
        margin: 0 auto;
        padding-top: 1rem;
    }

    .analysis-row {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 12px;
    }

    .badge {
        display: inline-flex;
        align-items: center;
        padding: 5px 12px;
        border-radius: 16px;
        font-size: 0.82em;
        font-weight: 500;
    }

    .badge-intent { background: #2d2b55; color: #b4b0ff; border: 1px solid #4a47a3; }
    .badge-positive { background: #1a3a2a; color: #6ee7a0; border: 1px solid #2d6b4a; }
    .badge-neutral { background: #2a2a1a; color: #e7e76e; border: 1px solid #6b6b2d; }
    .badge-negative { background: #3a1a1a; color: #e76e6e; border: 1px solid #6b2d2d; }
    .badge-pii { background: #1a2a3a; color: #6eb4e7; border: 1px solid #2d4a6b; }
    .badge-safe { background: #1a3a2a; color: #6ee7a0; border: 1px solid #2d6b4a; }
    .badge-unsafe { background: #3a1a1a; color: #e76e6e; border: 1px solid #6b2d2d; }

    .auto-label { font-size: 0.72em; color: #666; font-style: italic; }
    .review-label { font-size: 0.72em; color: #b4b0ff; font-style: italic; }

    h1 { font-size: 1.5rem !important; }
    footer { visibility: hidden; }
    [data-testid="stMetricValue"] { font-size: 1.1rem; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = SupportAgent()
    tools = {
        'knowledge_base': KnowledgeBaseTool(),
        'order_lookup': OrderLookupTool(),
        'escalation': EscalationTool()
    }
    st.session_state.agent.register_tools(tools)

if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'total_cost' not in st.session_state:
    st.session_state.total_cost = 0.0

if 'pending_result' not in st.session_state:
    st.session_state.pending_result = None

if 'editing' not in st.session_state:
    st.session_state.editing = False

if 'analysis_log' not in st.session_state:
    st.session_state.analysis_log = []


# ─── Sidebar ───
with st.sidebar:
    st.title("Support Copilot")
    st.caption("AI-powered customer support")
    st.divider()

    # Session stats
    msg_count = len([m for m in st.session_state.messages if m['role'] == 'customer'])
    auto_count = len([m for m in st.session_state.messages if m.get('metadata', {}).get('auto_sent')])
    reviewed_count = len([m for m in st.session_state.messages if m.get('metadata', {}).get('human_reviewed')])

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Messages", msg_count)
        st.metric("Auto-sent", auto_count)
    with col2:
        st.metric("Cost", f"${st.session_state.total_cost:.4f}")
        st.metric("Reviewed", reviewed_count)

    if st.session_state.agent.memory.metadata['turn_count'] > 0:
        summary = st.session_state.agent.memory.get_summary()
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Turns", summary['turn_count'])
        with col2:
            avg = summary['avg_sentiment']
            mood = "Positive" if avg > 0.6 else "Neutral" if avg > 0.4 else "Negative"
            st.metric("Mood", mood)

    st.divider()

    if st.button("New Conversation", use_container_width=True):
        st.session_state.agent.reset_conversation()
        st.session_state.messages = []
        st.session_state.pending_result = None
        st.session_state.editing = False
        st.session_state.total_cost = 0.0
        st.session_state.analysis_log = []
        st.rerun()

    # Analysis log
    if st.session_state.analysis_log:
        st.divider()
        st.subheader("Analysis Log")
        for i, log in enumerate(reversed(st.session_state.analysis_log[-10:]), 1):
            sentiment_emoji = {"very_positive": "😊", "positive": "🙂", "neutral": "😐",
                               "negative": "😟", "very_negative": "😡"}.get(log.get('sentiment', ''), "😐")
            label = f"#{len(st.session_state.analysis_log) - i + 1} {log['intent'].replace('_', ' ').title()}"
            with st.expander(label):
                st.markdown(f"**Intent:** {log['intent'].replace('_', ' ').title()} ({log['confidence']:.0%})")
                st.markdown(f"**Sentiment:** {sentiment_emoji} {log['sentiment']} ({log['score']:.2f})")
                st.markdown(f"**PII:** {'Detected' if log.get('pii') else 'None'}")
                st.markdown(f"**Safe:** {'Yes' if log.get('safe') else 'No'}")
                st.markdown(f"**Review:** {'Human' if log.get('needs_review') else 'Auto-sent'}")

    st.divider()
    st.caption("Simple messages auto-respond. Risky messages pause for human review.")


# ─── Main Chat Area ───
st.title("Customer Support")

# Render all committed messages
for msg in st.session_state.messages:
    role = "user" if msg["role"] == "customer" else "assistant"
    with st.chat_message(role):
        st.markdown(msg["content"])

        # Show metadata captions for agent messages
        if msg["role"] == "agent":
            meta = msg.get("metadata", {})
            parts = []
            if meta.get("intent"):
                parts.append(meta['intent'].replace('_', ' ').title())
            if meta.get("sentiment"):
                emoji = {"very_positive": "😊", "positive": "🙂", "neutral": "😐",
                         "negative": "😟", "very_negative": "😡"}.get(meta["sentiment"], "")
                if emoji:
                    parts.append(f"{emoji} {meta.get('sentiment_score', 0):.2f}")
            if meta.get("auto_sent"):
                parts.append("Auto")
            if meta.get("human_reviewed"):
                parts.append("Reviewed")
            if meta.get("escalated"):
                parts.append("Escalated")
            if meta.get("edited"):
                parts.append("Edited")
            if parts:
                css_class = "review-label" if meta.get("human_reviewed") else "auto-label"
                st.markdown(f'<span class="{css_class}">{" · ".join(parts)}</span>', unsafe_allow_html=True)


# ─── Review Panel (only when human review is needed) ───
if st.session_state.pending_result is not None:
    result = st.session_state.pending_result

    st.divider()
    st.markdown("**Human Review Required**")

    # Analysis badges
    sentiment_class = "positive" if result['sentiment_score'] > 0.6 else "neutral" if result['sentiment_score'] > 0.4 else "negative"
    pii_text = "PII Filtered" if result.get('pii_detected') else "No PII"
    safe_class = "safe" if result['safe'] else "unsafe"
    safe_text = "Safe" if result['safe'] else "Unsafe"

    st.markdown(f"""
    <div class="analysis-row">
        <span class="badge badge-intent">Intent: {result['intent'].replace('_', ' ').title()} ({result['intent_confidence']:.0%})</span>
        <span class="badge badge-{sentiment_class}">Sentiment: {result['sentiment'].replace('_', ' ').title()} ({result['sentiment_score']:.2f})</span>
        <span class="badge badge-pii">{pii_text}</span>
        <span class="badge badge-{safe_class}">{safe_text}</span>
    </div>
    """, unsafe_allow_html=True)

    # Warnings
    if result['escalated']:
        st.error("AUTO-ESCALATED: Customer needs immediate human attention")
    elif result['sentiment_score'] < 0.4:
        st.warning("Customer seems frustrated - consider escalating")

    # Suggested response
    if st.session_state.editing:
        st.markdown("**Edit Response:**")
        edited_response = st.text_area(
            "Edit response",
            value=result['response'],
            height=120,
            label_visibility="collapsed",
            key="edit_area"
        )
    else:
        with st.chat_message("assistant"):
            st.markdown(result['response'])
            st.markdown('<span class="review-label">Pending your approval</span>', unsafe_allow_html=True)

    # Action buttons
    btn_cols = st.columns(4)

    with btn_cols[0]:
        if st.button("Send", type="primary", use_container_width=True):
            st.session_state.messages.append({
                "role": "agent",
                "content": result['response'],
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "intent": result['intent'],
                    "sentiment": result['sentiment'],
                    "sentiment_score": result['sentiment_score'],
                    "pii_detected": result.get('pii_detected', False),
                    "safe": result['safe'],
                    "human_reviewed": True
                }
            })
            st.session_state.pending_result = None
            st.session_state.editing = False
            st.rerun()

    with btn_cols[1]:
        if st.session_state.editing:
            if st.button("Send Edited", use_container_width=True):
                st.session_state.messages.append({
                    "role": "agent",
                    "content": edited_response,
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {
                        "intent": result['intent'],
                        "sentiment": result['sentiment'],
                        "sentiment_score": result['sentiment_score'],
                        "human_reviewed": True,
                        "edited": True
                    }
                })
                st.session_state.pending_result = None
                st.session_state.editing = False
                st.rerun()
        else:
            if st.button("Edit", use_container_width=True):
                st.session_state.editing = True
                st.rerun()

    with btn_cols[2]:
        if st.button("Escalate", use_container_width=True):
            esc_tool = st.session_state.agent.tools.get('escalation')
            if esc_tool:
                last_customer_msg = ""
                for m in reversed(st.session_state.messages):
                    if m['role'] == 'customer':
                        last_customer_msg = m['content']
                        break
                escalation = esc_tool.create_escalation(
                    reason="Agent-initiated escalation",
                    priority="high",
                    customer_message=last_customer_msg,
                    intent=result['intent'],
                    sentiment_score=result['sentiment_score']
                )
                esc_msg = esc_tool.get_escalation_message(escalation)
            else:
                esc_msg = "Let me connect you with a specialist who can help."

            st.session_state.messages.append({
                "role": "agent",
                "content": esc_msg,
                "timestamp": datetime.now().isoformat(),
                "metadata": {"escalated": True, "human_reviewed": True}
            })
            st.session_state.pending_result = None
            st.session_state.editing = False
            st.rerun()

    with btn_cols[3]:
        if st.button("Reject", use_container_width=True):
            st.session_state.pending_result = None
            st.session_state.editing = False
            st.rerun()


# ─── Chat Input ───
if prompt := st.chat_input(
    "Type customer message...",
    disabled=st.session_state.pending_result is not None
):
    # Add customer message to chat
    st.session_state.messages.append({
        "role": "customer",
        "content": prompt,
        "timestamp": datetime.now().isoformat(),
        "metadata": {}
    })

    # Process with AI
    with st.spinner(""):
        result = st.session_state.agent.handle_message(prompt)
        st.session_state.total_cost += result['cost']

        # Log analysis
        st.session_state.analysis_log.append({
            'intent': result['intent'],
            'confidence': result['intent_confidence'],
            'sentiment': result['sentiment'],
            'score': result['sentiment_score'],
            'pii': result.get('pii_detected', False),
            'safe': result['safe'],
            'needs_review': result['needs_human_review'],
            'timestamp': datetime.now().isoformat()
        })

        if result['needs_human_review']:
            # Risky - pause for human review
            st.session_state.pending_result = result
        else:
            # Safe - auto-send response
            st.session_state.messages.append({
                "role": "agent",
                "content": result['response'],
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "intent": result['intent'],
                    "sentiment": result['sentiment'],
                    "sentiment_score": result['sentiment_score'],
                    "pii_detected": result.get('pii_detected', False),
                    "safe": result['safe'],
                    "auto_sent": True
                }
            })

    st.rerun()
