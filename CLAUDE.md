# CLAUDE.md

Guia para o Claude Code / agentes neste repositório.

## Propósito
Automatiza a preparação de **release notes de deploy** e a **sincronização de branches**: coleta cards
no Jira, valida por conteúdo, documenta a versão no Notion, notifica responsáveis e aciona o
`sync-repos-from-master` (que abre os PRs / dispara triggers). **MCP-first, código mínimo, clean
architecture** (referência: o próprio `sync-repos-from-master`). O **deploy real e os merges são do Ronan**.

> **Sem clients Python bespoke** (spec §3): a orquestração é a **skill sobre os MCPs** (Atlassian/Notion)
> + os `make` do `sync-repos-from-master`. Aciona-se com **"optimus prime iniciar"** no Claude Code
> (dentro do PyCharm), com o Claude conectado e os MCPs ativos. **Autônomo até o `make dry-run` do Sync
> Passo 1** (board único: doc no Notion + edita o `repos.yaml` + `make dry-run`); **o `make run` do Passo 1
> (abre os PRs pré-prod), merge, master (Passo 2) e triggers (Passo 3) = Ronan**.

## Comandos
Orquestrador (**Optimus Prime**), via slash command:
```
/optimus-prime verificar   # dry/seguro, não toca em nada (só relatório)
/optimus-prime executar    # board único: autônomo até o dry-run do Passo 1 (doc no Notion + edita YAML + dry-run); make run sob OK do Ronan
```
No `executar` de um board, os passos autônomos (versão-alvo automática → coletor → validador → montador
**cria/atualiza o Notion sem pedir OK** → notificador sandbox → **Sync**: edita o `repos.yaml` e roda o
`make dry-run` do Passo 1) rodam **sem aprovação humana** e terminam na mensagem única `Optimus Prime
retornando com o resultado = Confira`. A **única pausa** é **card genuinamente ambíguo** (heurística
só-banco não fecha, ou repo ≠ PR). **O `make run` do Passo 1 (abre os PRs pré-prod), merge, master
(Passo 2) e triggers (Passo 3)** seguem **sob comando explícito do Ronan**. Guia operacional: [`docs/COMANDOS.md`](docs/COMANDOS.md).
Comandos do `sync-repos-from-master` que o Optimus Prime dispara (sempre `dry-run` antes):
```
make dry-run PR_TITLE="<versão>"            # simulação segura do sync
make run PR_TITLE="<versão>"                # abre/atualiza PRs (auto_merge=false → NÃO mergeia)
make dry-run-triggers / make run-triggers   # deploy GCP — Passo 3, 100% do Ronan
```

## Arquitetura (papéis, não apps)
Skills por papel em `.claude/skills/`, orquestradas sobre MCPs (Atlassian + Notion) e `make`:
```
coletor → validador → montador → notificador → [Sync]
        (orquestrador "Optimus Prime" coordena tudo, com gates de segurança)
```
Fonte da verdade do comportamento: `spec/spec.md`.

## Fluxo de dados
Jira (Atlassian MCP, `read:jira-work`) → cards normalizados (§7) → validador (regra v2) →
aprovados × reprovados → montador (Notion, base "Versões - NewContract") → doc da versão →
Sync (`repos.yaml` **guiado pela doc do Notion**) → `make run` → PR.

## Fluxo de promoção de branches (Sync)
`make run` **sempre com `target` explícito**, **nunca direto pra master**:
1. `prerelease → teste_regressivo` (pré-prod) — Optimus Prime edita o YAML e roda o `make dry-run`; o
   **`make run` (abre os PRs) e o merge são do Ronan**.
2. `teste_regressivo → master` (prod) — **só sob comando do Ronan**; Optimus Prime só edita o YAML.
3. `make run-triggers` (ambientes dos clientes) — **100% do Ronan**, após OK do QA.
4. `master → develop/stage/prerelease` (pós-deploy) — **reusa exatamente os mesmos repos do ciclo ativo**; não inventa, não reduz e não reclassifica repos entre Passo 1/2/3 e sync de volta.

## Guardrails inquebráveis
- **Extração de links e gates D1/D2 = código determinístico em `tools/`** (o LLM não interpreta ADF);
  MCP-first mantido para I/O e escrita.
- **`repos.yaml` só comenta/descomenta + Sync inviolável:** o cwd é SEMPRE o workflow; NUNCA `cd` no
  `sync-repos-from-master`. O Optimus só (1) alterna o `#` de linhas existentes em
  `"$SYNC_REPO_PATH/repos.yaml"` e (2) roda `make -C "$SYNC_REPO_PATH" <alvo>`. Nunca reescreve/gera o
  YAML nem cria outro arquivo no sync; `.env`/`credentials/` do sync são intocáveis; backup/erros/
  execucoes ficam no workflow. Gate `tools/optimus_yaml_gate.py` reverte edição que não seja só de
  comentário (backup antes; exit 1 → restaura e para).
- **Autonomia até o `make dry-run` do Sync Passo 1:** no `executar` de board único, os passos rodam **sem
  aprovação humana** — inclui a doc no Notion, a edição do `repos.yaml` e o `make dry-run` do Passo 1 — e
  terminam na mensagem única `Confira`. **O `make run` do Passo 1 é sob OK explícito do Ronan.** **Única
  pausa:** card genuinamente ambíguo. No alvo `todos os boards`, ainda termina no Notion.
- **`make run` (Passo 1 e Passo 2), merge/master/prod e `run-triggers` = só o Ronan** (`auto_merge=false`);
  nada sobe sem autorização.
- **Pós-deploy inquebrável:** o sync `master → develop/stage/prerelease` mantém o mesmo conjunto de repos do ciclo
  que já foi validado nos passos anteriores; o Optimus nunca “filtra” repos por conta própria nem muda a lista na
  transição para `Sync Master`.
- **Gate por ação:** `dry-run` → parseia saída (`chave=valor`) + exit code (0 ok / 1 erro); **erro
  documenta em `erros/AAAA-MM-DD-*.md` e para**. **Todo `make run` (Passo 1 e Passo 2) e as triggers
  (Passo 3):** limpo → mostra e pede **comando explícito** do Ronan antes do real.
- **GATE-PROMO (nunca direto pra master):** antes de **QUALQUER** `make dry-run`/`make run`/triggers,
  `tools/optimus_promotion_gate.py "$SYNC_REPO_PATH/repos.yaml" --step <passo1|passo2|pos-deploy>` tem de
  retornar exit 0. Só aprova pares da whitelist (`tools/promotion.json`); bloqueia `master` vindo de fonte
  ≠ `teste_regressivo` (ex.: `prerelease→master`), self-sync e passo divergente. Exit 1 → não roda o
  `make`, restaura backup, documenta em `erros/` e para. Ao trocar de passo, ajuste `source` **e** `targets`.
- **GATE-TRIGGERS:** antes de `make dry-run`/`make run` (Passo 1/2/pós-deploy), `python3 tools/optimus_triggers_gate.py "$SYNC_REPO_PATH/repos.yaml" --expect none` — bloqueia se houver trigger ativo (dispararia em hora errada). Antes de `make dry-run-triggers`/`make run-triggers` (Passo 3), `python3 tools/optimus_triggers_gate.py "$SYNC_REPO_PATH/repos.yaml" --expect present` — bloqueia se não houver trigger ou se houver orfão. Exit 1 → não roda `make`, documenta e para.
- **Não inventar dado**; privilégio mínimo (Jira leitura; Notion só a base de releases).
- Execuções em `execucoes/*.json`; refino de skill/comando **só com OK do Ronan**.
- **Commits:** Conventional Commits em inglês, só com OK; **sem remote externo**.
