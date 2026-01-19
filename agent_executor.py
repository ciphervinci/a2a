"""
Agent Executor - Bridges the Dynatrace Agent with the A2A Protocol

This executor:
1. Receives A2A protocol messages
2. Parses user intent
3. Routes to appropriate Dynatrace agent skills
4. Returns formatted responses
"""
import re
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

from dynatrace_agent import DynatraceAgent


class DynatraceAgentExecutor(AgentExecutor):
    """
    A2A Agent Executor for the Dynatrace AI Agent.
    
    Routes incoming A2A messages to the appropriate Dynatrace agent skills:
    - get_problems: List open problems
    - analyze_problem: Root cause analysis
    - get_topology: Service dependencies
    - get_health: Entity health check
    - create_incident: ServiceNow summary
    - query: Natural language questions
    """
    
    def __init__(self):
        self.agent = DynatraceAgent()
    
    def _extract_query(self, context: RequestContext) -> str:
        """Extract the user's text message from the A2A request."""
        message = context.message
        if message and message.parts:
            for part in message.parts:
                if hasattr(part, 'text') and part.text:
                    return part.text
        return ""
    
    def _parse_intent(self, query: str) -> tuple[str, dict]:
        """
        Parse user query to determine which skill to invoke.
        
        Returns:
            tuple: (skill_name, parameters)
        """
        query_lower = query.lower().strip()
        
        # =====================================================================
        # Intent: Get Open Problems
        # Examples: "show problems", "list open issues", "what's wrong"
        # =====================================================================
        problem_patterns = [
            r"(?:show|list|get|what are|any)\s*(?:the\s*)?(?:open\s*)?problems?",
            r"what(?:'s| is) wrong",
            r"any\s*(?:open\s*)?issues?",
            r"current\s*(?:problems?|issues?|alerts?)",
            r"(?:show|list)\s*alerts?",
        ]
        
        for pattern in problem_patterns:
            if re.search(pattern, query_lower):
                # Check for time range
                time_match = re.search(r"(?:last|past)\s*(\d+)\s*(h|hour|d|day|w|week)", query_lower)
                if time_match:
                    num = time_match.group(1)
                    unit = time_match.group(2)[0]  # First char: h, d, or w
                    time_range = f"{num}{unit}"
                else:
                    time_range = "24h"
                
                return ("get_problems", {"time_range": time_range})
        
        # =====================================================================
        # Intent: Analyze Specific Problem
        # Examples: "analyze P-123", "root cause for P-456", "investigate problem P-789"
        # =====================================================================
        analyze_patterns = [
            r"(?:analyze|investigate|root\s*cause|details?\s*(?:for|of|about)?|explain)\s*(?:problem\s*)?[\"']?(P-\d+)[\"']?",
            r"(?:what(?:'s| is)\s*(?:causing|wrong\s*with))\s*(?:problem\s*)?[\"']?(P-\d+)[\"']?",
            r"[\"']?(P-\d+)[\"']?\s*(?:analysis|details?|root\s*cause)",
        ]
        
        for pattern in analyze_patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                # Try to find problem ID in original query (preserve case)
                problem_id_match = re.search(r"(P-\d+)", query, re.IGNORECASE)
                if problem_id_match:
                    return ("analyze_problem", {"problem_id": problem_id_match.group(1).upper()})
        
        # Also match just a problem ID by itself
        if re.match(r"^P-\d+$", query.strip(), re.IGNORECASE):
            return ("analyze_problem", {"problem_id": query.strip().upper()})
        
        # =====================================================================
        # Intent: Get Service Topology
        # Examples: "topology for OrderService", "dependencies of payment-service"
        # =====================================================================
        topology_patterns = [
            r"(?:topology|dependencies|dependency|architecture|map)\s*(?:for|of)?\s*[\"']?([a-zA-Z0-9_\-\.]+)[\"']?",
            r"(?:what\s*(?:does|services?))\s*[\"']?([a-zA-Z0-9_\-\.]+)[\"']?\s*(?:call|depend|connect)",
            r"[\"']?([a-zA-Z0-9_\-\.]+)[\"']?\s*(?:topology|dependencies|architecture)",
        ]
        
        for pattern in topology_patterns:
            match = re.search(pattern, query_lower)
            if match:
                service_name = match.group(1)
                # Find the actual service name from original query
                orig_match = re.search(rf"[\"']?({re.escape(service_name)})[\"']?", query, re.IGNORECASE)
                if orig_match:
                    return ("get_topology", {"service_name": orig_match.group(1)})
                return ("get_topology", {"service_name": service_name})
        
        # =====================================================================
        # Intent: Get Entity Health
        # Examples: "health of HOST-123", "status of SERVICE-456"
        # =====================================================================
        health_patterns = [
            r"(?:health|status|metrics?|check)\s*(?:for|of)?\s*[\"']?((?:HOST|SERVICE|PROCESS|APPLICATION)-[A-Z0-9]+)[\"']?",
            r"[\"']?((?:HOST|SERVICE|PROCESS|APPLICATION)-[A-Z0-9]+)[\"']?\s*(?:health|status|metrics?)",
            r"how\s*is\s*[\"']?((?:HOST|SERVICE|PROCESS|APPLICATION)-[A-Z0-9]+)[\"']?",
        ]
        
        for pattern in health_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return ("get_health", {"entity_id": match.group(1).upper()})
        
        # =====================================================================
        # Intent: Create ServiceNow Incident Summary
        # Examples: "create incident for P-123", "servicenow summary P-456"
        # =====================================================================
        incident_patterns = [
            r"(?:create|generate|make)\s*(?:servicenow\s*)?incident\s*(?:for|from)?\s*[\"']?(P-\d+)[\"']?",
            r"(?:servicenow|snow)\s*(?:summary|incident)\s*(?:for)?\s*[\"']?(P-\d+)[\"']?",
            r"[\"']?(P-\d+)[\"']?\s*(?:servicenow|snow|incident)",
        ]
        
        for pattern in incident_patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                # Find problem ID in original query
                problem_id_match = re.search(r"(P-\d+)", query, re.IGNORECASE)
                if problem_id_match:
                    return ("create_incident", {"problem_id": problem_id_match.group(1).upper()})
        
        # =====================================================================
        # Default: Natural Language Query
        # =====================================================================
        return ("query", {"question": query})
    
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """
        Handle incoming A2A requests.
        
        Routes the request to the appropriate Dynatrace agent skill
        based on the parsed intent.
        """
        query = self._extract_query(context)
        
        # Handle empty queries
        if not query:
            response = self._get_help_message()
            await event_queue.enqueue_event(new_agent_text_message(response))
            return
        
        # Parse intent and get parameters
        skill, params = self._parse_intent(query)
        
        # Route to appropriate skill
        try:
            if skill == "get_problems":
                response = await self.agent.get_open_problems(
                    time_range=params.get("time_range", "24h")
                )
            
            elif skill == "analyze_problem":
                response = await self.agent.analyze_problem(
                    problem_id=params["problem_id"]
                )
            
            elif skill == "get_topology":
                response = await self.agent.get_service_topology(
                    service_name=params["service_name"]
                )
            
            elif skill == "get_health":
                response = await self.agent.get_entity_health(
                    entity_id=params["entity_id"]
                )
            
            elif skill == "create_incident":
                response = await self.agent.create_incident_summary(
                    problem_id=params["problem_id"]
                )
            
            else:  # query (natural language)
                response = await self.agent.query(
                    question=params.get("question", query)
                )
        
        except Exception as e:
            response = f"❌ Error executing {skill}: {str(e)}"
        
        # Send response
        await event_queue.enqueue_event(new_agent_text_message(response))
    
    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Handle cancellation requests."""
        await event_queue.enqueue_event(
            new_agent_text_message("Task cancelled.")
        )
    
    def _get_help_message(self) -> str:
        """Return help message explaining available capabilities."""
        return """# 🔷 Dynatrace AI Agent

I'm your AI-powered observability assistant for Dynatrace! Here's what I can do:

## 📋 Available Commands

### 🚨 Get Problems
View open problems detected by Davis AI:
- "Show open problems"
- "List issues from the last 7 days"
- "Any current alerts?"

### 🔍 Analyze Problem (Root Cause)
Deep-dive into a specific problem:
- "Analyze P-12345678"
- "Root cause for P-87654321"
- "Investigate problem P-11111111"

### 🌐 Service Topology
View service dependencies:
- "Topology for OrderService"
- "Dependencies of payment-service"
- "What does checkout-api call?"

### 🏥 Entity Health
Check health of a specific entity:
- "Health of HOST-ABC123"
- "Status of SERVICE-XYZ789"
- "Metrics for PROCESS-DEF456"

### 📋 ServiceNow Integration
Create incident summary for ServiceNow:
- "Create incident for P-12345678"
- "ServiceNow summary P-87654321"

### 💬 Natural Language
Ask any question about your environment:
- "What services are affected by the current issues?"
- "Are there any database-related problems?"
- "How many hosts are monitored?"

---
**Tip:** Provide a Problem ID (like `P-12345678`) for detailed analysis!
"""
