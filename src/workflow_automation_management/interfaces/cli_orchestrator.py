"""CLI interfaces — entry point for Optimus Prime command."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from workflow_automation_management.application import Orchestrator, Reporter
from workflow_automation_management.infra import JiraCollector, NotionBuilder, load_config
from workflow_automation_management.shared import OrchestrationError, get_logger, logger

log = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for Optimus Prime."""
    parser = argparse.ArgumentParser(
        description="Optimus Prime — Release Notes Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  optimus-prime verificar              # Dry-run: collect, validate, summarize
  optimus-prime executar --versao 1.111.2  # Full run: collect, validate, build Notion

Modes:
  verificar — Safe mode (no side effects), shows what would happen
  executar  — Real mode (modifies Notion), with gates for human approval
        """,
    )
    
    parser.add_argument(
        "mode",
        choices=["verificar", "executar"],
        help="Execution mode",
    )
    
    parser.add_argument(
        "--versao",
        "--version",
        help="Target release version (e.g., 1.111.2). Auto-detected if not provided.",
    )
    
    parser.add_argument(
        "--card",
        help="Specific Jira card key to collect (e.g., PB-5740). If not provided, collects from statuses.",
    )
    
    parser.add_argument(
        "--projeto",
        "--project",
        default="PB",
        help="Jira project key (default: PB)",
    )
    
    parser.add_argument(
        "--sem-aprovacao",
        "--skip-approval",
        action="store_true",
        help="Skip human approval gates (use with caution)",
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level",
    )
    
    return parser


def main(argv: list[str] | None = None) -> int:
    """Main entry point for CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    
    try:
        # Load configuration
        config = load_config()
        
        # Initialize reporter
        reporter = Reporter(
            execucoes_dir=config.storage.execucoes_dir,
            erros_dir=config.storage.erros_dir,
        )
        
        # Initialize implementations
        collector = JiraCollector(cloud_id=config.jira.cloud_id)
        builder = NotionBuilder(database_id=config.notion.database_id)
        
        # Create orchestrator
        orchestrator = Orchestrator(
            collector_impl=collector,
            builder_impl=builder,
            reporter=reporter,
        )
        
        # Execute based on mode
        if args.mode == "verificar":
            logger.info("🔍 Optimus Prime — Modo VERIFICAÇÃO (dry-run)")
            summary = orchestrator.verify(
                version=args.versao,
                project=args.projeto,
                card_key=args.card,
            )
        else:  # executar
            logger.info("⚡ Optimus Prime — Modo EXECUÇÃO (completo)")
            summary = orchestrator.execute(
                version=args.versao,
                project=args.projeto,
                card_key=args.card,
                need_human_approval=not args.sem_aprovacao,
            )
        
        # Success
        logger.info(f"\n✅ Execução concluída: {summary.execution_id}")
        return 0
        
    except OrchestrationError as e:
        logger.error(f"❌ Erro de orquestração: {e}")
        return 1
    except Exception as e:
        logger.error(f"❌ Erro inesperado: {e}", exc_info=True)
        return 2


if __name__ == "__main__":
    sys.exit(main())
