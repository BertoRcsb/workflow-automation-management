# Tarefas — Esteira Inteligente de Release Notes

> Backlog vivo. Comportamento canônico: `spec/spec.md`. Plano geral: `spec/plan.md`.

## Feito
- [x] Skills por papel: `coletor`, `validador`, `montador`, `orquestrador` ("Optimus Prime").
- [x] Comando `/optimus-prime` (modos `verificar` | `executar`).
- [x] Fluxo E2E validado: PB-5740 → Notion Hotfix `1.111.2` → Sync Passo 1 → PR #245 (**sem merge**).
- [x] Gate de segurança por ação (dry-run → OK → real) + documentação de erro em `erros/`.
- [x] Registro de execução em `execucoes/*.json`.
- [x] Estrutura espelhando o `sync-repos-from-master` (spec/, docs/, README/CLAUDE/AGENTS).

## A fazer (próximo)
- [ ] Skill `notificador` de verdade (dev/PO/QA por canal oficial; hoje sandbox).
- [ ] Leitura diária multi-board (incidents + features + refatoração) — amplia o `coletor`.
- [ ] Confirmar grafia/ambientes das branches (`prerelease` / `teste_regressivo` / `master`).
- [ ] Índice de execuções (`execucoes/INDEX.md`) e/ou database "Execuções" no Notion (Fase 2).
- [ ] Commit inicial de `.claude/`, `spec/`, `docs/` (sem remote externo).

## Backlog de refino (spec §13)
- [ ] Nome do proc (cards só-banco); campo "Ação de Infra" no Jira; origem do "Merge realizado".
- [ ] Ler PR do painel Development quando o campo estiver vazio.
- [ ] Categorias na release; revalidação de cards corrigidos.

## Estudar (com o Ronan)
- [ ] Se/como o Optimus Prime poderá um dia mergear/deployar com segurança (hoje: **nunca**).
