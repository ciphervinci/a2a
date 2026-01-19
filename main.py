"""
A2A Dynatrace Agent Server - Main Entry Point
"""
import os
import uvicorn
from dotenv import load_dotenv

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from agent_executor import DynatraceAgentExecutor
from dynatrace_agent import DynatraceAgent

load_dotenv()


def get_agent_card(host: str, port: int) -> AgentCard:
    """Create the Agent Card for the Dynatrace Agent."""
    
    # Skill 1: Get Open Problems
    get_problems_skill = AgentSkill(
        id="get_problems",
        name="Get Open Problems",
        description="Retrieve open problems detected by Dynatrace Davis AI with severity and impact.",
        tags=["problems", "alerts", "davis", "monitoring"],
        examples=[
            "Show open problems",
            "List issues from the last 7 days",
            "Any current alerts?",
        ],
    )
    
    # Skill 2: Root Cause Analysis
    analyze_problem_skill = AgentSkill(
        id="analyze_problem",
        name="Root Cause Analysis",
        description="Deep root cause analysis with evidence correlation, deployment checks, and AI recommendations.",
        tags=["root-cause", "analysis", "troubleshooting", "davis"],
        examples=[
            "Analyze P-12345678",
            "Root cause for P-87654321",
            "Investigate problem P-11111111",
        ],
    )
    
    # Skill 3: Service Topology
    get_topology_skill = AgentSkill(
        id="get_topology",
        name="Service Topology",
        description="Get service dependencies and relationships from Smartscape topology.",
        tags=["topology", "dependencies", "smartscape", "architecture"],
        examples=[
            "Topology for OrderService",
            "Dependencies of payment-service",
            "What does checkout-api call?",
        ],
    )
    
    # Skill 4: Entity Health
    get_health_skill = AgentSkill(
        id="get_health",
        name="Entity Health Check",
        description="Check health status and metrics for hosts, services, and processes.",
        tags=["health", "metrics", "status", "monitoring"],
        examples=[
            "Health of HOST-ABC123",
            "Status of SERVICE-XYZ789",
            "Metrics for PROCESS-DEF456",
        ],
    )
    
    # Skill 5: ServiceNow Integration
    create_incident_skill = AgentSkill(
        id="create_incident",
        name="ServiceNow Incident Summary",
        description="Generate structured incident summary for ServiceNow integration with AI analysis.",
        tags=["servicenow", "incident", "integration", "itsm"],
        examples=[
            "Create incident for P-12345678",
            "ServiceNow summary P-87654321",
        ],
    )
    
    # Skill 6: Natural Language Query
    query_skill = AgentSkill(
        id="query",
        name="Natural Language Query",
        description="Answer natural language questions about the Dynatrace environment.",
        tags=["query", "question", "natural-language", "ai"],
        examples=[
            "What services are affected by current issues?",
            "Are there any database-related problems?",
            "How many hosts are being monitored?",
        ],
    )
    
    # Agent capabilities
    capabilities = AgentCapabilities(
        streaming=False,
        pushNotifications=False,
    )
    
    # Determine URL
    host_url = os.getenv("HOST_URL")
    if host_url:
        url = host_url.rstrip("/") + "/"
    else:
        url = f"http://{host}:{port}/"
    
    # Create Agent Card
    agent_card = AgentCard(
        name="Dynatrace AI Agent",
        description="AI-powered observability agent for Dynatrace. Provides problem detection, "
                    "root cause analysis, service topology, and ServiceNow integration. "
                    "Powered by Davis AI and Gemini.",
        url=url,
        version="1.0.0",
        defaultInputModes=DynatraceAgent.SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=DynatraceAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[
            get_problems_skill,
            analyze_problem_skill,
            get_topology_skill,
            get_health_skill,
            create_incident_skill,
            query_skill,
        ],
    )
    
    return agent_card


def create_app(host: str = "0.0.0.0", port: int = 8000):
    """Create and configure the A2A Starlette application."""
    
    agent_executor = DynatraceAgentExecutor()
    
    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=InMemoryTaskStore(),
    )
    
    app = A2AStarletteApplication(
        agent_card=get_agent_card(host, port),
        http_handler=request_handler,
    )
    
    return app.build()


def validate_environment():
    """Validate required environment variables."""
    required_vars = [
        ("DYNATRACE_URL", "Your Dynatrace environment URL"),
        ("DYNATRACE_API_TOKEN", "Dynatrace API token"),
        ("GEMINI_API_KEY", "Google Gemini API key"),
    ]
    
    missing = []
    for var, description in required_vars:
        if not os.getenv(var):
            missing.append(f"  - {var}: {description}")
    
    if missing:
        print("❌ Missing required environment variables:")
        print("\n".join(missing))
        print("\nSee .env.example for configuration details.")
        return False
    
    return True


def main():
    """Main entry point for the server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="A2A Dynatrace Agent Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument(
        "--port", 
        type=int, 
        default=int(os.getenv("PORT", 8000)),
        help="Port to listen on"
    )
    
    args = parser.parse_args()
    
    # Validate environment
    if not validate_environment():
        exit(1)
    
    # Print startup info
    dynatrace_url = os.getenv("DYNATRACE_URL", "").rstrip("/")
    
    print("=" * 60)
    print("🔷 Dynatrace A2A Agent")
    print("=" * 60)
    print(f"📍 Server: http://{args.host}:{args.port}")
    print(f"📋 Agent Card: http://{args.host}:{args.port}/.well-known/agent.json")
    print(f"🔗 Dynatrace: {dynatrace_url}")
    print("=" * 60)
    print("\n🚀 Starting server...\n")
    
    # Create and run app
    app = create_app(args.host, args.port)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
