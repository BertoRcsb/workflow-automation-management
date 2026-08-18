# Arquitetura — esquema visual do sistema

Diagramas Mermaid inline (renderizam no GitHub/VS Code/PyCharm sem exportar imagem) refletindo a
**arquitetura atual**: subagentes isolados + camada determinística em `tools/`.

> Comportamento canônico: [`../spec/spec.md`](../spec/spec.md) · Sequência normativa da esteira:
> [`../.claude/skills/orquestrador/SKILL.md`](../.claude/skills/orquestrador/SKILL.md) ·
> Contrato de handoff dos subagentes: [`../AGENTS.md`](../AGENTS.md) ·
> Índice dos gates: [`GATES.md`](GATES.md).
>
> Para slides/stakeholders existe a versão em imagens (histórico de julho/2026) em
> [`APRESENTACAO.md`](APRESENTACAO.md) — este arquivo é a referência técnica atualizada.

## 1. Visão em camadas

O Claude (orquestrador "Optimus Prime") coordena subagentes isolados; todo cálculo crítico é código
determinístico em `tools/` — o LLM chama o script e lê a saída, nunca decide de cabeça.

```mermaid
flowchart TB
    R["Ronan<br>/optimus-prime verificar | executar"]

    subgraph Orq["Orquestrador — Optimus Prime (Claude Code)"]
        O["coordena a esteira e governa o Sync"]
    end

    subgraph Sub["Subagentes (contexto isolado, ferramentas mínimas)"]
        C["coletor"]
        V["validador"]
        M["montador"]
        N["notificador (sandbox)"]
    end

    subgraph Tools["Camada determinística — tools/"]
        T1["optimus_extract.py<br>PR/repo do ADF"]
        T2["optimus_gates.py<br>regra v2 + D1/D2 + crosscheck"]
        T3["optimus_next_version.py<br>versão-alvo (semver)"]
        T4["optimus_sync.py — driver único<br>backup → GATE-YAML → GATE-PROMO → GATE-TRIGGERS → make"]
        T5["rules.json · promotion.json<br>config das regras"]
    end

    subgraph Bracos["Braços — I/O"]
        MCP1["MCP Atlassian<br>Jira, read-only"]
        MCP2["MCP Notion<br>base Versões - NewContract"]
        MK["make -C sync-repos-from-master"]
    end

    R --> O
    O --> C --> V --> M --> N
    C --> T1 --> MCP1
    V --> T2
    O --> T3
    M --> MCP2
    O --> T4 --> MK
    T2 -.-> T5
    T4 -.-> T5
```

## 2. Fluxo do `executar` (board único)

Autônomo até o `make dry-run` do Sync Passo 1; a partir daí, **todo `make run`, merge, master e
triggers exigem OK explícito do Ronan**. Única pausa antes disso: card genuinamente ambíguo.

```mermaid
sequenceDiagram
    actor R as Ronan
    participant O as Optimus Prime
    participant J as Jira (MCP)
    participant N as Notion (MCP)
    participant S as Sync (driver + make)

    R->>O: /optimus-prime executar (board)
    Note over O: versão-alvo via optimus_next_version.py
    O->>J: coletor — JQL do board + optimus_extract.py
    J-->>O: contrato normalizado (cards + PRs/repos)
    O->>O: validador — optimus_gates.py (regra v2, D1/D2)
    alt card genuinamente ambíguo
        O->>R: pergunta (única pausa)
        R-->>O: decisão
    end
    O->>N: montador — cria/atualiza a release (molde canônico)
    O->>O: notificador — rascunhos em sandbox
    O->>S: edita repos.yaml (toggle #) + make dry-run — Passo 1
    Note over O,S: sempre via optimus_sync.py (backup + 3 gates antes de todo make)
    O->>R: "Optimus Prime retornando com o resultado = Confira"
    Note over R,S: daqui em diante, cada ação real é gate por ação
    R->>O: OK Passo 1
    O->>S: make run (abre PRs pré-prod) — merge é do Ronan
    R->>O: OK Passo 2 (master)
    O->>S: dry-run + run PR_TITLE="Release X.Y.Z"
    R->>O: OK Passo 3 (triggers)
    O->>S: dry-run-triggers + run-triggers — builds aprovados no GCP
    O->>S: pós-deploy — mesmos repos, PR_TITLE="Sync Master" (OK antes do run)
    O->>O: grava execucoes/release-AAAA-MM-DD-NNN.json
```

## 3. Promoção de branches (Sync)

Nunca direto pra master; `optimus_promotion_gate` bloqueia prerelease→master, self-sync e passo
divergente. Triggers só no Passo 3.

```mermaid
flowchart LR
    P["prerelease"] -- "Passo 1<br>dry autônomo · run sob OK" --> TR["teste_regressivo"]
    TR -- "Passo 2 (master)<br>Ronan comanda" --> M["master"]
    M -- "Passo 3 (triggers)<br>Ronan comanda + aprova builds GCP" --> PROD(("prod"))
    M -. "pós-deploy: Sync Master<br>OK antes do run" .-> D["develop · stage · prerelease"]
```

## 4. Dentro do driver do Sync (`tools/optimus_sync.py`)

Toda ação no sync passa pelo driver — nunca `make` direto nem gates soltos.

```mermaid
flowchart LR
    A["backup do repos.yaml"] --> B["edição (toggle #)"]
    B --> G1["GATE-YAML"] --> G2["GATE-PROMO"] --> G3["GATE-TRIGGERS"] --> MK["make -C ..."]
    G1 & G2 & G3 -- "falha" --> ERR["restaura backup ·<br>documenta em erros/ · para (exit 1)"]
```
