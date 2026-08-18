# Índice dos gates — o que roda onde

> Fonte única do inventário. Cada gate mora em UM lugar; a coluna "Enforçado por" diz se é código
> determinístico (o LLM só chama e lê a saída) ou asserção que o LLM executa. Todos seguem o padrão:
> saída `chave=valor`, exit 0 = ok, exit 1 = **documenta em `erros/` e PARA**.

## Enforçados por código (`tools/`)

| Gate | Script | O que garante | Falha → |
|---|---|---|---|
| **GATE-ADF / falso-vazio** | `optimus_extract.py` | Extração de PR/repo do ADF; `parse_failed=true` quando o campo tem conteúdo e 0 URLs (nunca `[]` silencioso) | contrato marca o card; validador não aprova nem reprova |
| **Regra v2 + D1 + D2** | `optimus_gates.py` | Elegibilidade por conteúdo; exclusão por épico incompleto (D1) e PR compartilhada parcial (D2, fixpoint) | card excluído/ambíguo registrado em `gates.json` |
| **GATE-CROSSCHECK** | `optimus_gates.py` | Nunca "APENAS PROC" onde há PR; nunca aprovar `parse_failed` | exit 1 → documenta e para |
| **GATE-VER-1/VER-2** | `optimus_next_version.py` | Versão-alvo pelo maior semver numérico (nunca data); anti-colisão | exit 1 → decisão do Ronan |
| **GATE-YAML** | `optimus_yaml_gate.py` (via driver) | Edição do `repos.yaml` = só toggle de `#` (+ escalar `defaults.source` por passo) | driver restaura backup, documenta, para |
| **GATE-PROMO** | `optimus_promotion_gate.py` (via driver) | Par `source→targets` na whitelist (`promotion.json`); nunca direto pra master; sem self-sync; passo esperado = detectado | driver restaura backup, documenta, para |
| **GATE-TRIGGERS** | `optimus_triggers_gate.py` (via driver) | Triggers comentados fora do Passo 3 (`--expect none`); presentes e sem órfão no Passo 3 (`--expect present`) | driver documenta, para |
| **Driver do Sync** | `optimus_sync.py` | Encadeia backup → GATE-YAML → GATE-PROMO → GATE-TRIGGERS → `make`; restauração e documentação automáticas | exit 1 = já tratado; o LLM só PARA |

## Asserções executadas pelo LLM (montador)

| Gate | O que garante | Falha → |
|---|---|---|
| **GATE-CONJUNTO** | Cards na doc = exatamente `aprovados_finais` do validador (sem sobra, sem falta) | para e documenta |
| **GATE-MOLDE** | Re-fetch da página bate com `templates/release-notion.md`, campo a campo | para e documenta |
| **GATE-LINKS** | Célula de PR no Notion idêntica a `gates.json.rows[].pull_requests` | para e documenta |
| **GATE-IDEMPOT** | Página existente → `notion-update-page`; inexistente → `notion-create-pages` (nunca duplicar) | para e documenta |

## Gate humano (governança)

| Gate | Regra |
|---|---|
| **Gate por ação** | Todo `make run`/`run-triggers` (Passo 1, 2, 3 e pós-deploy) = **comando explícito do Ronan**; dry-run limpo → mensagem `Confira` e espera. Merge e aprovação de build no GCP = Ronan. |

Candidatos a virar código: GATE-CONJUNTO e GATE-LINKS (comparação mecânica de conjuntos/strings a
partir do `gates.json` + dump do re-fetch). GATE-MOLDE exige entender a estrutura da página — fica no LLM.
