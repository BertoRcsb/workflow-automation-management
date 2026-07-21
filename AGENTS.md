# AGENTS.md

Diretrizes canônicas para agentes: [`CLAUDE.md`](CLAUDE.md) (guardrails) · comportamento em
[`spec/spec.md`](spec/spec.md) · como rodar em [`docs/COMANDOS.md`](docs/COMANDOS.md).

Guardrails mais críticos (detalhe no `CLAUDE.md`):
- **MCP-first, código mínimo** — orquestre via skills + MCPs; **não** crie clients Python bespoke.
- 🛡️ **Dry-run antes** de toda ação real; parseie saída + exit code; erro → documente e **pare**.
- 🚫 **NUNCA** mergeie, suba pra master/prod ou dispare triggers sem OK do Ronan (`auto_merge=false`).
- 🔒 **Não invente dados** ausentes; privilégio mínimo.
- **Commits:** Conventional Commits em inglês, **só com OK do Ronan**, **sem remote externo**.
