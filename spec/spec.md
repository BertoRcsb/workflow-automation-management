# Spec — Esteira Inteligente de Release Notes (Jira → Notion)

> Documento **vivo** (v1, 2026-07-13). Funde a spec "Esteira Inteligente para Montagem de Pacotes
> de Deploy" com o que **validamos no 1º teste E2E**. Base de origem das **skills**.
> Relacionados: `workflow-with-automation-assisted-by-management.md` (plano geral), `PROPOSTA.md`,
> e o doc original `esteira-inteligente-para-montagem-de-pacotes-de-deploy.md`.
>
> **Escopo (não é só incidentes):** a esteira abrange (ou abrangerá) os boards de **incidents,
> features e refatoração**. O 1º ciclo foi validado em incidentes (PB), e daí cresce. (Por isso a
> esteira não é a "de incidentes"; a spec vive em `spec/spec.md`.)

## 1. Visão geral

Automatizar a preparação da **release notes** de deploy: coletar cards no Jira, **validar** por
conteúdo (não só status), separar **aprovados × reprovados**, registrar os aprovados no **Notion**
e **notificar** pendências dos reprovados. O deploy em si segue manual (`sync-repos-from-master`).

Quatro papéis + um orquestrador (podem ser módulos/prompts, não precisam ser 4 apps):

| Papel | Função | Estado atual |
|-------|--------|--------------|
| **Coletor** | busca cards candidatos no Jira | validado (JQL no PB) |
| **Validador** | aplica o gate de elegibilidade (regra v2) | validado |
| **Montador** | escreve/atualiza a release no Notion (molde 1.110.0) | validado |
| **Notificador** | comunica pendências dos reprovados | pendente (sandbox) |
| **Orquestrador** | coordena tudo + governa o Sync; segurança por ação, consolida, documenta erro | formalizado (skill `orquestrador` / **"Optimus Prime"**) |

## 2. Objetivo

- Somente cards **aptos por conteúdo** entram no pacote.
- Critérios aplicados de forma **consistente e configurável**.
- Release Notes **padronizada** (molde das versões anteriores).
- Responsáveis recebem **pendências** rapidamente.
- Toda decisão é **rastreável** e a execução é **idempotente**.

## 3. Decisão de arquitetura — **MCP-first**

> **Decisão #1 (recomendada):** implementar como **skill orquestrando os MCPs** (Atlassian + Notion),
> escrevendo Python **só onde o MCP não cobre** (parsear resposta grande, aplicar regra do YAML,
> consolidar o resumo). **Não** criar `jira_client.py`/`notion_client.py` próprios — isso repetiria o
> overengineering que o projeto quer evitar (`iac-platform`). Já provamos que coleta + validação +
> montagem saem 100% via MCP.
>
> O doc original sugere um serviço Python com clients dedicados; adotamos a **separação lógica** dele
> (Coletor/Validador/Montador/Notificador/Orquestrador) **sem** os clients bespoke.

## 4. Fluxo simplificado

```mermaid
flowchart LR
    A[Jira - projeto PB] --> B[Coletor]
    B --> C[Cards candidatos normalizados]
    C --> D[Validador - regra v2]
    D -->|Aprovado| E[Lista aprovados]
    D -->|Reprovado| F[Lista reprovados + pendencias]
    E --> G[Montador]
    G --> H[Release Notes no Notion]
    F --> I[Notificador - sandbox]
    I --> J[Responsavel - por ora so o Ronan]
```

## 5. Agentes

### 5.1 Coletor
Busca no Jira os cards candidatos e os normaliza (ver modelo em §7).
- **Entrada:** projeto(s), filtro JQL, status alvo, versão de destino.
- **Config atual:** projeto `PB`; `issuetype = Incidente`; status `Teste regressivo`, `Pronto para deploy`.
- **Um board por ciclo — NUNCA misturar:** coletar de **um** board por execução (**incidentes** *ou*
  **features** *ou* **refatoração**); o board é **parâmetro** da coleta. Cada board → sua própria
  release/hotfix. Misturar boards só com **OK explícito do Ronan** ("avisaremos ao Optimus"). Hoje: incidentes/PB.
- **Registro de boards (config, não texto solto):** cada board tem projeto/issuetype/status/JQL numa
  tabela na skill `coletor` ("Configuração atual"), com **ordem = prioridade**. Mapeamento **confirmado**
  (os 3 "boards" são visões dentro do `PB`; o MCP não expõe a API de boards, então o issuetype foi
  inferido pela população em status de deploy + OK do Ronan): **1º Linha de frente/incidentes = `Incidente`**
  · **2º Features = `Story`** · **3º Refatoração = `Story`** (menos importante). Status alvo iguais nos três.
- **Features × Refatoração (critério fino confirmado):** ambos são `Story`; a separação é **pelo
  título** — **Refatoração** = `summary ~ "Refatoração"` (cards `FRONT -`/`BACK -`/`Triagem -
  Refatoração ...`); **Features** = o complemento (`summary !~ "Refatoração"`). Refatoração é o 3º/menos
  importante. Card no board errado = refino do filtro (com OK do Ronan) — **nunca inventar** critério.
- **Varredura "todos os boards":** o orquestrador pode varrer os três **em sequência, por prioridade**
  (incidentes 1º), rodando a esteira **isolada por board** (coleta→validação→**Notion próprio**). Isso
  **reforça** a regra "nunca misturar" (cada board = sua release/hotfix); **não** é misturar. A varredura
  **termina no Notion** — o Sync/deploy segue **por-board e em dias diferentes**. Board sem filtro → pula
  e reporta. Ver §6.1.
- **Saída:** lista de cards com chave, título, status, responsável, produto, PR, repo, ação de dados.
- **Aprendizado:** respostas do Jira são **grandes** → pedir só os campos necessários e parsear
  (salvar em arquivo + Python quando estourar o limite de tokens).

### 5.2 Validador
Aplica o **gate por conteúdo** (o status **não** garante prontidão — confirmado na prática: os 3
cards em "Pronto para deploy" estavam vazios).

**Regra de elegibilidade v2:** um card **passa** se
1. tem **PR + repositório** (mudança de código), **OU**
2. é **somente ação de banco/proc** — sem PR, identificado por **Ação de dados = Sim**
   (PR/repo vazio ou `"N/A"` / `"Apenas PROC"`).

**Barra** quem **não tem nada** (sem PR, sem repo, sem ação de dados). `"N/A"` **não** é link válido.

**Heurística "só-banco legítimo"** (validada 2026-07-14, caso-modelo **PB-5778** — virou deploy
real em prod): para distinguir banco legítimo de "código que esqueceu a PR" →
`Ação de dados = Sim` **e** (assignee é responsável de banco **ou** a descrição cita
proc/procedure/carga/seleção/query) → **aprova sem exigir PR/repo**. PB-5778: Ação de dados=Sim,
sem PR/repo, assignee **Alexandre Bolonhini** (banco) + descrição sobre corrigir a procedure → aprovado.

- **Saída aprovados:** chave, título, responsável, resumo, categoria, evidências, data da validação.
- **Saída reprovados:** chave, título, responsável, `pending_items`, orientação, data.
- **Refino aberto:** ler PR do **painel Development** quando o campo estiver vazio.

### 5.3 Montador
Cria/atualiza a página da versão no Notion, no **molde 1.110.0**.
- **Tabela única:** `Item · Pull Requests · Tem Ação de Banco ? · Tem Ação de Infra ? · Merge Realizado ?`
  - **Item:** card como link **com título** e status (ex.: `[PB-5415 — <título>](.../browse/PB-5415) · <status>`).
    O *mention* nativo do Jira não é reproduzível via MCP; o link enriquecido é o equivalente suportado.
  - **Pull Requests:** URL da PR (código) ou `• APENAS PROC` (banco).
  - **Infra / Merge / nome do proc:** em branco até apurarmos (o agente **não inventa**).
- **Blocos:** Testes regressivos · Ambientes · Repositórios para Deploy · Participantes do Deploy
  (Dados: Alexandre Rudoi · QA: Dorgival Silva Filho · DevOps/Resp.: Ronan Berto / Yuri Stolai · sobreaviso: assignees).
- **Categorias possíveis (evolução):** correção · banco de dados · infraestrutura · melhoria ·
  alteração técnica · procedimento pós-deploy.
- **Idempotência:** não duplicar card; se a página da versão já existe, **atualizar** (usamos `replace_content`).
- **Verificação:** reler a página após escrever (já praticado).

### 5.4 Notificador
Comunica pendências dos reprovados. **Guardrail:** **sandbox** — só o Ronan por enquanto; **sem**
pingar Alexandre/Yuri sem ok explícito.
- **Canais possíveis:** Teams · e-mail · comentário no card · Notion. **Atenção:** o token do Jira
  hoje é **read-only** (`read:jira-work`) → comentar no card exigiria ampliar escopo.
- **Idempotente:** não renotificar o mesmo evento sem nova análise.
- **Registro:** card, responsável, pendências, canal, data/hora, status do envio.

## 6. Orquestração

```mermaid
sequenceDiagram
    actor R as Ronan (aprova)
    participant O as Orquestrador
    participant J as Atlassian MCP (read-only)
    participant V as Validador
    participant M as Montador
    participant N as Notion MCP
    participant T as Notificador (sandbox)

    R->>O: iniciar esteira (autonomo ate o Sync Passo 1)
    O->>O: versao-alvo automatica (Release X.(Y+1).0)
    O->>J: coletar (JQL: PB, Incidente, status alvo)
    J-->>O: cards + campos
    O->>V: validar por conteudo (regra v2)
    V-->>O: aprovados + reprovados (com pending_items)
    opt card genuinamente ambiguo (unica pausa antes do Notion)
        O->>R: pergunta (heuristica so-banco / repo!=PR)
        R-->>O: decisao
    end
    alt existem aprovados
        O->>M: montar release (sem pedir OK)
        M->>N: create/replace pagina da versao
        N-->>M: page_id + url
        M->>N: fetch (verificacao)
        N-->>M: conteudo renderizado
        M-->>O: release atualizada
    end
    alt existem reprovados
        O->>T: notificar pendencias (so Ronan)
        T-->>O: registro das notificacoes
    end
    O->>R: resumo consolidado (execucao)
    Note over R,N: Passo 1 do Sync roda no executar de board unico; master/triggers sob OK do Ronan
```

### 6.1 Optimus Prime (orquestrador) — modos, gates e o Sync

O orquestrador é a skill **"Optimus Prime"** (`.claude/skills/orquestrador/`). Ele **governa as
skills e o `sync-repos-from-master`**, com **um comando único** e dois modos:

- **`verificar`** — dry/seguro: roda a sequência sem tocar em nada (coletor → confere → montador
  **simula** o Notion → mostra o alvo do Sync + `make dry-run`). Só relatório.
- **`executar`** (board único) — roda a esteira **autônoma incluindo o Sync Passo 1** (versão-alvo
  automática → coletor → validador → montador cria a página **sem pedir OK** → edita o `repos.yaml` →
  `make dry-run` → se limpo, **`make run`** que abre os PRs pré-prod); **única pausa antes do Passo 1** é
  card genuinamente ambíguo. **Para depois do Passo 1**: merge, **master (Passo 2)** e **triggers (Passo
  3)** seguem sob comando explícito do Ronan (com gate de segurança por ação). No alvo `todos os boards`,
  a varredura **termina no Notion**. **Versão-alvo:** `Release` sequencial por board (`X.(Y+1).0`) —
  **incidente não é hotfix por padrão**; hotfix só quando o Ronan avisar.

**Alvo (independente do modo):** **`<board>`** (um board, padrão) ou **`todos os boards`** — varre os
três **em sequência, por prioridade (incidentes 1º)**, **isolados** (cada board → sua própria página no
Notion; nunca misturar). No alvo `todos os boards` a varredura **termina no Notion**; o Sync fica
**por-board e explícito** (fora do loop). Board sem filtro definido → **pula e reporta** "a definir".
Gatilhos: `Optimus Prime verificar todos os boards` / `Optimus Prime iniciar todos os boards`.

**Gate de segurança por ação:** toda ação do `sync-repos-from-master` roda antes em **dry-run**, parseia
a saída (`chave=valor`) + **exit code** (0 ok / 1 erro); se erro → **documenta e para**. **Passo 1**
(board único): se limpo → **dispara o `make run` automaticamente** (sem OK humano). **Master (Passo 2) e
triggers (Passo 3):** se limpo → **mostra e espera comando explícito** do Ronan antes do real.

**Governança do `repos.yaml` (guiada pela documentação):** lê o **doc da versão no Notion** e ativa
**apenas os repositórios de "Repositórios para Deploy"**; **o que não corresponder → comenta de volta**
(não entra no `make run`); **repo faltando → para e reporta** (Ronan adiciona).

**Fluxo de promoção de branches (nunca direto pra master; `make run` sempre com `target` explícito):**
- **Passo 1** — `source: prerelease` → `target: teste_regressivo` (pré-prod): edita o YAML,
  `make dry-run` e, se limpo, **`make run` automático** (PRs). **Sem OK humano entre dry-run e run.** Merge é do Ronan.
- **Passo 2** — `source: teste_regressivo` → `target: master` (prod): **só sob comando/override do Ronan**;
  por padrão o Optimus Prime edita o YAML + `make dry-run`, e roda o `make run` de master só sob override.
- **Passo 3** — `make run-triggers` (ambientes dos clientes; **não recebe `PR_TITLE`**): **100% do Ronan**,
  após OK do QA (aprovação do build no GCP é dele).
- Troca de `source`/`target` por passo é via **edição do YAML** (comentar/descomentar). Branches:
  `prerelease` → `teste_regressivo` → `master` (confirmar grafia exata antes do run real).

**Diretrizes inquebráveis:** **merge é só do Ronan** (manter `auto_merge=false`); **master (Passo 2),
deploy real (`make run-triggers`) e aprovação de build no GCP = do Ronan**; **hotfix** o Ronan conduz.
Erros viram **`erros/AAAA-MM-DD-*.md`** (base de refino, corrigido só com OK do Ronan).

## 7. Modelo de card normalizado

Contrato comum entre os agentes. **Nota:** a versão de destino **não** vem do card — é atribuída na
montagem do pacote; por isso fica no resumo de execução (§9), não no card.

```json
{
  "card_id": "PB-5415",
  "title": "Reaproveitamento automático reenvia documentos já aprovados",
  "issue_type": "Incidente",
  "status": "Teste regressivo",
  "owner": { "name": "Weverton Ferreira", "account_id": "..." },
  "product": "NewContract",
  "summary": "...",
  "category": "correcao",
  "links": {
    "jira": "https://bernhoeft.atlassian.net/browse/PB-5415",
    "repository": "https://bitbucket.org/bernhoeft/contractweb-v3",
    "pull_requests": ["https://bitbucket.org/bernhoeft/contractweb-v3/pull-requests/5164"]
  },
  "deploy_fields": {
    "acao_dados": "Nao",
    "acao_infra": null,
    "merge_realizado": null,
    "apenas_proc": false,
    "proc_name": null
  },
  "validation": {
    "result": "approved",
    "reason": "tem PR + repositorio",
    "checked_at": "2026-07-13T11:00:00-03:00",
    "pending_items": []
  }
}
```

## 8. Mapeamento de dados

### 8.1 Jira (leitura — escopo `read:jira-work`)
- **Site / cloudId:** `bernhoeft.atlassian.net` / `f36e5519-1f88-4f71-a406-75326e86deda`.
- **Projeto:** `PB` · **Issue type:** `Incidente` · **Status alvo:** `Teste regressivo`, `Pronto para deploy`.

| Info | Campo | ID |
|------|-------|-----|
| Link da PR | Links das PR's | `customfield_12400` |
| Link do repositório | Links do repositório | `customfield_12399` |
| Ação de dados | Ação de dados para deploy (Sim/Não) | `customfield_12297` |
| Merge realizado | Merge realizado? | `customfield_12401` |
| Produto | Produto | `customfield_11993` |
| Ação de infra | **não existe ainda** (a criar) | — |

### 8.2 Notion (leitura + escrita)
- **Database "Versões - NewContract":** data_source `23e19d89-2318-81ff-812d-000b6afb6b5a`;
  props: **Versão** (title), **Tipo** (select: Release / Hotfix).
- **Molde de conteúdo:** página `1.110.0`. **Base "notes" de teste:** `1.111.0 (teste)`.

## 9. Resumo consolidado da execução

```json
{
  "execution_id": "release-2026-07-13-001",
  "release_version": "1.111.0",
  "started_at": "2026-07-13T11:00:00-03:00",
  "finished_at": "2026-07-13T11:07:00-03:00",
  "cards_collected": 11,
  "cards_approved": 8,
  "cards_rejected": 3,
  "release_notes_updated": true,
  "notifications_sent": 0,
  "errors": []
}
```

## 10. Regra de validação como config (`deploy_requirements.yaml`)

Exemplo de externalização da regra v2 (evita hardcode; mudar regra = editar YAML):

```yaml
tipo_ciclo: incidente
projeto: PB
status_alvo: ["Teste regressivo", "Pronto para deploy"]
elegibilidade:
  aprovar_se_qualquer:
    - nome: "mudanca de codigo"
      exige: [pull_request, repositorio]
    - nome: "apenas banco/proc"
      exige: [acao_dados_sim]
      permite_sem: [pull_request, repositorio]
  reprovar_se:
    - "sem pull_request e sem repositorio e sem acao_dados"
  valores_invalidos_como_vazio: ["N/A", "Apenas PROC"]
```

## 11. Regras gerais

- **Rastreabilidade:** cada decisão registra agente, data/hora, card, critérios, resultado, justificativa, evidências.
- **Idempotência:** não duplicar cards na release, não renotificar sem nova análise, não gerar duas versões do mesmo pacote.
- **Intervenção humana:** revisão manual em critérios inconclusivos, dados contraditórios, exceção autorizada, evidências insuficientes. **O agente não inventa dados para preencher campo ausente.**
- **Segurança (privilégio mínimo):** Jira leitura (`read:jira-work`); Notion só a base de Release Notes; notificação com permissão restrita; repositório leitura.
- **Regra do projeto:** o assistente **não executa nada sem OK explícito do Ronan**; ele aprova cada passo.
- **Desempenho & custo:** **coleta enxuta** (só os campos necessários, sem `description` em lote — puxar
  sob demanda); no Notion, localizar via `query_data_sources` (SQL) e **verificar uma vez ao final**;
  **rodar no modelo mais barato por padrão**, escalando só em card ambíguo (ver as skills, "Modelo
  sugerido"). **Nunca** sacrificar o funcionamento por economia — na dúvida, mantém como está.

## 12. Escopo da 1ª versão × evoluções

**1ª versão (foco):** execução manual · coleta em um projeto · checklist fixo (v2) · listas aprovados/reprovados · atualização de uma página no Notion · geração das mensagens de pendência · registro da execução. Notificação automática **só** depois de definir o canal oficial.

**Evoluções:** execução agendada / disparada por mudança de status · integração Bitbucket/GitHub (validar PR, checar merge, painel Development) · categorias na release · revalidação de cards corrigidos · painel de acompanhamento · agentes independentes.

## 13. Backlog de refino (imediato)

- [ ] **Nome do proc** dos cards só-banco (ler descrição).
- [ ] **Ação de Infra** — criar campo no Jira e mapear.
- [ ] **Merge realizado** — vazio nos cards; definir origem (talvez painel Development).
- [ ] **PR no painel Development** quando o campo estiver vazio (pode destravar "Pronto para deploy").
- [ ] Checkboxes de **Testes regressivos** / **Ambientes** — definir origem.
- [ ] Decidir: release mistura "em teste" e "pronto p/ deploy" ou separa?
- [ ] Definir **canal** do Notificador e ampliar escopo do Jira **se** for comentar no card.
- [ ] Cravar o **template do Montador** (o que preencher / deixar em branco) pra não iterar layout.
