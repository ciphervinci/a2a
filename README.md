# 🎭 A2A Joke Generator Agent

A sample [Agent2Agent (A2A) Protocol](https://a2a-protocol.org/) server that tells jokes using Google's Gemini AI. This agent demonstrates how to build an A2A-compliant server that can be discovered and used by other AI agents.

## What is A2A?

The Agent2Agent (A2A) Protocol is an open standard that enables AI agents to discover and communicate with each other, regardless of their underlying frameworks or vendors. Think of it as a universal language for AI agents.

## Features

- 🤖 **A2A Protocol Compliant**: Fully implements the A2A specification
- 🎯 **Two Skills**:
  - **Tell Joke**: Generate jokes on any topic
  - **Explain Joke**: Explain why a joke is funny
- ⚡ **Powered by Gemini**: Uses Google's Gemini AI for intelligent responses
- 🚀 **Ready to Deploy**: Includes configurations for Render, Railway, and Docker

## Quick Start

### Prerequisites

- Python 3.10 or higher
- A [Google Gemini API key](https://aistudio.google.com/app/apikey) (free)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd a2a-joke-agent
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

5. **Run the server**
   ```bash
   python main.py
   ```

6. **Test the server**
   ```bash
   # In another terminal
   python test_client.py
   ```

### Verify It's Working

```bash
# Check the agent card
curl http://localhost:8000/.well-known/agent.json

# Send a joke request
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "Tell me a joke about programming"}],
        "messageId": "msg-1"
      }
    }
  }'
```

## 🚀 Deployment Options

### Option 1: Render (Recommended - Free Tier)

[Render](https://render.com) offers a free tier perfect for A2A agents.

1. **Push to GitHub**: Push this code to a GitHub repository

2. **Create a Render account**: Go to [render.com](https://render.com) and sign up

3. **Deploy from GitHub**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Render will auto-detect the `render.yaml` configuration

4. **Set Environment Variables**:
   - In the Render dashboard, go to your service
   - Navigate to "Environment" tab
   - Add `GEMINI_API_KEY` with your API key

5. **Your agent is live!** 
   - URL: `https://your-app-name.onrender.com`
   - Agent Card: `https://your-app-name.onrender.com/.well-known/agent.json`

> ⚠️ **Note**: Free tier services on Render spin down after 15 minutes of inactivity. The first request after spin-down may take 30-60 seconds.

### Option 2: Railway

[Railway](https://railway.app) offers a simple deployment with a free trial.

1. **Push to GitHub**

2. **Create Railway project**:
   - Go to [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository

3. **Set Environment Variables**:
   - `GEMINI_API_KEY`: Your API key
   - `PORT`: Railway sets this automatically

4. **Get your URL** from the Railway dashboard

### Option 3: Fly.io

[Fly.io](https://fly.io) offers global edge deployment with a free tier.

1. **Install the Fly CLI**:
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login and deploy**:
   ```bash
   fly auth login
   fly launch
   fly secrets set GEMINI_API_KEY=your_api_key_here
   fly deploy
   ```

### Option 4: Docker (Any Platform)

```bash
# Build the image
docker build -t a2a-joke-agent .

# Run locally
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key a2a-joke-agent

# Or push to a registry and deploy anywhere
docker tag a2a-joke-agent your-registry/a2a-joke-agent
docker push your-registry/a2a-joke-agent
```

## API Reference

### Agent Card Endpoint

```
GET /.well-known/agent.json
```

Returns the agent's capabilities and metadata.

### Message Endpoint

```
POST /
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": "unique-id",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [{"kind": "text", "text": "Your message here"}],
      "messageId": "unique-message-id"
    }
  }
}
```

### Example Messages

| Message | Result |
|---------|--------|
| `Tell me a joke` | Random joke |
| `Tell me a joke about cats` | Cat-themed joke |
| `Explain: Why did the chicken cross the road?` | Explanation of why it's funny |

## Project Structure

```
a2a-joke-agent/
├── main.py              # Server entry point
├── joke_agent.py        # Gemini-powered joke generation
├── agent_executor.py    # A2A protocol handler
├── test_client.py       # Test client script
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker configuration
├── render.yaml          # Render deployment config
├── .env.example         # Environment variables template
└── README.md            # This file
```

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    A2A Protocol Flow                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐     1. Discover      ┌───────────────────┐    │
│  │  Client  │ ──────────────────► │ /.well-known/     │    │
│  │  Agent   │                      │   agent.json      │    │
│  └──────────┘                      └───────────────────┘    │
│       │                                                      │
│       │ 2. Send Message (JSON-RPC)                          │
│       ▼                                                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              A2A Joke Agent Server                    │   │
│  │  ┌─────────────────┐    ┌────────────────────────┐   │   │
│  │  │ DefaultRequest  │───►│  JokeAgentExecutor     │   │   │
│  │  │    Handler      │    │  (agent_executor.py)   │   │   │
│  │  └─────────────────┘    └────────────────────────┘   │   │
│  │                                    │                  │   │
│  │                                    ▼                  │   │
│  │                         ┌────────────────────────┐   │   │
│  │                         │     JokeAgent          │   │   │
│  │                         │   (joke_agent.py)      │   │   │
│  │                         └────────────────────────┘   │   │
│  │                                    │                  │   │
│  └────────────────────────────────────│──────────────────┘   │
│                                       │                      │
│                                       ▼                      │
│                              ┌────────────────┐              │
│                              │  Gemini API    │              │
│                              └────────────────┘              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Resources

- [A2A Protocol Documentation](https://a2a-protocol.org/)
- [A2A Python SDK](https://github.com/a2aproject/a2a-python)
- [A2A Samples Repository](https://github.com/a2aproject/a2a-samples)
- [Google Gemini API](https://ai.google.dev/)

## License

MIT License - feel free to use this as a starting point for your own A2A agents!

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
