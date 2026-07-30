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
- **Molde de referência:** reler a **última página do mesmo `Tipo`** antes de montar
  (query por `Tipo` ordenando por `Criado em` desc).

## Molde de conteúdo (materializado — exemplo canônico: 1.114.0)
A página segue **exatamente** este padrão, sem improviso.

### Metadados
- **Ícone:** `📝`
- **Propriedades:**
  - `Versão` (title): `1.116.0` (ex.)
  - `Tipo` (select): `Release` ou `Hotfix`

### Tabela de itens
**Colunas (ordem exata):** `Item · Pull Requests · Tem Ação de Banco ? · Tem Ação de Infra ? · Merge Realizado ?`

**Linhas (um card por linha):**
- **Item:** `[PB-XXXX — <título completo do card>](https://bernhoeft.atlassian.net/browse/PB-XXXX) · <status>`
  (ex.: `[PB-5811 — Impossibilidade de Readmissão de Colaborador](https://bernhoeft.atlassian.net/browse/PB-5811) · Pronto para deploy`).
  O "mention" nativo do Jira **não** é reproduzível via MCP — o link markdown com título é o equivalente suportado.
- **Pull Requests:** **TODAS** as PRs do card (uma por linha / separadas, nunca só a primeira).
  Formato compacto: `[<slug-do-repo> #<num>](<url-da-PR>)`
  (ex.: `[contractweb-v3 #5184](https://bitbucket.org/bernhoeft/contractweb-v3/pull-requests/5184)`).
  **Só-banco:** `• APENAS PROC` (+ nome do proc quando disponível).
  **Nenhuma PR:** deixar vazio (não escrever `—` na tabela — isso é pra depois dos blocos).
- **Ação de Banco:** `Sim` / `Não` (de `deploy_fields.acao_dados` do card).
- **Ação de Infra / Merge:** deixar em branco (`—`) até apurar (**nunca inventar**).

### Blocos (nesta ordem, cada um um heading + conteúdo)
1. **Testes regressivos** — 3 checkboxes:
   - `[x] Aprovado` (por padrão, marca quando todos os cards foram aprovados em testes)
   - `[ ] Não aprovado`
   - `[ ] Sem testes regressivos`

2. **Ambientes** — 5 checkboxes (marca os que foram testados):
   - `[ ] NewContract`
   - `[ ] NewContract-VLI`
   - `[ ] Treinamento`
   - `[ ] Neoenergia`
   - `[ ] Preprod`

3. **Repositórios para Deploy:** — lista de URLs (deduplicated)
   (ex.: `- [https://bitbucket.org/bernhoeft/contractweb-v3](...)`)
   **Deve listar TODOS os repos únicos de todos os cards aprovados** — é este bloco que guia `repos.yaml`.

4. **Participantes do Deploy:** — heading sublinhado, cor marrom (`{color="brown"}`)
   Estrutura exata:
   - **Dados:** {color="brown"} — lista nomes (ex.: `- Alexandre Rudoi.`)
   - **DevOps:** {color="brown"} — lista nomes (ex.: `- Ronan Berto / Yuri Stolai.`)
   - **QA:** {color="brown"} — lista nomes (ex.: `- Dorgival Silva Filho.`)
   - **Responsavel Deploy:** {color="brown"} — lista nomes (ex.: `- Ronan Berto / Yuri Stolai.`)
   - **Desenvolvedores sobreaviso:** {color="brown"} — assignees dos cards aprovados

## Gates (asserções duras — param e documentam, nunca "passam" dado errado)

### GATE-CONJUNTO (reconciliação)
**Antes de escrever qualquer coisa:** o montador recebe uma lista de **aprovados do validador**
(chaves + contagem) e o conjunto de cards a montar. **Asserção:** o conjunto **deve ser idêntico** aos
aprovados (mesmas chaves, mesma contagem, sem deletar nem adicionar).

Se detectar **card fora dos aprovados** ou **aprovado ausente** → **PARA e documenta em `erros/`**.
Nenhum card entra na doc sem ter saído do gate do validador. (Este gate teria evitado o bug B
da 1.117.0, onde entrou PB-4761 não-aprovado e faltaram 4 aprovados.)

### GATE-MOLDE (fidelidade ao padrão)
No re-fetch final, **conferir que as colunas e blocos batem com a última página do mesmo Tipo**
(1.114.0 para Release; 1.111.1 para Hotfix, ex.). Comparação campo a campo:
- Colunas da tabela exatas.
- Nomes dos blocos e ordem.
- Checkboxes presentes.
- Estrutura de "Participantes" (headings marrom, nomes em lista).

Se divergir → **PARA e documenta**. (Restaura o critério "(colunas iguais às versões anteriores)"
removido no refactor do orquestrador.)

### GATE-LINKS (nenhuma célula vazia onde o card tem link)
No re-fetch, para **cada card que tem PR/repositório no contrato normalizado**, conferir que a
célula **não está vazia / `—`** na página do Notion. Se encontrar vazio onde deveria ter link →
**PARA e documenta** (pega o sintoma do PB-4786 na 1.117.0).

### GATE-IDEMPOT (sem duplicata)
- Se a página da versão **já existe** → **atualizar (usar `notion-update-page`)**, nunca criar outra.
- Se a página **não existe** → criar com `notion-create-pages`.

Isto impede a colisão/reubo de página que aconteceu na 1.117.0.

## Guardrails
- **Não inventar** Infra / Merge / repositório — deixar em branco.
- **Fidelidade ao card:** a doc reflete **exatamente** os links reais dos cards — **todas** as PRs e
  **todos** os repositórios (deduplicados), nunca só o primeiro. O Ronan **confia** nessa conferência.
- **Verificação enxuta:** reler a página com `notion-fetch` **uma vez, ao final** (não a cada
  linha/card) e aplicar GATE-MOLDE + GATE-LINKS. Menos ida-e-volta = mais rápido.

## Evolução / próximos papéis (este escopo vai crescer)
- **Categorias** na tabela/release.
- **Nome do proc** nas linhas só-banco.
- Preencher **Merge / Infra** quando a origem do dado estiver definida.
- Trocar o destino sem mudar o papel: reescrever apenas "Configuração atual".
