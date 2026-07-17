"""Jira Collector implementation (using Atlassian MCP)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from workflow_automation_management.domain import Card, CollectorPort
from workflow_automation_management.shared import CollectionError, logger

if TYPE_CHECKING:
    pass

log = logging.getLogger(__name__)


class JiraCollector(CollectorPort):
    """Fetch and normalize cards from Jira (Atlassian MCP integration)."""

    def __init__(self, cloud_id: str = "f36e5519-1f88-4f71-a406-75326e86deda"):
        """Initialize with Jira Cloud ID.
        
        Args:
            cloud_id: Atlassian Cloud ID (from spec/spec.md).
        """
        self.cloud_id = cloud_id
        self.logger = logger
        # TODO: Initialize MCP client for Atlassian
        # self.mcp_client = AtlassianMCPClient(cloud_id)

    def collect_cards(
        self,
        project: str = "PB",
        statuses: list[str] | None = None,
        issue_type: str = "Incidente",
        card_key: str | None = None,
        **kwargs,
    ) -> list[Card]:
        """Collect cards from Jira with filters.
        
        Args:
            project: Jira project key (e.g., "PB").
            statuses: Target statuses (e.g., ["Teste regressivo", "Pronto para deploy"]).
            issue_type: Issue type to filter (default: "Incidente").
            card_key: Optional specific card key (e.g., "PB-5740").
            **kwargs: Additional JQL filters.
        
        Returns:
            List of normalized Card objects.
        
        Raises:
            CollectionError: If Jira query fails.
        """
        if statuses is None:
            statuses = ["Teste regressivo", "Pronto para deploy"]
        
        try:
            # Build JQL query
            jql = self._build_jql(project, statuses, issue_type, card_key)
            self.logger.debug(f"JQL Query: {jql}")
            
            # Query Jira (TODO: replace with actual MCP call)
            # issues = self.mcp_client.search_jira_issues(jql)
            
            # For now, return mock data
            issues = self._mock_jira_response(project, card_key)
            
            # Normalize to Card objects
            cards = [self._normalize_card(issue) for issue in issues]
            
            self.logger.info(f"Collected {len(cards)} cards from Jira")
            return cards
            
        except Exception as e:
            raise CollectionError(f"Failed to collect from Jira: {e}") from e

    def _build_jql(
        self,
        project: str,
        statuses: list[str],
        issue_type: str,
        card_key: str | None,
    ) -> str:
        """Build a Jira Query Language string."""
        conditions = [f"project = {project}"]
        
        if card_key:
            conditions.append(f"key = {card_key}")
        else:
            conditions.append(f"issuetype = {issue_type}")
            status_clause = " OR ".join(f'status = "{s}"' for s in statuses)
            conditions.append(f"({status_clause})")
        
        return " AND ".join(conditions)

    def _mock_jira_response(self, project: str, card_key: str | None) -> list[dict[str, Any]]:
        """Return mock Jira response for testing."""
        # TODO: Remove once MCP integration is ready
        
        if card_key == "PB-5740":
            return [
                {
                    "key": "PB-5740",
                    "fields": {
                        "summary": 'Bloqueio no Autocadastro - Etapa 4 ("Nenhum e-mail cadastrado")',
                        "issuetype": {"name": "Bug"},
                        "status": {"name": "Teste regressivo"},
                        "assignee": {"displayName": "Anderson de Oliveira Santos"},
                        "customfield_10000": "NewContract",  # Product
                        "customfield_10001": "bernhoeft/bernhoeft-grt-autocadastro-front",  # Repo
                        "customfield_10002": [
                            "https://bitbucket.org/bernhoeft/bernhoeft-grt-autocadastro-front/pull-requests/244"
                        ],  # PRs
                        "customfield_10003": False,  # has_data_action
                        "description": "Fix for autocadastro blocking issue",
                    },
                }
            ]
        
        # Return empty if no matching filter
        return []

    def _normalize_card(self, jira_issue: dict[str, Any]) -> Card:
        """Normalize a Jira issue into a Card."""
        fields = jira_issue.get("fields", {})
        
        return Card(
            key=jira_issue.get("key", ""),
            title=fields.get("summary", ""),
            issue_type=fields.get("issuetype", {}).get("name", ""),
            status=fields.get("status", {}).get("name", ""),
            owner=fields.get("assignee", {}).get("displayName", ""),
            product=fields.get("customfield_10000", ""),  # Product field
            repository=fields.get("customfield_10001", ""),  # Repository field
            pull_requests=fields.get("customfield_10002", []),  # PR URLs
            has_data_action=fields.get("customfield_10003", False),  # Data action field
            description=fields.get("description", ""),
            jira_url=jira_issue.get("self", ""),
        )
