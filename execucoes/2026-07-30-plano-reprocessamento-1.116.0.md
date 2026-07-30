# Plano: Reprocessamento de 1.116.0 (v2 Corrigida)

**Objetivo:** reprocessar o board Features (1.116.0) com o fix de extração ADF, comparar com a versão atual no Notion e sincronizar.

## Estado Atual (1.116.0 Original)

**Página Notion:** [1.116.0](https://app.notion.com/p/3ad19d8923188164bed0fbe8e2debf45)

**Total de cards: 8** (documentados em execucoes/2026-07-30-features-montador-content.md)

### Cards com "APENAS PROC" (bugs suspeitos — têm PRs reais no Jira):
- **PB-5922**: • APENAS PROC (acao_dados=Sim) — legítimo (dados puro)
- **PB-5528**: • APENAS PROC (acao_dados=Sim) — **BUG**: tem 2 PRs reais (newcontract-front #1112, sla-api #195)
- **PB-5085**: • APENAS PROC (acao_dados=Sim) — **BUG**: tem 3 PRs reais (front #1178, autocadastro-front #228, autocadastro-api #348)
- **PB-4969**: • APENAS PROC (acao_dados=Sim) — **BUG**: tem 2 PRs reais (centraldocumentos-api #96, front #1180)

### Cards com PRs reais (corretos):
- **PB-5074**: 4 PRs (bernhoeft-grt-contractweb-api #1086, bernhoeft-grt-contractweb-front #1178, bernhoeft-grt-login-api #381, contractweb-v3 #5245) — sem mudança

### Cards vazios (bloqueados/pendentes):
- **PB-4978**: (sem PR, sem acao_dados) — reprovado
- **PB-4977**: (sem PR, sem acao_dados) — reprovado
- **PB-4976**: (sem PR, sem acao_dados) — reprovado

## Versão 2 (Corrigida)

**Página Notion:** [1.116.0 (v2 - Corrigida)](https://app.notion.com/p/3ad19d892318819591d7c7f9dcae1cdf)

Passos (sob OK do Ronan):

### Passo 1: Coleta + Extração (Optimus autônomo até aqui)

```bash
# Buscar cada card do Features board via MCP (adf)
# e salvar cru
python3 tools/optimus_extract.py execucoes/2026-07-30-features-1.116.0-raw.json \
  > execucoes/2026-07-30-features-1.116.0-contrato.json

# Validar + gates
python3 tools/optimus_gates.py execucoes/2026-07-30-features-1.116.0-contrato.json \
  tools/rules.json \
  > execucoes/2026-07-30-features-1.116.0-gates.json
```

### Passo 2: Montagem no Notion (v2)

- Usar `gates.json.rows` para montar a tabela
- PRs saem do contrato (label + url), não re-derivadas
- `• APENAS PROC` só quando `deploy_fields.apenas_proc == true`
- Escrever na página "1.116.0 (v2 - Corrigida)"

### Passo 3: Comparação (8 cards)

| Card | Original | v2 Corrigida | Mudança |
|------|----------|--------------|---------|
| **PB-5922** | • APENAS PROC | • APENAS PROC | Sem mudança (legítimo: dados puro) |
| **PB-5528** | • APENAS PROC | [newcontract-front #1112]<br>[sla-api #195] | **2 PRs recuperadas** (BUG FIXADO) |
| **PB-5085** | • APENAS PROC | [front #1178]<br>[autocadastro-front #228]<br>[autocadastro-api #348] | **3 PRs recuperadas** (BUG FIXADO) |
| **PB-5074** | [bernhoeft-grt-contractweb-api #1086]<br>[bernhoeft-grt-contractweb-front #1178]<br>[bernhoeft-grt-login-api #381]<br>[contractweb-v3 #5245] | (idem) | Sem mudança (já estava correto) |
| **PB-4969** | • APENAS PROC | [centraldocumentos-api #96]<br>[front #1180] | **2 PRs recuperadas** (BUG FIXADO) |
| **PB-4978** | (vazio) | (vazio) | Sem mudança (reprovado) |
| **PB-4977** | (vazio) | (vazio) | Sem mudança (reprovado) |
| **PB-4976** | (vazio) | (vazio) | Sem mudança (reprovado) |

### Passo 4: Sincronização

Uma vez validada a v2:
1. Copiar célula de PRs (coluna "Pull Requests") da v2 para a original
2. Atualizar "Repositórios para Deploy" se houver mudanças
3. Manter "Participantes do Deploy" (não mudam)
4. **Validar:** `gates.json.errors` = [] (GATE-CROSSCHECK)

### Passo 5: Trigger Sync (se OK do QA/PO)

```bash
# Atualizar repos.yaml com os repos da v2
# Rodar make dry-run
make dry-run PR_TITLE="1.116.0"

# Se limpo, rodar make run (abre/atualiza PRs pré-prod)
make run PR_TITLE="1.116.0"

# Após aprovação prod:
make dry-run-triggers
make run-triggers  # Deploy GCP
```

## Saída Esperada

**Antes:** 1.116.0 com 4 cards faltando PRs no Notion (bug mascarado por "APENAS PROC")
**Depois:** 1.116.0 (v2) com PRs reais + 1.116.0 original corrigido com as mesmas PRs

**Rastreabilidade:** `execucoes/2026-07-30-features-1.116.0-{raw,contrato,gates}.json` guardados para auditoria.

---

**Próximas ações:** Ronan confirma se quer proceder com Passo 1 (coleta via MCP).
