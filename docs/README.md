# Documentação — Esteira Inteligente de Release Notes

Índice da pasta `docs/`. Comportamento canônico (fonte da verdade): [`../spec/spec.md`](../spec/spec.md).
Landing do repo: [`../README.md`](../README.md).

## O que é cada doc
| Arquivo | O que é |
|---|---|
| [`ARQUITETURA.md`](ARQUITETURA.md) | **Esquema visual atualizado** — diagramas Mermaid inline da arquitetura atual (subagentes, camada `tools/`, fluxo do `executar`, promoção de branches, driver do Sync). |
| [`APRESENTACAO.md`](APRESENTACAO.md) | **Apresentação visual** — diagramas em imagem para slides/stakeholders (mesmo tema visual do `ARQUITETURA.md`) + exemplos reais. |
| [`COMANDOS.md`](COMANDOS.md) | **Guia operacional** — como rodar (receitas passo a passo, tabela "Sequência e gates", regras de ouro, mapa dos 3 boards). |
| [`SETUP.md`](SETUP.md) | **Primeira vez / pós-clone** — instalar o Claude Code, conectar os MCPs, apontar o `sync-repos-from-master`. |
| [`GATES.md`](GATES.md) | **Índice dos gates** — o que é código determinístico, o que é asserção do LLM, o que é gate humano. |
| [`ROADMAP.md`](ROADMAP.md) | **Evolução planejada** dos papéis (fonte única do backlog; mudança só com OK do usuário). |
| [`PROPOSTA.md`](PROPOSTA.md) | **Apresentação/histórico** — proposta original da solução. |
| [`archive/`](archive/) | Plano e tarefas de julho/2026 (checklists concluídos, mantidos por histórico). |

## Visão geral (1 parágrafo)
A esteira transforma cards prontos do Jira em uma **release/hotfix documentada no Notion** e prepara a
**sincronização de branches** no `sync-repos-from-master`. O maestro é o **Optimus Prime**: no `executar`
de board único roda **autônomo até o `make dry-run` do Sync Passo 1** (doc no Notion → edita o
`repos.yaml` → `make dry-run`) e emite a mensagem única `Confira` — o `make run` do Passo 1 (abre os
PRs), Merge, Master (Passo 2) e Triggers (Passo 3) são **sob OK do usuário**, com gate por ação. O deploy
real e os merges são do usuário.

## Como usar (resumo — passo a passo em `COMANDOS.md`)
```
Optimus Prime verificar <board|todos os boards>   # dry: coleta e valida de verdade (read-only), escrita zero — só relatório
Optimus Prime iniciar   <board|todos os boards>   # board único: autônomo até o make dry-run do Passo 1 (make run sob OK); todos os boards: até o Notion
```

## Configuração (IDs já públicos no repo)
- **Jira (Atlassian MCP, read-only):** cloudId `f36e5519-1f88-4f71-a406-75326e86deda`; projeto `PB`;
  status alvo `Teste regressivo` / `Pronto para deploy`. Campos em `../spec/spec.md` §8.
- **Notion:** base "Versões - NewContract" (data_source `23e19d89-2318-81ff-812d-000b6afb6b5a`);
  props `Versão` (title), `Tipo` (Release/Hotfix).
- **sync-repos-from-master:** `repos.yaml` (`source`/`targets` por passo; `auto_merge=false`); branches
  `prerelease` → `teste_regressivo` → `master`; credenciais no `.env` (repo separado).
