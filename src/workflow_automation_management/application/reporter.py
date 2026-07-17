"""Reporter — consolidates execution summaries and error documentation."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from workflow_automation_management.shared import logger

if TYPE_CHECKING:
    from workflow_automation_management.domain import ExecutionSummary, ValidationResult

log = logging.getLogger(__name__)


class Reporter:
    """Handle execution summaries and error logs."""

    def __init__(self, execucoes_dir: str | Path = "execucoes", erros_dir: str | Path = "erros"):
        """Initialize reporter with execution/error storage directories."""
        self.execucoes_dir = Path(execucoes_dir)
        self.erros_dir = Path(erros_dir)
        self.logger = logger
        
        # Ensure directories exist
        self.execucoes_dir.mkdir(parents=True, exist_ok=True)
        self.erros_dir.mkdir(parents=True, exist_ok=True)

    def save_execution(self, summary: ExecutionSummary) -> Path:
        """Save execution summary to JSON.
        
        Returns:
            Path to the saved file.
        """
        filename = f"release-{summary.date}-{summary.execution_id.split('-')[-1]}.json"
        filepath = self.execucoes_dir / filename
        
        data = {
            "execution_id": summary.execution_id,
            "date": summary.date,
            "release_version": summary.release_version,
            "release_type": summary.release_type,
            "trigger": summary.trigger,
            "cards_collected": summary.cards_collected,
            "cards_approved": summary.cards_approved,
            "cards_rejected": summary.cards_rejected,
            "cards": summary.cards,
            "release_notes_updated": summary.release_notes_updated,
            "notion_page": summary.notion_page,
            "notifications_sent": summary.notifications_sent,
            "stopped_at": summary.stopped_at,
            "status": summary.status,
            "errors": summary.errors,
            "relatorio": summary.relatorio,
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"📝 Execução salva | {filepath}")
        return filepath

    def save_error(self, error_slug: str, context: dict) -> Path:
        """Save detailed error documentation.
        
        Args:
            error_slug: Slug for the error (e.g., "jira-connection-timeout")
            context: Error context (command, params, exit_code, stdout, stderr, etc)
        
        Returns:
            Path to the saved error file.
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{date_str}-{error_slug}.md"
        filepath = self.erros_dir / filename
        
        # Build markdown
        markdown = f"""# Erro: {error_slug}

**Data:** {datetime.now().isoformat()}

## Contexto
```
{json.dumps(context, indent=2, ensure_ascii=False)}
```

## Diagnóstico
- **Etapa:** {context.get('stage', 'N/A')}
- **Skill:** {context.get('skill', 'N/A')}
- **Exit Code:** {context.get('exit_code', 'N/A')}
- **Motivo:** {context.get('reason', 'N/A')}

## Hipótese
{context.get('hypothesis', 'Análise a fazer')}

## Ação Recomendada
{context.get('recommended_action', 'Revisar com o Ronan')}
"""
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown)
        
        self.logger.error(f"📋 Erro documentado | {filepath}")
        return filepath

    def build_summary_report(
        self,
        execution_id: str,
        version: str,
        release_type: str,
        cards_collected: int,
        cards_approved: int,
        cards_rejected: int,
        status: str,
        errors: list[str] | None = None,
    ) -> str:
        """Build a human-friendly summary report."""
        errors_str = "\n".join(f"  - {e}" for e in (errors or []))
        
        report = f"""
╔════════════════════════════════════════════════════════════════════╗
║                   OPTIMUS PRIME — EXECUÇÃO                         ║
╚════════════════════════════════════════════════════════════════════╝

📋 RESUMO
  Execução: {execution_id}
  Versão:   {version}
  Tipo:     {release_type}
  Status:   {status}

📊 COLETA & VALIDAÇÃO
  Total coletado:  {cards_collected}
  Aprovado:        {cards_approved}
  Rejeitado:       {cards_rejected}

{"❌ ERROS" + "\n" + errors_str if errors else "✅ SEM ERROS"}

{'═' * 72}
""".strip()
        
        return report
