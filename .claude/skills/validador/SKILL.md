---
name: validador
description: >-
  Use quando o usuário quer decidir se itens coletados estão aptos a entrar num
  pacote de deploy/release — aplicar o gate de elegibilidade por conteúdo e
  separar aprovados × reprovados com as pendências. Gatilhos: "validar cards",
  "esse card entra?", "quais barrar", "checar elegibilidade", "separar aprovados
  e reprovados". Contexto atual: cards de deploy (regra v2); papel agnóstico.
---

# Validador

Aplica o **gate por conteúdo**: o **status não garante prontidão** (comprovado — cards
em "Pronto para deploy" estavam vazios). Recebe itens normalizados do `coletor` e
devolve **aprovados × reprovados** para o `montador` e o `notificador`.

> Fonte da verdade do projeto: `spec/spec.md`. Esta skill é a
> versão operacional deste papel.

## Regra de elegibilidade v2
Um item **passa** se:
1. tem **PR + repositório** (mudança de código), **OU**
2. é **só ação de banco/proc** — `Ação de dados = Sim`, sem PR/repo.

**Barra** quem não tem **nada** (sem PR, sem repo, sem ação de dados).
`"N/A"` e `"Apenas PROC"` **não** contam como link válido.

## Heurística "só-banco legítimo" (validada em 2026-07-14 — caso-modelo PB-5778)
Para distinguir **banco legítimo** de **"código que esqueceu a PR"**:

> `Ação de dados = Sim` **e** (assignee é responsável de banco **ou** a descrição
> cita proc / procedure / carga / seleção / query) → **aprova sem exigir PR/repo**.

Caso-modelo **PB-5778**: `Ação de dados = Sim`, sem PR/repo, assignee **Alexandre
Bolonhini** (banco) e descrição sobre corrigir a *procedure/seleção* → **APROVADO**.

## Saída
- **Aprovados:** chave, título, responsável, resumo, categoria, evidências, `checked_at`.
- **Reprovados:** chave, título, responsável, `pending_items`, orientação, `checked_at`.

## Guardrails
- O agente **não inventa** dado para preencher campo ausente.
- Casos inconclusivos / contraditórios / exceções → **intervenção humana** (Ronan aprova).

## Regra como config (evita hardcode)
Externalizar a regra em `deploy_requirements.yaml` (ver spec §10) — mudar a regra =
editar o YAML, não a skill.

## Evolução / próximos papéis (este escopo vai crescer)
- **Revalidar** cards corrigidos.
- **Categorias** (correção · banco · infra · melhoria · alteração técnica · pós-deploy).
- Regras distintas por **tipo de ciclo**.
