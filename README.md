# Workflow with Automation Assisted by Management

> # RODAR A ESTEIRA
> **Precisa de um "cérebro" (Claude) ligado** — isto **não roda sozinho**. As skills/comandos só
> executam com o **Claude Code conectado + MCPs ativos + projeto aberto**. O cérebro é o Claude; os
> braços são os MCPs + o `make` do sync.
> **Você fala/escreve:** `Optimus Prime, iniciar` → equivale a **`/optimus-prime executar`**
> (ou **`/optimus-prime verificar`** para ensaiar em *dry*, sem tocar em nada).
> **Guia operacional (comandos passo a passo + gates):** [`docs/COMANDOS.md`](docs/COMANDOS.md)
> **Primeira vez / configurar (clonou agora?):** [`docs/SETUP.md`](docs/SETUP.md)

Governança de deploy assistida por automação: **Jira → Notion → Sync/Deploy (GCP)**, com o
orquestrador **"Optimus Prime"** conduzindo a esteira e o Ronan aprovando cada passo crítico.

> **Automação assiste, gestão controla.** Nada mergeia nem sobe pra prod sem o Ronan.

## Como usar (quick start)
Invoque o orquestrador pelo comando:
```
/optimus-prime verificar     # dry/seguro: coleta, valida, simula Notion e Sync — NÃO toca em nada
/optimus-prime executar      # board único: autônomo até o make dry-run do Passo 1 (doc no Notion + edita YAML + dry-run); make run sob OK do Ronan
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
- **Apresentação visual (diagramas Mermaid):** [`docs/APRESENTACAO.md`](docs/APRESENTACAO.md)
- **Receita de bolo (comandos):** [`docs/COMANDOS.md`](docs/COMANDOS.md)
- **Comportamento (fonte da verdade):** [`spec/spec.md`](spec/spec.md)
- **Plano geral:** [`spec/plan.md`](spec/plan.md) · **Tarefas:** [`spec/task.md`](spec/task.md)
- **Guia técnico + comandos:** [`CLAUDE.md`](CLAUDE.md) · **Índice de docs:** [`docs/README.md`](docs/README.md)
- **Diretrizes p/ agentes:** [`AGENTS.md`](AGENTS.md) · **Apresentação:** [`docs/PROPOSTA.md`](docs/PROPOSTA.md)
