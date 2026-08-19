---
name: validador
description: >-
  Use quando o usuário quer decidir se itens coletados estão aptos a entrar num
  pacote de deploy/release — aplicar o gate de elegibilidade por conteúdo e
  separar aprovados × reprovados com as pendências. Gatilhos: "validar cards",
  "esse card entra?", "quais barrar", "checar elegibilidade", "separar aprovados
  e reprovados". Contexto atual: cards de deploy (regra v2); papel agnóstico.
---

# Validador

Aplica o **gate por conteúdo**: o **status não garante prontidão** (comprovado — cards
em "Pronto para deploy" estavam vazios). Recebe itens normalizados do `coletor` e
devolve **aprovados × reprovados** para o `montador` e o `notificador`.

> Fonte da verdade do projeto: `spec/spec.md`. Esta skill é a
> versão operacional deste papel.

## Regra de elegibilidade v2
Um item **passa** se:
1. tem **PR + repositório** (mudança de código), **OU**
2. é **só ação de banco/proc** — `Ação de dados = Sim`, sem PR/repo.

**Barra** quem não tem **nada** (sem PR, sem repo, sem ação de dados).
`"N/A"` e `"Apenas PROC"` **não** contam como link válido.

**GATE-FALSO-VAZIO:** **nunca reprovar por "sem PR/repo" um card com `parse_failed: true`** (do
`coletor` GATE-ADF) nem com ADF cru não-vazio. Se um card chegar com `parse_failed: true`:
- Reconhecer que o link **existe mas a extração falhou** — não é ausência real.
- **Devolver ao coletor** para re-extração / debug (ou escalar ao usuário se persistir).
- **Não** aplicar a regra v2 (não aprovar nem reprovar) até resolver.

**Execução determinística:** a regra v2, D1, D2 e o GATE-CROSSCHECK rodam em
`python3 tools/optimus_gates.py <contrato.json> tools/rules.json [epic_status.json]`. O validador
consome `gates.json`. `parse_failed` vira status "parse_failed" (nem aprova nem reprova).
Os **motivos saem do código com os contadores reais** (`pr=N, repo=N, acao_dados=...`) — nunca
parafrasear nem trocar por mensagem genérica (incidente 2026-08-19 PB-5728: "sem PR" relatado para
card com 6 PRs). `avisos` (ex.: `repo_field_com_pr`) são pendência informativa, nunca reprovação.

**Repositório derivado da PR:** o extractor deriva `repositories` das URLs de PR
(`bitbucket.org/<ws>/<repo>/pull-requests/<n>`) — campo Repositório vazio com PR válida **satisfaz
a regra 1** (mesma lógica do caso PB-5599 abaixo, agora em código; caso-modelo PB-5728).

**PR por referência de card (conta como PR válida):** quando o `coletor` herda a PR de **outro card
referenciado** (o campo apontava pra `PB-XXXX` em vez de link do Bitbucket — ver `coletor`), essa PR
**compartilhada vale como PR + repositório** para a regra 1. Caso-modelo **PB-5599** (herdou a PR do
PB-5651, `login-api #365`) → **APROVADO**.

## Heurística "só-banco legítimo" (validada em 2026-07-14 — caso-modelo PB-5778)
Para distinguir **banco legítimo** de **"código que esqueceu a PR"**:

> `Ação de dados = Sim` **e** (assignee é responsável de banco **ou** a descrição
> cita proc / procedure / carga / seleção / query) → **aprova sem exigir PR/repo**.

Caso-modelo **PB-5778**: `Ação de dados = Sim`, sem PR/repo, assignee **Alexandre
Bolonhini** (banco) e descrição sobre corrigir a *procedure/seleção* → **APROVADO**.

## Regras de dependência (aplicar DEPOIS da regra v2, antes de fechar o pacote)
Nasceram do deploy truncado de **2026-07-22** (ver `erros/2026-07-22-deploy-truncado-dependencias.md`).
São **duas informações diferentes** — um card pode cair numa, na outra, ou nas duas. Em ambas a ação é
**exclusão automática**, **sem notificação**. **"Excluir" significa apenas: NÃO entrar na doc do Notion /
no pacote de deploy** (deixar de fora) — **não** altera o card no Jira, **não** mexe em PR/branch, **não**
apaga nada. Cards excluídos **só voltam com ordem explícita do usuário, de um PO ou de um gestor**. Toda
exclusão é **registrada** em `execucoes/` (card + qual regra). **Nunca incluir** irmão automaticamente —
a automação só **deixa de fora** (direção segura).

### D1 — Épico incompleto → segura os cards do épico
- Todo card com `parent` (épico): checar se o **épico está completo**.
- **Épico completo (definição operacional):** todos os filhos **não cancelados** estão em status de
  deploy (`Teste regressivo` / `Pronto para deploy`) ou já deployados. Se **qualquer** filho não
  cancelado ainda estiver em desenvolvimento/teste/code-review, o épico está **incompleto**.
- Épico incompleto → **excluir do pacote todos os cards daquele épico** (não sobe parcial de épico).
  A exclusão usa o motivo **"D1: épico X incompleto"** (registrado em `gates.json.excluidos_d1`).
  Para D1 geral (fora de PB-5768) o orquestrador fornece `epic_status.json` = `{ "<epicKey>": {"completo": true|false} }`,
  montado com uma JQL `parent = <epicKey>` por épico presente (completo = todos os filhos não-cancelados em status de deploy ou já deployados).
  Épico all-or-nothing do `rules.json` é sempre incompleto até ordem explícita.
- Casos-modelo: [[epico-pb-5768-all-or-nothing]] (38 filhos, maioria em dev) e **PB-236** (irmão
  PB-4786 reprovado/sem PR deixa o épico incompleto).

### D2 — PR compartilhada → tudo ou nada no pacote
- Para cada **PR usada por mais de um card** (mesma `pull_request`), levantar **todos** os cards que a usam.
- **Todos no pacote** → ok. **Todos fora** → ok (nada a subir). **Parcial** (um ou mais dentro, um ou
  mais fora) → **não subir**: **excluir do pacote** os cards que estavam dentro (a PR não sobe truncada).
- Caso-modelo: PB-4726/4727 compartilham `#1048`/`#4910` com PB-5316 e `#195` com PB-5528 — se algum
  ficasse de fora, todos saíam.

> D1 é vínculo **estrutural** (épico); D2 é **mesmo código** (PR). Dados vêm do `coletor` (`epic` +
> `pull_requests`). Definição de "épico completo" acima **confirmada pelo usuário (2026-07-22)**: todos os filhos não-cancelados em status de deploy ou já deployados.

## Saída
- **Aprovados:** chave, título, responsável, resumo, categoria, evidências, `checked_at`.
- **Reprovados:** chave, título, responsável, `pending_items`, orientação, `checked_at`.

## Guardrails
- O agente **não inventa** dado para preencher campo ausente.
- Casos inconclusivos / contraditórios / exceções → `status: blocked`, documentação da evidência e
  retorno ao Optimus. Não pedir autorização ao usuário durante a esteira.
- **Modelo:** agnóstico — sem pin; herda o da sessão (a regra v2 roda em `optimus_gates.py`, não
  no modelo). Card ambíguo (heurística só-banco não fecha, ou dado divergente tipo repo ≠ PR) falha
  fechado; não escala nem inventa decisão.

## Regra como config (evita hardcode)
A regra vive em `tools/rules.json` (ver spec §10) — mudar a regra = editar o JSON, não a skill.

> Evolução planejada deste papel: `docs/ROADMAP.md`.
