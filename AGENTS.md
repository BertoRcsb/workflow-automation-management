# Arquitetura de Subagentes — Workflow Automation Management

## Autoridade Canônica

1. **CLAUDE.md** — Constituição do projeto
2. **spec/spec.md** — Fonte da verdade funcional
3. **Optimus Prime** (`.claude/commands/optimus-prime.md`) — Orquestrador único

## Subagentes Canônicos

Exatamente **4 papéis** da spec:

| Papel | Arquivo | Skill | Responsabilidade |
|-------|---------|-------|------------------|
| **Coletor** | `.claude/agents/coletor.md` | `coletor` | Busca cards no Jira, normaliza, executa `optimus_extract.py` |
| **Validador** | `.claude/agents/validador.md` | `validador` | Aplica gates (D1/D2), regra v2, executa `optimus_gates.py` |
| **Montador** | `.claude/agents/montador.md` | `montador` | Cria/atualiza release no Notion via MCPs |
| **Notificador** | `.claude/agents/notificador-sandbox.md` | (nenhuma) | Gera rascunhos de notificação (sandbox) |

**Nenhum 5º papel.** O papel "Auditor" foi adicionado pela tentativa anterior e não faz parte da spec — foi removido.

## Hierarquia de Execução

```
Ronan
  ↓
/optimus-prime
  ↓
Optimus Prime (Orquestrador)
  ├→ Coletor (contexto novo via Agent)
  │    ↓ devolve artefatos + status
  │
  ├→ Validador (contexto novo via Agent)
  │    ↓ devolve artefatos + status
  │
  ├→ Montador (contexto novo via Agent)
  │    ↓ devolve artefatos + status
  │
  ├→ Notificador (contexto novo via Agent)
  │    ↓ devolve artefatos + status
  │
  └→ Sync (Optimus executa, não delega)
      ├ edita repos.yaml
      ├ gates determinísticos
      └ make dry-run
```

## Princípios

### 1. **Contexto Novo por Subagente**

Cada invocação é uma chamada **Agent** independente:

```
optimus_prime = invoke Agent(subagent_name)
// sem resume, sem compartilhamento de contexto anterior
// cada subagente começa limpo
```

### 2. **Cada Subagente Carrega Apenas Sua Skill**

- **Coletor** carrega `.claude/skills/coletor/SKILL.md`
- **Validador** carrega `.claude/skills/validador/SKILL.md`
- **Montador** carrega `.claude/skills/montador/SKILL.md`
- **Notificador** não tem skill de produção (sandbox)

Nenhum subagente carrega múltiplas skills.

### 3. **Subagentes Nunca Chamam Subagentes**

- Subagentes **NÃO têm Agent permitido**
- Só o Optimus Prime pode invocar Agent
- Subagentes devolvem resultado → Optimus valida → Optimus chama próximo

### 4. **Optimus Valida Antes de Avançar**

Após cada subagente, Optimus validada:

```json
{
  "agent": "nome",
  "status": "ok|blocked|error",
  "artifact_paths": [...],
  "counts": {...},
  "questions": [],
  "errors": []
}
```

Formato mínimo. Sem schema complexo.

### 5. **Falha Interrompe**

- Gate falha → documenta em `erros/` e **para**
- Card ambíguo → **pergunta ao Ronan**
- Sem retry automático (máximo uma repetição por erro de formato)

## Ferramentas por Subagente

| Subagente | Permite | Proíbe |
|-----------|---------|--------|
| Coletor | Read, Grep, Glob, Bash, Write, MCPs Atlassian | Edit, Agent |
| Validador | Read, Grep, Glob, Bash, Write | Edit, Agent |
| Montador | Read, Grep, Glob, Write, MCPs Notion | Edit, Bash, Agent |
| Notificador | Read, Grep, Glob, Write | Edit, Bash, Agent |

## Arquivos Não Modificáveis

**Determinísticos (o LLM não toca):**

- `tools/optimus_extract.py` — extrai PR/repo de ADF
- `tools/optimus_gates.py` — aplica D1/D2
- `tools/optimus_yaml_gate.py` — valida edição de YAML
- `tools/optimus_promotion_gate.py` — valida promoção (nunca master direto)
- `tools/optimus_triggers_gate.py` — valida triggers por passo

## Arquivos Removidos (Tentativa Anterior)

Não faziam parte da spec:

- `.claude/agents/auditor-release.md` — papel não canônico
- `tools/optimus_agent_guard.py` — controle de ferramentas desnecessário
- `tools/optimus_handoff.py` — validação de handoff complexa
- `tools/optimus_release_audit.py` — auditoria duplicada
- `tools/optimus_sync_guard.py` — controle de sync redundante
- `tests/test_optimus_security.py` — testes de componentes removidos

## Execução dos Modos

### Modo `verificar`

```
/optimus-prime verificar <board>
```

- Subagentes executam em contextos novos
- Coletor (leitura) → Validador → Montador (simulado, sem escrever)
- Notificador (simulado)
- **Não toca em nada**
- Entrega relatório + plano
- **Não emite "Confira"**

### Modo `executar`

```
/optimus-prime executar <board>
```

- Subagentes em contextos novos
- Coletor → Validador → Montador (escreve real no Notion)
- Notificador (sandbox)
- Optimus prepara Sync, edita YAML, gates determinísticos
- `make dry-run` Passo 1
- Emite **"Optimus Prime retornando com o resultado = Confira"**
- **Para** — o `make run` é comando explícito do Ronan

## Validação Interativa

Confirme que os 4 subagentes estão reconhecidos:

```bash
# Dentro do Claude Code:
/agents
```

Esperado:
- ✓ coletor
- ✓ validador
- ✓ montador
- ✓ notificador-sandbox

**Não** deve aparecer `auditor-release`.

## Próximas Etapas (Não Implementadas Nesta Tarefa)

1. Paralelismo (subagentes independentes podem rodar em paralelo → futuro)
2. Notificador de produção (hoje sandbox)
3. Otimização de modelo (hoje tudo Haiku; escala em ambiguidade)
4. Integração com CI/CD (hoje manual via Ronan)

---

**Data da simplificação:** 2026-08-17
**Status:** Implementação concluída e validada
**Contato:** Ronan Berto
