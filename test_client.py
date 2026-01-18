"""
Test Client for the A2A Joke Generator Server

This script demonstrates how to interact with the A2A server
using HTTP requests directly.

Usage:
    python test_client.py [--url http://localhost:8000]
"""
import argparse
import json
import httpx
import uuid


def get_agent_card(base_url: str) -> dict:
    """Fetch the agent card from the server."""
    url = f"{base_url}/.well-known/agent.json"
    response = httpx.get(url)
    response.raise_for_status()
    return response.json()


def send_message(base_url: str, message: str) -> dict:
    """
    Send a message to the A2A agent using the JSON-RPC protocol.
    
    The A2A protocol uses JSON-RPC 2.0 for communication.
    """
    url = base_url.rstrip("/")
    
    # Create the JSON-RPC request
    request_body = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [
                    {
                        "kind": "text",
                        "text": message
                    }
                ],
                "messageId": str(uuid.uuid4()),
            }
        }
    }
    
    response = httpx.post(
        url,
        json=request_body,
        headers={"Content-Type": "application/json"},
        timeout=30.0
    )
    response.raise_for_status()
    return response.json()


def extract_response_text(response: dict) -> str:
    """Extract the text response from the JSON-RPC response."""
    try:
        result = response.get("result", {})
        
        # The response could be a Task or a Message
        if "messages" in result:
            messages = result["messages"]
            if messages:
                last_message = messages[-1]
                parts = last_message.get("parts", [])
                for part in parts:
                    if part.get("kind") == "text":
                        return part.get("text", "")
        
        # Or it might be directly in artifacts
        if "artifacts" in result:
            artifacts = result["artifacts"]
            if artifacts:
                for artifact in artifacts:
                    parts = artifact.get("parts", [])
                    for part in parts:
                        if part.get("kind") == "text":
                            return part.get("text", "")
        
        # Fallback: return the raw result
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error parsing response: {e}\nRaw: {json.dumps(response, indent=2)}"


def main():
    parser = argparse.ArgumentParser(description="Test client for A2A Joke Agent")
    parser.add_argument(
        "--url", 
        default="http://localhost:8000",
        help="Base URL of the A2A server"
    )
    args = parser.parse_args()
    
    base_url = args.url.rstrip("/")
    
    print("=" * 60)
    print("🎭 A2A Joke Generator - Test Client")
    print("=" * 60)
    
    # Step 1: Fetch the agent card
    print("\n📇 Fetching Agent Card...")
    try:
        agent_card = get_agent_card(base_url)
        print(f"   Name: {agent_card.get('name')}")
        print(f"   Description: {agent_card.get('description')}")
        print(f"   Version: {agent_card.get('version')}")
        print(f"   Skills: {[s['name'] for s in agent_card.get('skills', [])]}")
    except Exception as e:
        print(f"   ❌ Error fetching agent card: {e}")
        return
    
    # Step 2: Test various requests
    test_messages = [
        "Tell me a joke",
        "Tell me a joke about programming",
        "Tell me a joke about cats",
        "Explain: Why did the programmer quit his job? Because he didn't get arrays!",
    ]
    
    for msg in test_messages:
        print(f"\n{'='*60}")
        print(f"📤 Sending: {msg}")
        print("-" * 60)
        
        try:
            response = send_message(base_url, msg)
            text = extract_response_text(response)
            print(f"📥 Response:\n{text}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n{'='*60}")
    print("✅ Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
