# AGENTS.md

Diretrizes para agentes (Claude Code e afins) neste repositório.

- **MCP-first, código mínimo.** Orquestre via skills + MCPs (Atlassian/Notion) + `make`; **não** crie
  clients Python bespoke (evitar o overengineering do `iac-platform`).
- **Use as skills por papel** (`coletor` / `validador` / `montador` / `orquestrador`); não reimplemente
  o trabalho delas. O comando de entrada é **`/optimus-prime`** (`verificar` | `executar`).
- **Segurança por ação:** rode `dry-run` antes de qualquer ação que muda algo; parseie saída + exit
  code; erro → **documente** em `erros/AAAA-MM-DD-*.md` e **pare**.
- 🚫 **NUNCA mergeie e NUNCA suba pra master/prod** sem autorização explícita do Ronan
  (`auto_merge=false` sempre). `make run` **sempre com `target` explícito**; nunca direto pra master.
- **Guiado pela documentação:** ative no `repos.yaml` **só os repos que constam na doc da versão no
  Notion**; comente o resto. Repo faltando → **pare e reporte**.
- **Não invente dados** ausentes (deixe em branco). Privilégio mínimo.
- **Commits:** Conventional Commits, em inglês, corpo explicativo. **Só commitar com OK do Ronan.**
  **Sem remote externo** por ora.
- **Atualize** `spec/spec.md` (comportamento) e `spec/task.md` (tarefas) quando algo mudar.
