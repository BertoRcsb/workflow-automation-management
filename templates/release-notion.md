# Template canônico da página de versão no Notion (Release e Hotfix)

> **Fonte única do molde** (GATE-MOLDE do montador). O re-fetch final compara a página criada contra
> ESTA estrutura, campo a campo. Mudar o molde = editar este arquivo (com OK do Ronan), nunca improvisar
> na montagem. Exemplo canônico que originou o template: página 1.114.0 (Release) / 1.111.1 (Hotfix).

## Metadados

- **Ícone:** `📝`
- **Propriedades:**
  - `Versão` (title): `<X.Y.Z>`
  - `Tipo` (select): `Release` ou `Hotfix`

## Tabela de itens (um card aprovado por linha)

Colunas, na ordem exata:

| Item | Pull Requests | Tem Ação de Banco ? | Tem Ação de Infra ? | Merge Realizado ? |
|---|---|---|---|---|
| `[PB-XXXX — <título completo>](https://bernhoeft.atlassian.net/browse/PB-XXXX) · <status>` | `[<repo #num>](<url>)` separadas por `<br>` — TODAS as PRs do contrato; `• APENAS PROC` só quando `deploy_fields.apenas_proc == true`; nenhuma PR = vazio | `Sim` / `Não` (de `deploy_fields.acao_dados`) | `—` (até apurar) | `—` (até apurar) |

A célula de PR vem pronta de `gates.json.rows[].pull_requests` (`tools/optimus_gates.py`) — nunca
reinterpretar o card.

Título de card contendo `|` quebra a tabela — substituir por barra larga `｜` no texto (link intacto).
Numa doc nova, os checkboxes de Testes regressivos/Ambientes nascem desmarcados (QA marca depois);
`[x] Aprovado` só quando todos os cards já passaram nos testes.

## Blocos (nesta ordem, cada um heading + conteúdo)

### Testes regressivos

- [x] Aprovado
- [ ] Não aprovado
- [ ] Sem testes regressivos

(`Aprovado` marcado por padrão quando todos os cards passaram nos testes.)

### Ambientes

- [ ] NewContract
- [ ] NewContract-VLI
- [ ] Treinamento
- [ ] Neoenergia
- [ ] Preprod

### Repositórios para Deploy:

Lista de URLs, deduplicada — **TODOS os repos únicos de todos os cards aprovados** (é este bloco que
guia o `repos.yaml`):

- [https://bitbucket.org/bernhoeft/<repo>](https://bitbucket.org/bernhoeft/<repo>)

### Participantes do Deploy:

Headings sublinhados, cor marrom (`{color="brown"}`), nomes em lista:

- **Dados:** — ex.: `- Alexandre Rudoi.`
- **DevOps:** — ex.: `- Ronan Berto / Yuri Stolai.`
- **QA:** — ex.: `- Dorgival Silva Filho.`
- **Responsavel Deploy:** — ex.: `- Ronan Berto / Yuri Stolai.`
- **Desenvolvedores sobreaviso:** — assignees dos cards aprovados
