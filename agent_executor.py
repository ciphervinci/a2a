"""
Agent Executor - Bridges the Joke Agent with the A2A Protocol
"""
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from joke_agent import JokeAgent


class JokeAgentExecutor(AgentExecutor):
    """
    A2A Agent Executor for the Joke Generator Agent.
    
    This class bridges the A2A protocol with our JokeAgent implementation,
    handling incoming requests and generating appropriate responses.
    """
    
    def __init__(self):
        self.agent = JokeAgent()
    
    def _extract_query(self, context: RequestContext) -> str:
        """Extract the user's query from the request context."""
        message = context.message
        if message and message.parts:
            for part in message.parts:
                if hasattr(part, 'text') and part.text:
                    return part.text
        return ""
    
    def _parse_command(self, query: str) -> tuple[str, str | None]:
        """
        Parse the user's query to determine what action to take.
        
        Returns:
            tuple: (action, parameter)
            - action: 'tell_joke' or 'explain_joke'
            - parameter: topic for tell_joke, or the joke text for explain_joke
        """
        query_lower = query.lower().strip()
        
        # Check if user wants an explanation
        if query_lower.startswith("explain:") or query_lower.startswith("why is this funny:"):
            joke_text = query.split(":", 1)[1].strip() if ":" in query else ""
            return ("explain_joke", joke_text)
        
        # Check for topic-specific joke requests
        topic_keywords = ["about", "on", "regarding", "related to"]
        for keyword in topic_keywords:
            if keyword in query_lower:
                parts = query_lower.split(keyword, 1)
                if len(parts) > 1:
                    topic = parts[1].strip().rstrip("?!.")
                    return ("tell_joke", topic)
        
        # Default: just tell a random joke
        # Try to extract any topic hints from the query
        if "joke" in query_lower:
            # Remove common words to find potential topic
            words_to_remove = ["tell", "me", "a", "joke", "please", "can", "you", "give", "another", "one", "more"]
            words = query_lower.replace("?", "").replace("!", "").split()
            remaining = [w for w in words if w not in words_to_remove]
            if remaining:
                return ("tell_joke", " ".join(remaining))
        
        return ("tell_joke", None)
    
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """
        Handle incoming A2A requests.
        
        This method is called when a client sends a message to the agent.
        It processes the request and sends the response back via the event queue.
        """
        query = self._extract_query(context)
        
        if not query:
            response = "Hi! I'm the Joke Agent! 🎭\n\nTry asking me:\n- 'Tell me a joke'\n- 'Tell me a joke about programming'\n- 'Explain: [paste a joke here]'"
        else:
            action, parameter = self._parse_command(query)
            
            if action == "explain_joke" and parameter:
                response = await self.agent.explain_joke(parameter)
            elif action == "tell_joke":
                response = await self.agent.tell_joke(parameter)
            else:
                response = await self.agent.tell_joke()
        
        # Send the response back to the client
        await event_queue.enqueue_event(new_agent_text_message(response))
    
    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Handle cancellation requests."""
        await event_queue.enqueue_event(
            new_agent_text_message("Task cancelled. No more jokes for now! 😢")
        )
