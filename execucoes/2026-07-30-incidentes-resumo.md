# Optimus Prime — Verificar Incidentes

**Data:** 2026-07-30  
**Modo:** VERIFICAR (dry, sem alterações)  
**Alvo:** incidentes (board único)  

## Versão-alvo
**1.82.0** (Release — próxima após 1.81.0)

## Coleta (Jira)
**4 cards** no status `Teste regressivo` / `Pronto para deploy`:
- PB-5912: [BUG] Erro de validação de passaporte (Teste regressivo)
- PB-5906: Relatório SLA - Prazo coluna (Teste regressivo)
- PB-5772: [BUG] Status de documentos incorreto (Teste regressivo)
- PB-5728: Refatoração - Colaboradores - Erro de instabilidade (Pronto para deploy)

## Validação (Regra v2 + Gates D1/D2)
| Status | Count | Cards |
|--------|-------|-------|
| Aprovados | 3 | PB-5912, PB-5906, PB-5772 |
| Reprovados | 1 | PB-5728 (sem PR, sem repo, sem ação dados) |
| D1 (épico) | — | Sem violação |
| D2 (PR) | — | Sem violação |

## Repositórios para Deploy
- **contractweb-v3** (PRs: #5248, #5229)
- **bernhoeft-grt-sla-api** (PR: #207)

## Próximos passos (modo executar)
1. Criar Release 1.82.0 no Notion
2. Editar repos.yaml (ativar 2 repos, comentar resto)
3. Rodar `make dry-run PR_TITLE="[Release] 1.82.0"`
4. Se sucesso: emitir "Confira" e parar (make run sob OK do Ronan)

## Rastreabilidade
- Raw: `2026-07-30-incidentes-raw.json` (4 issues do Jira)
- Contrato: `2026-07-30-incidentes-contrato.json` (normalizado)
- Gates: `2026-07-30-incidentes-gates.json` (validação)
