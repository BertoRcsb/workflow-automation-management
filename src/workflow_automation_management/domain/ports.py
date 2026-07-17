"""Port definitions (abstract interfaces) for the three main skills."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from workflow_automation_management.domain.models import Card, Release, ValidationResult


class CollectorPort(ABC):
    """Contract for the Collector skill (Jira integration)."""

    @abstractmethod
    def collect_cards(self, **kwargs) -> list[Card]:
        """Fetch and normalize cards from Jira (project, status, etc).
        
        Returns:
            List of normalized Card objects ready for validation.
        """
        pass


class ValidatorPort(ABC):
    """Contract for the Validator skill (eligibility rules)."""

    @abstractmethod
    def validate_card(self, card: Card) -> ValidationResult:
        """Apply validation rule v2 + "só-banco" heuristic.
        
        Returns:
            ValidationResult with status (approved/rejected/blocked) + reason.
        """
        pass


class BuilderPort(ABC):
    """Contract for the Builder skill (Notion documentation)."""

    @abstractmethod
    def create_or_update_release(self, release: Release) -> str:
        """Create/update release notes page in Notion.
        
        Returns:
            Notion page URL.
        """
        pass

    @abstractmethod
    def fetch_release(self, version: str) -> Release | None:
        """Fetch existing release from Notion by version.
        
        Returns:
            Release object or None if not found.
        """
        pass


class LoggerProtocol(Protocol):
    """Duck-typed logger interface."""

    def debug(self, msg: str, *args, **kwargs) -> None:
        """Log debug message."""
        pass

    def info(self, msg: str, *args, **kwargs) -> None:
        """Log info message."""
        pass

    def warning(self, msg: str, *args, **kwargs) -> None:
        """Log warning message."""
        pass

    def error(self, msg: str, *args, **kwargs) -> None:
        """Log error message."""
        pass
