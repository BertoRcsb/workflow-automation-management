# CLAUDE.md

Guia para o Claude Code / agentes neste repositório.

## Propósito
Automatiza a preparação de **release notes de deploy** e a **sincronização de branches**: coleta cards
no Jira (MCP Atlassian), valida por conteúdo, documenta a versão no Notion, notifica responsáveis e
aciona o `sync-repos-from-master`. **MCP-first, código mínimo, clean architecture.** O **deploy real e
os merges são do usuário**. Sem clients Python bespoke (spec §3): a orquestração é a skill sobre os MCPs
+ os `make` do `sync-repos-from-master`.

## Fontes da verdade (cada regra mora em UM lugar)
| O quê | Onde |
|---|---|
| Comportamento funcional (contrato §7, regra v2, molde) | `spec/spec.md` |
| Sequência, gates e guardrails da esteira | `.claude/skills/orquestrador/SKILL.md` (+ `REFERENCE.md` sob demanda) |
| Papéis executáveis | `.claude/skills/{coletor,validador,montador}/SKILL.md` |
| Arquitetura de subagentes e contrato de handoff | `AGENTS.md` |
| Guia operacional (receitas do usuário) | `docs/COMANDOS.md` |
| Índice dos gates (o que roda onde) | `docs/GATES.md` |
| Config das regras (all-or-nothing, db_owners, promoção) | `tools/rules.json` · `tools/promotion.json` |
| Catálogo canônico do `repos.yaml` (restauração do Sync) | `reference/sync-repos-from-master/README.md` |

## Comandos
```
/optimus-prime verificar   # dry/seguro, só relatório
/optimus-prime executar    # board único: autônomo até o make dry-run do Sync Passo 1 → mensagem "Confira"
```

## Arquitetura (papéis, não apps)
```
coletor → validador → montador → notificador → [Sync]
        (orquestrador "Optimus Prime" coordena, com gates de segurança)
```
Extração de links e gates = **código determinístico em `tools/`** (o LLM não interpreta ADF nem
recalcula regra de cabeça); MCP-first para I/O e escrita.

## Guardrails (resumo de uma linha — a redação normativa está na skill do orquestrador)
- **Autonomia:** informado modo + board, `verificar` e `executar` trabalham silenciosamente, sem
  microaprovações; `executar` roda sozinho até Notion revalidado + `make dry-run` do Sync Passo 1.
  O primeiro gate conversacional é `Confira`; **todo `make run`, merge, master e triggers = OK explícito
  do usuário**. Ambiguidade/erro falha fechado, documenta e bloqueia sem pedir autorização para contornar.
- **Sync inviolável:** nunca `cd` no sync; só alternar `#` no `repos.yaml` + `make -C`; gates
  determinísticos (`optimus_yaml_gate`, `optimus_promotion_gate`, `optimus_triggers_gate`) antes de
  todo `make`; **nunca direto pra master**.
- **Erro → documenta em `erros/` e para.** Não inventar dado; privilégio mínimo.
- **Pós-deploy** reusa exatamente os mesmos repos do ciclo ativo (nunca filtra/reclassifica).
- Execuções em `execucoes/`; refino de skill/comando **só com OK do usuário**.
- **Commits:** Conventional Commits em inglês, só com OK; **sem remote externo**.
