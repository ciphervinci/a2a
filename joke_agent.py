"""
Joke Generator Agent - Uses Google Gemini API to generate jokes
"""
import os
from google import genai


class JokeAgent:
    """A joke-telling AI agent powered by Google Gemini."""
    
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash"
    
    async def tell_joke(self, topic: str | None = None) -> str:
        """Generate a joke, optionally about a specific topic."""
        
        if topic:
            prompt = f"""You are a professional comedian. Tell me a funny, 
            clean, and original joke about: {topic}
            
            Keep it short (2-4 lines max) and family-friendly.
            Just give me the joke directly without any introduction."""
        else:
            prompt = """You are a professional comedian. Tell me a funny, 
            clean, and original joke. 
            
            Keep it short (2-4 lines max) and family-friendly.
            Just give me the joke directly without any introduction."""
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            return f"Oops! My joke generator broke down. Error: {str(e)}"
    
    async def explain_joke(self, joke: str) -> str:
        """Explain why a joke is funny (for those who don't get it)."""
        
        prompt = f"""Explain why this joke is funny in a simple, 
        friendly way (keep it brief):
        
        Joke: {joke}"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            return f"Sorry, I couldn't explain that joke. Error: {str(e)}"
