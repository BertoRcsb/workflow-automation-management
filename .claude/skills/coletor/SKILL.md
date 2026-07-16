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
- **Não** valida nem escreve em destino — isso é do `validador` / `montador`.

## Configuração atual — Jira via MCP Atlassian (read-only, escopo `read:jira-work`)
- **cloudId:** `f36e5519-1f88-4f71-a406-75326e86deda` (bernhoeft.atlassian.net)
- **Projeto:** `PB` · **Issue type:** `Incidente` (um tipo por ciclo)
- **Status alvo:** `Teste regressivo`, `Pronto para deploy`
- **JQL:** `project = PB AND issuetype = Incidente AND status in ("Teste regressivo","Pronto para deploy")`
- **Campos a ler:**

  | Info | Campo |
  |------|-------|
  | Link da PR | `customfield_12400` |
  | Link do repositório | `customfield_12399` |
  | Ação de dados (Sim/Não) | `customfield_12297` |
  | Merge realizado | `customfield_12401` |
  | Produto | `customfield_11993` |
  | Ação de infra | **não existe ainda** (campo a criar) |

- **Ferramentas:** `mcp__atlassian__searchJiraIssuesUsingJql`, `mcp__atlassian__getJiraIssue`
  (usar `fields` explícito + `responseContentFormat: "markdown"`).

## Modelo normalizado (contrato de saída)
```json
{
  "card_id": "PB-5778",
  "title": "...",
  "issue_type": "Incidente",
  "status": "Teste regressivo",
  "owner": { "name": "...", "account_id": "..." },
  "product": "NewContract",
  "summary": "...",
  "links": { "jira": "...", "repository": null, "pull_requests": [] },
  "deploy_fields": {
    "acao_dados": "Sim", "acao_infra": null, "merge_realizado": null,
    "apenas_proc": false, "proc_name": null
  }
}
```
A **versão de destino não vem do card** — é atribuída na montagem do pacote.

## Evolução / próximos papéis (este escopo vai crescer)
- Ler PR do **painel Development** quando o campo estiver vazio.
- Extrair o **nome do proc** da descrição (cards só-banco).
- Outras fontes/ciclos: outros projetos, issue types (refatoração etc.), Bitbucket/GitHub direto.
- Trocar a ferramenta sem mudar o papel: reescrever apenas "Configuração atual".
