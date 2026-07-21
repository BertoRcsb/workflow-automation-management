#  Guia operacional — comandos do Optimus Prime

> **Guia operacional único** (como rodar). Comportamento canônico: [`../spec/spec.md`](../spec/spec.md).

## ⚠️ ANTES DE TUDO: isto precisa de um "cérebro" (Claude) ligado

Este projeto **não é um script standalone** — não tem `main.py`, não tem `make run` que roda sozinho.
Tudo aqui (skills, comando `/optimus-prime`, esteira) é **instrução** que só ganha vida quando há um
**motor de execução — o Claude (Claude Code)** — lendo essas instruções e operando as ferramentas.

> **Sem o Claude conectado, nada disto executa.** As skills carregam, mas não têm quem as rode.

**O "cérebro" é o Claude; os "braços" são os MCPs + o `make` do `sync-repos-from-master`.** Por isso,
**o passo 0 de qualquer receita é ligar o cérebro e os braços:**

| Ingrediente | O que é | Como garantir |
|---|---|---|
| 🧠 **Claude Code ativo** | o motor que lê as skills e executa | aberto no PyCharm (ou terminal/VS Code), autenticado, com créditos |
| 📂 **Projeto aberto** | carrega as skills + o `/optimus-prime` | abrir a pasta `workflow-automation-management` |
| 🔌 **MCP Atlassian** | ler cards do Jira | `/mcp` → **Connected** |
| 🔌 **MCP Notion** | escrever a release/hotfix | `/mcp` → **Connected** |
| 🔧 **`sync-repos-from-master`** ao lado | abrir PRs / disparar deploy | clonado como irmão (`../`) ou `SYNC_REPO_PATH`, com `.env` configurado |

> ⚠️ **Autônomo até o Notion, não desassistido depois:** no `executar`, a esteira roda **sozinha até
> criar a doc no Notion** (a única pausa antes é **card genuinamente ambíguo**). **Do Sync em diante**
> o Claude **pausa em cada ação** (dry-run → OK) e **merge/master/`run-triggers` são sempre seus**.
> Consome créditos por execução.

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

##  Receita 2 — Rodar a esteira até o Notion (por board)

**Quando:** você quer documentar as releases/hotfix no Notion (um por board).

1. Garanta o **passo 0**.
2. Escreva:
   ```
   Optimus Prime iniciar todos os boards
   ```
   (ou um board só: `Optimus Prime iniciar incidentes`)
3. A esteira roda **autônoma até o Notion** — versão-alvo automática → coletor → validador → montador
   **cria/atualiza a página no Notion sem pedir OK** (+ re-fetch de verificação). **Não pausa** na
   versão-alvo, nem no rascunho, nem no "posso criar".
   - **Única pausa antes do Notion:** **card genuinamente ambíguo** (a heurística só-banco não fecha,
     ou o dado diverge — ex.: repo ≠ PR). Aí o Optimus **pergunta** — nunca inventa.
   - **Versão-alvo:** `Release` sequencial `X.(Y+1).0` por board. **Incidente NÃO é hotfix por
     padrão** — hotfix só quando **você avisar**.
4. A varredura **para no Notion**. O deploy é a Receita 3, **por-board e em dias diferentes**
   (incidentes primeiro) — e aí sim **sob seu OK a cada ação**.

---

##  Receita 3 — Sincronizar/deployar (Sync) — os passos seus

**Quando:** a release já está no Notion e você vai promover branches / deployar. **Do Sync em diante,
tudo é sob seu OK, com gate por ação** (dry-run → parseia saída + exit code → **espera OK** → real).
Comandos do `sync-repos-from-master`:

```
make dry-run PR_TITLE="[Release]/[Hotfix] <versão>"   # simulação segura (sempre antes)
make run     PR_TITLE="[Release]/[Hotfix] <versão>"   # abre/atualiza PRs (auto_merge=false → NÃO mergeia)
make dry-run-triggers                                 # simula o deploy GCP
make run-triggers                                     # deploy GCP (SEM PR_TITLE) — 100% seu, pós-QA
```

Promoção de branches (**`make run` sempre com `target` explícito, nunca direto pra master**):
1. **Passo 1** `prerelease → teste_regressivo` — Optimus roda o `make run` (após seu OK); **você mergeia**.
2. **Passo 2** `teste_regressivo → master` — **você comanda**; Optimus só edita o YAML.
3. **Passo 3** `make run-triggers` (ambientes dos clientes) — **100% seu**, e você **aprova os builds no GCP**.
4. **Pós-deploy** `master → develop/stage/prerelease` — `make run PR_TITLE="Sync Master"`.

---

##  Sequência e gates (o que roda por baixo)

No `executar`, os passos **1–5 e 7 rodam AUTÔNOMOS** (a doc no Notion é criada sem OK). O **Gate
(Ronan)** só aparece **do Sync (Passo 6) em diante**. No alvo `todos os boards`, os passos 1–5 e 7
rodam **por board** (incidentes 1º, isolados); o Passo 6 fica **fora do loop** (por-board e explícito).

| # | Etapa | Comando por baixo | Autônomo? / Gate (Ronan) |
|---|-------|-------------------|--------------------------|
| 1 | **Versão-alvo** | lê a última no Notion; próxima `X.(Y+1).0` como `Release` | ✅ autônomo (incidente ≠ hotfix por padrão) |
| 2 | **Coletor** | Atlassian MCP (`getJiraIssue` / JQL) | ✅ autônomo (erro de leitura → documenta e para) |
| 3 | **Validador** | regra v2 + heurística só-banco | ✅ autônomo — **pausa SÓ em card genuinamente ambíguo** |
| 4 | **Montador** | Notion (`create-pages` + re-fetch) | ✅ autônomo — **cria/atualiza no Notion sem OK** |
| 5 | **Notificador** | *sandbox* (pulado por ora) | ✅ autônomo (só mostra pro Ronan) |
| — | **↑ PARA AQUI (no Notion)** | | |
| 6.0 | **Sync — edita `repos.yaml`** | ativa **só os repos da doc**; comenta o resto | edição do YAML é autônoma; **gate no `make run`** |
| 6.1 | **Passo 1** `prerelease → teste_regressivo` | `make dry-run PR_TITLE="[…] X"` → `make run PR_TITLE="[…] X"` | **OK antes do `make run`** → **Ronan mergeia** |
| 6.2 | **Passo 2** `teste_regressivo → master` | edita YAML (source/target) → `make dry-run` → `make run` | **Ronan comanda** + OK → **Ronan mergeia** → **QA testa** |
| 6.3 | **Passo 3** triggers (clientes) | descomenta `triggers:` → `make dry-run-triggers` → **`make run-triggers`** *(sem PR_TITLE)* | **Ronan comanda** (pós-QA) + **aprova os builds no GCP** |
| 6.4 | **Pós-deploy — sync de volta** | edita YAML `source: master`, `targets: [develop, stage, prerelease]` → `make dry-run` → `make run` | **OK antes do `make run`** → **Ronan mergeia** |
| 7 | **Resumo** | grava `execucoes/release-AAAA-MM-DD-NNN.json` | ✅ autônomo |

---

##  Cola rápida (todos os comandos)

```
# DRY (não toca em nada)
Optimus Prime verificar todos os boards
Optimus Prime verificar incidentes | features | refatoração

# EXECUTAR (autônomo até o Notion; para antes do Sync)
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
- 🤖 **Autônomo até o Notion:** no `executar`, passos 1–5 e 7 rodam **sem pedir OK** (a doc é criada
  automaticamente). **Única pausa antes do Notion:** card genuinamente ambíguo.
- 🛡️ **Gate por ação (Sync em diante):** `dry-run` antes de toda ação real → parseia saída + exit code
  (0 ok / 1 erro); erro → documenta em `erros/` e **para**; limpo → mostra e **espera OK** antes do real.
- 🚫 **Merge, master/prod e `run-triggers` = só o Ronan** (`auto_merge=false`). O Optimus **sempre
  pergunta antes** de master (Passo 2) e das triggers (Passo 3).
- 👁️ **`verificar` nunca executa** — só relatório.
- 🧭 **Um board por release** — a varredura "todos os boards" é sequencial e isolada (nunca mistura).
- 🔒 **Não inventa dado**; privilégio mínimo (Jira leitura; Notion só a base de releases).
- 📓 **`make run` sempre com `target` explícito**; **nunca** direto pra master. `make run-triggers`
  **não recebe `PR_TITLE`**. Convenção do `PR_TITLE`: `[Release]`/`[Hotfix] <versão>`; pós-deploy = `Sync Master`.

## 🗺️ Mapeamento dos boards (o que cada um coleta no Jira — projeto PB)
| Prioridade | Board | Filtro (JQL) |
|---|---|---|
| 1º | **Linha de frente / incidentes** | `issuetype = Incidente` |
| 2º | **Features** | `issuetype = Story AND summary !~ "Refatoração"` |
| 3º | **Refatoração** | `issuetype = Story AND summary ~ "Refatoração"` |

Status alvo dos três: `Teste regressivo`, `Pronto para deploy`. Detalhe e refino: `.claude/skills/coletor/SKILL.md`.
