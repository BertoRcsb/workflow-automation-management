# Documentação — Esteira Inteligente de Release Notes

Índice da pasta `docs/`. Comportamento canônico (fonte da verdade): [`../spec/spec.md`](../spec/spec.md).
Landing do repo: [`../README.md`](../README.md).

## O que é cada doc
| Arquivo | O que é |
|---|---|
| [`COMANDOS.md`](COMANDOS.md) | **Guia operacional** — como rodar (receitas passo a passo, tabela "Sequência e gates", regras de ouro, mapa dos 3 boards). |
| [`SETUP.md`](SETUP.md) | **Primeira vez / pós-clone** — instalar o Claude Code, conectar os MCPs, apontar o `sync-repos-from-master`. |

## Visão geral (1 parágrafo)
A esteira transforma cards prontos do Jira em uma **release/hotfix documentada no Notion** e prepara a
**sincronização de branches** no `sync-repos-from-master`. O maestro é o **Optimus Prime**: no `executar`
roda **autônomo até o Notion** e **para** — o Sync/deploy em diante é **sob OK do Ronan**, com gate por
ação. O deploy real e os merges são do Ronan.

## Como usar (resumo — passo a passo em `COMANDOS.md`)
```
Optimus Prime verificar <board|todos os boards>   # dry: coleta, valida, simula — NÃO toca em nada
Optimus Prime iniciar   <board|todos os boards>   # autônomo até o Notion (para antes do Sync)
```

## Configuração (IDs já públicos no repo)
- **Jira (Atlassian MCP, read-only):** cloudId `f36e5519-1f88-4f71-a406-75326e86deda`; projeto `PB`;
  status alvo `Teste regressivo` / `Pronto para deploy`. Campos em `../spec/spec.md` §8.
- **Notion:** base "Versões - NewContract" (data_source `23e19d89-2318-81ff-812d-000b6afb6b5a`);
  props `Versão` (title), `Tipo` (Release/Hotfix).
- **sync-repos-from-master:** `repos.yaml` (`source`/`targets` por passo; `auto_merge=false`); branches
  `prerelease` → `teste_regressivo` → `master`; credenciais no `.env` (repo separado).
