# Plano de Correção — Versões 1.116.0 e 1.117.0

**Data:** 2026-07-30  
**Status:** Planejado (espera execução com Optimus Prime + Track 1 ativa)

## Resumo da bagunça a corrigir

| Versão | Criada | Status | Problema |
|--------|--------|--------|----------|
| **1.116.0** | 2026-07-30 | ? | TBD (investigar) |
| **1.117.0** | 2026-07-28 (antes de 1.115.0/1.115.1!) | Errada | Cards fora do padrão, links faltando (ADF), versionamento fora de ordem |

### Evidência do problema 1.117.0
- Criada: 2026-07-28 14:12:42 (ANTES de 1.115.0 em 07-28 15:52 e 1.115.1 em 07-28 22:01)
- Cards na página: 6 (PB-5528, PB-5316, PB-4786, PB-4761, PB-4727, PB-4726)
- Cards aprovados pelo validador: 8 (faltam: PB-4962, PB-4969, PB-5074, PB-5085)
- Cards que passou verificar (todos os boards): 13
- Links faltando: PB-4786 com `—` em PR/repo (bug ADF)
- Cards errados: entrou PB-4761 (não-aprovado) e PB-4786 (REPROVADO v2)

## Fluxo de correção por versão

### Para 1.116.0
1. **Investigar:** ler o arquivo de execução de 1.116.0 (se existe) ou a página do Notion para entender qual board e qual foi o pacote.
2. **Reidentificar:** rodar `coletor` + `validador` com a receita do Track 1 (parse ADF novo) para este board.
3. **Comparar:** cards da página vs. aprovados do validador → identificar o que está errado.
4. **Refazer:** atualizar a página (GATE-IDEMPOT) com o molde correto (Track 1) e passar por todos os gates.

### Para 1.117.0
1. **Versão-alvo:** 1.117.0 deve ser a **próxima após 1.116.0** (se 1.116.0 = 1.115.X, então 1.117.0 é ok; caso contrário, reconciliar).
2. **Board identificado:** features (a partir do context de "Optimus Prime iniciar features" no relato do Ronan).
3. **Recoleta:** rodar `coletor` + `validador` para features, com parse ADF novo.
4. **Reconciliação (GATE-CONJUNTO):** cards aprovados devem ser reconciliados (8 no validador, ou 13 se houver override?).
5. **Refazer página:** atualizar com molde correto, passar por GATE-CONJUNTO/MOLDE/LINKS.

## Pasos de execução (via Optimus Prime, após Track 1 ativa)

```
Optimus Prime iniciar features --versao [1.116.0 ou 1.117.0] [--card PB-...]
```

O Optimus rodará:
1. Versão-alvo: usar o número passado em `--versao` (ou calcular se omitido) — GATE-VER-1/2 deteceta colisão.
2. Coletor: features → parse ADF + registrar PR/repo com URL count.
3. Validador: aplicar regra v2 + GATE-FALSO-VAZIO (não reprovar parse_failed).
4. Montador: GATE-CONJUNTO (cards aprovados = página) + GATE-MOLDE/LINKS + GATE-IDEMPOT (atualizar).
5. Sync: editar repos.yaml + dry-run (autônomo).
6. Mensagem `Confira` ao fim.

## Pós-correção

- Auditoria: `execucoes/` grava resumo com antes/depois (quantos cards, PRs, repos, links).
- Próximas corridas: com Track 1 ativa, nenhuma página deve sair errada (gates impedem).
