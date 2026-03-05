# Customer Support Copilot

An AI-powered customer support agent built with **AWS Bedrock (Claude 3.5 Haiku)**, **spaCy NLP**, and **Streamlit**. It reads customer messages, understands intent, detects emotion, filters sensitive data, generates safe responses, and knows when to call a human.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock-orange?logo=amazonaws&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red?logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## What It Does

```
Customer sends: "Where's my order #12345?"
                        |
          +-------------+-------------+
          |             |             |
     PII Filter   Intent Detect  Sentiment
     (hides SSN,  (order_status)  (neutral)
      emails...)       |             |
          +-------------+-------------+
                        |
                  AI Generates Response
                        |
                  Safety Guardrails
                  (check for PII leaks,
                   professional tone)
                        |
              +---------+---------+
              |                   |
         Safe message?       Risky message?
         Auto-send            Human reviews
              |                   |
         "Your order         Agent sees analysis,
          shipped Mar 1!"    decides: send/edit/
                             escalate/reject
```

**Simple messages auto-respond.** Greetings, order status, FAQ questions, shipping info — the AI handles these instantly like a real chatbot.

**Risky messages pause for human review.** Refund requests, complaints, angry customers, low-confidence responses — a human agent sees the full analysis and decides what to do.

---

## Features

| Feature | Description |
|---------|-------------|
| **PII Detection** | Regex + spaCy NER to detect and redact SSNs, emails, phone numbers, credit cards, and names before the AI ever sees them |
| **Intent Classification** | 8 intents detected via few-shot prompting: order status, refund, product question, shipping, account help, complaint, general inquiry, greeting |
| **Sentiment Analysis** | 5-level emotion detection (very positive to very negative) with auto-escalation for angry customers |
| **Safety Guardrails** | Multi-layer response validation: PII leakage check, professional language, empathy matching, policy compliance |
| **Smart Auto-respond** | Safe messages handled automatically; risky messages flagged for human review |
| **Conversation Memory** | Multi-turn context tracking across the entire conversation |
| **Tool Integration** | Knowledge base search, order lookup, and human escalation with priority levels |
| **SRE Monitoring** | Rolling-window metrics, anomaly detection, and critical alerts for PII failures |
| **Cost Tracking** | Per-interaction cost tracking for Bedrock API usage |

---

## Tech Stack

- **AI Model**: AWS Bedrock — Claude 3.5 Haiku (fast, cheap, good)
- **NLP**: spaCy `en_core_web_lg` for Named Entity Recognition
- **UI**: Streamlit with chat-style interface
- **Language**: Python 3.10+

---

## Quick Start

### 1. Clone and install

```bash
git clone <your-repo-url>
cd Customer_Support_Copilot_Agent
pip install -r requirements.txt
python -m spacy download en_core_web_lg
```

### 2. Configure AWS credentials

Create a `.env` file:

```env
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=us-east-1
BEDROCK_MODEL=us.anthropic.claude-3-5-haiku-20241022-v1:0
```

### 3. Run the chatbot

```bash
streamlit run app.py
```

### 4. Run tests

```bash
python -m tests.test_pii_filter
python -m tests.test_intent
python -m tests.test_sentiment
python -m tests.test_guardrails
python -m tests.test_agent
python -m tests.test_end_to_end
```

---

## Project Structure

```
Customer_Support_Copilot_Agent/
|
+-- src/                          # Core engine
|   +-- pii_filter.py             # PII detection & redaction (regex + spaCy)
|   +-- intent_classifier.py      # Intent classification (8 categories)
|   +-- sentiment_analyzer.py     # Sentiment analysis (5 levels)
|   +-- guardrails.py             # Response safety validation
|   +-- agent_core.py             # Main orchestrator (ties everything together)
|   +-- conversation_memory.py    # Multi-turn conversation tracking
|   +-- bedrock_client.py         # AWS Bedrock API wrapper
|   +-- cost_tracker.py           # API cost tracking
|   +-- sre_monitor.py            # Health monitoring & alerting
|
+-- tools/                        # Agent tools
|   +-- knowledge_base.py         # FAQ & policy search
|   +-- order_lookup.py           # Order status lookup (simulated)
|   +-- escalation.py             # Human escalation with priority
|
+-- instructions/                 # Agent behavior (editable, no code changes needed)
|   +-- base_instructions.md      # Core principles
|   +-- support_agent_instructions.md  # Response strategies per intent
|   +-- escalation_guidelines.md  # When and how to escalate
|
+-- tests/                        # Test suite
|   +-- test_pii_filter.py        # PII detection tests
|   +-- test_intent.py            # Intent classification tests
|   +-- test_sentiment.py         # Sentiment analysis tests
|   +-- test_guardrails.py        # Safety guardrails tests
|   +-- test_agent.py             # Agent integration tests
|   +-- test_end_to_end.py        # Full pipeline tests
|
+-- data/knowledge_base/faq.txt   # FAQ content
+-- app.py                        # Streamlit chatbot UI
+-- requirements.txt              # Python dependencies
```

---

## How the Pipeline Works

Every customer message goes through this pipeline:

### 1. PII Filter
Scans for sensitive data using regex patterns (SSN, email, phone, credit card) and spaCy NER (names). Redacts before the AI sees anything.

```
Input:  "My SSN is 123-45-6789 and email is john@test.com"
Output: "My SSN is [SSN_REDACTED] and email is [EMAIL_REDACTED]"
```

### 2. Intent Classifier
Uses few-shot prompting with Claude to classify into one of 8 intents with a confidence score.

### 3. Sentiment Analyzer
Detects emotional state on a 0-1 scale. Scores below 0.3 trigger automatic escalation to a human agent.

### 4. Response Generation
Claude generates a customer-facing response using loaded instruction files + conversation context.

### 5. Safety Guardrails
Multi-layer validation before any response reaches the customer:
- PII leakage detection (did the AI accidentally include personal info?)
- Professional language check
- Empathy matching (angry customer gets empathetic response)
- Policy compliance (no false promises)

### 6. Smart Routing
The system decides automatically:
- **Auto-send** for safe, simple messages (greetings, order status, FAQ)
- **Human review** for risky messages (refunds, complaints, angry customers, low confidence)

---

## Instruction-Based Design

The agent's behavior is defined in markdown files, not hardcoded. Anyone can change how the agent responds by editing these files — no code changes needed:

- `instructions/base_instructions.md` — Core principles (be helpful, never share PII, escalate when unsure)
- `instructions/support_agent_instructions.md` — Per-intent response strategies and tone guidelines
- `instructions/escalation_guidelines.md` — Priority levels and escalation templates

---

## SRE Monitoring

The `SREMonitor` tracks system health with rolling-window metrics:

| Metric | Target | Alert Trigger |
|--------|--------|---------------|
| PII filter success rate | 99%+ | Any failure = CRITICAL |
| Escalation rate | ~15% | >30% = WARNING |
| Avg sentiment | >0.5 | <0.3 = WARNING |
| Cost per interaction | ~$0.008 | 5x spike = WARNING |

---

## Built With

This project was built as a production-grade demonstration of:

- **AI safety** — PII protection, guardrails, human-in-the-loop
- **Instruction-based agent design** — behavior defined in config, not code
- **Smart automation** — AI handles what it can, humans handle what it can't
- **Observability** — SRE monitoring, cost tracking, analysis logging

---

*Powered by AWS Bedrock (Claude 3.5 Haiku) | PII-Protected | GDPR/CCPA Compliant*
