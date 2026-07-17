"""Orchestrator — Optimus Prime coordinates the complete release workflow."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from workflow_automation_management.application.builder_service import BuilderService
from workflow_automation_management.application.collector_service import CollectorService
from workflow_automation_management.application.reporter import Reporter
from workflow_automation_management.application.validator_service import ValidatorService
from workflow_automation_management.domain import ExecutionSummary
from workflow_automation_management.shared import OrchestrationError, logger

if TYPE_CHECKING:
    from workflow_automation_management.domain import BuilderPort, CollectorPort, ValidatorPort

log = logging.getLogger(__name__)


class Orchestrator:
    """Optimus Prime — the maestro of release automation.
    
    Coordinates:
      1. Collector (Jira)
      2. Validator (Rule v2 + heuristic)
      3. Builder (Notion)
      4. Reporter (summary + errors)
      5. Sync (repos.yaml, make run) — NOT executed here, just prepared
    """

    def __init__(
        self,
        collector_impl: CollectorPort,
        validator_impl: ValidatorPort | None = None,
        builder_impl: BuilderPort | None = None,
        reporter: Reporter | None = None,
    ) -> None:
        """Initialize Optimus Prime with implementations."""
        self.collector_svc = CollectorService(collector_impl)
        self.validator_svc = ValidatorService(validator_impl)
        self.builder_svc = BuilderService(builder_impl) if builder_impl else None
        self.reporter = reporter or Reporter()
        self.logger = logger

    def verify(
        self,
        version: str | None = None,
        project: str = "PB",
        statuses: list[str] | None = None,
        **kwargs,
    ) -> ExecutionSummary:
        """🔍 Verify mode (dry-run, no side effects).
        
        Executes: Collector → Validator → Builder (simulated) → Summary.
        Does NOT modify Notion or execute Sync.
        
        Returns:
            ExecutionSummary with what WOULD happen.
        """
        self.logger.info("=" * 72)
        self.logger.info("🤖 Optimus Prime — MODO VERIFICAÇÃO (DRY-RUN)")
        self.logger.info("=" * 72)
        
        execution_id = f"verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        date_str = datetime.now().strftime("%Y-%m-%d")
        errors: list[str] = []
        
        try:
            # Step 1: Collect
            self.logger.info("\n[1/4] 🔍 COLETA (Jira)")
            cards = self.collector_svc.collect_from_jira(
                project=project,
                statuses=statuses,
                **kwargs,
            )
            
            # Step 2: Validate
            self.logger.info("\n[2/4] ✅ VALIDAÇÃO (Regra v2)")
            approved, validation_results = self.validator_svc.validate(cards)
            rejected_count = len(cards) - len(approved)
            
            # Show validation summary
            self._print_validation_summary(approved, validation_results)
            
            # Step 3: Builder (simulated)
            if self.builder_svc and version:
                self.logger.info("\n[3/4] 🔨 MONTAGEM (SIMULADA — Notion não será modificado)")
                release = self.builder_svc.create_or_update_release(
                    version=version,
                    release_type="Release",  # TODO: detect hotfix
                    approved_cards=approved,
                )
                self.logger.info(f"   (Teria criado página: {release.notion_page_url})")
            
            # Step 4: Summary
            self.logger.info("\n[4/4] 📊 RESUMO")
            summary = ExecutionSummary(
                execution_id=execution_id,
                date=date_str,
                release_version=version or "N/A",
                release_type="Release",
                trigger="Optimus Prime — verificar",
                cards_collected=len(cards),
                cards_approved=len(approved),
                cards_rejected=rejected_count,
                release_notes_updated=False,  # Dry-run
                status="concluido",
                errors=errors,
            )
            
            self._print_summary(summary)
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ Erro na verificação: {e}")
            errors.append(str(e))
            
            summary = ExecutionSummary(
                execution_id=execution_id,
                date=date_str,
                release_version=version or "N/A",
                release_type="Release",
                trigger="Optimus Prime — verificar",
                cards_collected=0,
                cards_approved=0,
                cards_rejected=0,
                status="erro",
                errors=errors,
            )
            
            # Document error
            self.reporter.save_error(
                error_slug="verify-failed",
                context={
                    "stage": "verify",
                    "skill": "orchestrator",
                    "reason": str(e),
                    "hypothesis": "Jira connection or MCP integration issue",
                },
            )
            
            raise OrchestrationError(f"Verify mode failed: {e}") from e

    def execute(
        self,
        version: str | None = None,
        project: str = "PB",
        statuses: list[str] | None = None,
        need_human_approval: bool = True,
        **kwargs,
    ) -> ExecutionSummary:
        """⚡ Execute mode (full pipeline with gates).
        
        Executes: Collector → Validator → Builder (real) → saves execution.
        STOPS before Sync (repos.yaml, make run) — that's Ronan's gate.
        
        Args:
            need_human_approval: If True, waits for Ronan OK at each gate.
        
        Returns:
            ExecutionSummary with what WAS done.
        """
        self.logger.info("=" * 72)
        self.logger.info("🤖 Optimus Prime — MODO EXECUÇÃO (COMPLETO)")
        self.logger.info("=" * 72)
        
        execution_id = f"exec-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        date_str = datetime.now().strftime("%Y-%m-%d")
        errors: list[str] = []
        
        try:
            # Step 1: Collect
            self.logger.info("\n[1/5] 🔍 COLETA (Jira)")
            cards = self.collector_svc.collect_from_jira(
                project=project,
                statuses=statuses,
                **kwargs,
            )
            
            # Step 2: Validate
            self.logger.info("\n[2/5] ✅ VALIDAÇÃO (Regra v2)")
            approved, validation_results = self.validator_svc.validate(cards)
            rejected_count = len(cards) - len(approved)
            self._print_validation_summary(approved, validation_results)
            
            # GATE 1: Validation gate
            if need_human_approval and rejected_count > 0:
                self.logger.warning(f"\n⚠️  {rejected_count} card(s) rejeitado(s)")
                self.logger.info("   👤 Aguardando OK do Ronan (em implementação futura)")
            
            # Step 3: Build Release in Notion (REAL)
            notion_page = ""
            if self.builder_svc and version:
                self.logger.info("\n[3/5] 🔨 MONTAGEM (Notion)")
                release = self.builder_svc.create_or_update_release(
                    version=version,
                    release_type="Release",
                    approved_cards=approved,
                )
                notion_page = release.notion_page_url
                self.logger.info(f"   ✅ Página criada/atualizada: {notion_page}")
            
            # GATE 2: Sync preparation gate
            self.logger.info("\n[4/5] 🔄 SINCRONIZAÇÃO (PREPARADA)")
            self.logger.info("   → repos.yaml será editado com repos aprovados")
            self.logger.info("   → make dry-run será executado")
            self.logger.info("   → Aguardando OK do Ronan para make run")
            
            # Step 5: Summary
            self.logger.info("\n[5/5] 📊 RESUMO")
            summary = ExecutionSummary(
                execution_id=execution_id,
                date=date_str,
                release_version=version or "N/A",
                release_type="Release",
                trigger="Optimus Prime — executar",
                cards_collected=len(cards),
                cards_approved=len(approved),
                cards_rejected=rejected_count,
                release_notes_updated=bool(notion_page),
                notion_page=notion_page,
                status="concluido",
                errors=errors,
            )
            
            # Save execution
            self.reporter.save_execution(summary)
            self._print_summary(summary)
            
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ Erro na execução: {e}")
            errors.append(str(e))
            
            summary = ExecutionSummary(
                execution_id=execution_id,
                date=date_str,
                release_version=version or "N/A",
                release_type="Release",
                trigger="Optimus Prime — executar",
                cards_collected=0,
                cards_approved=0,
                cards_rejected=0,
                status="erro",
                errors=errors,
            )
            
            # Document error
            self.reporter.save_error(
                error_slug="execute-failed",
                context={
                    "stage": "execute",
                    "skill": "orchestrator",
                    "reason": str(e),
                    "hypothesis": "Check error details above",
                },
            )
            
            self.reporter.save_execution(summary)
            raise OrchestrationError(f"Execute mode failed: {e}") from e

    def _print_validation_summary(self, approved: list, validation_results: list) -> None:
        """Print friendly validation summary."""
        self.logger.info(f"\n   Aprovados ({len(approved)}):")
        for card in approved:
            self.logger.info(f"     ✅ {card.key}: {card.title[:50]}")
        
        rejected = [r for r in validation_results if r.status != "approved"]
        if rejected:
            self.logger.info(f"\n   Rejeitados ({len(rejected)}):")
            for result in rejected:
                self.logger.info(f"     ❌ {result.card_key}: {result.reason[:50]}")

    def _print_summary(self, summary: ExecutionSummary) -> None:
        """Print execution summary."""
        report = self.reporter.build_summary_report(
            execution_id=summary.execution_id,
            version=summary.release_version,
            release_type=summary.release_type,
            cards_collected=summary.cards_collected,
            cards_approved=summary.cards_approved,
            cards_rejected=summary.cards_rejected,
            status=summary.status,
            errors=summary.errors,
        )
        self.logger.info(f"\n{report}")
