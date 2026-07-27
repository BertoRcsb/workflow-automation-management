# AGENTS.md

Diretrizes canônicas para agentes: [`CLAUDE.md`](CLAUDE.md) (guardrails) · comportamento em
[`spec/spec.md`](spec/spec.md) · como rodar em [`docs/COMANDOS.md`](docs/COMANDOS.md).

Guardrails mais críticos (detalhe no `CLAUDE.md`):
- **MCP-first, código mínimo** — orquestre via skills + MCPs; **não** crie clients Python bespoke.
- **Dry-run antes** de toda ação real; parseie saída + exit code; erro → documente e **pare**. **Todo
  `make run` (Passo 1, Passo 2) e as triggers (Passo 3) são sob OK explícito do Ronan.**
- **NUNCA** rode `make run`, mergeie, suba pra master/prod ou dispare triggers sem OK do Ronan
  (`auto_merge=false`).
- **Não invente dados** ausentes; **capture TODOS os links reais de cada card** (repos e PRs/merge — um
  card pode ter vários); privilégio mínimo.
- **Commits:** Conventional Commits em inglês, **só com OK do Ronan**, **sem remote externo**.
