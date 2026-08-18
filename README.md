# Workflow with Automation Assisted by Management

> # RODAR A ESTEIRA
> **Precisa de um "cérebro" (Claude) ligado** — isto **não roda sozinho**. As skills/comandos só
> executam com o **Claude Code conectado + MCPs ativos + projeto aberto**. O cérebro é o Claude; os
> braços são os MCPs + o `make` do sync.
> **Você fala/escreve:** `Optimus Prime, iniciar` → equivale a **`/optimus-prime executar`**
> (ou **`/optimus-prime verificar`** para ensaiar em *dry*, sem tocar em nada).
> **Guia operacional (comandos passo a passo + gates):** [`docs/COMANDOS.md`](docs/COMANDOS.md)
> **Primeira vez / configurar (clonou agora?):** [`docs/SETUP.md`](docs/SETUP.md)

Governança de deploy assistida por automação: **Jira → Notion → Sync/Deploy (GCP)**, com o
orquestrador **"Optimus Prime"** conduzindo a esteira e o usuário aprovando cada passo crítico.

> **Automação assiste, gestão controla.** Nada mergeia nem sobe pra prod sem o usuário.

## Pré-requisitos para executar o Optimus Prime

1. **Clonar os dois repositórios como diretórios irmãos** (lado a lado, na mesma pasta-mãe):
   ```bash
   git clone <este-repo> workflow-automation-management
   git clone <sync-repos-from-master> ../sync-repos-from-master
   ```
2. **Abrir o Claude Code dentro de `workflow-automation-management`** (terminal, VS Code ou PyCharm).
   As skills (`.claude/skills/`) e o comando `/optimus-prime` carregam automaticamente.
3. **Autenticar os MCPs Atlassian/Jira e Notion** com `/mcp`: aprove os servidores declarados em
   `.mcp.json` e faça o login (OAuth) em cada um até aparecerem como **Connected**.
4. **Jira é somente leitura e pesquisa** — a esteira nunca escreve no Jira.
5. **Notion permite somente leitura, criação e atualização da release** — **nunca exclusão**.
6. **As credenciais do Bitbucket ficam exclusivamente no ambiente já existente do
   `sync-repos-from-master`** (o `.env` dele) — este repositório não as recebe nem as replica.
7. **O Bitbucket precisa somente destes escopos:**
   - `read:repository:bitbucket`
   - `read:pullrequest:bitbucket`
   - `write:pullrequest:bitbucket`
8. **Nenhum token, senha ou credencial** pode ser escrito no README, no workflow, nos agentes,
   nas skills, em `execucoes/` ou em commits.
9. **O `sync-repos-from-master` é inviolável:**
   - não criar arquivos ou diretórios nele;
   - não alterar seus scripts;
   - não reformatar o `repos.yaml`;
   - permitir somente ativar ou desativar entradas já existentes por meio de `#`;
   - executar somente os comandos já definidos pelo próprio Sync;
   - nunca realizar merge automático.
10. **O usuário continua sendo a autoridade final** sobre merges, master/prod e triggers.

## Como usar (quick start)
```
/optimus-prime verificar incidentes    # dry/seguro: coleta, valida, simula Notion e Sync — NÃO toca em nada
/optimus-prime executar incidentes     # board único: autônomo até o dry-run do Sync Passo 1 → mensagem "Confira"
```
O `executar` **para obrigatoriamente depois de apresentar o `make dry-run` do Passo 1**. Daí em diante,
tudo exige **autorização explícita do usuário**: `make run`, criação definitiva de PRs, Passo 2, triggers,
sincronização e merge.

## Fluxo (quem faz o quê)
```
Usuário → /optimus-prime → Optimus Prime (orquestrador)
          ├→ Coletor      (subagente) — Jira → contrato via tools/optimus_extract.py
          ├→ Validador    (subagente) — regra v2 + D1/D2 via tools/optimus_gates.py
          ├→ Montador     (subagente) — página no Notion no molde templates/release-notion.md
          ├→ Notificador  (subagente) — rascunhos (sandbox)
          └→ Sync (o próprio Optimus) — repos.yaml + make via driver tools/optimus_sync.py
```
Cada papel roda como **subagente isolado** (contexto novo, ferramentas mínimas — ver
[`AGENTS.md`](AGENTS.md)). Todo cálculo crítico é **código determinístico em `tools/`** — o LLM chama
o script e lê a saída, nunca decide de cabeça (versão-alvo, extração de ADF, elegibilidade, gates do
Sync). Inventário completo: [`docs/GATES.md`](docs/GATES.md).

## Camada determinística (`tools/`)
| Script | Papel |
|---|---|
| `optimus_extract.py` | extrai PR/repo do ADF do Jira (contrato do coletor) |
| `optimus_gates.py` | regra v2 + D1/D2 + GATE-CROSSCHECK (veredito do validador) |
| `optimus_next_version.py` | versão-alvo pelo maior semver + anti-colisão |
| `optimus_sync.py` | **driver único do Sync**: backup → GATE-YAML → GATE-PROMO → GATE-TRIGGERS → `make` |
| `rules.json` · `promotion.json` | config das regras (fonte única — mudar regra = editar JSON) |

Testes: `make test` (cria o venv e roda a suíte).

## Documentação
- **Esquema visual da arquitetura (Mermaid, atualizado):** [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md)
- **Apresentação para stakeholders (imagens):** [`docs/APRESENTACAO.md`](docs/APRESENTACAO.md)
- **Receita de bolo (comandos):** [`docs/COMANDOS.md`](docs/COMANDOS.md)
- **Comportamento (fonte da verdade):** [`spec/spec.md`](spec/spec.md) · **Esteira (gates/guardrails):** [`.claude/skills/orquestrador/SKILL.md`](.claude/skills/orquestrador/SKILL.md)
- **Roadmap:** [`docs/ROADMAP.md`](docs/ROADMAP.md) · **Gates:** [`docs/GATES.md`](docs/GATES.md) · **Histórico (plano/tarefas de julho):** [`docs/archive/`](docs/archive/)
- **Guia técnico (índice):** [`CLAUDE.md`](CLAUDE.md) · **Índice de docs:** [`docs/README.md`](docs/README.md)
- **Subagentes:** [`AGENTS.md`](AGENTS.md) · **Apresentação:** [`docs/PROPOSTA.md`](docs/PROPOSTA.md)
- **Catálogo canônico do `repos.yaml` (restauração de backup do Sync):** [`reference/sync-repos-from-master/`](reference/sync-repos-from-master/README.md)
