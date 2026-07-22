# 2026-07-22 — Deploy truncado por dependências entre cards (épico e PR compartilhada)

## Resumo
O deploy da **1.113.0 (features)** foi **cancelado pelo Ronan** e não vai acontecer. Ao longo do dia,
vários cards relacionados entre si (por **épico** e por **PR compartilhada**) entraram/saíram do pacote
de forma inconsistente, gerando risco de deploy **parcial/truncado**. **O erro não foi da esteira nem do
Ronan:** a origem foi a **seleção de dev/PO movendo cards cedo demais** para `Teste regressivo` /
`Pronto para deploy` (status não reflete prontidão real do conjunto).

## O que aconteceu (cronologia)
- **PB-5157** foi retirado a pedido, depois readicionado — é do épico **PB-5159 "Melhorias na Tela de
  Análise"** e compartilha as **mesmas 3 PRs** (newcontract-front #1073, analysis-api #448, storage #609)
  com PB-5330/5331/5713. Tirar/pôr um sem os irmãos deixava o conjunto incoerente.
- **PB-5786** estava na 1.113.0, mas é filho do épico **PB-5768 "Refatoração Melhorias Onda 1"**
  (all-or-nothing, épico incompleto) → removido.
- **1.114.0 (refatoração)** tinha PB-5173/5166/5110 — todos filhos do PB-5768 → removidos (página esvaziada).
- **Épico PB-236 "Relatório SLA"**: cluster no pacote (PB-4726, PB-4727, PB-5316, PB-5528) acoplado por
  PRs compartilhadas (#1048, #195, #4910); o irmão **PB-4786** está reprovado (sem PR) e fora → épico
  incompleto.
- **~38 cards** movidos para status de deploy indevidamente eram, em grande parte, filhos do PB-5768.

## Causa raiz
1. Cards movidos para status de deploy **antes** de o conjunto (épico) estar pronto.
2. **PRs compartilhadas** entre cards: subir um card sem os co-donos da mesma PR = deploy truncado.
3. A esteira, até então, **só sinalizava** essas dependências — não segurava sozinha.

## Correção adotada (para não repetir) — vira regra de skill
No `validador`, duas **regras de dependência** (exclusão **automática**, **sem notificação**; liberar só
por **ordem explícita do Ronan / PO / gestor**; toda exclusão registrada em `execucoes/`):
- **D1 — Épico incompleto:** card de épico cujos filhos não-cancelados **não estão todos** em status de
  deploy → **excluir** os cards desse épico (não sobe parcial de épico).
- **D2 — PR compartilhada parcial:** se a mesma PR é usada por vários cards e **nem todos** estão no
  pacote → **excluir** os que estavam dentro (a PR não sobe truncada). Todos dentro = ok; todos fora = ok.
- `coletor` passa a **expor** `epic` (parent) e o **grupo de cards por PR** para o `validador` decidir.

## Onde ficou registrado
- Skills: `.claude/skills/validador/SKILL.md` (D1/D2) e `.claude/skills/coletor/SKILL.md` (dados de épico/PR).
- Memórias: `regras-dependencia-deploy`, `epico-pb-5768-all-or-nothing`, `cards-mesmo-epico-mesmas-prs`.

## Pendências (governança do Ronan)
- **1.113.0 cancelada:** decidir o que fazer com os 8 PRs do Passo 1 já abertos (prerelease→teste_regressivo)
  e com a página 1.113.0 no Notion (arquivar/anular?).
- Confirmar a **definição de "épico completo"** usada na D1 (todos os filhos não-cancelados em status de deploy).
- Upstream: alinhar com dev/PO para **não mover cards cedo** para status de deploy.
