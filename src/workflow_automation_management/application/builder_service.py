"""Builder Service — orchestrates Release Notes page creation/update in Notion."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from workflow_automation_management.domain import Card, Release, ReleaseItem, ValidationResult
from workflow_automation_management.shared import BuildError, logger

if TYPE_CHECKING:
    from workflow_automation_management.domain import BuilderPort

log = logging.getLogger(__name__)


class BuilderService:
    """Orchestrate release notes creation/update in Notion."""

    def __init__(self, builder_impl: BuilderPort) -> None:
        """Initialize with a concrete Builder implementation."""
        self.builder = builder_impl
        self.logger = logger

    def create_or_update_release(
        self,
        version: str,
        release_type: str,
        approved_cards: list[Card],
        repos_to_deploy: list[str] | None = None,
    ) -> Release:
        """Create or update a Release Notes page in Notion.
        
        Args:
            version: Release version (e.g., "1.111.2")
            release_type: "Release" or "Hotfix"
            approved_cards: Cards approved by validator
            repos_to_deploy: List of repos to include in "Repositórios para Deploy" block
        
        Returns:
            Release object with Notion page URL populated.
        
        Raises:
            BuildError: If creation/update fails.
        """
        self.logger.info(
            f"🔨 Montador iniciado | versão={version} | tipo={release_type} | "
            f"cards={len(approved_cards)}"
        )
        
        try:
            # Build release model from approved cards
            release = self._build_release_model(
                version=version,
                release_type=release_type,
                cards=approved_cards,
                repos_to_deploy=repos_to_deploy,
            )
            
            # Create/update in Notion
            page_url = self.builder.create_or_update_release(release)
            release.notion_page_url = page_url
            
            # Re-fetch to verify (ensure consistency)
            fetched = self.builder.fetch_release(version)
            if not fetched:
                raise BuildError(f"Page created but re-fetch failed for version {version}")
            
            self.logger.info(f"✅ Montagem concluída | página={page_url}")
            return release
        except Exception as e:
            msg = f"❌ Erro na montagem: {e}"
            self.logger.error(msg)
            raise BuildError(msg) from e

    def _build_release_model(
        self,
        version: str,
        release_type: str,
        cards: list[Card],
        repos_to_deploy: list[str] | None = None,
    ) -> Release:
        """Build a Release object from validated cards."""
        items: list[ReleaseItem] = []
        
        for card in cards:
            # Pull requests: URLs or "• APENAS PROC" for banco-only
            pr_display = card.pull_requests
            if not pr_display and card.has_data_action:
                pr_display = ["• APENAS PROC"]
            
            item = ReleaseItem(
                card_key=card.key,
                title=card.title,
                owner=card.owner,
                pull_requests=pr_display,
                has_data_action=card.has_data_action,
            )
            items.append(item)
        
        return Release(
            version=version,
            release_type=release_type,  # type: ignore
            items=items,
            repos_to_deploy=repos_to_deploy or [],
        )
