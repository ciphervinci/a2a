"""
Dynatrace API Client - Handles all interactions with Dynatrace REST API v2

This module provides methods to:
- Fetch problems detected by Davis AI
- Get entity topology and relationships
- Retrieve metrics data
- Access root cause evidence
"""
import os
from datetime import datetime, timedelta
from typing import Any
import httpx


class DynatraceClient:
    """
    Client for Dynatrace REST API v2.
    
    Provides methods to interact with:
    - Problems API v2 (Davis AI detected issues)
    - Entities API v2 (Topology/Smartscape)
    - Metrics API v2 (Performance data)
    - Events API v2 (Deployment, config changes)
    """
    
    def __init__(self):
        """Initialize the Dynatrace client with environment variables."""
        self.base_url = os.getenv("DYNATRACE_URL", "").rstrip("/")
        self.api_token = os.getenv("DYNATRACE_API_TOKEN", "")
        
        if not self.base_url:
            raise ValueError("DYNATRACE_URL environment variable is required")
        if not self.api_token:
            raise ValueError("DYNATRACE_API_TOKEN environment variable is required")
        
        self.headers = {
            "Authorization": f"Api-Token {self.api_token}",
            "Content-Type": "application/json",
        }
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: dict | None = None,
        json_data: dict | None = None
    ) -> dict[str, Any]:
        """Make an async HTTP request to Dynatrace API."""
        url = f"{self.base_url}/api/v2/{endpoint}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                json=json_data,
            )
            response.raise_for_status()
            return response.json()
    
    # =========================================================================
    # PROBLEMS API v2 - Davis AI Detected Issues
    # =========================================================================
    
    async def get_problems(
        self,
        status: str = "OPEN",
        from_time: str = "now-24h",
        to_time: str = "now",
        problem_selector: str | None = None,
        entity_selector: str | None = None,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """
        Get list of problems detected by Davis AI.
        
        Args:
            status: OPEN, CLOSED, or empty for all
            from_time: Start time (e.g., 'now-24h', 'now-7d', timestamp)
            to_time: End time
            problem_selector: Filter problems (e.g., 'severityLevel("AVAILABILITY")')
            entity_selector: Filter by affected entities
            page_size: Number of results per page
            
        Returns:
            Dict with 'problems' list and pagination info
        """
        params = {
            "from": from_time,
            "to": to_time,
            "pageSize": page_size,
            "fields": "+evidenceDetails,+impactAnalysis,+recentComments",
        }
        
        if status:
            params["problemSelector"] = f'status("{status}")'
            if problem_selector:
                params["problemSelector"] += f",{problem_selector}"
        elif problem_selector:
            params["problemSelector"] = problem_selector
            
        if entity_selector:
            params["entitySelector"] = entity_selector
        
        return await self._make_request("GET", "problems", params=params)
    
    async def get_problem_details(self, problem_id: str) -> dict[str, Any]:
        """
        Get detailed information about a specific problem.
        
        Includes:
        - Root cause evidence (metrics, events, availability)
        - Impact analysis (affected users, services, applications)
        - Affected entities
        - Related deployment events
        
        Args:
            problem_id: The Dynatrace problem ID (e.g., 'P-12345678')
            
        Returns:
            Detailed problem object with evidence and impact
        """
        params = {
            "fields": "+evidenceDetails,+impactAnalysis,+recentComments"
        }
        return await self._make_request("GET", f"problems/{problem_id}", params=params)
    
    # =========================================================================
    # ENTITIES API v2 - Topology/Smartscape
    # =========================================================================
    
    async def get_entities(
        self,
        entity_selector: str,
        from_time: str = "now-2h",
        fields: str | None = None,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """
        Get monitored entities based on selector.
        
        Args:
            entity_selector: Entity filter (e.g., 'type("SERVICE")', 'entityId("SERVICE-123")')
            from_time: Time range start
            fields: Additional fields to include (e.g., 'properties,toRelationships')
            page_size: Results per page
            
        Returns:
            Dict with 'entities' list
        """
        params = {
            "entitySelector": entity_selector,
            "from": from_time,
            "pageSize": page_size,
        }
        
        if fields:
            params["fields"] = fields
        
        return await self._make_request("GET", "entities", params=params)
    
    async def get_entity(
        self, 
        entity_id: str,
        from_time: str = "now-2h",
    ) -> dict[str, Any]:
        """
        Get details of a specific entity including relationships.
        
        Args:
            entity_id: Entity ID (e.g., 'HOST-ABC123', 'SERVICE-XYZ789')
            from_time: Time range for relationship data
            
        Returns:
            Entity details with properties and relationships
        """
        params = {
            "from": from_time,
            "fields": "+properties,+toRelationships,+fromRelationships,+tags",
        }
        return await self._make_request("GET", f"entities/{entity_id}", params=params)
    
    async def get_entity_topology(
        self,
        entity_id: str,
        depth: int = 2,
    ) -> dict[str, Any]:
        """
        Get the topology (dependencies) around an entity.
        
        This is useful for understanding service dependencies,
        which processes run on which hosts, etc.
        
        Args:
            entity_id: Starting entity ID
            depth: How many relationship levels to traverse
            
        Returns:
            Entity with its relationships
        """
        # Get the entity with relationships
        entity = await self.get_entity(entity_id)
        
        # Build topology map
        topology = {
            "root": entity,
            "upstream": [],  # Entities that call this one
            "downstream": [],  # Entities this one calls
        }
        
        # Get relationships
        if "toRelationships" in entity:
            for rel_type, rel_entities in entity.get("toRelationships", {}).items():
                for rel_entity in rel_entities:
                    topology["downstream"].append({
                        "relationship": rel_type,
                        "entity": rel_entity,
                    })
        
        if "fromRelationships" in entity:
            for rel_type, rel_entities in entity.get("fromRelationships", {}).items():
                for rel_entity in rel_entities:
                    topology["upstream"].append({
                        "relationship": rel_type,
                        "entity": rel_entity,
                    })
        
        return topology
    
    # =========================================================================
    # METRICS API v2 - Performance Data
    # =========================================================================
    
    async def get_metrics(
        self,
        metric_selector: str,
        entity_selector: str | None = None,
        from_time: str = "now-1h",
        to_time: str = "now",
        resolution: str = "5m",
    ) -> dict[str, Any]:
        """
        Query metrics data.
        
        Args:
            metric_selector: Metric to query (e.g., 'builtin:service.response.time')
            entity_selector: Filter entities
            from_time: Start time
            to_time: End time
            resolution: Data resolution (e.g., '1m', '5m', '1h')
            
        Returns:
            Metrics data with values
        """
        params = {
            "metricSelector": metric_selector,
            "from": from_time,
            "to": to_time,
            "resolution": resolution,
        }
        
        if entity_selector:
            params["entitySelector"] = entity_selector
        
        return await self._make_request("GET", "metrics/query", params=params)
    
    async def get_service_metrics(
        self,
        service_id: str,
        from_time: str = "now-1h",
    ) -> dict[str, Any]:
        """
        Get key performance metrics for a service.
        
        Args:
            service_id: Service entity ID
            from_time: Time range start
            
        Returns:
            Dict with response time, throughput, error rate
        """
        metrics = {}
        
        # Response time
        response_time = await self.get_metrics(
            metric_selector="builtin:service.response.time:avg",
            entity_selector=f'entityId("{service_id}")',
            from_time=from_time,
        )
        metrics["response_time"] = response_time
        
        # Throughput
        throughput = await self.get_metrics(
            metric_selector="builtin:service.requestCount.total:rate(1m)",
            entity_selector=f'entityId("{service_id}")',
            from_time=from_time,
        )
        metrics["throughput"] = throughput
        
        # Error rate
        error_rate = await self.get_metrics(
            metric_selector="builtin:service.errors.total.rate",
            entity_selector=f'entityId("{service_id}")',
            from_time=from_time,
        )
        metrics["error_rate"] = error_rate
        
        return metrics
    
    async def get_host_metrics(
        self,
        host_id: str,
        from_time: str = "now-1h",
    ) -> dict[str, Any]:
        """
        Get key metrics for a host.
        
        Args:
            host_id: Host entity ID
            from_time: Time range start
            
        Returns:
            Dict with CPU, memory, disk metrics
        """
        metrics = {}
        
        # CPU usage
        cpu = await self.get_metrics(
            metric_selector="builtin:host.cpu.usage:avg",
            entity_selector=f'entityId("{host_id}")',
            from_time=from_time,
        )
        metrics["cpu_usage"] = cpu
        
        # Memory usage
        memory = await self.get_metrics(
            metric_selector="builtin:host.mem.usage:avg",
            entity_selector=f'entityId("{host_id}")',
            from_time=from_time,
        )
        metrics["memory_usage"] = memory
        
        return metrics
    
    # =========================================================================
    # EVENTS API v2 - Deployments, Configuration Changes
    # =========================================================================
    
    async def get_events(
        self,
        event_selector: str | None = None,
        entity_selector: str | None = None,
        from_time: str = "now-24h",
        to_time: str = "now",
    ) -> dict[str, Any]:
        """
        Get events (deployments, config changes, custom events).
        
        Args:
            event_selector: Filter events (e.g., 'eventType("CUSTOM_DEPLOYMENT")')
            entity_selector: Filter by affected entities
            from_time: Start time
            to_time: End time
            
        Returns:
            List of events
        """
        params = {
            "from": from_time,
            "to": to_time,
            "pageSize": 100,
        }
        
        if event_selector:
            params["eventSelector"] = event_selector
        if entity_selector:
            params["entitySelector"] = entity_selector
        
        return await self._make_request("GET", "events", params=params)
    
    async def get_recent_deployments(
        self,
        entity_selector: str | None = None,
        from_time: str = "now-7d",
    ) -> dict[str, Any]:
        """
        Get recent deployment events.
        
        Args:
            entity_selector: Filter by entity
            from_time: How far back to look
            
        Returns:
            List of deployment events
        """
        event_selector = 'eventType("CUSTOM_DEPLOYMENT")'
        return await self.get_events(
            event_selector=event_selector,
            entity_selector=entity_selector,
            from_time=from_time,
        )
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def format_problem_summary(self, problem: dict) -> str:
        """Format a problem into a human-readable summary."""
        title = problem.get("title", "Unknown Problem")
        status = problem.get("status", "UNKNOWN")
        severity = problem.get("severityLevel", "UNKNOWN")
        impact = problem.get("impactLevel", "UNKNOWN")
        
        # Get affected entities
        affected = problem.get("affectedEntities", [])
        affected_names = [e.get("name", e.get("entityId", {}).get("id", "Unknown")) 
                        for e in affected[:5]]
        
        # Get root cause entity
        root_cause = problem.get("rootCauseEntity", {})
        root_cause_name = root_cause.get("name", "Unknown")
        
        # Start/end times
        start_time = problem.get("startTime", 0)
        end_time = problem.get("endTime", -1)
        
        if start_time:
            start_str = datetime.fromtimestamp(start_time / 1000).strftime("%Y-%m-%d %H:%M:%S")
        else:
            start_str = "Unknown"
            
        if end_time > 0:
            end_str = datetime.fromtimestamp(end_time / 1000).strftime("%Y-%m-%d %H:%M:%S")
        else:
            end_str = "Ongoing"
        
        summary = f"""
📋 **Problem: {title}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• **Status:** {status}
• **Severity:** {severity}
• **Impact Level:** {impact}
• **Started:** {start_str}
• **Ended:** {end_str}
• **Root Cause Entity:** {root_cause_name}
• **Affected Entities:** {', '.join(affected_names)}
"""
        return summary.strip()
    
    def format_evidence_summary(self, evidence_details: dict) -> str:
        """Format root cause evidence into readable text."""
        details = evidence_details.get("details", [])
        
        if not details:
            return "No evidence details available."
        
        evidence_text = []
        for evidence in details:
            evidence_type = evidence.get("evidenceType", "UNKNOWN")
            display_name = evidence.get("displayName", "Unknown Evidence")
            is_root_cause = evidence.get("rootCauseRelevant", False)
            
            marker = "🔴" if is_root_cause else "🔵"
            
            evidence_text.append(f"{marker} **{evidence_type}**: {display_name}")
            
            # Add specific details based on evidence type
            if evidence_type == "METRIC":
                metric_id = evidence.get("metricId", "")
                if metric_id:
                    evidence_text.append(f"   Metric: {metric_id}")
            elif evidence_type == "EVENT":
                event_type = evidence.get("eventType", "")
                if event_type:
                    evidence_text.append(f"   Event Type: {event_type}")
        
        return "\n".join(evidence_text)
