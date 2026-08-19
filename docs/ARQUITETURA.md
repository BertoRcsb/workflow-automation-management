# Arquitetura — esquema visual do sistema

Diagramas Mermaid inline (renderizam no GitHub/VS Code/PyCharm sem exportar imagem) refletindo a
**arquitetura atual**: subagentes isolados + camada determinística em `tools/`.

> Comportamento canônico: [`../spec/spec.md`](../spec/spec.md) · Sequência normativa da esteira:
> [`../.claude/skills/orquestrador/SKILL.md`](../.claude/skills/orquestrador/SKILL.md) ·
> Contrato de handoff dos subagentes: [`../AGENTS.md`](../AGENTS.md) ·
> Índice dos gates: [`GATES.md`](GATES.md).
>
> Para slides/stakeholders, use [`APRESENTACAO.md`](APRESENTACAO.md) — mesmos temas em imagens
> exportadas ([`diagramas/`](diagramas/)). Este arquivo é a referência técnica, fonte dos detalhes.
>
> Legenda de cores/formas (comum a todos): **âmbar/estádio** = ação humana (usuário) ·
> **azul** = LLM (Optimus/subagentes) · **verde/subrotina** = código determinístico ·
> **cinza/hexágono** = sistema externo (MCP/make) · **vermelho** = falha/parada.

## 1. Visão em camadas

O Claude (orquestrador "Optimus Prime") coordena subagentes isolados; todo cálculo crítico é código
determinístico em `tools/` — o LLM chama o script e lê a saída, nunca decide de cabeça.

```mermaid
%%{init: {"theme":"base","themeVariables":{"fontSize":"13px","lineColor":"#8A94A6","primaryColor":"#EDF1F5","primaryBorderColor":"#5A6B7B","primaryTextColor":"#2D3B48","clusterBkg":"#FAFBFC","clusterBorder":"#D5DBE3","edgeLabelBackground":"#FFFFFF"},"flowchart":{"curve":"basis","nodeSpacing":26,"rankSpacing":34}}}%%
flowchart TB
    U(["Usuário<br>/optimus-prime verificar | executar"]):::humano

    subgraph Orq["Orquestrador — Optimus Prime (Claude Code)"]
        O(["coordena a esteira e governa o Sync"]):::llm
    end

    subgraph Sub["Subagentes (contexto isolado, ferramentas mínimas)"]
        C["coletor"]:::llm
        V["validador"]:::llm
        M["montador"]:::llm
        N["notificador (sandbox)"]:::llm
    end

    subgraph Tools["Camada determinística — tools/"]
        T1[["optimus_extract.py<br>PR/repo do ADF"]]:::det
        T2[["optimus_gates.py<br>regra v2 + D1/D2 + crosscheck"]]:::det
        T3[["optimus_next_version.py<br>versão-alvo (semver)"]]:::det
        T4[["optimus_sync.py — driver único<br>backup → 3 gates → make"]]:::det
        T5[("rules.json<br>promotion.json")]:::det
    end

    subgraph Bracos["Braços — I/O"]
        MCP1{{"MCP Atlassian<br>Jira · read-only"}}:::io
        MCP2{{"MCP Notion<br>base Versões - NewContract"}}:::io
        MK{{"make -C sync-repos-from-master"}}:::io
    end

    U --> O
    O --> C --> V --> M --> N
    C --> T1 --> MCP1
    V --> T2
    O --> T3
    M --> MCP2
    O --> T4 --> MK
    T2 -.-> T5
    T4 -.-> T5

    classDef humano fill:#FFF3D6,stroke:#B7791F,color:#7B4B12,stroke-width:1.5px
    classDef llm fill:#E8ECFB,stroke:#4C5FD5,color:#2A3577
    classDef det fill:#DDF3E7,stroke:#2F855A,color:#1C4532
    classDef io fill:#EDF1F5,stroke:#5A6B7B,color:#2D3B48
```

## 2. Fluxo do `executar` (board único)

Autônomo até o `make dry-run` do Sync Passo 1; a partir daí, **todo `make run`, merge, master e
triggers exigem OK explícito do usuário**. Não há microaprovações antes disso; ambiguidade ou erro
falha fechado, é documentado e encerra com bloqueio objetivo.

```mermaid
%%{init: {"theme":"base","themeVariables":{"fontSize":"13px","actorBkg":"#E8ECFB","actorBorder":"#4C5FD5","actorTextColor":"#2A3577","signalColor":"#5A6B7B","signalTextColor":"#2D3B48","noteBkgColor":"#FFF3D6","noteBorderColor":"#B7791F","noteTextColor":"#7B4B12","labelBoxBkgColor":"#EDF1F5","labelBoxBorderColor":"#5A6B7B"}}}%%
sequenceDiagram
    actor U as Usuário
    participant O as Optimus Prime
    participant J as Jira (MCP)
    participant N as Notion (MCP)
    participant S as Sync (driver + make)

    U->>O: /optimus-prime executar (board)
    Note over O: versão-alvo via optimus_next_version.py
    O->>J: coletor — JQL do board + optimus_extract.py
    J-->>O: contrato normalizado (cards + PRs/repos)
    O->>O: validador — optimus_gates.py (regra v2, D1/D2)
    alt card genuinamente ambíguo
        O->>O: refino automático único
        O->>O: se persistir, documenta e encerra blocked
    end
    O->>N: montador — cria/atualiza a release (molde canônico)
    O->>O: notificador — rascunhos em sandbox
    O->>S: edita repos.yaml (toggle #) + make dry-run — Passo 1
    Note over O,S: sempre via optimus_sync.py (backup + 3 gates antes de todo make)
    O->>U: "Optimus Prime retornando com o resultado = Confira"
    Note over U,S: daqui em diante, cada ação real é gate por ação
    U->>O: OK Passo 1
    O->>S: make run (abre PRs pré-prod) — merge é do usuário
    U->>O: OK Passo 2 (master)
    O->>S: dry-run + run PR_TITLE="Release X.Y.Z"
    U->>O: OK Passo 3 (triggers)
    O->>S: dry-run-triggers + run-triggers — builds aprovados no GCP
    O->>S: pós-deploy — mesmos repos, PR_TITLE="Sync Master" (OK antes do run)
    O->>O: grava execucoes/release-AAAA-MM-DD-NNN.json
```

## 3. Promoção de branches (Sync)

Nunca direto pra master; `optimus_promotion_gate` bloqueia prerelease→master, self-sync e passo
divergente. Triggers só no Passo 3.

```mermaid
%%{init: {"theme":"base","themeVariables":{"fontSize":"13px","lineColor":"#8A94A6","primaryColor":"#EDF1F5","primaryBorderColor":"#5A6B7B","primaryTextColor":"#2D3B48","edgeLabelBackground":"#FFFFFF"},"flowchart":{"curve":"basis","nodeSpacing":30,"rankSpacing":56}}}%%
flowchart LR
    P["prerelease"]:::io -- "Passo 1<br>dry autônomo · run sob OK" --> TR["teste_regressivo"]:::io
    TR -- "Passo 2 (master)<br>usuário comanda" --> M["master"]:::io
    M -- "Passo 3 (triggers)<br>usuário comanda + aprova builds GCP" --> PROD(["prod"]):::humano
    M -. "pós-deploy: Sync Master<br>OK antes do run" .-> D["develop · stage · prerelease"]:::io
    classDef humano fill:#FFF3D6,stroke:#B7791F,color:#7B4B12,stroke-width:1.5px
    classDef io fill:#EDF1F5,stroke:#5A6B7B,color:#2D3B48
```

## 4. Dentro do driver do Sync (`tools/optimus_sync.py`)

Toda ação no sync passa pelo driver — nunca `make` direto nem gates soltos.

```mermaid
%%{init: {"theme":"base","themeVariables":{"fontSize":"13px","lineColor":"#8A94A6","primaryColor":"#EDF1F5","primaryBorderColor":"#5A6B7B","primaryTextColor":"#2D3B48","edgeLabelBackground":"#FFFFFF"},"flowchart":{"curve":"basis","nodeSpacing":26,"rankSpacing":40}}}%%
flowchart LR
    A[["backup do repos.yaml"]]:::det --> B["edição (toggle #)"]:::llm
    B --> G1[["GATE-YAML"]]:::det --> G2[["GATE-PROMO"]]:::det --> G3[["GATE-TRIGGERS"]]:::det --> MK{{"make -C ..."}}:::io
    G1 & G2 & G3 -- "falha" --> ERR["restaura backup ·<br>documenta em erros/ · para (exit 1)"]:::alerta
    classDef llm fill:#E8ECFB,stroke:#4C5FD5,color:#2A3577
    classDef det fill:#DDF3E7,stroke:#2F855A,color:#1C4532
    classDef io fill:#EDF1F5,stroke:#5A6B7B,color:#2D3B48
    classDef alerta fill:#FBE1E1,stroke:#C53030,color:#742A2A
```
