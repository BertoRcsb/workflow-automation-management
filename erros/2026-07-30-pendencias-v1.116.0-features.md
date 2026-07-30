# 2026-07-30 — Pendências v1.116.0 (Features) — Notificador SANDBOX

> Registro de auditoria: v1.116.0 é um deploy de dados puro (0 repositórios). 1 card aprovado (PB-5922).
> 5 cards bloqueados por D1 automática (épico PB-5768 all-or-nothing incompleto). Nenhuma notificação externa.

## 1. Versão v1.116.0 — Escopo

| Campo | Valor |
|---|---|
| Board | Features |
| Cards Aprovados | 1 |
| Cards Bloqueados (D1) | 5 |
| Repositórios para Deploy | 0 |
| Tipo de Deploy | Dados Puro |

## 2. Card Aprovado

| Key | Nome | Status | Tipo | Observação |
|---|---|---|---|---|
| PB-5922 | API Catraca: Disponibilizar vínculos | Pronto para Deploy | acao_dados | Sem PR/repo vinculada; deploy apenas de dados/configuração |

## 3. Cards Bloqueados por D1 (Épico PB-5768 All-or-Nothing Incompleto)

Épico: **PB-5768 — Refatoração Melhorias Onda 1** (all-or-nothing, 38 filhos total; 19 em desenvolvimento)

| Key | Status | Motivo da Exclusão |
|---|---|---|
| PB-5833 | Teste Regressivo | Filho de PB-5768; épico incompleto |
| PB-5807 | Teste Regressivo | Filho de PB-5768; épico incompleto |
| PB-5788 | Teste Regressivo | Filho de PB-5768; épico incompleto |
| PB-5786 | Teste Regressivo | Filho de PB-5768; épico incompleto |
| PB-5781 | Teste Regressivo | Filho de PB-5768; épico incompleto |

**Gatilho:** D1 automática (spec §5.2 — Regras de Dependência). Nenhuma notificação enviada.

## 4. Escopo de Deploy — Dados Puro

**v1.116.0 é um deploy de configuração/dados exclusivamente**:
- PB-5922 (API Catraca) é `acao_dados=Sim`
- Nenhum repositório de código vinculado
- Sincronização = apenas metadados de configuração
- Não requer sincronização de branches (prerelease/teste_regressivo/master)

**Status:** Pronto para sincronização de dados.

## 5. Notificações (SANDBOX)

- **D1 silenciosas (PB-5768):** Nenhuma notificação enviada (exclusão automática conforme spec).
- **V2 (sem links):** PB-5922 está sem PR/repo vinculada, mas é intencionalmente `acao_dados` — confirmado como válido.
- **Notificador:** Modo SANDBOX — apenas auditoria. Ronan pode proceder ao `make dry-run` do Passo 1.

## 6. Próximos Passos

- ✓ Notificador registrou pendências
- ⧐ Aguardando comando do Ronan: `make dry-run PR_TITLE="v1.116.0"`
- ⧐ Após dry-run: `make run PR_TITLE="v1.116.0"` (abertura de PR pré-prod)

**Status Final:** `pronto_para_sync`
