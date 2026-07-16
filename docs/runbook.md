# ▶️ Runbook — rodar a esteira (Optimus Prime)

> **Comando único — você fala/escreve:** `Optimus Prime, iniciar`
> → equivale a **`/optimus-prime executar`** (ou **`/optimus-prime verificar`** para ensaiar em
> *dry*, sem tocar em nada).

## Sequência completa (o que roda por baixo) e seus gates

| # | Etapa | Comando por baixo | Gate (Ronan) |
|---|-------|-------------------|--------------|
| 0 | **Versão-alvo** | lê a última no Notion, propõe a próxima | confirma versão + Release/**Hotfix** |
| 1 | **Coletor** | Atlassian MCP (`getJiraIssue` / JQL) | — |
| 2 | **Validador** | regra v2 + heurística | **OK do rascunho** (aprovados × reprovados) |
| 3 | **Montador** | Notion (`create-pages` + re-fetch) | OK pra escrever no Notion |
| 4 | **Notificador** | *sandbox* (pulado por ora) | — |
| 5 | **Sync — edita `repos.yaml`** | ativa **só os repos da doc**; comenta o resto | — |
| 5.1 | **Passo 1** `prerelease → teste_regressivo` | `make dry-run PR_TITLE="[Hotfix] X"` → `make run PR_TITLE="[Hotfix] X"` | **OK antes do `make run`** → **Ronan mergeia** |
| 5.2 | **Passo 2** `teste_regressivo → master` | edita YAML (source/target) → `make dry-run` → `make run PR_TITLE="[Hotfix] X"` | **Ronan comanda** + OK → **Ronan mergeia** → **QA testa** |
| 5.3 | **Passo 3** triggers (clientes) | descomenta `triggers:` do repo → `make dry-run-triggers` → **`make run-triggers`** *(sem PR_TITLE)* | **Ronan comanda** (pós-QA) + **aprova os builds no GCP** |
| 6 | **Pós-deploy — sync de volta** | edita YAML `source: master`, `targets: [develop, stage, prerelease]` → `make dry-run` → `make run` | **OK antes do `make run`** → **Ronan mergeia** |
| 7 | **Resumo** | grava `execucoes/release-AAAA-MM-DD-NNN.json` | — |

## Regras de ouro (embutidas)
- `auto_merge=false` **sempre** · `make run` **sempre com `target` explícito** · **nunca** direto pra master.
- **Merge e aprovação de build = só o Ronan.** O Optimus Prime **sempre pergunta antes** de master/triggers.
- `make run-triggers` **não recebe `PR_TITLE`**. Convenção do `PR_TITLE` do `make run`: `[Hotfix]`/`[Release] <versão>`.
- **Quais triggers rodar** ainda **não** estão no Notion — vêm de instrução do Ronan + `triggers:` do `repos.yaml`.

## Modos
- `/optimus-prime verificar` — ensaio **dry**: coleta, valida, simula Notion e mostra o alvo do Sync, **sem tocar em nada**.
- `/optimus-prime executar` — roda de verdade, **pausando pra OK** a cada ação que muda algo.
