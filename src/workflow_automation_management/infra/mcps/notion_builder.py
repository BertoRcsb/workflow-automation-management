"""Notion Builder implementation (using Notion MCP)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from workflow_automation_management.domain import BuilderPort, Release
from workflow_automation_management.shared import BuildError, logger

if TYPE_CHECKING:
    pass

log = logging.getLogger(__name__)


class NotionBuilder(BuilderPort):
    """Create/update Release Notes page in Notion (Notion MCP integration)."""

    def __init__(self, database_id: str = "23e19d89-2318-81ff-812d-000b6afb6b5a"):
        """Initialize with Notion database ID.
        
        Args:
            database_id: Notion database ID for "Versões - NewContract" (from spec).
        """
        self.database_id = database_id
        self.logger = logger
        self._mock_pages: dict[str, dict] = {}  # In-memory storage for testing
        # TODO: Initialize MCP client for Notion
        # self.mcp_client = NotionMCPClient(database_id)

    def create_or_update_release(self, release: Release) -> str:
        """Create or update a Release Notes page in Notion.
        
        Args:
            release: Release object with version, items, etc.
        
        Returns:
            URL of the Notion page.
        
        Raises:
            BuildError: If creation/update fails.
        """
        try:
            self.logger.info(f"Creating/updating Notion page for v{release.version}")
            
            # Check if page exists
            existing = self.fetch_release(release.version)
            
            if existing:
                # Update existing page
                page_url = self._update_page(release)
                self.logger.info(f"Updated existing page: {page_url}")
            else:
                # Create new page
                page_url = self._create_page(release)
                self.logger.info(f"Created new page: {page_url}")
            
            return page_url
            
        except Exception as e:
            raise BuildError(f"Failed to create/update Notion page: {e}") from e

    def fetch_release(self, version: str) -> Release | None:
        """Fetch an existing release from Notion by version.
        
        Args:
            version: Release version (e.g., "1.111.2").
        
        Returns:
            Release object or None if not found.
        """
        try:
            self.logger.debug(f"Fetching release {version} from Notion")
            
            # Query Notion database for page with version (TODO: actual MCP call)
            # pages = self.mcp_client.query_database(
            #     database_id=self.database_id,
            #     filter={"property": "Versão", "title": {"equals": version}},
            # )
            
            # For now, return None (page doesn't exist)
            pages = self._mock_fetch(version)
            
            if not pages:
                return None
            
            # Parse page into Release object
            return self._parse_page(pages[0])
            
        except Exception as e:
            self.logger.warning(f"Could not fetch release {version}: {e}")
            return None

    def _create_page(self, release: Release) -> str:
        """Create a new page in Notion."""
        # TODO: Call Notion MCP to create page
        # return self.mcp_client.create_page(...)
        
        # For now, store in mock storage and generate URL
        page_url = f"https://app.notion.com/p/notion-mock-{release.version}"
        page_id = f"page-{release.version}"
        
        self._mock_pages[release.version] = {
            "id": page_id,
            "properties": {
                "Versão": {"title": [{"text": {"content": release.version}}]},
                "Tipo": {"select": {"name": release.release_type}},
            },
            "url": page_url,
        }
        
        return page_url

    def _update_page(self, release: Release) -> str:
        """Update an existing page in Notion."""
        # TODO: Call Notion MCP to update page
        # return self.mcp_client.update_page(...)
        
        # Update mock storage
        if release.version in self._mock_pages:
            self._mock_pages[release.version]["properties"]["Tipo"] = {
                "select": {"name": release.release_type}
            }
            return self._mock_pages[release.version]["url"]
        
        return release.notion_page_url or "https://app.notion.com/p/mock-url"

    def _mock_fetch(self, version: str) -> list[dict]:
        """Return mock Notion response for testing."""
        # Check in-memory mock storage first
        if version in self._mock_pages:
            return [self._mock_pages[version]]
        
        # Default mock for 1.110.0
        if version == "1.110.0":
            return [
                {
                    "id": "page-1",
                    "properties": {
                        "Versão": {"title": [{"text": {"content": "1.110.0"}}]},
                        "Tipo": {"select": {"name": "Release"}},
                        "Repositórios para Deploy": {"rich_text": ["autocadastro-front"]},
                    },
                    "url": "https://app.notion.com/p/39f19d89231881e4a2ebea8cb573467e",
                }
            ]
        
        return []

    def _parse_page(self, page: dict) -> Release:
        """Parse a Notion page into a Release object."""
        props = page.get("properties", {})
        
        return Release(
            version=props.get("Versão", {}).get("title", [{}])[0].get("text", {}).get("content", ""),
            release_type=props.get("Tipo", {}).get("select", {}).get("name", "Release"),  # type: ignore
            notion_page_url=page.get("url", ""),
            notion_page_id=page.get("id", ""),
        )
