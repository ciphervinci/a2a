# 🔷 A2A Dynatrace AI Agent

An [A2A Protocol](https://a2a-protocol.org/) compliant agent that integrates with Dynatrace for observability, root cause analysis, and ServiceNow integration.

## 🎯 Use Case: Smart Ops & Root-Cause Analysis

This agent enables the following workflow:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Dynatrace → ServiceNow Integration Flow                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   1️⃣ DETECT                                                                  │
│   ┌──────────────────┐                                                       │
│   │  Dynatrace       │  Davis AI detects database latency spike             │
│   │  Davis AI        │                                                       │
│   └────────┬─────────┘                                                       │
│            │                                                                 │
│   2️⃣ NOTIFY via A2A                                                          │
│            ▼                                                                 │
│   ┌──────────────────┐     ┌──────────────────┐                             │
│   │  Dynatrace A2A   │────▶│  ServiceNow AI   │  Enriched context:          │
│   │  Agent (this!)   │     │  Agent           │  • Service topology         │
│   └──────────────────┘     └────────┬─────────┘  • Error patterns           │
│                                     │            • Recent deployments        │
│   3️⃣ ANALYZE                        │                                        │
│                                     ▼                                        │
│                            ┌──────────────────┐                             │
│                            │  Root-Cause      │  Correlates:                │
│                            │  Agent           │  • Logs                     │
│                            └────────┬─────────┘  • CI/CD changes            │
│                                     │            • Metrics                   │
│   4️⃣ REMEDIATE                      │                                        │
│                                     ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  "Root cause: DB index change on 2026-01-17.                       │   │
│   │   Suggested remediation: revert index + monitor performance."       │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🛠️ Features (A2A Skills)

| Skill | Description |
|-------|-------------|
| **Get Problems** | List open problems from Davis AI with severity and impact |
| **Root Cause Analysis** | Deep analysis with evidence correlation and AI recommendations |
| **Service Topology** | View Smartscape dependencies (upstream/downstream) |
| **Entity Health** | Check health and metrics for hosts, services, processes |
| **ServiceNow Integration** | Generate structured incident summaries for ServiceNow |
| **Natural Language Query** | Ask questions about your environment in plain English |

## 📋 Prerequisites

1. **Dynatrace Environment** with API access
2. **Dynatrace API Token** with these scopes:
   - `problems.read`
   - `entities.read`
   - `metrics.read`
   - `events.read`
3. **Google Gemini API Key** (free at [aistudio.google.com](https://aistudio.google.com/app/apikey))

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone <your-repo-url>
cd a2a-dynatrace-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

Required variables:
```bash
DYNATRACE_URL=https://abc12345.live.dynatrace.com
DYNATRACE_API_TOKEN=dt0c01.XXXXXXXX.YYYYYYYY...
GEMINI_API_KEY=your_gemini_key
```

### 3. Run the Server

```bash
python main.py
```

### 4. Test

```bash
# In another terminal
python test_client.py

# Or use curl
curl http://localhost:8000/.well-known/agent.json
```

## 🔌 API Examples

### Get Open Problems

```bash
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "Show open problems"}],
        "messageId": "msg-1"
      }
    }
  }'
```

### Analyze a Problem

```bash
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "2",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "Analyze P-12345678"}],
        "messageId": "msg-2"
      }
    }
  }'
```

### Create ServiceNow Incident

```bash
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "3",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "Create incident for P-12345678"}],
        "messageId": "msg-3"
      }
    }
  }'
```

## 🚀 Deployment

### Render (Recommended - Free Tier)

1. Push to GitHub
2. Go to [render.com](https://render.com)
3. New → Web Service → Connect GitHub repo
4. Add environment variables in dashboard:
   - `DYNATRACE_URL`
   - `DYNATRACE_API_TOKEN`
   - `GEMINI_API_KEY`
5. Deploy!

### Docker

```bash
docker build -t a2a-dynatrace-agent .
docker run -p 8000:8000 \
  -e DYNATRACE_URL=https://... \
  -e DYNATRACE_API_TOKEN=dt0c01... \
  -e GEMINI_API_KEY=... \
  a2a-dynatrace-agent
```

## 📁 Project Structure

```
a2a-dynatrace-agent/
├── main.py              # A2A server entry point
├── dynatrace_client.py  # Dynatrace REST API v2 client
├── dynatrace_agent.py   # AI-powered agent with skills
├── agent_executor.py    # A2A protocol bridge
├── test_client.py       # Test client
├── requirements.txt     # Dependencies
├── Dockerfile          # Container config
├── render.yaml         # Render deployment
├── .env.example        # Environment template
└── README.md           # This file
```

## 🔒 Creating a Dynatrace API Token

1. Go to Dynatrace → **Settings** → **Integration** → **Dynatrace API**
2. Click **Generate token**
3. Name: `A2A Agent`
4. Enable scopes:
   - ✅ `problems.read` - Read problems
   - ✅ `entities.read` - Read entities
   - ✅ `metrics.read` - Read metrics
   - ✅ `events.read` - Read events
5. Click **Generate** and copy the token

## 🤝 A2A Multi-Agent Integration

This agent is designed to work with other A2A agents:

```
┌─────────────────┐     A2A      ┌─────────────────┐
│  Dynatrace      │◀────────────▶│  ServiceNow     │
│  Agent          │              │  Agent          │
└─────────────────┘              └─────────────────┘
        │                                │
        │ A2A                            │ A2A
        ▼                                ▼
┌─────────────────┐              ┌─────────────────┐
│  CI/CD          │              │  Slack          │
│  Agent          │              │  Agent          │
└─────────────────┘              └─────────────────┘
```

### Sample ServiceNow Integration Flow

1. **Dynatrace Agent** detects problem → sends to **ServiceNow Agent**
2. **ServiceNow Agent** creates incident with enriched data
3. **ServiceNow Agent** requests root cause from **Dynatrace Agent**
4. **Dynatrace Agent** provides analysis with deployment correlation
5. **ServiceNow Agent** updates incident with remediation suggestions

## 📚 Resources

- [A2A Protocol](https://a2a-protocol.org/)
- [Dynatrace API Documentation](https://docs.dynatrace.com/docs/dynatrace-api)
- [Dynatrace Problems API v2](https://docs.dynatrace.com/docs/dynatrace-api/environment-api/problems-v2)
- [Google Gemini API](https://ai.google.dev/)

## 📄 License

MIT License
