# SETUP — configurar e usar o Optimus Prime (após clonar)

Este projeto é **MCP-first**: a esteira roda **dentro do Claude Code** (o Claude opera os MCPs e segue
as skills). **Não é um script standalone** — precisa do Claude conectado. Siga os passos abaixo.

## Pré-requisitos
1. **Claude Code** instalado e autenticado (conta Anthropic com créditos). Pode ser no terminal, no
   VS Code ou no **PyCharm** (integração Claude Code).
2. **Acessos** (com a sua conta):
   - **Jira** da Bernhoeft (projeto **PB**) — leitura.
   - **Notion** — base **"Versões - NewContract"**.
   - **Bitbucket** e **GCP** (Cloud Build) — só se você for rodar os passos de Sync/deploy.
3. **`sync-repos-from-master`** clonado (repo **separado**) — necessário só pros passos de Sync/deploy.

## Passo a passo
### 1. Clonar e abrir
```bash
git clone <este-repo> workflow-automation-management
```
Abra a pasta no **Claude Code** (ou no PyCharm com o Claude Code). As **skills** (`.claude/skills/`) e o
comando **`/optimus-prime`** carregam automaticamente.

### 2. Conectar os MCPs (Atlassian + Notion)
O repo já traz **`.mcp.json`** declarando os servidores (sem segredos). Ao abrir, o Claude Code vai
**sugerir aprovar** os MCPs `atlassian` e `notion`. Depois:
```
/mcp        # aprove e faça o login (OAuth) em cada um
```
Confirme que aparecem **Connected**. (Cada pessoa faz o próprio OAuth — nada de token no repo.)

### 3. Configurar o deploy (sync-repos-from-master) — opcional (só p/ Sync/deploy)
Este repo **não** inclui o deploy tool. Clone-o **ao lado** (repo-irmão) ou aponte o caminho:
```bash
# recomendado: clonar como irmão
git clone <sync-repos-from-master> ../sync-repos-from-master
# ou definir o caminho:
export SYNC_REPO_PATH=/caminho/para/sync-repos-from-master
```
Configure o `.env` dele (tokens Bitbucket/GCP) e rode `make setup` — **ver o README do próprio
`sync-repos-from-master`**. Guardrail: manter **`auto_merge=false`**.

## Como usar
No Claude Code (com MCPs conectados), escreva:
```
optimus prime verificar <board>          # DRY: mostra o que faria, sem executar nada
optimus prime iniciar <board>            # board único: autônoma até o make dry-run do Passo 1 (make run sob OK do Ronan)
optimus prime verificar todos os boards  # DRY dos três (um bloco por board)
optimus prime iniciar todos os boards    # varre os três, incidentes 1º, 1 Notion por board (para no Notion)
```
- **`<board>`** = **incidentes** | **features** | **refatoração** (um por vez; **nunca misturar**).
- **`todos os boards`** = varredura **sequencial por prioridade** (incidentes 1º), **isolada** (cada board
  → sua própria release/hotfix no Notion). **Termina no Notion**; o Sync/deploy segue **por-board** depois.
  Mapeamento: **incidentes** = `Incidente` · **features** = `Story` **sem** "Refatoração" no título ·
  **refatoração** = `Story` **com** "Refatoração" no título (o 3º/menos importante). Board sem mapeamento → **pulado e reportado**.
- Se não informar o board, o Optimus **pergunta** qual é.
- Roteiro completo dos passos e comandos: [`COMANDOS.md`](COMANDOS.md).

## Regras que o Optimus sempre respeita (guardrails)
- **Merge, master/prod e `run-triggers` = só o Ronan** (`auto_merge=false`); nada sobe sem OK.
- **`verificar` nunca executa** — só apresenta o plano.
- **Um board por vez** — nunca misturar (misturar só com OK explícito).
- **Dry-run antes** de qualquer ação real; erros documentados em `erros/`; execuções em `execucoes/`.

## O que NÃO vai no repo (você provê)
Créditos do Claude · OAuth dos MCPs · acessos (Jira/Notion/Bitbucket/GCP) · `.env` do sync tool.
Sem isso, as skills carregam mas não têm o que operar.
