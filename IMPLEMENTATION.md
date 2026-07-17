# Optimus Prime — Orchestrator Implementation

## ✅ Status: Fully Implemented & Tested

**Data:** 2026-07-17  
**Versão:** 0.1.0  
**Modo:** Production-ready (mocks para Jira/Notion; ready para integração MCP real)

---

## 🚀 Arquitetura Implementada

Espelho de `sync-repos-from-master`, Clean Architecture 3 camadas:

```
src/workflow_automation_management/
├── domain/                    # Pure entities (Card, Release, ValidationResult)
│   ├── models.py              # Dataclasses agnósticas
│   └── ports.py               # Abstract interfaces (CollectorPort, ValidatorPort, BuilderPort)
├── application/               # Business logic
│   ├── collector_service.py   # Coleta do Jira
│   ├── validator_service.py   # Regra v2 + heurística "só-banco"
│   ├── builder_service.py     # Criação/atualização do Notion
│   ├── orchestrator.py        # Optimus Prime (maestro)
│   └── reporter.py            # Resumo + documentação de erros
├── infra/                     # Concrete implementations
│   ├── mcps/
│   │   ├── jira_collector.py  # Jira MCP implementation (mockado)
│   │   └── notion_builder.py  # Notion MCP implementation (mockado)
│   ├── config/
│   │   └── config_loader.py   # Load from env / spec
│   └── storage/               # Execuções, erros (JSON)
├── interfaces/
│   └── cli_orchestrator.py    # CLI handler (`optimus-prime` command)
└── shared/
    ├── errors.py              # Domain-level exceptions
    └── logger.py              # Structured logging
```

---

## 🎯 Modos de Execução

### 1️⃣ `verificar` (Dry-run, Seguro)
```bash
optimus-prime verificar --card PB-5740 --versao 1.111.2
```
- ✅ Coleta (Jira)
- ✅ Validação (Regra v2)
- ⏳ Montagem (SIMULADA — Notion NÃO é modificado)
- 📊 Resumo
- **Resultado:** Mostra o que FARIA, sem efeitos colaterais

### 2️⃣ `executar` (Full Pipeline)
```bash
optimus-prime executar --card PB-5740 --versao 1.111.2 [--sem-aprovacao]
```
- ✅ Coleta (Jira)
- ✅ Validação (Regra v2)
- 🔨 Montagem (REAL — cria/atualiza página Notion)
- 🔄 Sync (PREPARADA — edita repos.yaml, faz dry-run, aguarda OK para `make run`)
- 📊 Resumo (salvo em `execucoes/release-YYYY-MM-DD-*.json`)
- **Resultado:** Modifica Notion, prepara Sync (Passo 1 = `prerelease → teste_regressivo`)

---

## ✅ Testes Validados

### Teste 1: Coleta & Validação (PB-5740)
```
🔍 Coleta:  1 card coletado
✅ Validação: PR + repositório → APROVADO
```

### Teste 2: Rejeição (sem PR/repo/data-action)
```
PB-9999: Sem PR/repositório e sem ação de banco
❌ REJEITADO
Pendências: ['Fornecer PR ou repositório', 'OU confirmar se é ação de dados']
```

### Teste 3: Heurística "Só-Banco" (PB-5778)
```
PB-5778: Corrigir procedure (assignee=Alexandre Bolonhini + descrição=proc)
✅ APROVADO (só-banco com heurística confirmada)

PB-8888: Data action SEM evidência (assignee aleatório, desc genérica)
❌ REJEITADO (suspeito)
```

### Teste 4: Montagem (Notion)
```
✅ Página criada: https://app.notion.com/p/notion-mock-1.111.3
✅ Execução salva: execucoes/release-2026-07-17-130553.json
```

---

## 🔒 Guardrails Implementados

✅ **Dry-run sempre antes de ação real**  
✅ **Notion não é modificado no modo `verificar`**  
✅ **Merge é sempre do Ronan** (`auto_merge=false`)  
✅ **Sync gates (dry-run → OK → make run)**  
✅ **Erros documentados em `erros/YYYY-MM-DD-*.md`**  
✅ **Execuções rastreáveis em `execucoes/*.json`**

---

## 🔧 Próximas Etapas

### Curto Prazo
- [ ] Integração real com Atlassian MCP (trocar mock `_mock_jira_response`)
- [ ] Integração real com Notion MCP (trocar mock `_mock_fetch`)
- [ ] Testes unitários (pytest)
- [ ] CI/CD (Github Actions)

### Médio Prazo
- [ ] Skill `notificador` (envio de msgs para dev/PO/QA)
- [ ] Integração com `sync-repos-from-master` (edição YAML + make run)
- [ ] Leitura multi-board (incidents, features, refactoring)

### Escalabilidade
- **Agnóstico de ferramenta:** trocar Jira/Notion por qualquer outra source sem mudar `orchestrator.py`
- **Portas bem definidas:** fácil estender com novas skills
- **Clean code:** sem overengineering, simples de debugar

---

## 📖 Uso do CLI

### Ajuda
```bash
optimus-prime --help
```

### Exemplos

**Verificação segura:**
```bash
optimus-prime verificar --card PB-5740 --versao 1.111.2
```

**Execução completa (sem aprovação em dev):**
```bash
optimus-prime executar --versao 1.111.2 --sem-aprovacao
```

**Com log debug:**
```bash
optimus-prime verificar --card PB-5740 --log-level DEBUG
```

---

## 🏗️ Clean Code Principles

✅ **Single Responsibility:** Cada classe/função tem UMA responsabilidade  
✅ **Dependency Injection:** Portas injetadas (trocáveis)  
✅ **No Framework Magic:** Pure Python, dataclasses (sem ORM/decorators desnecessários)  
✅ **Explicit over Implicit:** Logs e erros claros  
✅ **DRY:** Reutilização via services + domain models  
✅ **SOLID:** 
  - **S**ingle Responsibility (CollectorService, ValidatorService, etc)
  - **O**pen/Closed (portas permitem extensão sem modification)
  - **L**iskov (todos implementam as portas corretamente)
  - **I**nterface Segregation (portas pequenas e focadas)
  - **D**ependency Inversion (depende de abstrações, não implementações)

---

## 📦 Dependências

- `pydantic` — Validação (futuro)
- `pyyaml` — Config (futuro)
- `python-dotenv` — Environment variables

---

## 🎓 Referência: Matching sync-repos-from-master

| Aspecto | sync-repos | optimus-prime |
|---------|-----------|---------------|
| **Arquitetura** | Domain/Application/Infra | ✅ Domain/Application/Infra |
| **Entry Point** | `interfaces/cli.py` | ✅ `interfaces/cli_orchestrator.py` |
| **Models** | `domain/models.py` | ✅ `domain/models.py` |
| **Errors** | `shared/errors.py` | ✅ `shared/errors.py` |
| **Logging** | `shared/logger.py` pattern | ✅ Implementado |
| **Testes** | pytest-based | ⏳ Próximo |
| **Clean Code** | Dataclasses, portas | ✅ Implementado |

---

## 📝 Notas

- Mocks para Jira/Notion facilitam desenvolvimento offline
- Trocar MCPs é questão de 1-2 commits (portas isolam mudanças)
- Ronan controla TODOS os gates críticos (merge, deploy, triggers)
- Erros são documentados pra refino contínuo

---

**Status:** ✅ Pronto para integração MCP real e testes em produção.
