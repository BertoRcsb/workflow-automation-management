# Arquitetura de Subagentes — Workflow Automation Management

## Autoridade canônica

1. **CLAUDE.md** — índice do projeto (fontes da verdade)
2. **spec/spec.md** — fonte da verdade funcional
3. **`.claude/skills/orquestrador/SKILL.md`** — sequência, gates e guardrails da esteira

## Subagentes canônicos (4 papéis + worker efêmero de fan-out)

| Papel | Arquivo | Skill | Responsabilidade |
|-------|---------|-------|------------------|
| **Coletor** | `.claude/agents/coletor.md` | `coletor` | Busca cards no Jira, normaliza, executa `optimus_extract.py`; decide fan-out |
| **Worker de coleta** | `.claude/agents/coletor-card.md` | `coletor` | Worker efêmero de coleta por lote, despachado só pelo Optimus em fan-out |
| **Validador** | `.claude/agents/validador.md` | `validador` | Aplica gates (regra v2, D1/D2), executa `optimus_gates.py` |
| **Montador** | `.claude/agents/montador.md` | `montador` | Cria/atualiza release no Notion via MCP |
| **Notificador** | `.claude/agents/notificador-sandbox.md` | (nenhuma) | Gera rascunhos de notificação (sandbox) |

As ferramentas permitidas/proibidas de cada um estão no **frontmatter do próprio arquivo do agente**
(fonte única — não duplicar aqui).

## Hierarquia de execução

```
Usuário
  ↓
/optimus-prime
  ↓
Optimus Prime (orquestrador)
  ├→ Coletor      (contexto novo via Agent) → devolve artefatos + status
  ├→ Validador    (contexto novo via Agent) → devolve artefatos + status
  ├→ Montador     (contexto novo via Agent) → devolve artefatos + status
  ├→ Notificador  (contexto novo via Agent) → devolve artefatos + status
  └→ Sync (Optimus executa, não delega): edita repos.yaml → gates determinísticos → make dry-run
```

## Princípios

1. **Contexto novo por subagente** — cada invocação é uma chamada Agent independente; sem resume,
   sem compartilhamento de contexto anterior.
2. **Cada subagente carrega apenas sua skill** — nunca múltiplas.
3. **Subagentes nunca chamam subagentes** — só o Optimus Prime invoca Agent. Workers efêmeros também são
   despachados só pelo Optimus Prime; a consolidação do fan-out é determinística (`tools/optimus_card_aggregate.py`),
   sem agente consolidador.
4. **Optimus valida antes de avançar** — consome o contrato de handoff (abaixo) de cada subagente.
5. **Autonomia sem microaprovações** — modo + alvo autorizam o Optimus a coordenar todas as ações
   internas da esteira. Subagentes não pedem permissão ao usuário; devolvem handoff ao Optimus.
6. **Falha interrompe** — gate falha ou card ambíguo → documenta em `erros/`, devolve `blocked` e
   para sem pedir autorização para contornar; máximo uma repetição por erro de formato.
7. **Gate humano único no escopo autônomo** — depois do Notion revalidado + `dry-run` do Passo 1,
   o Optimus emite `Confira` e aguarda o comando do usuário para `make run`. Gates posteriores de
   master, merge e triggers permanecem inalterados.

## Contrato de handoff (formato mínimo, sem schema complexo)

```json
{
  "agent": "nome",
  "status": "ok|blocked|error",
  "artifact_paths": [],
  "counts": {},
  "questions": [],
  "errors": [],
  "fanout": false,
  "manifest_path": "execucoes/<data>-<board>-manifesto.json",
  "batch_id": "<bNN>"
}
```

Campos opcionais `fanout`/`manifest_path` aparecem no handoff do coletor quando há fan-out; `batch_id`
aparece no handoff do worker `coletor-card`.

## Camada determinística (o LLM não modifica)

`tools/optimus_extract.py` · `optimus_card_manifest.py` · `optimus_card_aggregate.py` ·
`optimus_gates.py` · `optimus_yaml_gate.py` ·
`optimus_promotion_gate.py` · `optimus_triggers_gate.py` — ver `docs/GATES.md`.

## Próximas etapas

Consolidadas em `docs/ROADMAP.md`.
