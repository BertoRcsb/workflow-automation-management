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
- **Ferramentas:** `mcp__notion__notion-create-pages`, `mcp__notion__notion-update-page`, `notion-fetch`, `notion-query-data-sources`.
  - **Localizar versão/última página: use `notion-query-data-sources` (SQL) — rápido e estável.**
    **Evite `notion-search`** (semântico, lento/instável nesta base).
- **Modelo sugerido:** barato (ex.: Haiku) — montagem é escrita mecânica no molde.

## Molde de conteúdo — fonte única: `templates/release-notion.md`
A página segue **exatamente** o template versionado em **`templates/release-notion.md`** (metadados,
colunas da tabela, blocos, checkboxes e participantes), sem improviso. Leia o template ANTES de montar.
A célula de PR vem pronta de `gates.json.rows[].pull_requests` — nunca reinterpretar o card.
Ação de Infra / Merge ficam `—` até apurar (**nunca inventar**). Mudar o molde = editar o template
(com OK do usuário).

## Gates (asserções duras — param e documentam, nunca "passam" dado errado)

### GATE-CONJUNTO (reconciliação)
**Antes de escrever qualquer coisa:** o montador recebe uma lista de **aprovados do validador**
(chaves + contagem) e o conjunto de cards a montar. **Asserção:** o conjunto **deve ser idêntico** aos
aprovados (mesmas chaves, mesma contagem, sem deletar nem adicionar).

Se detectar **card fora dos aprovados** ou **aprovado ausente** → **PARA e documenta em `erros/`**.
Nenhum card entra na doc sem ter saído do gate do validador. (Este gate teria evitado o bug B
da 1.117.0, onde entrou PB-4761 não-aprovado e faltaram 4 aprovados.)

### GATE-MOLDE (fidelidade ao padrão)
No re-fetch final, **conferir que a página bate com `templates/release-notion.md`**, campo a campo:
- Colunas da tabela exatas.
- Nomes dos blocos e ordem.
- Checkboxes presentes.
- Estrutura de "Participantes" (headings marrom, nomes em lista).

Se divergir → **PARA e documenta**.

### GATE-LINKS (célula bate exatamente com o contrato; APENAS PROC é suspeito)
Usar `python3 tools/optimus_gates.py <contrato.json> tools/rules.json > gates.json` e montar a tabela
a partir de `gates.json.rows` (a célula de PR vem pronta). No re-fetch final, para cada card conferir
que a célula do Notion é **idêntica** a `rows[].pull_requests`. "• APENAS PROC" só é aceito quando
`deploy_fields.apenas_proc == true`. Se `gates.json.errors` não estiver vazio (GATE-CROSSCHECK) →
**PARA e documenta em `erros/`** (pega o PB-5528/5085/4969: APENAS PROC com PR real).

### GATE-IDEMPOT (sem duplicata)
- Se a página da versão **já existe** → **atualizar (usar `notion-update-page`)**, nunca criar outra.
- Se a página **não existe** → criar com `notion-create-pages`.

Isto impede a colisão/reubo de página que aconteceu na 1.117.0.

## Guardrails
- **Não inventar** Infra / Merge / repositório — deixar em branco.
- **Fidelidade ao card:** a doc reflete **exatamente** os links reais dos cards — **todas** as PRs e
  **todos** os repositórios (deduplicados), nunca só o primeiro. O usuário **confia** nessa conferência.
- **Verificação enxuta:** reler a página com `notion-fetch` **uma vez, ao final** (não a cada
  linha/card) e aplicar GATE-MOLDE + GATE-LINKS. Menos ida-e-volta = mais rápido.

> Evolução planejada deste papel: `docs/ROADMAP.md`.
