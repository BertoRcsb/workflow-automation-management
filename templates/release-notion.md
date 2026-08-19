# Template canônico da página de versão no Notion (Release e Hotfix)

> **Fonte única do molde** (GATE-MOLDE do montador). O re-fetch final compara a página criada contra
> ESTA estrutura, campo a campo. Mudar o molde = editar este arquivo (com OK do usuário), nunca improvisar
> na montagem. Exemplo canônico que originou o template: página 1.114.0 (Release) / 1.111.1 (Hotfix).

## Metadados

- **Ícone:** `📝`
- **A página é SEMPRE uma linha da base "Versões - NewContract"** (`data_source_id`
  `23e19d89-2318-81ff-812d-000b6afb6b5a`). No `notion-create-pages`, passar
  `parent: { data_source_id: "23e19d89-..." }` — **nunca** criar página solta
  (sem parent = página órfã sem propriedades; incidente 2026-08-19). O `Tipo` só
  existe como propriedade quando a página é linha da base.
- **Propriedades (obrigatórias, setadas na criação):**
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

## Blocos (nesta ordem, sintaxe LITERAL confirmada nas páginas reais 1.118.1 e 1.120.0)

**Regra de formatação (não improvisar):** os três primeiros blocos são **rótulo em
negrito** (`**Testes regressivos**`, `**Ambientes**`, `**Repositórios para Deploy:**`)
— **NÃO** heading `##`/`###`. O bloco de participantes é **heading H2 sublinhado**, e
cada papel é **negrito + `{color="brown"}`**. Copiar a estrutura abaixo ao pé da letra.

### Testes regressivos

Rótulo: `**Testes regressivos**`. Numa doc nova todos desmarcados (QA marca depois);
`[x] Aprovado` só quando todos os cards já passaram.

```
**Testes regressivos**
- [ ] Aprovado
- [ ] Não aprovado
- [ ] Sem testes regressivos
```

### Ambientes

Rótulo: `**Ambientes**`. **Seis** opções (inclui `Prod`), desmarcadas numa doc nova:

```
**Ambientes**
- [ ] NewContract
- [ ] NewContract-VLI
- [ ] Treinamento
- [ ] Neoenergia
- [ ] Preprod
- [ ] Prod
```

### Repositórios para Deploy:

Rótulo: `**Repositórios para Deploy:**`. Lista de URLs, deduplicada — **TODOS os repos
únicos de todos os cards aprovados** (é este bloco que guia o `repos.yaml`):

```
**Repositórios para Deploy:**
- [https://bitbucket.org/bernhoeft/<repo>](https://bitbucket.org/bernhoeft/<repo>)
```

### Participantes do Deploy:

Cabeçalho é **H2 sublinhado**: `## <span underline="true">Participantes do Deploy:</span>`.
Cada papel é **negrito + `{color="brown"}`** com os nomes em lista logo abaixo (nomes
terminam em ponto). Elenco fixo = **dado canônico** em `tools/deploy_roster.json` (não é
"exemplo"); sobreaviso = **assignees dos cards aprovados**. **Nunca deixar `—`.** O erro
de 2026-08-19 foi usar `## Papel` (H2) em vez de `**Papel:** {color="brown"}` (negrito).

```
## <span underline="true">Participantes do Deploy:</span>
**Dados:** {color="brown"}
- Alexandre Rudoi.
**DevOps:** {color="brown"}
- Ronan Berto / Yuri Stolai.
**QA:** {color="brown"}
- Dorgival Silva Filho.
**Responsavel Deploy:** {color="brown"}
- Ronan Berto / Yuri Stolai.
**Desenvolvedores sobreaviso:** {color="brown"}
- <assignee 1>.
- <assignee 2>.
```

O GATE-MONTAGEM (`tools/optimus_montage_gate.py`) confere, no conteúdo REAL da página
(re-fetch), que a página está na base, com `Tipo`/`Versão` corretos, e que cada nome
canônico + cada assignee aparece — falha fechado se algum estiver ausente ou `—`.
