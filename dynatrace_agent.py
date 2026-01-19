"""
Dynatrace AI Agent - Combines Dynatrace observability data with AI-powered analysis

This agent provides:
1. Problem Detection & Alerting (Davis AI integration)
2. Root Cause Analysis with AI reasoning
3. Service Topology Analysis
4. Impact Assessment
5. Remediation Suggestions
"""
import os
import json
from datetime import datetime
from typing import Any
from google import genai

from dynatrace_client import DynatraceClient


class DynatraceAgent:
    """
    AI-powered Dynatrace Agent for observability and root cause analysis.
    
    This agent:
    - Fetches problems and metrics from Dynatrace
    - Uses Gemini AI to analyze and correlate data
    - Provides intelligent root cause analysis
    - Suggests remediation actions
    """
    
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]
    
    def __init__(self):
        """Initialize Dynatrace client and Gemini AI."""
        self.dynatrace = DynatraceClient()
        
        # Initialize Gemini for AI analysis
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        self.genai_client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash"
    
    async def _ai_analyze(self, prompt: str) -> str:
        """Use Gemini to analyze data and generate insights."""
        try:
            response = self.genai_client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            return f"AI analysis unavailable: {str(e)}"
    
    # =========================================================================
    # SKILL 1: Get Open Problems
    # =========================================================================
    
    async def get_open_problems(self, time_range: str = "24h") -> str:
        """
        Get all open problems detected by Davis AI.
        
        Args:
            time_range: How far back to look (e.g., '24h', '7d')
            
        Returns:
            Formatted list of open problems with severity and impact
        """
        try:
            from_time = f"now-{time_range}"
            result = await self.dynatrace.get_problems(
                status="OPEN",
                from_time=from_time,
            )
            
            problems = result.get("problems", [])
            
            if not problems:
                return f"✅ **No open problems** detected in the last {time_range}. Your environment is healthy!"
            
            # Format the problems
            output = [f"🚨 **{len(problems)} Open Problem(s)** detected in the last {time_range}:\n"]
            
            for i, problem in enumerate(problems, 1):
                output.append(f"\n**{i}. {problem.get('title', 'Unknown')}**")
                output.append(f"   • Problem ID: `{problem.get('problemId', 'N/A')}`")
                output.append(f"   • Severity: {problem.get('severityLevel', 'N/A')}")
                output.append(f"   • Impact: {problem.get('impactLevel', 'N/A')}")
                
                # Root cause entity
                root_cause = problem.get("rootCauseEntity", {})
                if root_cause:
                    output.append(f"   • Root Cause: {root_cause.get('name', 'Unknown')}")
                
                # Affected entities count
                affected = problem.get("affectedEntities", [])
                output.append(f"   • Affected Entities: {len(affected)}")
            
            return "\n".join(output)
            
        except Exception as e:
            return f"❌ Error fetching problems: {str(e)}"
    
    # =========================================================================
    # SKILL 2: Analyze Problem (Root Cause Analysis)
    # =========================================================================
    
    async def analyze_problem(self, problem_id: str) -> str:
        """
        Perform deep root cause analysis on a specific problem.
        
        This skill:
        1. Fetches problem details from Dynatrace
        2. Gets evidence (metrics, events, topology)
        3. Checks for recent deployments
        4. Uses AI to correlate and analyze
        5. Provides root cause determination and remediation suggestions
        
        Args:
            problem_id: The Dynatrace problem ID (e.g., 'P-12345')
            
        Returns:
            Comprehensive root cause analysis with recommendations
        """
        try:
            # Step 1: Get problem details
            problem = await self.dynatrace.get_problem_details(problem_id)
            
            title = problem.get("title", "Unknown Problem")
            status = problem.get("status", "UNKNOWN")
            severity = problem.get("severityLevel", "UNKNOWN")
            
            # Step 2: Extract evidence
            evidence_details = problem.get("evidenceDetails", {})
            evidence_list = evidence_details.get("details", [])
            
            # Step 3: Get affected entities
            affected_entities = problem.get("affectedEntities", [])
            root_cause_entity = problem.get("rootCauseEntity", {})
            
            # Step 4: Get impact analysis
            impact_analysis = problem.get("impactAnalysis", {})
            impacts = impact_analysis.get("impacts", [])
            
            # Step 5: Check for recent deployments near the root cause entity
            deployments = []
            if root_cause_entity:
                entity_id = root_cause_entity.get("entityId", {}).get("id", "")
                if entity_id:
                    try:
                        deploy_result = await self.dynatrace.get_recent_deployments(
                            entity_selector=f'entityId("{entity_id}")',
                            from_time="now-7d"
                        )
                        deployments = deploy_result.get("events", [])
                    except:
                        pass  # Deployments are optional context
            
            # Step 6: Build context for AI analysis
            ai_context = {
                "problem_title": title,
                "severity": severity,
                "root_cause_entity": root_cause_entity.get("name", "Unknown"),
                "root_cause_entity_type": root_cause_entity.get("entityId", {}).get("type", "Unknown"),
                "evidence": [
                    {
                        "type": e.get("evidenceType"),
                        "name": e.get("displayName"),
                        "is_root_cause": e.get("rootCauseRelevant", False)
                    }
                    for e in evidence_list[:10]  # Limit to top 10
                ],
                "affected_entities_count": len(affected_entities),
                "impacted_users": sum(
                    i.get("impactedUsers", 0) for i in impacts if isinstance(i.get("impactedUsers"), int)
                ),
                "recent_deployments": [
                    {
                        "title": d.get("title", "Unknown"),
                        "timestamp": d.get("startTime", 0)
                    }
                    for d in deployments[:5]
                ]
            }
            
            # Step 7: AI-powered analysis
            ai_prompt = f"""You are an expert SRE/DevOps engineer analyzing a Dynatrace problem.

**Problem Context:**
{json.dumps(ai_context, indent=2)}

Based on this data, provide:

1. **Root Cause Determination**: What is the most likely root cause based on the evidence?

2. **Correlation Analysis**: Are there any correlations between the evidence (e.g., deployment before the issue, metric anomalies)?

3. **Impact Assessment**: How severe is this issue and what is affected?

4. **Recommended Remediation**: What specific actions should the ops team take?

5. **Prevention**: How can this be prevented in the future?

Be specific and actionable. Reference the actual evidence provided."""

            ai_analysis = await self._ai_analyze(ai_prompt)
            
            # Step 8: Build the response
            output = [
                f"# 🔍 Root Cause Analysis: {title}",
                f"\n**Problem ID:** `{problem_id}`",
                f"**Status:** {status} | **Severity:** {severity}",
                f"\n---\n",
                f"## 📊 Evidence Summary\n",
            ]
            
            # Add evidence
            for evidence in evidence_list[:5]:
                marker = "🔴" if evidence.get("rootCauseRelevant") else "⚪"
                output.append(f"{marker} **{evidence.get('evidenceType', 'N/A')}**: {evidence.get('displayName', 'N/A')}")
            
            # Add deployment info if any
            if deployments:
                output.append(f"\n## 🚀 Recent Deployments\n")
                for deploy in deployments[:3]:
                    timestamp = deploy.get("startTime", 0)
                    if timestamp:
                        deploy_time = datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M")
                    else:
                        deploy_time = "Unknown"
                    output.append(f"• {deploy.get('title', 'Unknown')} ({deploy_time})")
            
            # Add AI analysis
            output.append(f"\n---\n")
            output.append(f"## 🤖 AI-Powered Analysis\n")
            output.append(ai_analysis)
            
            return "\n".join(output)
            
        except Exception as e:
            return f"❌ Error analyzing problem {problem_id}: {str(e)}"
    
    # =========================================================================
    # SKILL 3: Get Service Topology
    # =========================================================================
    
    async def get_service_topology(self, service_name: str) -> str:
        """
        Get the topology/dependencies for a service.
        
        Shows:
        - What calls this service (upstream)
        - What this service calls (downstream)
        - Host/process relationships
        
        Args:
            service_name: Name or ID of the service
            
        Returns:
            Service topology map with dependencies
        """
        try:
            # First, find the service by name
            if service_name.startswith("SERVICE-"):
                entity_selector = f'entityId("{service_name}")'
            else:
                entity_selector = f'type("SERVICE"),entityName.contains("{service_name}")'
            
            result = await self.dynatrace.get_entities(
                entity_selector=entity_selector,
                fields="+toRelationships,+fromRelationships,+properties",
            )
            
            entities = result.get("entities", [])
            
            if not entities:
                return f"❌ No service found matching '{service_name}'"
            
            service = entities[0]
            service_id = service.get("entityId", "")
            service_display_name = service.get("displayName", service_name)
            
            output = [
                f"# 🌐 Service Topology: {service_display_name}",
                f"\n**Entity ID:** `{service_id}`\n",
            ]
            
            # Upstream (what calls this service)
            from_relationships = service.get("fromRelationships", {})
            output.append("## ⬆️ Upstream (Callers)")
            
            callers = from_relationships.get("calls", [])
            if callers:
                for caller in callers[:10]:
                    output.append(f"  • {caller.get('type', 'Unknown')}: {caller.get('id', 'Unknown')}")
            else:
                output.append("  No upstream callers detected")
            
            # Downstream (what this service calls)
            to_relationships = service.get("toRelationships", {})
            output.append("\n## ⬇️ Downstream (Dependencies)")
            
            dependencies = to_relationships.get("calls", [])
            if dependencies:
                for dep in dependencies[:10]:
                    output.append(f"  • {dep.get('type', 'Unknown')}: {dep.get('id', 'Unknown')}")
            else:
                output.append("  No downstream dependencies detected")
            
            # Host/Process relationships
            runs_on = to_relationships.get("runsOn", [])
            if runs_on:
                output.append("\n## 🖥️ Infrastructure")
                for host in runs_on[:5]:
                    output.append(f"  • Runs on: {host.get('id', 'Unknown')}")
            
            return "\n".join(output)
            
        except Exception as e:
            return f"❌ Error getting topology: {str(e)}"
    
    # =========================================================================
    # SKILL 4: Get Entity Health
    # =========================================================================
    
    async def get_entity_health(self, entity_id: str) -> str:
        """
        Get health status and key metrics for an entity.
        
        Args:
            entity_id: Entity ID (HOST-xxx, SERVICE-xxx, etc.)
            
        Returns:
            Health status with relevant metrics
        """
        try:
            entity = await self.dynatrace.get_entity(entity_id)
            
            entity_type = entity.get("type", "UNKNOWN")
            display_name = entity.get("displayName", entity_id)
            
            output = [
                f"# 🏥 Entity Health: {display_name}",
                f"\n**Type:** {entity_type}",
                f"**ID:** `{entity_id}`\n",
            ]
            
            # Get relevant metrics based on entity type
            if entity_type == "HOST":
                metrics = await self.dynatrace.get_host_metrics(entity_id)
                output.append("## 📊 Host Metrics (Last Hour)")
                
                # Format CPU
                cpu_data = metrics.get("cpu_usage", {}).get("result", [])
                if cpu_data:
                    output.append(f"  • CPU Usage: Queried")
                
                # Format Memory
                mem_data = metrics.get("memory_usage", {}).get("result", [])
                if mem_data:
                    output.append(f"  • Memory Usage: Queried")
                    
            elif entity_type == "SERVICE":
                metrics = await self.dynatrace.get_service_metrics(entity_id)
                output.append("## 📊 Service Metrics (Last Hour)")
                output.append("  • Response Time, Throughput, Error Rate: Queried")
            
            # Check for open problems affecting this entity
            problems_result = await self.dynatrace.get_problems(
                entity_selector=f'entityId("{entity_id}")',
                status="OPEN",
                from_time="now-24h",
            )
            
            problems = problems_result.get("problems", [])
            if problems:
                output.append(f"\n## ⚠️ Open Problems ({len(problems)})")
                for p in problems[:3]:
                    output.append(f"  • {p.get('title', 'Unknown')}")
            else:
                output.append("\n## ✅ No Open Problems")
            
            return "\n".join(output)
            
        except Exception as e:
            return f"❌ Error getting entity health: {str(e)}"
    
    # =========================================================================
    # SKILL 5: Create Incident Summary (for ServiceNow integration)
    # =========================================================================
    
    async def create_incident_summary(self, problem_id: str) -> str:
        """
        Create a structured incident summary suitable for ServiceNow.
        
        This generates a JSON-formatted summary that can be used to
        create enriched incident records in ServiceNow.
        
        Args:
            problem_id: Dynatrace problem ID
            
        Returns:
            JSON structure with incident details for ServiceNow
        """
        try:
            # Get problem details
            problem = await self.dynatrace.get_problem_details(problem_id)
            
            # Extract key information
            title = problem.get("title", "Unknown Problem")
            severity = problem.get("severityLevel", "UNKNOWN")
            impact_level = problem.get("impactLevel", "UNKNOWN")
            status = problem.get("status", "UNKNOWN")
            
            # Time information
            start_time = problem.get("startTime", 0)
            end_time = problem.get("endTime", -1)
            
            if start_time:
                start_str = datetime.fromtimestamp(start_time / 1000).isoformat()
            else:
                start_str = None
                
            if end_time > 0:
                end_str = datetime.fromtimestamp(end_time / 1000).isoformat()
            else:
                end_str = None
            
            # Root cause
            root_cause = problem.get("rootCauseEntity", {})
            root_cause_name = root_cause.get("name", "Unknown")
            root_cause_type = root_cause.get("entityId", {}).get("type", "Unknown")
            
            # Evidence
            evidence_details = problem.get("evidenceDetails", {})
            evidence_list = [
                {
                    "type": e.get("evidenceType"),
                    "description": e.get("displayName"),
                    "isRootCause": e.get("rootCauseRelevant", False)
                }
                for e in evidence_details.get("details", [])[:10]
            ]
            
            # Affected entities
            affected = [
                {
                    "name": e.get("name"),
                    "type": e.get("entityId", {}).get("type"),
                    "id": e.get("entityId", {}).get("id")
                }
                for e in problem.get("affectedEntities", [])[:20]
            ]
            
            # Build ServiceNow-friendly structure
            incident_data = {
                "source": "Dynatrace Davis AI",
                "problemId": problem_id,
                "title": title,
                "severity": severity,
                "impactLevel": impact_level,
                "status": status,
                "startTime": start_str,
                "endTime": end_str,
                "rootCause": {
                    "entity": root_cause_name,
                    "entityType": root_cause_type,
                    "entityId": root_cause.get("entityId", {}).get("id")
                },
                "evidence": evidence_list,
                "affectedEntities": affected,
                "dynatraceUrl": f"{self.dynatrace.base_url}/#problems/problemdetails;pid={problem_id}"
            }
            
            # Add AI-generated summary
            ai_prompt = f"""Summarize this IT incident in 2-3 sentences for a ServiceNow ticket:
            
Problem: {title}
Severity: {severity}
Root Cause Entity: {root_cause_name} ({root_cause_type})
Evidence: {', '.join([e['description'] for e in evidence_list[:5] if e.get('description')])}

Be concise and technical."""

            ai_summary = await self._ai_analyze(ai_prompt)
            incident_data["aiSummary"] = ai_summary
            
            # Format output
            output = [
                "# 📋 ServiceNow Incident Summary",
                f"\n**Problem:** {title}",
                f"**Severity:** {severity} | **Impact:** {impact_level}",
                f"\n**Root Cause:** {root_cause_name} ({root_cause_type})",
                f"\n**AI Summary:** {ai_summary}",
                f"\n---\n",
                "## 📦 Structured Data (JSON)\n",
                "```json",
                json.dumps(incident_data, indent=2),
                "```"
            ]
            
            return "\n".join(output)
            
        except Exception as e:
            return f"❌ Error creating incident summary: {str(e)}"
    
    # =========================================================================
    # SKILL 6: Natural Language Query
    # =========================================================================
    
    async def query(self, question: str) -> str:
        """
        Answer natural language questions about the Dynatrace environment.
        
        Args:
            question: Natural language question
            
        Returns:
            AI-generated answer based on Dynatrace data
        """
        try:
            # Determine what data we need based on the question
            question_lower = question.lower()
            
            context_data = {}
            
            # Fetch relevant data based on question keywords
            if any(word in question_lower for word in ["problem", "issue", "alert", "incident"]):
                problems_result = await self.dynatrace.get_problems(
                    status="OPEN",
                    from_time="now-24h"
                )
                context_data["open_problems"] = [
                    {
                        "title": p.get("title"),
                        "severity": p.get("severityLevel"),
                        "rootCause": p.get("rootCauseEntity", {}).get("name")
                    }
                    for p in problems_result.get("problems", [])[:10]
                ]
            
            if any(word in question_lower for word in ["service", "application"]):
                services_result = await self.dynatrace.get_entities(
                    entity_selector='type("SERVICE")',
                    from_time="now-2h"
                )
                context_data["services"] = [
                    s.get("displayName") 
                    for s in services_result.get("entities", [])[:20]
                ]
            
            if any(word in question_lower for word in ["host", "server", "infrastructure"]):
                hosts_result = await self.dynatrace.get_entities(
                    entity_selector='type("HOST")',
                    from_time="now-2h"
                )
                context_data["hosts"] = [
                    h.get("displayName")
                    for h in hosts_result.get("entities", [])[:20]
                ]
            
            # Generate AI response
            ai_prompt = f"""You are a Dynatrace expert assistant. Answer the following question based on the environment data provided.

**Question:** {question}

**Available Environment Data:**
{json.dumps(context_data, indent=2) if context_data else "No specific data fetched - provide general guidance."}

Provide a helpful, specific answer. If the data doesn't contain enough information, explain what additional queries might help."""

            response = await self._ai_analyze(ai_prompt)
            
            return response
            
        except Exception as e:
            return f"❌ Error processing query: {str(e)}"
