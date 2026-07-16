# Workflow with Automation Assisted by Management

> # ▶️ RODAR A ESTEIRA
> **Você fala/escreve:** `Optimus Prime, iniciar` → equivale a **`/optimus-prime executar`**
> (ou **`/optimus-prime verificar`** para ensaiar em *dry*, sem tocar em nada).
> **Roteiro completo (comandos por passo):** [`docs/runbook.md`](docs/runbook.md)

Governança de deploy assistida por automação: **Jira → Notion → Sync/Deploy (GCP)**, com o
orquestrador **"Optimus Prime"** conduzindo a esteira e o Ronan aprovando cada passo crítico.

> **Automação assiste, gestão controla.** Nada mergeia nem sobe pra prod sem o Ronan.

## Como usar (quick start)
Invoque o orquestrador pelo comando:
```
/optimus-prime verificar     # dry/seguro: coleta, valida, simula Notion e Sync — NÃO toca em nada
/optimus-prime executar      # sequência completa até o make run (Passo 1), com gate + aprovação
```

## Papéis (skills em `.claude/skills/`)
| Papel | Função |
|-------|--------|
| **coletor** | busca e normaliza cards no Jira (Atlassian MCP, read-only) |
| **validador** | gate de elegibilidade por conteúdo (regra v2 + heurística) |
| **montador** | escreve/atualiza a release/hotfix no Notion (molde) |
| **notificador** | comunica pendências a dev/PO/QA (sandbox — a estruturar) |
| **orquestrador** ("Optimus Prime") | governa tudo + o `sync-repos-from-master`, com segurança por ação |

## Documentação
- **Comportamento (fonte da verdade):** [`spec/spec.md`](spec/spec.md)
- **Plano geral:** [`spec/plan.md`](spec/plan.md) · **Tarefas:** [`spec/task.md`](spec/task.md)
- **Guia técnico + comandos:** [`CLAUDE.md`](CLAUDE.md) · **Passo a passo:** [`docs/README.md`](docs/README.md)
- **Diretrizes p/ agentes:** [`AGENTS.md`](AGENTS.md) · **Apresentação:** [`PROPOSTA.md`](PROPOSTA.md)
