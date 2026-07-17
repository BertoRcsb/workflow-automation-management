"""Workflow Automation Management — Release Notes Orchestrator."""

__version__ = "0.1.0"

from workflow_automation_management.application import Orchestrator, Reporter
from workflow_automation_management.domain import (
    Card,
    ExecutionSummary,
    Release,
    ValidationResult,
)
from workflow_automation_management.infra import JiraCollector, NotionBuilder, load_config
from workflow_automation_management.interfaces import main

__all__ = [
    "Orchestrator",
    "Reporter",
    "Card",
    "Release",
    "ValidationResult",
    "ExecutionSummary",
    "JiraCollector",
    "NotionBuilder",
    "load_config",
    "main",
]
