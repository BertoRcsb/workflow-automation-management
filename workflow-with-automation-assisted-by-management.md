# Workflow with Automation Assisted by Management — Plano de Execução

> Orquestração Jira → Notion → Deploy (GCP). Governança simplificada e rastreável.
> Documento operacional (checklist). Visão de apresentação: ver `PROPOSTA.md`.

## Contexto

Hoje o deploy é parcialmente automatizado pelo `sync-repos-from-master` (Python/Poetry),
que cria PRs no **Bitbucket** e dispara **triggers do Cloud Build (GCP)** — mas o passo
humano/organizacional antes do deploy é frágil:

- No **Jira**, cada card tem 5 campos importantes para o deploy, mas eles **não são
  obrigatórios**. Muitos devs esquecem de preencher, e o card avança para
  **"Teste Regressivo"** / **"Pronto para Deploy"** sem as informações necessárias.
- Sem esses dados estruturados, não dá para um agente **ler os cards prontos** de forma
  confiável nem **popular o Notion** (organização das releases do *New Contract*).

**Objetivo:** automação **leve** que conecte as áreas — Jira → Notion →
`sync-repos-from-master` (deploy manual) — priorizando **MCPs oficiais**.

Os 5 campos obrigatórios do card:

| # | Campo | Significado | Estado |
|---|-------|-------------|--------|
| 1 | **Ação de dados** | Precisa de alteração/script de banco de dados? (sim/não) | já existe |
| 2 | **Link do repositório** | URL do repo | já existe |
| 3 | **Link da PR** | URL da Pull Request | já existe |
| 4 | **Ação de infra** | Precisa de mudança de infraestrutura? (sim/não) | **a criar** |
| 5 | **Flags** | Flags associadas ao card | já existe |

### Princípios de design
- **Arquitetura limpa + código limpo** (padrão do `sync-repos-from-master`), responsabilidade única.
- **MCP-first / mínimo código**: só escrever código quando o MCP não cobrir.
- **Segurança e governança simplificada e rastreável**.

## Como vamos trabalhar (regra do projeto)
- **O assistente não executa nada.** Papel: planejar, definir passos, revisar.
- **Quem executa é o Ronan.** Cada passo é feito por ele; o assistente entrega a instrução.
- **Ordem:** (1) planejar → (2) revisar → (3) implementar **segurança** → (4) refinar execuções.

## Visão geral da arquitetura (leve, MCP-first)

```
[Jira] --(gate nativo: exige os 5 campos na transição)--> card "Pronto p/ Deploy"
   |  (agente lê via Atlassian Rovo MCP — busca JQL por status)
   v
[Orquestração leve] --(Notion MCP)--> [Notion: release do New Contract]
   |  (handoff: lista de repos/PRs prontos)
   v
[sync-repos-from-master] --(você roda manualmente)--> PRs Bitbucket + triggers GCP
```

---

## Status atual / Pivot (2026-07-11)

- **Fase 1 (gate no Jira) BLOQUEADA** — aguardando autorização de admin para criar/alterar
  campos (já solicitada pelo Ronan).
- **POC em andamento enquanto isso:** adiantar Fase 2 (ler cards) → Fase 3 (documentar no
  Notion) → **Fase 5 (notificações)**, em **modo sandbox** (página de teste no Notion,
  notificações só para o próprio Ronan — **sem** pingar terceiros reais até validar).
- Observação: sem o gate, cards podem estar **sem** "Ação de dados"/"Ação de infra"
  preenchidos; as regras de notificação de BD/infra só disparam para cards que já os tenham.

---

## Fase 1 — Gate no Jira (PRIORIDADE)

Forçar o preenchimento dos 5 campos como **condição para transicionar** o card para
"Teste Regressivo" / "Pronto para Deploy".

### 1.1 — Criar o campo "Ação de infra" (pré-requisito)
- Criar o **custom field** "Ação de infra" (seleção sim/não), adicionar à **tela** do tipo de
  issue e anotar o `customfield_id`. Requer admin (verificar acesso).

### 1.2 — Verificar o tipo do projeto Jira (bloqueante)
- **Company-managed** → tem **Field Required Validator** nativo (ideal; requer admin).
- **Team-managed** → **não** tem; usar "Restrict Transition", app do Marketplace, ou plano B.
- Checar no rodapé do board / *Project settings*.

### 1.3 — Caminho A (recomendado, se company-managed + admin)
- Adicionar **Validators** *Field Required* nas transições para "Teste Regressivo" e
  "Pronto para Deploy", exigindo os 5 campos. Campos sim/não como seleção obrigatória.
- Mensagem de erro clara. Regra auditável no histórico do workflow.

### 1.4 — Plano B (externo, se team-managed OU sem admin)
- Escrever **módulo novo, enxuto, do zero**, seguindo a arquitetura limpa do
  `sync-repos-from-master` (`domain` com contrato, `infra/providers/jira_client.py` só de I/O
  REST v3 com `urllib` e token de escopo mínimo, caso de uso em `application`).
- Ler cards sem os campos → **reverter transição** + **comentar** o que falta (rastreável).

### 1.5 — Passos executáveis (checklist — executados por você)

> **Você executa cada passo**; o assistente só descreve. Anotar os itens 📝.

**Passo 0 — Levantar o cenário (anotar)**
- [ ] 📝 Nome e **chave** do projeto Jira (ex.: `NEWC-123` → chave `NEWC`).
- [ ] 📝 Projeto é **Team-managed** ou **Company-managed**? → decide Caminho A vs B.
- [ ] 📝 **Nível de acesso**: admin do site / admin do projeto / usuário comum?
- [ ] 📝 Nome **exato** dos status alvo ("Teste Regressivo" / "Pronto para Deploy").
- [ ] 📝 Nome **exato** da **transição** que leva a cada um.

**Passo 1 — Criar o campo "Ação de infra"**
- [ ] *Settings → Issues → Custom fields → Create field*.
- [ ] Tipo: **seleção Sim/Não** (não texto livre).
- [ ] Nome: **"Ação de infra"**.
- [ ] Associar à **tela (screen)** do tipo de issue do fluxo.
- [ ] 📝 Anotar o `customfield_id`.

**Passo 2 — Mapear os IDs dos 5 campos**
- [ ] Obter `customfield_id` de cada campo via `https://SEU-SITE.atlassian.net/rest/api/3/field`
      (logado) ou *Settings → Issues → Custom fields*.
- [ ] 📝 Anotar os 5 IDs.

**Passo 3 — Configurar o gate**
- *Caminho A:* editar workflow → adicionar Validator *Field Required* nas transições →
  mensagem clara → **publicar**. (Se o nativo não cobrir, app JSU/JMWE.)
- *Caminho B:* marcar inviabilidade nativa → planejar módulo externo (1.4).

**Passo 4 — Testar o gate**
- [ ] Card de teste sem campos → mover → deve **bloquear**.
- [ ] Preencher os 5 → mover → deve **permitir**.
- [ ] 📝 Registrar resultado.

---

## Fase 2 — Leitura dos cards prontos (Atlassian Rovo MCP)
- Ativar **Atlassian Rovo MCP** (`https://mcp.atlassian.com/v1/mcp`, OAuth 2.1). Adicionar
  manualmente à config de MCP (servidor remoto).
- Buscar via **JQL** por `status in ("Teste Regressivo","Pronto para Deploy")` e ler os 5 campos.
- Saída: lista `{ card, repo, pr, ação_dados, ação_infra, flags }`.

## Fase 3 — Popular o Notion (Notion MCP)
- Ativar **Notion MCP** (`mcp.notion.com/mcp`, OAuth).
- A partir das versões/releases do New Contract já no Notion, criar/atualizar as entradas de
  teste regressivo com os cards da Fase 2. Definir o mapeamento de database/página.

## Fase 4 — Handoff para o deploy (`sync-repos-from-master`)
- A lista de repos/PRs prontos alimenta o `repos.yaml` ou a API (`POST /sync`, `GET /projects`).
- Deploy segue **manual** (`make run` / triggers). Não mexer no motor.

## Fase 5 — Notificações dos responsáveis

Ao processar cada card pronto / em deploy, notificar automaticamente:

| Gatilho | Quem notificar | Papel |
|---------|----------------|-------|
| Sempre (por card) | **Dev(s) responsável(is)** pelo card (assignee) | dono da tarefa — avisar do deploy do card |
| **Ação de dados = Sim** | **Alexandre Rudoi Bolonhini** | responsável por banco de dados |
| **Ação de infra = Sim** | **Ronan Berto** e **Yuri Stolai** | DevOps / infraestrutura |

- **Canal:** a definir (Jira @mention no card / e-mail / Teams / Slack).
- **Rastreável:** registrar cada notificação (log + comentário no card). **Idempotente:** não
  notificar o mesmo evento duas vezes.
- **Sandbox no POC:** notificações só para o próprio Ronan até validar; nada de pingar
  terceiros reais sem ok explícito.
- **Conteúdo da doc no Notion:** re-ler as bases das **versões do New Contract** já armazenadas
  e **atualizá-las** conforme os cards sobem, até a finalização do deploy (estado vivo por
  versão). Melhorias podem ser mediadas por consulta durante a execução.

---

## Segurança e governança
- **Privilégio mínimo** (escopo por serviço; segredos fora do versionamento).
- **Rastreabilidade** (comentário no card / log; nada silencioso).
- **Dry-run primeiro**; **idempotência**; **separação read/write**.
- **Governança nativa** preferida (gate no Jira, auditável).

## Reuso
- `sync-repos-from-master` — motor de deploy e **referência de arquitetura limpa**. Não mexer no núcleo.
- Credenciais: `ATLASSIAN_EMAIL`/token (`sync-repos-from-master/.env`), `gcloud`, service account GCP.
- MCPs a ativar: **Atlassian Rovo** e **Notion**.

## Itens a estudar / decidir
1. Tipo do projeto Jira + acesso → define Fase 1.
2. IDs dos custom fields dos 5 campos.
3. "Flags": marcador nativo do Jira ou feature flags? Onde ficam no card?
4. Estrutura do Notion (qual database/página das releases).
5. Onde mora a orquestração (skill/prompt sobre MCPs — sugestão inicial — vs módulo/serviço).

## Verificação (por fase)
- **Fase 1:** card sem campos → bloqueia; com campos → permite. (Plano B: reverte + comenta.)
- **Fase 2:** busca JQL via Rovo MCP retorna os cards certos com os 5 campos.
- **Fase 3:** entrada criada/atualizada no Notion para um card pronto.
- **Fase 4:** lista gerada + `make dry-run` batem com os cards.

---

## Retomar aqui (POC — próximos passos)

**Contexto de retomada:** Fase 1 (gate no Jira) bloqueada aguardando autorização de admin.
POC em andamento: Fase 2 (ler cards) → Fase 3 (doc no Notion) → Fase 5 (notificações), em
sandbox. Docs deste projeto em `/home/ronan/workflow-automation-management/`.

**Passo A — Conectar os MCPs (executado pelo Ronan; OAuth é interativo):**
- Atlassian Rovo:
  `claude mcp add --transport http atlassian https://mcp.atlassian.com/v1/mcp`
- Notion:
  `claude mcp add --transport http notion https://mcp.notion.com/mcp`
- Depois, autenticar cada um via `/mcp` (login OAuth no navegador).

**Passo B — Teste de leitura (seguro, read-only):** buscar via JQL os cards em
"Teste Regressivo"/"Pronto para Deploy" e listar os 5 campos de cada.

**Passo C — Doc no Notion (sandbox):** criar/atualizar em uma **página de teste** a partir das
versões do New Contract; nada em páginas reais até validar.

**Passo D — Notificações (sandbox):** disparar só para o próprio Ronan; matriz de responsáveis
na Fase 5. Sem pingar Alexandre/Yuri até ok explícito.

**Decisões abertas (definir na retomada):**
1. **Canal de notificação:** Jira @mention / e-mail / Microsoft Teams / Slack?
2. **Estrutura do Notion:** onde ficam as bases das versões do New Contract (qual database/página)?
3. **Identidade dos responsáveis:** handles/e-mails de Alexandre (BD) e Yuri (infra) — só usar após ok.
