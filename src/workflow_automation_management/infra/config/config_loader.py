"""Configuration loader — reads spec and environment settings."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from workflow_automation_management.shared import ConfigError, logger


@dataclass
class JiraConfig:
    """Jira configuration."""

    cloud_id: str = "f36e5519-1f88-4f71-a406-75326e86deda"
    project: str = "PB"
    issue_type: str = "Incidente"
    target_statuses: list[str] = None  # type: ignore

    def __post_init__(self):
        if self.target_statuses is None:
            self.target_statuses = ["Teste regressivo", "Pronto para deploy"]


@dataclass
class NotionConfig:
    """Notion configuration."""

    database_id: str = "23e19d89-2318-81ff-812d-000b6afb6b5a"
    base_name: str = "Versões - NewContract"


@dataclass
class StorageConfig:
    """Storage configuration."""

    execucoes_dir: str = "execucoes"
    erros_dir: str = "erros"


@dataclass
class Config:
    """Global configuration."""

    jira: JiraConfig
    notion: NotionConfig
    storage: StorageConfig


def load_config(spec_path: str | Path = "spec/spec.md") -> Config:
    """Load configuration from spec file or environment.
    
    Reads from:
      1. Environment variables (JIRA_CLOUD_ID, etc)
      2. spec/spec.md (fallback defaults)
    
    Args:
        spec_path: Path to spec file (for documentation purposes).
    
    Returns:
        Config object with all settings.
    
    Raises:
        ConfigError: If required settings are missing.
    """
    try:
        jira_config = JiraConfig(
            cloud_id=os.getenv(
                "JIRA_CLOUD_ID", "f36e5519-1f88-4f71-a406-75326e86deda"
            ),
            project=os.getenv("JIRA_PROJECT", "PB"),
            issue_type=os.getenv("JIRA_ISSUE_TYPE", "Incidente"),
        )
        
        notion_config = NotionConfig(
            database_id=os.getenv(
                "NOTION_DATABASE_ID", "23e19d89-2318-81ff-812d-000b6afb6b5a"
            ),
            base_name=os.getenv("NOTION_BASE_NAME", "Versões - NewContract"),
        )
        
        storage_config = StorageConfig(
            execucoes_dir=os.getenv("EXECUCOES_DIR", "execucoes"),
            erros_dir=os.getenv("ERROS_DIR", "erros"),
        )
        
        config = Config(
            jira=jira_config,
            notion=notion_config,
            storage=storage_config,
        )
        
        logger.info(
            f"✅ Config loaded | project={config.jira.project} | "
            f"notion_db={config.notion.database_id[:8]}..."
        )
        return config
        
    except Exception as e:
        raise ConfigError(f"Failed to load configuration: {e}") from e
