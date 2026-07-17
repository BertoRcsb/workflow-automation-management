"""Collector Service — orchestrates the collection phase."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from workflow_automation_management.domain import Card, CardStatus
from workflow_automation_management.shared import CollectionError, logger

if TYPE_CHECKING:
    from workflow_automation_management.domain import CollectorPort

log = logging.getLogger(__name__)


class CollectorService:
    """Orchestrate card collection from Jira."""

    def __init__(self, collector_impl: CollectorPort) -> None:
        """Initialize with a concrete Collector implementation."""
        self.collector = collector_impl
        self.logger = logger

    def collect_from_jira(
        self,
        project: str = "PB",
        statuses: list[CardStatus] | None = None,
        **kwargs,
    ) -> list[Card]:
        """Collect cards from Jira with given filters.
        
        Args:
            project: Jira project key (default: "PB")
            statuses: Target statuses (default: ["Teste regressivo", "Pronto para deploy"])
            **kwargs: Additional filters (card_key, etc)
        
        Returns:
            List of normalized Card objects.
        
        Raises:
            CollectionError: If collection fails.
        """
        if statuses is None:
            statuses = ["Teste regressivo", "Pronto para deploy"]
        
        self.logger.info(
            f"🔍 Coletor iniciado | projeto={project} | status={statuses} | kwargs={kwargs}"
        )
        
        try:
            cards = self.collector.collect_cards(
                project=project,
                statuses=statuses,
                **kwargs,
            )
            self.logger.info(f"✅ Coleta concluída | total={len(cards)} cards")
            return cards
        except Exception as e:
            msg = f"❌ Erro na coleta: {e}"
            self.logger.error(msg)
            raise CollectionError(msg) from e
