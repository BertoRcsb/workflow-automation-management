---
name: coletor
description: >-
  Use quando o usuário quer coletar/buscar itens de trabalho candidatos a um
  pacote de deploy/release e normalizá-los para as etapas seguintes (validador
  → montador). Gatilhos: "coletar cards", "buscar cards prontos pra deploy",
  "quais cards estão em teste regressivo / pronto para deploy", etapa de coleta
  ao montar release notes. Contexto atual: cards do Jira (projeto PB) via MCP
  Atlassian, mas o papel é agnóstico de ferramenta.
---

# Coletor

Papel da esteira de release notes que **busca os itens candidatos** a um pacote de
deploy e os **normaliza** num contrato comum para os papéis seguintes (`validador`
→ `montador`). É **agnóstico de ferramenta**: hoje lê do Jira, mas a lógica do papel
não muda se a fonte mudar — para trocar de fonte, reescreva só a seção
"Configuração atual".

> Fonte da verdade do projeto: `spec/spec.md`. Esta skill é a versão operacional/executável deste papel.

## Responsabilidade (única)
- Buscar os itens candidatos na fonte configurada.
- Pedir **só os campos necessários** — respostas grandes estouram o contexto; se
  precisar, salvar a resposta em arquivo e parsear.
- Entregar cada item no **modelo normalizado** (abaixo).
- **Capturar TODOS os links reais do card:** os campos de repositório e de PR/merge podem conter **mais
  de um** link — extrair **todos** para `repositories` / `pull_requests` (arrays), **nunca só o primeiro**.
  **Ordenar e deduplicar** (PR/repo compartilhada entre irmãos do mesmo épico conta uma vez). **Nunca
  inventar** e **nunca omitir** — o que não existir no card fica vazio.
- **PR por referência de card:** se o campo de PR **não** trouxer link do Bitbucket mas **referenciar
  outro card** (`PB-XXXX`, ex.: "Pr no card PB-5651"), **resolver e herdar a PR/repo desse card
  referenciado** como PR **compartilhada** (registrar que é a mesma PR do card X). Só herda o que
  **existe** no card referenciado — **nunca inventa**; se lá também não houver PR, deixa vazio.
- **Épico (parent):** ler o `parent` de cada card. Filhos do **mesmo épico** costumam compartilhar as
  **mesmas PRs/repos** (validado: épico **PB-5159 "Melhorias na Tela de Análise"** →
  PB-5157/5330/5331/5713 usam as mesmas 3 PRs: newcontract-front #1073, analysis-api #448, storage #609).
  Capturar o épico para (1) tratar PRs repetidas como **PR compartilhada** (contar/deployar uma vez) e
  (2) **sinalizar** quando irmãos do mesmo épico ficarem de fora do pacote (possível dependência — ver
  [[pb-5853-retido-com-pb-5157]]). O `coletor` **expõe** o épico (`epic`) e o **grupo de cards por PR
  compartilhada**; quem **decide excluir** é o `validador` (regras **D1 — épico incompleto** e **D2 — PR
  compartilhada parcial**): exclusão **automática**, **sem notificação**; liberar só por **ordem explícita
  do usuário / PO / gestor**. Ver [[regras-dependencia-deploy]].
- **Épicos all-or-nothing** (ex.: [[epico-pb-5768-all-or-nothing]] — "Refatoração Melhorias Onda 1") são
  o caso extremo da **D1**: não montar/deployar parcial mesmo que filhos estejam em `Teste
  regressivo`/`Pronto para deploy`. **Nunca incluir** irmão automaticamente — a automação só **exclui**.
- **Não** valida nem escreve em destino — isso é do `validador` / `montador`.
- **Um board por vez:** coletar de **UM** board por execução — **incidentes** *ou* **features** *ou*
  **refatoração** — **nunca misturar**. O board é **parâmetro** da coleta (não fixo). Misturar boards
  numa mesma coleta/release só com **OK explícito do usuário** ("avisaremos ao Optimus").
- **Varredura "todos os boards":** quando o orquestrador pede os três, coletar **um por vez, em
  sequência**, na **ordem de prioridade do registro** (incidentes 1º) — cada board vira **sua própria**
  coleta → validação → release/hotfix (nunca um pacote combinado). Ver [[orquestrador]].

## Configuração atual — Jira via MCP Atlassian (read-only, escopo `read:jira-work`)
- **cloudId:** `f36e5519-1f88-4f71-a406-75326e86deda` (bernhoeft.atlassian.net)

### Decisão de fan-out (determinística — antes de qualquer fetch de card)
1. Rodar a JQL do board (registro abaixo) pedindo SÓ as chaves (`fields: ["key"]`) e salvar o
   resultado em `execucoes/<data>-<board>-jql.json`.
2. Rodar `python3 tools/optimus_card_manifest.py execucoes/<data>-<board>-jql.json <board> <data> > execucoes/<data>-<board>-manifesto.json`.
   O script decide (config `tools/workers.json`): quantidade de cards, lotes, caminhos e concorrência.
   **O coletor não decide fan-out de cabeça.**
3. **`fanout: false`** → seguir o fluxo monolítico desta skill, inalterado (raw/remote/contrato do board).
4. **`fanout: true`** → NÃO coletar os cards: devolver handoff com `fanout: true` e
   `manifest_path`, e encerrar. O Optimus Prime despacha os workers `coletor-card` (um por lote,
   em ondas de `params.max_workers`) e agrega com
   `python3 tools/optimus_card_aggregate.py <manifesto> > execucoes/<data>-<board>-contrato.json`.

### Modo card (worker `coletor-card`)
Quando invocado como worker de um lote (agente `coletor-card`): coletar SOMENTE as `keys`
recebidas, na ordem, com o fluxo obrigatório de parse abaixo (ADF + `optimus_extract.py`),
gravando nos três caminhos exatos recebidos (`raw_path`, `remote_path`, `contrato_path`).
Sem JQL, sem escopo próprio, sem validação. Problema num card → registrar no contrato
(`parse_failed`/aviso) e reportar em `errors[]`; nunca inventar nem omitir.

### Parse de PR/repositório = tools/optimus_extract.py (determinístico, não fazer à mão)
Os campos `customfield_12400` (PR) e `customfield_12399` (repositório) chegam em ADF. **O coletor NÃO
interpreta ADF de cabeça.** Fluxo obrigatório:
1. Buscar cada card com `getJiraIssue` usando **`responseContentFormat: "adf"`** e `fields` explícito
   (os 6 campos da tabela + `parent` + `status` + `assignee` + `summary`). Nunca `markdown` para estes
   campos (em markdown o inlineCard perde `attrs.url` e a extração zera).
2. (Opcional, fecha "PR aberta pelo Dev") buscar `getJiraIssueRemoteIssueLinks` por card e salvar
   `execucoes/<data>-<board>-remote.json` no formato `{ "PB-XXXX": ["<url PR>", ...] }`.
3. Salvar o cru em `execucoes/<data>-<board>-raw.json` e rodar
   `python3 tools/optimus_extract.py execucoes/<data>-<board>-raw.json execucoes/<data>-<board>-remote.json > execucoes/<data>-<board>-contrato.json`.
4. Usar o contrato do script como saída do coletor. GATE-ADF e o falso-vazio já são enforçados no
   código: repo **derivado da URL da PR**; URL de PR no campo Repositório é interpretada (flag
   `repo_field_com_pr`, aviso não-bloqueante); `parse_failed=true` só quando o campo tinha
   link/resíduo **não interpretado** — nunca emitir `[]` silencioso.

### Refinamento automático de `parse_failed`

Quando o Optimus reenviar chaves específicas apó bloqueio do Validador, faça **uma única tentativa**:

1. Re-fetch de cada card com `responseContentFormat: "adf"`, incluindo os campos de PR/repositório.
2. Consultar `getJiraIssueRemoteIssueLinks` novamente.
3. Salvar cru e remote links como `execucoes/<data>-<board>-refino-1-{raw,remote}.json`.
4. Rodar novamente `optimus_extract.py` e salvar `*-refino-1-contrato.json`.
5. Devolver o novo caminho no handoff. Não investigar manualmente, não mudar parser e não perguntar
   ao usuário. Se continuar `parse_failed`, devolva a evidência para bloqueio fail-closed.
6. No fluxo com fan-out, o refino é executado pelo worker `coletor-card` (só as chaves afetadas)
   e o Optimus reagrega com `optimus_card_aggregate.py <manifesto> <refino-1-contrato.json>`
   (o override substitui os cards refinados por `card_id`).

### Registro de boards (fonte única — o board é config, não texto solto)
Cada board seleciona uma linha → monta o JQL → normaliza (modelo abaixo). **Ordem = prioridade**
(incidentes sempre 1º). **Board sem JQL → pula e reporta** "filtro a definir" (não coleta, **não inventa**).

| # (prioridade) | board (nome no Jira) | projeto | issuetype | status alvo | JQL | estado |
|---|-------|---------|-----------|-------------|-----|--------|
| 1 | **Linha de frente** (= incidentes) | `PB` | `Incidente` | `Teste regressivo`, `Pronto para deploy` | `project = PB AND issuetype = Incidente AND status in ("Teste regressivo","Pronto para deploy")` | definido |
| 2 | **Features** | `PB` | `Story` (sem "Refatoração" no título) | `Teste regressivo`, `Pronto para deploy` | `project = PB AND issuetype = Story AND summary !~ "Refatoração" AND status in ("Teste regressivo","Pronto para deploy")` | definido |
| 3 | **Refatoração** | `PB` | `Story` (com "Refatoração" no título) | `Teste regressivo`, `Pronto para deploy` | `project = PB AND issuetype = Story AND summary ~ "Refatoração" AND status in ("Teste regressivo","Pronto para deploy")` | definido |

> **Como o mapeamento foi cravado:** os três "boards" do Jira (*Projetos Bernhoeft › Linha de frente /
> Features / Refatoração*) são **visões dentro do projeto `PB`** — o MCP **não expõe a API de
> boards/filtros**, então o issuetype de cada um foi **inferido pela população em status de deploy** e
> **confirmado pelo usuário**. Board sem mapeamento → **pula e reporta** (não inventa).
>
> **Features × Refatoração (critério fino confirmado pelo usuário):** ambos são `Story`; a separação é
> **pelo título** — **Refatoração = título contém "Refatoração"** (heurística `summary ~ "Refatoração"`,
> observada nos cards: `FRONT -`/`BACK -`/`Triagem - Refatoração ...`); **Features = o complemento**
> (`summary !~ "Refatoração"`). **Refatoração é o board menos importante (3º).** Se um card ficar no
> board errado, é sinal de refino do critério (ajustar o filtro com OK do usuário) — **não inventar**
> outro critério por conta própria.
>
> **Prioridade (ordem da varredura "todos os boards"):** 1º **Linha de frente/incidentes** (principal) →
> 2º **Features** (principal) → 3º **Refatoração** (menos importante).

**Board 1 (Linha de frente / incidentes) — detalhe:**
- **Projeto:** `PB` · **Issue type:** `Incidente` (um tipo por ciclo)
- **Status alvo:** `Teste regressivo`, `Pronto para deploy`
- **JQL:** `project = PB AND issuetype = Incidente AND status in ("Teste regressivo","Pronto para deploy")`
- **Campos a ler:**

  | Info | Campo |
  |------|-------|
  | Link da PR | `customfield_12400` (pode conter **múltiplos** URLs → extrair todos) |
  | Link do repositório | `customfield_12399` (pode conter **múltiplos** URLs → extrair todos) |
  | Ação de dados (Sim/Não) | `customfield_12297` |
  | Merge realizado | `customfield_12401` |
  | Produto | `customfield_11993` |
  | Épico (parent) | `parent` (chave + summary do épico) |
  | Ação de infra | **não existe ainda** (campo a criar) |

- **Ferramentas:** `mcp__atlassian__searchJiraIssuesUsingJql`, `mcp__atlassian__getJiraIssue`
  (usar `fields` explícito + `responseContentFormat: "adf"` para campos de PR/repo; coleta enxuta em lote pode seguir markdown).
- **Coleta enxuta (rápida e barata):** peça **só os campos da tabela acima** (chave/summary/status/
  assignee + os customfields). **NÃO** traga `description` nem `*all` na busca em lote — é o que estoura
  o limite e força salvar-e-parsear. Precisa da descrição (heurística só-banco / card ambíguo)? Puxe
  **sob demanda, por card**, com `getJiraIssue` incluindo `description`. Menos payload = mais rápido e menos token.
- **Modelo:** agnóstico — sem pin; herda o da sessão. A coleta é mecânica e a corretude vem do
  `optimus_extract.py`, não do modelo.

## Modelo normalizado (contrato de saída)
```json
{
  "card_id": "PB-5778",
  "title": "...",
  "issue_type": "Incidente",
  "status": "Teste regressivo",
  "owner": { "name": "...", "account_id": "..." },
  "product": "NewContract",
  "epic": { "key": "PB-5159", "summary": "Melhorias na Tela de Análise" },
  "summary": "...",
  "links": { "jira": "...", "repositories": [], "pull_requests": [] },  // itens: { "label": "repo #num", "url": "https://.../pull-requests/N" }
  "parse_status": {
    "parse_failed": false,
    "pr_url_count": 2,
    "repo_url_count": 1
  },
  "deploy_fields": {
    "acao_dados": "Sim", "acao_infra": null, "merge_realizado": null,
    "apenas_proc": false, "proc_name": null
  }
}
```
- **versão de destino:** não vem do card — é atribuída na montagem do pacote.
- **parse_status.parse_failed:** `true` se o campo ADF tinha link/resíduo que a extração **não
  interpretou** (re-extraído e ainda perdido). `false` caso contrário — texto sem URL é `*_sem_link`,
  e URL de PR no campo Repositório é interpretada (vira PR + repo derivado), não falha.
- **parse_status.pr_url_count / repo_url_count:** contagem de URLs extraídas para debug/auditoria
  (`repositories` inclui os repos derivados das URLs de PR).
- **parse_status.repo_field_com_pr:** `true` quando o campo Repositório continha URL de PR —
  aviso não-bloqueante para corrigir o card no Jira.

> Evolução planejada deste papel: `docs/ROADMAP.md`.
