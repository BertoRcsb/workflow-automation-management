# CLAUDE.md

Guia para o Claude Code / agentes neste repositório.

## Propósito
Automatiza a preparação de **release notes de deploy** e a **sincronização de branches**: coleta cards
no Jira, valida por conteúdo, documenta a versão no Notion, notifica responsáveis e aciona o
`sync-repos-from-master` (que abre os PRs / dispara triggers). **MCP-first, código mínimo, clean
architecture** (referência: o próprio `sync-repos-from-master`). O **deploy real e os merges são do Ronan**.

> **Sem clients Python bespoke** (spec §3): a orquestração é a **skill sobre os MCPs** (Atlassian/Notion)
> + os `make` do `sync-repos-from-master`. Aciona-se com **"optimus prime iniciar"** no Claude Code
> (dentro do PyCharm), com o Claude conectado e os MCPs ativos. **Autônomo até o Sync Passo 1** (board
> único: dry-run + `make run` que abre os PRs pré-prod); **merge, master (Passo 2) e triggers (Passo 3) = Ronan**.

## Comandos
Orquestrador (**Optimus Prime**), via slash command:
```
/optimus-prime verificar   # dry/seguro, não toca em nada (só relatório)
/optimus-prime executar    # board único: autônomo incluindo o Sync Passo 1 (dry-run + make run, PRs pré-prod)
```
No `executar` de um board, os passos 1–7 (versão-alvo automática → coletor → validador → montador **cria/atualiza
o Notion sem pedir OK** → notificador sandbox → **Sync Passo 1**: edita o `repos.yaml`, `make dry-run` e, se
limpo, **`make run`** automático → resumo) rodam **sem aprovação humana**. A **única pausa** é **card
genuinamente ambíguo** (heurística só-banco não fecha, ou repo ≠ PR). **Merge, master (Passo 2) e triggers
(Passo 3)** seguem **sob comando explícito do Ronan**. Guia operacional: [`docs/COMANDOS.md`](docs/COMANDOS.md).
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
1. `prerelease → teste_regressivo` (pré-prod) — Optimus Prime roda; **merge é do Ronan**.
2. `teste_regressivo → master` (prod) — **só sob comando do Ronan**; Optimus Prime só edita o YAML.
3. `make run-triggers` (ambientes dos clientes) — **100% do Ronan**, após OK do QA.

## Guardrails inquebráveis
- **Autonomia até o Sync Passo 1:** no `executar` de board único, passos 1–7 rodam **sem aprovação
  humana** — inclui a doc no Notion, a edição do `repos.yaml` e, com dry-run limpo, o `make run` do
  Passo 1. **Única pausa:** card genuinamente ambíguo. No alvo `todos os boards`, ainda termina no Notion.
- **Merge/master/prod e `run-triggers` = só o Ronan** (`auto_merge=false`); nada sobe sem autorização.
- **Gate por ação:** `dry-run` → parseia saída (`chave=valor`) + exit code (0 ok / 1 erro). **Passo 1:**
  erro documenta em `erros/AAAA-MM-DD-*.md` e **para**; **limpo → dispara o `make run` automaticamente**.
  **Master (Passo 2) e triggers (Passo 3):** limpo → mostra e pede **comando explícito** antes do real.
- **Não inventar dado**; privilégio mínimo (Jira leitura; Notion só a base de releases).
- Execuções em `execucoes/*.json`; refino de skill/comando **só com OK do Ronan**.
- **Commits:** Conventional Commits em inglês, só com OK; **sem remote externo**.
