# 2026-07-23 — Mapa de rollback do teste_regressivo (para extração com o gestor)

> Apoio à cirurgia manual (Ronan + gestor). A esteira NÃO executa revert/reset — isto é só o mapa
> PR × card × repositório do que entrou/mistura. Fonte: `execucoes/` + Jira (PB). Números conferidos
> no Jira em 2026-07-23. A 1.113.0 foi **cancelada** (ver `2026-07-22-deploy-truncado-dependencias.md`).

## 1. Como o "entrelaçamento" acontece
O sync `prerelease → teste_regressivo` é **por branch**, não por card: carrega **todos** os commits que
estavam em `prerelease`. Então o código dos cards certos e dos que não deviam subir entrou **junto**, num
único PR de sync por repo. Reverter o PR de sync desfaz **tudo**; para manter o legítimo é preciso
reverter **PRs de card específicos** dentro da branch.

## 2. PRs de sync do Passo 1 (prerelease → teste_regressivo) — o que aterrissou por repo
(execução `release-2026-07-22-001-features-1.113.0-passo1`)

| Repositório | PR de sync (teste_regressivo) |
|---|---|
| bernhoeft-grt-login-api | #376 |
| bernhoeft-grt-contractweb-front | #1135 |
| contractweb-v3 | #5214 |
| bernhoeft-grt-newcontract-front | #1137 |
| bernhoeft-grt-analysis-api | #454 |
| bernhoeft-grt-relatorios | #869 |
| bernhoeft-grt-storage | #630 |
| bernhoeft-grt-sla-api | #200 |

## 3. Cards do Lucas Lage e Silva — PRs e repositórios
| Card | Épico | Repositório | PR |
|---|---|---|---|
| PB-4726 | PB-236 Relatório SLA | newcontract-front / sla-api / contractweb-v3 | #1048 / #195 / #4910 |
| PB-4727 | PB-236 Relatório SLA | newcontract-front / sla-api / contractweb-v3 | #1048 / #195 / #4910 (mesmas do 4726) |
| PB-4786 | PB-236 Relatório SLA | — | sem PR/repo (reprovado) |
| PB-3428 | (sem épico) | contractweb-v3 | #4311 |
| PB-3429 | (sem épico) | contractweb-v3 | #4312 |
| PB-3431 | (sem épico) | contractweb-v3 | #4313 |
| PB-3433 | (sem épico) | contractweb-v3 | #4314 |
| PB-3436 | (sem épico) | contractweb-v3 | #4315 |
| PB-3437 | (sem épico) | contractweb-v3 | #4316 |
| PB-3491 | (sem épico) | contractweb-v3 | #4317 |
| PB-3492 | (sem épico) | contractweb-v3 | #4318 |

> Os 8 Tasks (#4311–#4318) estão em "Pronto para deploy" mas NÃO entraram em nenhum pacote nosso — se o
> dev os mergeou em prerelease/master, estão misturados em `contractweb-v3`. Conferir na branch.

## 4. Cards dos épicos no pacote 1.113.0 — PRs e repositórios
| Épico | Cards | PRs (repo #num) |
|---|---|---|
| PB-236 Relatório SLA | PB-4726, PB-4727, PB-5316, PB-5528 | newcontract-front #1048, sla-api #195, contractweb-v3 #4910, newcontract-front #1112 |
| PB-5159 Melhorias na Tela de Análise | PB-5157, PB-5330, PB-5331, PB-5713 | newcontract-front #1073, analysis-api #448, storage #609 |
| PB-4769 Relatório de Usuários Ativos | PB-4761 | newcontract-front #972, relatorios #804, contractweb-v3 #5202, login-api #369, contractweb-front #1120 (+ PROC) |

## 5. PRs COMPARTILHADAS (a "mistura" — mesma PR em vários cards; reverter uma afeta todos)
| PR | Repositório | Cards |
|---|---|---|
| #1048 | newcontract-front | PB-4726, PB-4727, PB-5316 |
| #195 | sla-api | PB-4726, PB-4727, PB-5528 |
| #4910 | contractweb-v3 | PB-4726, PB-4727, PB-5316 |
| #1073 | newcontract-front | PB-5157, PB-5330, PB-5331, PB-5713 |
| #448 | analysis-api | PB-5157, PB-5330, PB-5331, PB-5713 |
| #609 | storage | PB-5157, PB-5330, PB-5331, PB-5713 |

## 6. Por repositório — o que precisa ser separado em teste_regressivo
**contractweb-v3 (sync #5214) — MAIOR ponto de mistura:**
- 1.113.0 (features): #4910 (PB-4726/4727/5316), #5202 (PB-4761)
- Lucas / otimização de query (não-pacote): #4311–#4318 (PB-3428/3429/3431/3433/3436/3437/3491/3492)

**bernhoeft-grt-newcontract-front (sync #1137):**
- #1048 (PB-4726/4727/5316), #1112 (PB-5528), #1073 (PB-5157/5330/5331/5713), #972 (PB-4761)

**bernhoeft-grt-contractweb-front (sync #1135):**
- Pacote: #1120 (PB-4761)
- NÃO deveriam ter subido: #1076 (PB-5786, retirado) e #1003 (PB-5110/5166/5173 — refatoração do épico PB-5768)

**bernhoeft-grt-sla-api (sync #200):** #195 (PB-4726/4727/5528)
**bernhoeft-grt-analysis-api (sync #454):** #448 (PB-5157/5330/5331/5713)
**bernhoeft-grt-storage (sync #630):** #609 (PB-5157/5330/5331/5713)
**bernhoeft-grt-login-api (sync #376):** #369 (PB-4761)
**bernhoeft-grt-relatorios (sync #869):** #804 (PB-4761)

## 7. Cards que NÃO deviam ter subido (alvos da extração)
- **PB-5786** (contractweb-front #1076) — filho do épico PB-5768.
- **PB-5110 / PB-5166 / PB-5173** (contractweb-front #1003) — filhos do PB-5768 (eram a 1.114.0).
- **Épico PB-5768 "Refatoração Melhorias Onda 1"** (all-or-nothing, incompleto) — 38 filhos; conferir na
  branch se outros filhos foram mergeados por dev/PO. Filhos hoje em status de deploy: PB-5110, 5115,
  5162, 5166, 5169, 5173, 5723, 5732, 5734, 5735, 5786, 5788, 5809, 5728.

## 8. Ressalvas
- Só tenho visão de **PR × card** (Jira/nossos registros). **Quais commits estão de fato mergeados em
  cada branch** só olhando o git de cada repo — isso é a etapa da cirurgia (você + gestor).
- Reverter PR compartilhada (seção 5) afeta **todos** os cards daquela PR — cuidar para não derrubar o legítimo.
- A 1.113.0 está cancelada, mas os cards de features podem ser legítimos numa release futura limpa —
  decidir por card o que volta.
