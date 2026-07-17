"""Domain-level errors — semantic exceptions for orchestration."""

from __future__ import annotations


class OrchestrationError(Exception):
    """Base exception for all orchestration failures."""

    pass


class CollectionError(OrchestrationError):
    """Failed to collect cards from Jira."""

    pass


class ValidationError(OrchestrationError):
    """Validation gate encountered an issue (not a card being invalid)."""

    pass


class BuildError(OrchestrationError):
    """Failed to create/update Notion page."""

    pass


class SyncError(OrchestrationError):
    """Sync (repos.yaml, make run) encountered an issue."""

    pass


class NotFoundError(OrchestrationError):
    """Resource not found (e.g., release not in Notion)."""

    pass


class ConfigError(OrchestrationError):
    """Configuration is missing or invalid."""

    pass
