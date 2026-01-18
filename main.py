"""
A2A Joke Generator Server - Main Entry Point

This A2A-compliant server exposes a joke-telling agent powered by Google Gemini.
It can tell jokes on any topic and explain why jokes are funny.

Usage:
    python main.py --host 0.0.0.0 --port 8000
    
Environment Variables:
    GEMINI_API_KEY: Your Google Gemini API key (required)
    PORT: Server port (optional, for deployment platforms like Render)
"""
import os
import uvicorn
from dotenv import load_dotenv

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)

from agent_executor import JokeAgentExecutor
from joke_agent import JokeAgent

# Load environment variables from .env file (for local development)
load_dotenv()


def get_agent_card(host: str, port: int) -> AgentCard:
    """
    Create and return the Agent Card for the Joke Agent.
    
    The Agent Card is like a business card for your agent - it tells
    other agents and clients what this agent can do.
    """
    
    # Define the skills this agent offers
    tell_joke_skill = AgentSkill(
        id="tell_joke",
        name="Tell a Joke",
        description="Generates a funny, clean joke. Optionally about a specific topic.",
        tags=["joke", "humor", "comedy", "entertainment"],
        examples=[
            "Tell me a joke",
            "Tell me a joke about programming",
            "Give me a joke about cats",
            "I need a laugh, tell me something funny about office life",
        ],
    )
    
    explain_joke_skill = AgentSkill(
        id="explain_joke",
        name="Explain a Joke",
        description="Explains why a joke is funny for those who don't get it.",
        tags=["explain", "humor", "comedy"],
        examples=[
            "Explain: Why did the chicken cross the road? To get to the other side!",
            "Why is this funny: A SQL query walks into a bar, walks up to two tables and asks... 'Can I join you?'",
        ],
    )
    
    # Define agent capabilities
    capabilities = AgentCapabilities(
        streaming=False,  # We don't support streaming responses (yet)
        pushNotifications=False,  # We don't support push notifications
    )
    
    # Determine the URL based on environment
    # For deployment, use the HOST_URL environment variable
    host_url = os.getenv("HOST_URL")
    if host_url:
        url = host_url.rstrip("/") + "/"
    else:
        url = f"http://{host}:{port}/"
    
    # Create the Agent Card
    agent_card = AgentCard(
        name="Joke Generator Agent",
        description="A friendly AI comedian that tells jokes on any topic! "
                    "Powered by Google Gemini. Ask for a joke or get one explained.",
        url=url,
        version="1.0.0",
        defaultInputModes=JokeAgent.SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=JokeAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[tell_joke_skill, explain_joke_skill],
    )
    
    return agent_card


def create_app(host: str = "0.0.0.0", port: int = 8000):
    """Create and configure the A2A Starlette application."""
    
    # Create the agent executor
    agent_executor = JokeAgentExecutor()
    
    # Create the request handler with an in-memory task store
    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=InMemoryTaskStore(),
    )
    
    # Create the A2A application
    app = A2AStarletteApplication(
        agent_card=get_agent_card(host, port),
        http_handler=request_handler,
    )
    
    return app.build()


def main():
    """Main entry point for the server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="A2A Joke Generator Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument(
        "--port", 
        type=int, 
        default=int(os.getenv("PORT", 8000)),  # Use PORT env var for platforms like Render
        help="Port to listen on"
    )
    
    args = parser.parse_args()
    
    # Validate that we have the required API key
    if not os.getenv("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY environment variable is required!")
        print("Get your free API key at: https://aistudio.google.com/app/apikey")
        exit(1)
    
    print(f"🎭 Starting Joke Generator A2A Server...")
    print(f"📍 Host: {args.host}")
    print(f"📍 Port: {args.port}")
    print(f"🔗 Agent Card URL: http://{args.host}:{args.port}/.well-known/agent.json")
    print("-" * 50)
    
    # Create and run the app
    app = create_app(args.host, args.port)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
