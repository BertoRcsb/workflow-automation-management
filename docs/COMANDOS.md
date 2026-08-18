# Guia operacional — comandos do Optimus Prime

> **Guia operacional único** (como rodar). Comportamento canônico e guardrails:
> [`../.claude/skills/orquestrador/SKILL.md`](../.claude/skills/orquestrador/SKILL.md) e
> [`../spec/spec.md`](../spec/spec.md). Este arquivo não redefine regra — só ensina a usar.

## ANTES DE TUDO: isto precisa de um "cérebro" (Claude) ligado

Este projeto **não é um script standalone** — não tem `main.py` que roda sozinho. Tudo aqui (skills,
comando `/optimus-prime`, esteira) é **instrução** que só ganha vida com o **Claude Code** lendo-as e
operando as ferramentas. **O "cérebro" é o Claude; os "braços" são os MCPs + o `make` do
`sync-repos-from-master`.** Passo 0 de qualquer receita:

| Ingrediente | O que é | Como garantir |
|---|---|---|
| **Claude Code ativo** | o motor que lê as skills e executa | aberto no PyCharm (ou terminal/VS Code), autenticado, com créditos |
| **Projeto aberto** | carrega as skills + o `/optimus-prime` | abrir a pasta `workflow-automation-management` |
| **MCP Atlassian** | ler cards do Jira | `/mcp` → **Connected** |
| **MCP Notion** | escrever a release/hotfix | `/mcp` → **Connected** |
| **`sync-repos-from-master`** ao lado | abrir PRs / disparar deploy | clonado como irmão (`../`) ou `SYNC_REPO_PATH`, com `.env` configurado |

> **Resumo do contrato:** no `executar` de um board, a esteira roda **sozinha até o `make dry-run` do
> Sync Passo 1** e termina na mensagem única `Optimus Prime retornando com o resultado = Confira`.
> Única pausa antes: card genuinamente ambíguo. **Todo `make run`, merge, master e triggers = seu.**
> No alvo `todos os boards`, a varredura termina no Notion. Consome créditos por execução.

---

## Receita 1 — Ensaiar tudo sem risco (DRY)

**Quando:** você quer ver o que a esteira faria, sem tocar em nada.

```
Optimus Prime verificar todos os boards
Optimus Prime verificar incidentes | features | refatoração   # um board só
```

Leia o relatório (um bloco por board, aprovados × reprovados). **Nada é alterado.**

---

## Receita 2 — Rodar a esteira (iniciar)

**Quando:** documentar a release no Notion e, num board único, deixar o `repos.yaml` editado e o
`make dry-run` do Passo 1 conferido (o `make run` que abre os PRs fica para o seu OK).

```
Optimus Prime iniciar incidentes         # um board: vai ATÉ o make dry-run do Passo 1
Optimus Prime iniciar todos os boards    # varredura: cada board vai só ATÉ o Notion
Optimus Prime, iniciar                   # pergunta o board
```

- **Versão-alvo:** `Release` sequencial `X.(Y+1).0` por board, automática. Incidente **não** é
  hotfix por padrão — hotfix só quando você avisar (ou via `--versao`).
- **Depois da mensagem `Confira`:** você autoriza o `make run` do Passo 1 (abre os PRs,
  `auto_merge=false`). Merge, master (Passo 2) e triggers (Passo 3) também são seus — Receita 3.

---

## Receita 3 — Sincronizar/deployar (Sync) — os passos seus

**Quando:** abrir os PRs pré-prod, promover para master e deployar. Todo `make run` é **sob seu
comando**, sempre com dry-run antes. Comandos do `sync-repos-from-master`:

```
make dry-run PR_TITLE="[Release]/[Hotfix] <versão>"   # simulação segura (sempre antes)
make run     PR_TITLE="[Release]/[Hotfix] <versão>"   # abre/atualiza PRs (auto_merge=false → NÃO mergeia)
make dry-run-triggers                                 # simula o deploy GCP
make run-triggers                                     # deploy GCP (SEM PR_TITLE) — 100% seu, pós-QA
```

Promoção de branches (`make run` sempre com `target` explícito, nunca direto pra master):

1. **Passo 1** `prerelease → teste_regressivo` — Optimus edita o YAML e roda `make dry-run` (dentro
   do `iniciar`); o `make run` é sob seu OK; **você mergeia**.
2. **Passo 2** `teste_regressivo → master` — **você comanda**; Optimus edita YAML + `make dry-run`;
   o `make run` de master só sob seu override explícito.
3. **Passo 3** `make run-triggers` (ambientes dos clientes) — **100% seu**; você aprova os builds no GCP.
4. **Pós-deploy** `master → develop/stage/prerelease` — `make run PR_TITLE="Sync Master"`; herda o
   **mesmo conjunto de repos** do ciclo (mudança na lista = erro de sequência).

---

## Sequência e gates (o que roda por baixo)

| # | Etapa | Comando por baixo | Autônomo? / Gate (Ronan) |
|---|-------|-------------------|--------------------------|
| 1 | **Versão-alvo** | próxima `X.(Y+1).0` pela última no Notion | autônomo |
| 2 | **Coletor** | Atlassian MCP + `tools/optimus_extract.py` | autônomo (erro → documenta e para) |
| 3 | **Validador** | `tools/optimus_gates.py` (regra v2 + D1/D2) | autônomo — pausa SÓ em card ambíguo |
| 4 | **Montador** | Notion (create/update + re-fetch) | autônomo — sem pedir OK |
| 5 | **Notificador** | *sandbox* | autônomo (só mostra pro Ronan) |
| — | **↑ todos os boards PARAM AQUI (Notion)** · board único segue | | |
| 6.0 | **Sync — edita `repos.yaml`** | toggle de `#` + gates determinísticos | autônomo |
| 6.1 | **Passo 1** | `make dry-run` → mensagem `Confira` → `make run` | dry autônomo; **run sob seu OK** |
| 6.2 | **Passo 2** (master) | edita YAML → `make dry-run` → `make run` | **você comanda** → QA testa |
| 6.3 | **Passo 3** (triggers) | `make dry-run-triggers` → `make run-triggers` | **você comanda** + aprova builds GCP |
| 6.4 | **Pós-deploy** | mesmos repos → `make run PR_TITLE="Sync Master"` | **OK antes do run** |
| 7 | **Resumo** | grava `execucoes/release-AAAA-MM-DD-NNN.json` | autônomo |

Índice completo dos gates (o que é script, o que é LLM): [`GATES.md`](GATES.md).
Mapeamento dos boards (JQL, prioridade): `.claude/skills/coletor/SKILL.md`, "Registro de boards".
