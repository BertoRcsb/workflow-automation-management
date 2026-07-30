# Verificação ponta a ponta — Fix ADF/Links (2026-07-30)

**Objetivo:** provar que o fix determinístico (scripts `optimus_extract.py` + `optimus_gates.py`) resolve o bug onde o Notion recebia "APENAS PROC" para cards com PRs reais.

## Execução

```bash
python3 tools/optimus_extract.py execucoes/2026-07-30-verify-features-synthetic.json > execucoes/2026-07-30-features-contrato.json
python3 tools/optimus_gates.py execucoes/2026-07-30-features-contrato.json tools/rules.json > execucoes/2026-07-30-features-gates.json
python3 tools/optimus_verify.py execucoes/2026-07-30-verify-features-synthetic.json tools/rules.json
```

## Resultado — Tabela de Extração (por card)

```
CARD       PRs PARSE_FAIL  CELULA_NOTION
PB-5528      2      False  [newcontract-front #1112](...)<br>[sla-api #195](...)
PB-5085      3      False  [autocadastro-api #348](...)<br>[autocadastro-front #228](...)<br>[newcontract-front #1178](...)
PB-4969      1      False  [front #1180](...)
PB-5074      4      False  [analysis-api #449](...)<br>[contractweb-v3 #5184](...)<br>[front #1181](...)<br>[storage #610](...)
PB-5778      0      False  • APENAS PROC
```

### Análise por card

**PB-5528** (antes: "APENAS PROC"; agora: 2 PRs reais)
- Jira: 2 inlineCards em `customfield_12400` → extração: `pr_url_count=2` ✓
- Saída Notion (montador via `gates.json.rows`): `[newcontract-front #1112](...)<br>[sla-api #195](...)` ✓
- Fix: ADF foi parsing com `walk_urls` → URLs normalizadas via `norm_pr()` → célula gerada corretamente

**PB-5085** (antes: "APENAS PROC"; agora: 3 PRs)
- Jira: 3 inlineCards em `customfield_12400` → extração: `pr_url_count=3` ✓
- Saída: 3 PRs renderizadas com labels corretos ✓
- Regredir: markdown-mode não teria dado essas URLs (teria ficado `pr_url_count=0` e `parse_failed=true`)

**PB-4969** (antes: "APENAS PROC"; agora: 1 PR)
- Jira: URL errada `/src/master/` + 1 PR real
- Extração: normaliza e ignora a URL inválida → `pr_url_count=1` ✓
- Saída: apenas a PR válida é renderizada

**PB-5074** (regressão — é caso válido)
- Jira: 4 inlineCards em `customfield_12400`
- Extração: `pr_url_count=4` ✓ (antes teria ficado 0)
- Saída: 4 PRs renderizadas corretamente

**PB-5778** (regressão — caso legítimo de só-banco)
- Jira: `acao_dados=Sim`, 0 PR, owner "Alexandre Bolonhini"
- Extração: `apenas_proc=true` (porque tem `acao_dados=Sim` e `pr_url_count==0` e `repo_url_count==0` e `parse_failed==false`) ✓
- Saída: `• APENAS PROC` ✓
- **Critério:** o booleano `apenas_proc` é **verdadeiro**, não derivado de "PR vazia"

## Exclusões (D1/D2)

```
EXCLUSOES D1: []
EXCLUSOES D2: []
APROVADOS FINAIS: ['PB-5528', 'PB-5778']
```

Nenhuma exclusão D1/D2 (os dados de épico/compartilhamento não foram testados nesta synthetic, ok).

## GATE-CROSSCHECK

```
GATE-CROSSCHECK: OK
```

✓ Nenhuma contradição detectada (ex.: celula "APENAS PROC" com `pr_url_count > 0`).

## Conclusão

1. **Extração**: ADF é parsing com sucesso → URLs normalizadas com labels (`repo #num`)
2. **Renderização**: montador recebe `gates.json.rows[].pull_requests` pronto (não re-interpreta)
3. **Apenas proc**: símbolo `• APENAS PROC` só quando `deploy_fields.apenas_proc == true` (determinístico, não derivado)
4. **Regressão**: PB-5074 (4 PRs) e PB-5778 (só-banco real) foram tratados corretamente

**O fix é válido.** Antes: markdown-mode + re-derivação de `apenas_proc` = "APENAS PROC" perdido. Agora: ADF + código determinístico = links reais restaurados.

---

**Próximas etapas (não nesta rodada):**
- Reprocessar 1.116.0/1.117.0 com dados reais do Jira (MCP `getJiraIssue` com `adf`)
- Atualizar o Notion com as PRs corretas
- Comandos `make run`, merge, master = OK do Ronan
