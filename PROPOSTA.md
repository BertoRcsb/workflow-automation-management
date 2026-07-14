# Workflow with Automation Assisted by Management
### Proposta de solução — Governança de Deploy assistida por automação (Jira → Notion → GCP)

| | |
|---|---|
| **Autor** | Ronan Berto |
| **Status** | Preview / Proposta |
| **Data** | 2026-07-11 |
| **Escopo desta etapa** | Planejamento e prova de viabilidade — Fase 1 (gate no Jira) |
| **Stack de referência** | Python (arquitetura limpa), MCPs oficiais (Atlassian Rovo, Notion) |

---

## 1. Sumário executivo

O processo de deploy hoje já conta com automação parcial (`sync-repos-from-master`), mas o
**passo organizacional que antecede o deploy é frágil**: cards no Jira avançam para
"Teste Regressivo" e "Pronto para Deploy" **sem as informações mínimas necessárias**, porque os
campos correspondentes **não são obrigatórios**.

Esta proposta descreve uma automação **leve, segura e rastreável** que:

1. **Impõe um "portão" (gate) no Jira** — o card só avança se os dados de deploy estiverem
   preenchidos.
2. **Lê os cards prontos** de forma confiável (via MCP oficial da Atlassian).
3. **Organiza as releases no Notion** automaticamente, com base nas versões do *New Contract*.
4. **Entrega a lista pronta** ao motor de deploy existente, que continua sendo acionado
   manualmente.

O princípio norteador é **fazer o mínimo necessário com o máximo de governança**: priorizar
recursos nativos e MCPs prontos, evitando reescrever integrações ou construir plataformas
grandes para um problema pontual.

---

## 2. O problema

```
Situação atual:

  Dev conclui a tarefa
        │
        ▼
  Move o card no Jira  ──►  "Teste Regressivo" / "Pronto para Deploy"
        │                         │
        │                         └── campos de deploy VAZIOS (não obrigatórios)
        ▼
  Time de deploy / automação NÃO sabe, com confiança:
     • qual repositório                • se precisa de ação de dados (BD)
     • qual PR                         • se precisa de ação de infra
     • quais flags
```

**Consequências:**
- Retrabalho e idas e vindas para descobrir informações que deveriam estar no card.
- Risco de deploy incompleto (esquecer um script de banco, uma mudança de infra ou uma flag).
- Impossível automatizar o passo seguinte (Notion, deploy) sem dados estruturados e confiáveis.

**Causa-raiz:** os campos existem, mas **não são obrigatórios** — e um deles
(**"Ação de infra"**) **ainda nem foi criado**.

---

## 3. As informações que todo card precisa ter

| # | Campo | O que responde | Estado atual |
|---|-------|----------------|--------------|
| 1 | **Ação de dados** | Precisa de alteração/script de banco de dados? | já existe |
| 2 | **Link do repositório** | Qual repositório | já existe |
| 3 | **Link da PR** | Qual Pull Request | já existe |
| 4 | **Ação de infra** | Precisa de mudança de infraestrutura? | **a criar** |
| 5 | **Flags** | Flags associadas ao card | já existe |

---

## 4. A solução proposta

Uma cadeia de automação **em quatro elos**, cada um com responsabilidade única:

```
┌──────────────┐   gate nativo:        ┌───────────────────────┐
│    JIRA      │──exige os 5 campos──► │ card "Pronto p/Deploy"│
└──────────────┘   na transição        └───────────┬───────────┘
                                                    │  leitura via
                                                    │  Atlassian Rovo MCP (JQL)
                                                    ▼
┌───────────────────────────┐   Notion MCP    ┌───────────────────────────┐
│ Orquestração leve          │───────────────►│ NOTION: release New Contract│
│ (skill/prompt ou módulo)   │                │ (teste regressivo por versão)│
└───────────┬───────────────┘                 └───────────────────────────┘
            │ handoff: lista de repos/PRs prontos
            ▼
┌───────────────────────────┐
│ sync-repos-from-master     │  ── você aciona ──►  PRs Bitbucket + triggers Cloud Build (GCP)
│ (motor de deploy já pronto)│
└───────────────────────────┘
```

**Decisões de arquitetura:**
- **MCP-first / código mínimo:** usar os MCPs oficiais da Atlassian e do Notion em vez de
  reescrever clientes de API.
- **Arquitetura limpa:** se algum código for necessário, segue o padrão em camadas já usado no
  `sync-repos-from-master` (`interfaces → application → domain → infra → shared`).
- **Não reinventar o deploy:** o `sync-repos-from-master` permanece intacto como motor final.

---

## 5. Roadmap por fases

| Fase | Objetivo | Como | Depende de |
|------|----------|------|-----------|
| **1. Gate no Jira** *(prioridade)* | Impedir que o card avance sem os 5 campos | Validators nativos do workflow (ou fallback externo) | Tipo do projeto Jira + acesso admin |
| **2. Leitura dos cards** | Identificar, com confiança, o que está pronto | Busca JQL via Atlassian Rovo MCP | Fase 1 concluída + IDs dos campos |
| **3. Notion** | Registrar teste regressivo por versão do New Contract | Notion MCP (create/update) | Estrutura do Notion definida |
| **4. Handoff p/ deploy** | Entregar a lista pronta ao motor de deploy | Alimenta `repos.yaml` / API do sync | Fases anteriores |

> A execução é **incremental e verificável**: cada fase é validada antes da próxima.

---

## 6. Segurança e governança

Pilares que atravessam todas as fases:

- **Privilégio mínimo** — tokens/OAuth com o menor escopo necessário por serviço; segredos
  nunca versionados.
- **Rastreabilidade** — toda ação automatizada deixa registro (comentário no card e/ou log
  estruturado). Nada de mudança silenciosa.
- **Dry-run primeiro** — validar sem efeitos colaterais antes de agir de fato.
- **Idempotência** — reexecutar não duplica dados.
- **Separação leitura/escrita** — reduz o raio de impacto de qualquer falha.
- **Governança nativa quando possível** — preferir a regra dentro do próprio Jira, auditável
  pelo histórico do workflow, sem serviço externo com credenciais de escrita.

---

## 7. Escopo desta etapa e forma de trabalho

- **Foco imediato:** Fase 1 — o gate no Jira (incluindo criar o campo "Ação de infra").
- **Modelo de trabalho:** o planejamento define os passos; **a execução é feita pelo Ronan**,
  passo a passo. A automação assiste; a gestão (pessoas + processo) permanece no controle —
  daí o nome *Workflow with Automation Assisted by Management*.

---

## 8. Próximos passos imediatos (Fase 1)

1. **Levantar o cenário** — tipo do projeto Jira (team vs company-managed), nível de acesso,
   nomes exatos dos status e transições.
2. **Criar o campo "Ação de infra"** (seleção Sim/Não) e anotar seu `customfield_id`.
3. **Mapear os IDs** dos 5 campos.
4. **Configurar o gate** (validators na transição) e **testar** com um card de exemplo.

> O detalhamento operacional de cada passo está no plano de execução
> (`workflow-with-automation-assisted-by-management`, Fase 1.5 — checklist).
