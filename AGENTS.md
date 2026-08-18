# Arquitetura de Subagentes — Workflow Automation Management

## Autoridade canônica

1. **CLAUDE.md** — índice do projeto (fontes da verdade)
2. **spec/spec.md** — fonte da verdade funcional
3. **`.claude/skills/orquestrador/SKILL.md`** — sequência, gates e guardrails da esteira

## Subagentes canônicos (exatamente 4 papéis da spec — nenhum 5º)

| Papel | Arquivo | Skill | Responsabilidade |
|-------|---------|-------|------------------|
| **Coletor** | `.claude/agents/coletor.md` | `coletor` | Busca cards no Jira, normaliza, executa `optimus_extract.py` |
| **Validador** | `.claude/agents/validador.md` | `validador` | Aplica gates (regra v2, D1/D2), executa `optimus_gates.py` |
| **Montador** | `.claude/agents/montador.md` | `montador` | Cria/atualiza release no Notion via MCP |
| **Notificador** | `.claude/agents/notificador-sandbox.md` | (nenhuma) | Gera rascunhos de notificação (sandbox) |

As ferramentas permitidas/proibidas de cada um estão no **frontmatter do próprio arquivo do agente**
(fonte única — não duplicar aqui).

## Hierarquia de execução

```
Ronan
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
3. **Subagentes nunca chamam subagentes** — só o Optimus Prime invoca Agent.
4. **Optimus valida antes de avançar** — consome o contrato de handoff (abaixo) de cada subagente.
5. **Falha interrompe** — gate falha → documenta em `erros/` e para; card ambíguo → pergunta ao
   Ronan; sem retry automático (máximo uma repetição por erro de formato).

## Contrato de handoff (formato mínimo, sem schema complexo)

```json
{
  "agent": "nome",
  "status": "ok|blocked|error",
  "artifact_paths": [],
  "counts": {},
  "questions": [],
  "errors": []
}
```

## Camada determinística (o LLM não modifica)

`tools/optimus_extract.py` · `optimus_gates.py` · `optimus_yaml_gate.py` ·
`optimus_promotion_gate.py` · `optimus_triggers_gate.py` — ver `docs/GATES.md`.

## Próximas etapas (não implementadas)

1. Paralelismo entre subagentes independentes
2. Notificador de produção (hoje sandbox)
3. Integração com CI/CD (hoje manual via Ronan)
