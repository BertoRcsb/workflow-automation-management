# Documentação — Esteira Inteligente de Release Notes

Doc de **como usar tudo** (modo de execução e passo a passo). Comportamento canônico: `spec/spec.md`.

## Visão geral
A esteira transforma cards prontos do Jira em uma **release/hotfix documentada no Notion** e prepara a
**sincronização de branches** no `sync-repos-from-master`. O maestro é o **Optimus Prime**, que
coordena as skills e aplica **segurança por ação** e **aprovação humana**. O deploy real e os merges
são do Ronan.

## Modo de execução
```
/optimus-prime verificar   # dry: coleta, valida, simula Notion e mostra o alvo do Sync — NÃO toca em nada
/optimus-prime executar    # completa até o make run (Passo 1), pausando pra OK a cada ação que muda algo
```

## Passo a passo (`executar`)
1. **Versão-alvo** — lê a última no Notion e propõe a próxima (release/hotfix). **Hotfix o Ronan confirma.**
2. **Coletor** — busca o(s) card(s) no Jira (Atlassian MCP) e normaliza (contrato §7).
3. **Validador** — regra v2 (PR+repo **ou** só-banco) + heurística "só-banco"; mostra o **rascunho**
   (aprovados × reprovados) e **espera OK**.
4. **Montador** — cria/atualiza a página da versão no Notion (molde das versões anteriores) e
   **re-verifica via re-fetch**.
5. **Notificador** — *sandbox*: gera mensagens p/ dev/PO/QA e mostra só pro Ronan (envio real a fazer).
6. **Sync (`sync-repos-from-master`)** — guiado pela doc do Notion:
   - Ativa no `repos.yaml` **só os repos de "Repositórios para Deploy"**; comenta o resto. Repo
     faltando → **para e reporta**.
   - **Passo 1:** `source: prerelease` → `target: teste_regressivo` → `make dry-run` → OK → `make run` (PR).
   - **Passo 2:** `teste_regressivo → master` → **só sob comando do Ronan** (Optimus Prime só edita o YAML).
   - **Passo 3:** `make run-triggers PR_TITLE="<versão>"` → **100% do Ronan**, após OK do QA.
7. **Resumo** consolidado (§9) → exibido e salvo em `execucoes/*.json`.

## Comandos (referência)
| Comando | O que faz | Quem |
|---|---|---|
| `/optimus-prime verificar` | esteira em dry, sem tocar em nada | Optimus Prime |
| `/optimus-prime executar` | esteira até o `make run` (Passo 1) | Optimus Prime (com OK) |
| `make dry-run PR_TITLE=…` | simula o sync | Optimus Prime |
| `make run PR_TITLE=…` | abre/atualiza PRs (auto_merge=false) | Optimus Prime (Passo 1) / Ronan (Passo 2) |
| merge do PR | promove a branch | **só Ronan** |
| `make run-triggers PR_TITLE=…` | deploy GCP nos clientes | **só Ronan** |

## Configuração
- **Jira (Atlassian MCP, read-only):** cloudId `f36e5519-1f88-4f71-a406-75326e86deda`; projeto `PB`;
  status alvo `Teste regressivo` / `Pronto para deploy`. Campos em `spec/spec.md` §8.
- **Notion:** base "Versões - NewContract" (data_source `23e19d89-2318-81ff-812d-000b6afb6b5a`);
  props `Versão` (title), `Tipo` (Release/Hotfix).
- **sync-repos-from-master:** `repos.yaml` (`source`/`targets` por passo; `auto_merge=false`); branches
  `prerelease` → `teste_regressivo` → `master`; credenciais no `.env` (Bitbucket/GCP).

## Exemplo real (E2E validado — 2026-07-16)
PB-5740 (Bug, "Teste regressivo", repo `autocadastro-front`, PR #244) → aprovado (PR+repo) →
Notion **Hotfix 1.111.2** → Sync Passo 1 (`prerelease → teste_regressivo`) → **PR #245 aberto, sem
merge**. Registro em `execucoes/release-2026-07-16-001.json`.

## Limites atuais
- Notificador em sandbox (sem envio real). Leitura diária multi-board a fazer.
- Sem rollback; trigger é assíncrono (não espera o build). Merge/prod = só Ronan.
