#  Guia operacional — comandos do Optimus Prime

> **Guia operacional único** (como rodar). Comportamento canônico: [`../spec/spec.md`](../spec/spec.md).

## ANTES DE TUDO: isto precisa de um "cérebro" (Claude) ligado

Este projeto **não é um script standalone** — não tem `main.py`, não tem `make run` que roda sozinho.
Tudo aqui (skills, comando `/optimus-prime`, esteira) é **instrução** que só ganha vida quando há um
**motor de execução — o Claude (Claude Code)** — lendo essas instruções e operando as ferramentas.

> **Sem o Claude conectado, nada disto executa.** As skills carregam, mas não têm quem as rode.

**O "cérebro" é o Claude; os "braços" são os MCPs + o `make` do `sync-repos-from-master`.** Por isso,
**o passo 0 de qualquer receita é ligar o cérebro e os braços:**

| Ingrediente | O que é | Como garantir |
|---|---|---|
| **Claude Code ativo** | o motor que lê as skills e executa | aberto no PyCharm (ou terminal/VS Code), autenticado, com créditos |
| **Projeto aberto** | carrega as skills + o `/optimus-prime` | abrir a pasta `workflow-automation-management` |
| **MCP Atlassian** | ler cards do Jira | `/mcp` → **Connected** |
| **MCP Notion** | escrever a release/hotfix | `/mcp` → **Connected** |
| **`sync-repos-from-master`** ao lado | abrir PRs / disparar deploy | clonado como irmão (`../`) ou `SYNC_REPO_PATH`, com `.env` configurado |

> **Autônomo até o Sync Passo 1, não desassistido depois:** no `executar` de um board, a esteira roda
> **sozinha até abrir os PRs pré-prod** (Passo 1: doc no Notion → edita `repos.yaml` → `make dry-run` →
> se limpo, `make run`). A única pausa antes é **card genuinamente ambíguo**. **Depois do Passo 1**
> (merge, master/Passo 2, `run-triggers`/Passo 3) é **sempre seu** — o Claude pausa e espera comando.
> No alvo `todos os boards`, a varredura ainda **termina no Notion**. Consome créditos por execução.

---

##  Receita 1 — Ensaiar tudo sem risco (DRY)

**Quando:** você quer ver o que a esteira faria, sem tocar em nada.

1. Garanta o **passo 0** (cérebro + braços ligados, acima).
2. Escreva no Claude:
   ```
   Optimus Prime verificar todos os boards
   ```
3. Leia o relatório: **3 blocos** (incidentes → features → refatoração), cada um com **aprovados ×
   reprovados**. **Nada é alterado.**

> Variante de **um board só**: `Optimus Prime verificar incidentes` (ou `features` / `refatoração`).

---

##  Receita 2 — Rodar a esteira (iniciar)

**Quando:** documentar a release no Notion e, num board único, já abrir os PRs pré-prod (Sync Passo 1).

1. Garanta o **passo 0**.
2. Escreva:
   ```
   Optimus Prime iniciar incidentes        # um board: vai ATÉ o Sync Passo 1 (abre os PRs pré-prod)
   Optimus Prime iniciar todos os boards    # varredura: cada board vai só ATÉ o Notion
   ```
3. **Board único** — roda autônoma: versão-alvo automática → coletor → validador → montador
   **cria/atualiza a página no Notion sem pedir OK** (+ re-fetch) → **Sync Passo 1**: edita o
   `repos.yaml` (só os repos da doc), `make dry-run` e, se **limpo**, **`make run`** (abre os PRs
   `prerelease → teste_regressivo`). **Não pausa** na versão-alvo, no rascunho, no "posso criar", na
   edição do YAML, nem entre dry-run e `make run`.
   - **Única pausa:** **card genuinamente ambíguo** (a heurística só-banco não fecha, ou o dado diverge
     — ex.: repo ≠ PR). Aí o Optimus **pergunta** — nunca inventa.
   - **Versão-alvo:** `Release` sequencial `X.(Y+1).0` por board. **Incidente NÃO é hotfix por
     padrão** — hotfix só quando **você avisar**.
4. **Depois do Passo 1:** os PRs estão abertos (`auto_merge=false`). **Merge, master (Passo 2) e
   triggers (Passo 3)** são seus — ver Receita 3.
5. **Todos os boards:** a varredura **para no Notion**; o Sync é por-board, em dias diferentes
   (incidentes primeiro) — Receita 3.

---

##  Receita 3 — Sincronizar/deployar (Sync) — os passos seus

**Quando:** promover para master e deployar (os passos que são seus). O **Passo 1** (pré-prod) já roda
dentro do `iniciar` de board único; aqui ficam **master (Passo 2), triggers (Passo 3) e pós-deploy** —
**sob seu comando**, com gate por ação (dry-run → parseia saída + exit code → **espera comando** → real).
Comandos do `sync-repos-from-master`:

```
make dry-run PR_TITLE="[Release]/[Hotfix] <versão>"   # simulação segura (sempre antes)
make run     PR_TITLE="[Release]/[Hotfix] <versão>"   # abre/atualiza PRs (auto_merge=false → NÃO mergeia)
make dry-run-triggers                                 # simula o deploy GCP
make run-triggers                                     # deploy GCP (SEM PR_TITLE) — 100% seu, pós-QA
```

Promoção de branches (**`make run` sempre com `target` explícito, nunca direto pra master**):
1. **Passo 1** `prerelease → teste_regressivo` — Optimus roda `make dry-run` e, se limpo, o `make run`
   **automaticamente** (dentro do `iniciar` de board único); **você mergeia**.
2. **Passo 2** `teste_regressivo → master` — **você comanda**; Optimus edita o YAML + `make dry-run`, e
   roda o `make run` de master **só sob seu override explícito**.
3. **Passo 3** `make run-triggers` (ambientes dos clientes) — **100% seu**, e você **aprova os builds no GCP**.
4. **Pós-deploy** `master → develop/stage/prerelease` — `make run PR_TITLE="Sync Master"`.

---

##  Sequência e gates (o que roda por baixo)

No `executar` de um board, os passos **1–5, 6.0–6.1 e 7 rodam AUTÔNOMOS** (doc no Notion + edição do
YAML + `make dry-run`/`make run` do Passo 1, sem OK). O **Gate (Ronan)** aparece **de master (6.2) em
diante**. No alvo `todos os boards`, os passos 1–5 e 7 rodam **por board** (incidentes 1º, isolados) e a
varredura **para no Notion** — o Passo 6 fica **fora do loop** (por-board e explícito, depois).

| # | Etapa | Comando por baixo | Autônomo? / Gate (Ronan) |
|---|-------|-------------------|--------------------------|
| 1 | **Versão-alvo** | lê a última no Notion; próxima `X.(Y+1).0` como `Release` | autônomo (incidente ≠ hotfix por padrão) |
| 2 | **Coletor** | Atlassian MCP (`getJiraIssue` / JQL) | autônomo (erro de leitura → documenta e para) |
| 3 | **Validador** | regra v2 + heurística só-banco | autônomo — **pausa SÓ em card genuinamente ambíguo** |
| 4 | **Montador** | Notion (`create-pages` + re-fetch) | autônomo — **cria/atualiza no Notion sem OK** |
| 5 | **Notificador** | *sandbox* (pulado por ora) | autônomo (só mostra pro Ronan) |
| — | **↑ todos os boards PARAM AQUI (Notion)** · board único segue p/ 6.1 | | |
| 6.0 | **Sync — edita `repos.yaml`** | ativa **só os repos da doc**; comenta o resto | autônomo (edição do YAML sem OK) |
| 6.1 | **Passo 1** `prerelease → teste_regressivo` | `make dry-run PR_TITLE="[…] X"` → (limpo) `make run PR_TITLE="[…] X"` | autônomo (dry-run limpo → `make run`) → **Ronan mergeia** |
| 6.2 | **Passo 2** `teste_regressivo → master` | edita YAML (source/target) → `make dry-run` → `make run` | **Ronan comanda** + OK → **Ronan mergeia** → **QA testa** |
| 6.3 | **Passo 3** triggers (clientes) | descomenta `triggers:` → `make dry-run-triggers` → **`make run-triggers`** *(sem PR_TITLE)* | **Ronan comanda** (pós-QA) + **aprova os builds no GCP** |
| 6.4 | **Pós-deploy — sync de volta** | edita YAML `source: master`, `targets: [develop, stage, prerelease]` → `make dry-run` → `make run` | **OK antes do `make run`** → **Ronan mergeia** |
| 7 | **Resumo** | grava `execucoes/release-AAAA-MM-DD-NNN.json` | autônomo |

---

##  Cola rápida (todos os comandos)

```
# DRY (não toca em nada)
Optimus Prime verificar todos os boards
Optimus Prime verificar incidentes | features | refatoração

# EXECUTAR (board único: até o Sync Passo 1; todos os boards: até o Notion)
Optimus Prime iniciar todos os boards
Optimus Prime iniciar incidentes | features | refatoração
Optimus Prime, iniciar            # pergunta o board

# Também disparam a esteira:
"iniciar deploy" · "montar e preparar a release" · "rodar a esteira"

# Sync/Deploy (no sync-repos-from-master; sempre dry-run antes, sob OK do Ronan)
make dry-run / make run PR_TITLE="[Release]/[Hotfix] <versão>"
make dry-run-triggers / make run-triggers
```

##  Regras de ouro (o cérebro nunca quebra)
- **Autônomo até o Sync Passo 1** (board único): passos 1–7 rodam **sem pedir OK** — doc no Notion,
  edição do YAML e, com dry-run limpo, o `make run` do Passo 1. **Única pausa:** card genuinamente
  ambíguo. No alvo `todos os boards`, ainda para no Notion.
- **Gate por ação:** `dry-run` antes de toda ação real → parseia saída + exit code (0 ok / 1 erro); erro
  → documenta em `erros/` e **para**. **Passo 1:** limpo → `make run` automático. **Master (Passo 2) e
  triggers (Passo 3):** limpo → mostra e **espera comando explícito** antes do real.
- **Merge, master/prod e `run-triggers` = só o Ronan** (`auto_merge=false`). O Optimus **sempre
  pergunta antes** de master (Passo 2) e das triggers (Passo 3).
- **`verificar` nunca executa** — só relatório.
- **Um board por release** — a varredura "todos os boards" é sequencial e isolada (nunca mistura).
- **Não inventa dado**; privilégio mínimo (Jira leitura; Notion só a base de releases).
- **`make run` sempre com `target` explícito**; **nunca** direto pra master. `make run-triggers`
  **não recebe `PR_TITLE`**. Convenção do `PR_TITLE`: `[Release]`/`[Hotfix] <versão>`; pós-deploy = `Sync Master`.

## Mapeamento dos boards (o que cada um coleta no Jira — projeto PB)
| Prioridade | Board | Filtro (JQL) |
|---|---|---|
| 1º | **Linha de frente / incidentes** | `issuetype = Incidente` |
| 2º | **Features** | `issuetype = Story AND summary !~ "Refatoração"` |
| 3º | **Refatoração** | `issuetype = Story AND summary ~ "Refatoração"` |

Status alvo dos três: `Teste regressivo`, `Pronto para deploy`. Detalhe e refino: `.claude/skills/coletor/SKILL.md`.
