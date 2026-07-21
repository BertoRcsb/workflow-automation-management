# CLAUDE.md

Guia para o Claude Code / agentes neste repositório.

## Propósito
Automatiza a preparação de **release notes de deploy** e a **sincronização de branches**: coleta cards
no Jira, valida por conteúdo, documenta a versão no Notion, notifica responsáveis e aciona o
`sync-repos-from-master` (que abre os PRs / dispara triggers). **MCP-first, código mínimo, clean
architecture** (referência: o próprio `sync-repos-from-master`). O **deploy real e os merges são do Ronan**.

> **Sem clients Python bespoke** (spec §3): a orquestração é a **skill sobre os MCPs** (Atlassian/Notion)
> + os `make` do `sync-repos-from-master`. Aciona-se com **"optimus prime iniciar"** no Claude Code
> (dentro do PyCharm), com o Claude conectado e os MCPs ativos. **Autônomo até o Notion**; do Sync em
> diante pausa em cada ação (merge/master/triggers = Ronan).

## Comandos
Orquestrador (**Optimus Prime**), via slash command:
```
/optimus-prime verificar   # dry/seguro, não toca em nada (só relatório)
/optimus-prime executar    # autônomo ATÉ criar a doc no Notion; PARA antes do Sync (make run)
```
No `executar`, os passos 1–5 e 7 (versão-alvo automática → coletor → validador → montador **cria/atualiza
o Notion sem pedir OK** → notificador sandbox → resumo) rodam **sem aprovação humana**. A **única pausa
antes do Notion** é **card genuinamente ambíguo** (heurística só-banco não fecha, ou repo ≠ PR). **Do Sync
em diante** (Passo 6, `make run` etc.) é **sob OK explícito do Ronan**, com **gate por ação**. Guia
operacional: [`docs/COMANDOS.md`](docs/COMANDOS.md).
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
- 🤖 **Autonomia até o Notion:** no `executar`, passos 1–5 e 7 rodam **sem aprovação humana** (a doc no
  Notion é criada automaticamente). **Única pausa antes do Notion:** card genuinamente ambíguo.
- 🚫 **Merge/master/prod e `run-triggers` = só o Ronan** (`auto_merge=false`); nada sobe sem autorização.
- 🛡️ **Gate por ação (Sync em diante):** `dry-run` → parseia saída (`chave=valor`) + exit code (0 ok /
  1 erro) → erro documenta em `erros/AAAA-MM-DD-*.md` e **para** → limpo pede **OK** antes do real. A
  esteira **não dispara `make` sozinha**.
- 🔒 **Não inventar dado**; privilégio mínimo (Jira leitura; Notion só a base de releases).
- 📓 Execuções em `execucoes/*.json`; refino de skill/comando **só com OK do Ronan**.
- **Commits:** Conventional Commits em inglês, só com OK; **sem remote externo**.
