"""Domain models — canonical representations, independent of MCPs/APIs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

# Status do card no Jira
CardStatus = Literal["Teste regressivo", "Pronto para deploy", "Em Progresso"]

# Resultado da validação
ValidationStatus = Literal["approved", "rejected", "blocked"]


@dataclass(slots=True)
class Card:
    """Canonical Jira card (issue) representation after collection."""

    key: str  # Ex: "PB-5740"
    title: str
    issue_type: str  # "Incidente", "Bug", "Feature", etc
    status: CardStatus
    owner: str  # Responsável
    product: str  # Produto (Ex: "NewContract")
    repository: str | None = None  # Ex: "bernhoeft/autocadastro-front"
    pull_requests: list[str] = field(default_factory=list)  # URLs
    has_data_action: bool = False  # "Ação de dados = Sim"?
    description: str = ""
    jira_url: str = ""
    collected_at: datetime = field(default_factory=datetime.now)


@dataclass(slots=True)
class ValidationResult:
    """Result of applying validation rules (v2 + "só-banco" heuristic)."""

    card_key: str
    status: ValidationStatus  # "approved" | "rejected" | "blocked"
    reason: str  # Detalhamento do motivo
    evidence: str = ""  # O que levou à decisão (PR+repo / só-banco / etc)
    pending_items: list[str] = field(default_factory=list)  # Items to fix
    guidance: str = ""  # Orientação pro dev (se reprovado)
    validated_at: datetime = field(default_factory=datetime.now)


@dataclass(slots=True)
class ReleaseItem:
    """Item in a Release Notes page (Notion)."""

    card_key: str
    title: str
    owner: str
    pull_requests: list[str] | str  # URLs ou "• APENAS PROC"
    has_data_action: bool = False
    has_infra_action: bool = False
    merge_completed: bool = False


@dataclass(slots=True)
class Release:
    """Release/Hotfix documentation in Notion."""

    version: str  # "1.111.2"
    release_type: Literal["Release", "Hotfix"]
    items: list[ReleaseItem] = field(default_factory=list)
    notion_page_url: str = ""
    notion_page_id: str = ""
    tests: str = ""  # "Testes regressivos" block
    environments: str = ""  # "Ambientes" block
    repos_to_deploy: list[str] = field(default_factory=list)  # "Repositórios para Deploy"
    participants: str = ""  # "Participantes do Deploy" block
    created_at: datetime = field(default_factory=datetime.now)


@dataclass(slots=True)
class ExecutionSummary:
    """Consolidated summary of an orchestration run."""

    execution_id: str  # "release-2026-07-16-001"
    date: str
    release_version: str
    release_type: Literal["Release", "Hotfix"]
    trigger: str  # What prompted this run
    cards_collected: int
    cards_approved: int
    cards_rejected: int
    cards: list[dict] = field(default_factory=list)
    release_notes_updated: bool = False
    notion_page: str = ""
    notifications_sent: int = 0
    sync_passo_1_executed: bool = False
    stopped_at: str = ""
    status: Literal["em_andamento", "concluido", "erro"] = "em_andamento"
    errors: list[str] = field(default_factory=list)
    relatorio: str = ""
