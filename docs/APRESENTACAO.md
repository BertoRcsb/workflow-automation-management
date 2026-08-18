# Esteira Inteligente de Release Notes — Apresentação

> **Workflow with Automation Assisted by Management** · Governança de deploy assistida por automação
> **Jira → Notion → Deploy (GCP)**, conduzida pelo orquestrador **"Optimus Prime"**.
>
> Documento visual de apresentação. **Comportamento canônico (fonte da verdade):** [`../spec/spec.md`](../spec/spec.md).
> Os diagramas abaixo são **imagens** (`docs/diagramas/*.png`) — renderizam em qualquer preview
> (PyCharm, VS Code, GitHub, Notion) sem extensão. Fontes Mermaid e versões `.svg` em [`diagramas/`](diagramas/).

---

## 1. Sumário executivo

O deploy do *New Contract* já tinha automação parcial (`sync-repos-from-master`), mas o **passo
organizacional antes do deploy era frágil**: cards no Jira avançavam para deploy **sem as informações
mínimas**. A esteira fecha essa lacuna — **lê os cards prontos, valida por conteúdo, documenta a release
no Notion e prepara o deploy** — com **governança rastreável** e o **controle sempre com o time**
(*"a automação assiste, a gestão controla"*).

<img src="diagramas/01-sumario-executivo.png" alt="Diagrama 1" width="820">

**Destaques**
- **MCP-first, código mínimo** — orquestra ferramentas oficiais (Atlassian, Notion) e o `make` do deploy.
- **Autônoma até o `make dry-run` do Sync Passo 1** (board único); todo `make run`, Merge, Master e Triggers **sempre sob aprovação do usuário**.
- **Rastreável e idempotente** — cada execução registrada; nada silencioso.

---

## 2. O problema

Os 5 campos de deploy do card **não eram obrigatórios** — e um deles ("Ação de infra") nem existia. Sem
dados estruturados, o time de deploy trabalhava no escuro e a automação do passo seguinte era inviável.

<img src="diagramas/02-problema.png" alt="Diagrama 2" width="540">

**Os 5 campos que todo card precisa:** Ação de dados · Link do repositório · Link da PR · Ação de infra
*(a criar)* · Flags.

---

## 3. Arquitetura em camadas

A esteira **não é um script que roda sozinho**: ela é um conjunto de instruções que ganham vida quando o
**Claude (o "cérebro")** está conectado e opera os **"braços"** (MCPs + `make`). Cada papel roda como
**subagente isolado** (contexto novo, ferramentas mínimas), e todo cálculo crítico fica na **camada
determinística `tools/`**.

<img src="diagramas/03-arquitetura-camadas.png" alt="Diagrama 3" width="660">

**Destaques**
- **Sem clients Python bespoke** — a orquestração é a skill sobre os MCPs (evita overengineering).
- **Cálculo crítico é código, não LLM** — extração de ADF, regra v2 + D1/D2, versão-alvo e os gates do
  Sync vivem em `tools/`; o LLM chama o script e lê a saída, nunca decide de cabeça.
- **Privilégio mínimo**: Jira só leitura; Notion só a base de releases.
- Trocar de ferramenta **não muda o papel** — só a seção "Configuração atual" de cada skill.

---

## 4. Papéis da esteira

<img src="diagramas/04-papeis.png" alt="Diagrama 4" width="880">

| Papel | Função | Estado |
|---|---|---|
| **coletor** | Busca cards no Jira (Atlassian MCP) e normaliza | Concluído |
| **validador** | Gate de elegibilidade por conteúdo (regra v2 + heurística) | Concluído |
| **montador** | Cria/atualiza a release/hotfix no Notion (molde padrão) | Concluído |
| **notificador** | Comunica pendências a dev/PO/QA | Em sandbox |
| **orquestrador** | Coordena tudo + governa o Sync; segurança por ação | Concluído · "Optimus Prime" |

---

## 5. Fluxo de execução (modelo atual)

No `iniciar`/`executar` de **board único**, a esteira roda **autônoma até o `make dry-run` do Sync Passo
1** (documenta a release no Notion → edita o `repos.yaml` → `make dry-run`). A **única pausa** é um
**card genuinamente ambíguo**. No alvo `todos os boards`, a varredura **termina no Notion** (Sync
por-board, depois). Ao fim do escopo autônomo, o Optimus emite **uma única** mensagem:
`Optimus Prime retornando com o resultado = Confira`. O **`make run` do Passo 1** (abre os PRs pré-prod)
só roda **depois**, sob OK do usuário.

<img src="diagramas/05-fluxo-execucao.png" alt="Diagrama 5" width="800">

**Destaques**
- **Autonomia até o `make dry-run` do Sync Passo 1** (board único) = velocidade sem perder rastreabilidade.
- **Incidente não é hotfix por padrão** — é Release comum; hotfix só quando o usuário avisar.
- Todo `make run` (Passo 1, Master, Triggers) e o Merge, **tudo é sob aprovação** do usuário (ver §8 e §9).

---

## 6. Varredura "todos os boards"

Um comando varre os três boards **em sequência, por prioridade**, **totalmente isolados** — cada board
gera **sua própria release e sua própria página no Notion**. **Nunca** se misturam cards de boards
diferentes.

<img src="diagramas/06-varredura-boards.png" alt="Diagrama 6" width="520">

**Mapeamento dos boards** (visões dentro do projeto Jira `PB`; status alvo: `Teste regressivo` / `Pronto para deploy`):

| Prioridade | Board | Filtro (JQL) |
|---|---|---|
| 1º | **Linha de frente / incidentes** | `issuetype = Incidente` |
| 2º | **Features** | `issuetype = Story AND summary !~ "Refatoração"` |
| 3º | **Refatoração** | `issuetype = Story AND summary ~ "Refatoração"` |

---

## 7. Regra de elegibilidade v2

O **status não garante prontidão** — a validação é **por conteúdo**. Um card passa se tem **PR +
repositório** *ou* é **legitimamente só-banco**.

<img src="diagramas/07-regra-elegibilidade.png" alt="Diagrama 7" width="580">

> `"N/A"` **não** conta como link. A heurística "só-banco legítimo" foi validada em produção (caso PB-5778).

---

## 8. Promoção de branches & deploy

`make run` **sempre com `target` explícito**, **nunca direto pra master**. Cada seta indica **quem faz**.

<img src="diagramas/08-promocao-branches.png" alt="Diagrama 8" width="880">

**Destaques**
- **Passo 1** o Optimus edita o YAML e roda o `make dry-run`; o **`make run` (abre os PRs) e o merge são
  do usuário** (`auto_merge=false`).
- **Passo 2 (master)** e **Passo 3 (triggers)** = **comando explícito do usuário**; ele aprova os builds no GCP.
- Após o deploy, a master é sincronizada de volta para as branches de trabalho.

---

## 9. Governança & segurança

Da fase de Sync em diante, **toda ação que muda algo** passa por um **gate por ação**: simula primeiro,
verifica, e só executa o real com **OK explícito**. Nada toca o sync sem passar pelo **driver
`tools/optimus_sync.py`** — backup do `repos.yaml` e 3 gates determinísticos antes de todo `make`.

<img src="diagramas/09-governanca-seguranca.png" alt="Diagrama 9" width="580">

**Guardrails inquebráveis**
- **Merge, master/prod e `run-triggers` = só o usuário.**
- **`verificar` nunca executa** — só relatório.
- **Um board por release** — nunca misturar.
- **Privilégio mínimo** · **sem segredos no repositório** · **não inventar dados ausentes**.

---

## 10. Exemplos reais

### 10.1 Ciclo E2E completo — Hotfix 1.111.2 (em produção)

<img src="diagramas/10-ciclo-e2e-hotfix.png" alt="Diagrama 10" width="880">

Ciclo fechado **sem erros**: coleta → validação → Notion → PR → deploy aprovado pelo usuário. Registrado
em `execucoes/release-2026-07-16-001.json`.

### 10.2 Varredura "todos os boards" (dry-run — 2026-07-20)

Ensaio seguro (não tocou em nada), 3 blocos isolados:

| Board | Filtro | Cards | Aprovados × Reprovados |
|---|---|---|---|
| Linha de frente / incidentes | `Incidente` | 6 | 3 × 3 |
| Features | `Story` sem "Refatoração" | 7 | 5 × 2 |
| Refatoração | `Story` com "Refatoração" | 10 | 3 × 7 |

O gate por conteúdo funcionou: muitos cards de refatoração ainda sem PR/repo caíram (corretamente) em
"reprovado", virando pendência a comunicar.

---

## 11. Roadmap / evolução

<img src="diagramas/11-roadmap.png" alt="Diagrama 11" width="820">

---

> **Como apresentar:** os diagramas são imagens em [`diagramas/`](diagramas/) — o preview do PyCharm/VS Code
> mostra tudo sem extensão. Para slides, use os `.svg` (vetoriais) ou os `.png` da mesma pasta. Para editar
> um diagrama, altere o `.mmd` correspondente e regenere (ver [`diagramas/README.md`](diagramas/README.md)).
