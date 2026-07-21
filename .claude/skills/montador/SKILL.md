---
name: montador
description: >-
  Use quando o usuário quer criar/atualizar a documentação de uma release/hotfix
  a partir de itens aprovados — montar a página no molde padrão das versões
  anteriores. Gatilhos: "montar a release notes", "criar release/hotfix",
  "atualizar a página da versão", "documentar o pacote de deploy". Contexto
  atual: base "Versões - NewContract" no Notion via MCP; papel agnóstico.
---

# Montador

Cria/atualiza a página da versão (**release** ou **hotfix**) a partir dos aprovados
do `validador`, no **molde** das versões anteriores. **Agnóstico de ferramenta**:
hoje escreve no Notion — para trocar o destino, reescreva só "Configuração atual".

> Fonte da verdade do projeto: `spec/spec.md`. Esta skill é a
> versão operacional deste papel.

## Configuração atual — Notion via MCP
- **data_source "Versões - NewContract":** `23e19d89-2318-81ff-812d-000b6afb6b5a`
- **Propriedades:** `Versão` (title) · `Tipo` (select: `Release` / `Hotfix`)
- **Ferramentas:** `mcp__notion__notion-create-pages`, `notion-fetch`, `notion-query-data-sources`.
  - **Localizar versão/última página: use `notion-query-data-sources` (SQL) — rápido e estável.**
    **Evite `notion-search`** (semântico, lento/instável nesta base).
- **Modelo sugerido:** barato (ex.: Haiku) — montagem é escrita mecânica no molde.
- **Molde de referência:** reler a **última página do mesmo `Tipo`** antes de montar
  (query por `Tipo` ordenando por `Criado em` desc).

## Molde de conteúdo
- **Tabela:** `Item · Pull Requests · Tem Ação de Banco ? · Tem Ação de Infra ? · Merge Realizado ?`
  - **Item:** card linkado **com título** (e status) —
    `[PB-XXXX — <título do card>](https://bernhoeft.atlassian.net/browse/PB-XXXX) · <status>`.
    Enriquece a leitura. *(O "mention" nativo do Jira **não** é reproduzível via MCP — o link com título
    é o equivalente suportado e verificável no re-fetch.)*
  - **Pull Requests:** URL da PR (código) **ou** `• APENAS PROC` (item só-banco).
  - **Infra / Merge:** em branco até apurar (**não inventar**).
- **Blocos:** Testes regressivos · Ambientes · Repositórios para Deploy · Participantes
  do Deploy (Dados: Alexandre Rudoi B. · QA: Dorgival Silva Filho · DevOps/Resp.:
  Yuri Stolai / Ronan Berto · sobreaviso: assignees do(s) card(s)).

## Guardrails
- **Idempotência:** não duplicar card; se a página da versão já existe, **atualizar**
  (usar replace do conteúdo), não criar outra.
- **Não inventar** Infra / Merge / repositório — deixar em branco.
- **Verificação enxuta:** reler a página com `notion-fetch` **uma vez, ao final** (não a cada
  linha/card) e conferir tabela + propriedades. Menos ida-e-volta = mais rápido.

## Evolução / próximos papéis (este escopo vai crescer)
- **Categorias** na tabela/release.
- **Nome do proc** nas linhas só-banco.
- Preencher **Merge / Infra** quando a origem do dado estiver definida.
- Trocar o destino sem mudar o papel: reescrever apenas "Configuração atual".
