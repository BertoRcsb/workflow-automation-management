"""Validator Service — applies eligibility rules (v2 + "só-banco" heuristic)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from workflow_automation_management.domain import Card, ValidationResult, ValidationStatus
from workflow_automation_management.shared import ValidationError, logger

if TYPE_CHECKING:
    from workflow_automation_management.domain import ValidatorPort

log = logging.getLogger(__name__)


class ValidatorService:
    """Validate cards using Rule v2 (PR+repo OR só-banco) + heuristic."""

    def __init__(self, validator_impl: ValidatorPort | None = None) -> None:
        """Initialize with optional validator implementation (for future MCP/API integration)."""
        self.validator = validator_impl
        self.logger = logger

    def validate(self, cards: list[Card]) -> tuple[list[Card], list[ValidationResult]]:
        """Validate a batch of cards and return (approved, validation_results).
        
        Rule v2:
        - Approved: has (PR + repository) OR (has_data_action=True AND banco_heuristic)
        - Rejected: none of the above
        
        Banco heuristic: has_data_action=True AND
          (assignee is database person OR description mentions proc/procedure/carga/query)
        
        Returns:
            (approved_cards, all_validation_results)
        """
        self.logger.info(f"🔍 Validador iniciado | total={len(cards)} cards")
        
        approved: list[Card] = []
        results: list[ValidationResult] = []
        
        for card in cards:
            result = self._apply_rule_v2(card)
            results.append(result)
            
            if result.status == "approved":
                approved.append(card)
                self.logger.info(f"✅ {card.key} aprovado ({result.evidence})")
            else:
                self.logger.warning(f"❌ {card.key} rejeitado ({result.reason})")
        
        self.logger.info(
            f"📊 Validação concluída | aprovados={len(approved)} / "
            f"rejeitados={len(results) - len(approved)}"
        )
        
        return approved, results

    def _apply_rule_v2(self, card: Card) -> ValidationResult:
        """Apply Rule v2 to a single card."""
        # Rule 1: Has PR + Repository (code change)
        has_pr = bool(card.pull_requests)
        has_repo = bool(card.repository and card.repository.lower() not in ("n/a", "apenas proc"))
        
        if has_pr and has_repo:
            return ValidationResult(
                card_key=card.key,
                status="approved",
                reason="PR + Repositório presente",
                evidence="PR+repo",
            )
        
        # Rule 2: Only data action (banco) — with heuristic
        if card.has_data_action:
            if self._is_legitimate_banco_action(card):
                return ValidationResult(
                    card_key=card.key,
                    status="approved",
                    reason="Ação apenas de banco (com heurística confirmada)",
                    evidence="só-banco (proc/procedure/query/carga detectado ou assignee banco)",
                )
            # has_data_action=True but NO heuristic match → suspicious
            return ValidationResult(
                card_key=card.key,
                status="rejected",
                reason="Ação de dados marcada mas sem evidência de proc/procedure ou responsável de banco",
                pending_items=["Confirmar tipo de ação de banco", "Verificar assignee"],
                guidance="Valide se é realmente apenas banco ou se falta PR/repo",
            )
        
        # Rule 3: No PR, no repo, no data action → REJECT
        return ValidationResult(
            card_key=card.key,
            status="rejected",
            reason="Sem PR/repositório e sem ação de banco",
            pending_items=["Fornecer PR ou repositório", "OU confirmar se é ação de dados"],
            guidance="Adicione PR/repo do código ou marque 'Ação de dados = Sim' se for proc/carga",
        )

    def _is_legitimate_banco_action(self, card: Card) -> bool:
        """Heuristic to detect legitimate database actions."""
        # Check if assignee is in known database team
        known_banco_people = [
            "alexandre bolonhini",
            "banco",
            "dba",
            "sql",
        ]
        assignee_lower = (card.owner or "").lower()
        if any(person in assignee_lower for person in known_banco_people):
            return True
        
        # Check if description mentions banco-related keywords
        banco_keywords = [
            "procedure",
            "proc",
            "proc_",
            "carga",
            "query",
            "sql",
            "banco",
            "seleção",
            "procedure",
        ]
        desc_lower = (card.description or "").lower()
        return any(kw in desc_lower for kw in banco_keywords)
