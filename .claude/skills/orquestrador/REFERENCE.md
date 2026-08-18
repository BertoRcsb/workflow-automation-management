# Orquestrador — Referência estendida

Detalhes operacionais lidos **sob demanda**. Os **gates e guardrails que valem sempre estão no `SKILL.md`** — este arquivo só elabora casos, sintaxe e roadmap. Se houver conflito, o `SKILL.md` prevalece.

---

## 1. Alvo da varredura: um board × "todos os boards"

O **alvo** é parâmetro (separado do modo). Sem alvo, o Optimus **pergunta** qual board.

- **`<board>`** (incidentes | features | refatoração) — roda **um** board (comportamento de sempre).
- **`todos os boards`** — varre os três **em sequência, na ordem de prioridade do registro do `coletor` (incidentes SEMPRE 1º)**. Cada board é **totalmente isolado**: sua própria coleta → validação → versão-alvo → **sua própria página no Notion** (release/hotfix por board). **NUNCA** se misturam cards de boards diferentes (invariante §5.1 — a varredura reforça a regra, não a viola).
  - A varredura **termina no Notion**: o **Sync** (`repos.yaml` + `make run`) **não** entra no loop — segue **por-board e explícito**, como hoje (deploys em dias diferentes, incidentes primeiro).
  - **Board sem mapeamento** → **pula e reporta** naquele bloco; os demais seguem normalmente. Definir filtro = descoberta via MCP + OK do Ronan (ver `coletor`, "Registro de boards"). **Nunca inventar JQL.**
  - Combina com os dois modos: **`verificar todos os boards`** (dry, só relatório — um bloco por board) e **`iniciar todos os boards`** (executa até o Notion de cada board, com os gates por ação).
  - **Ordem/prioridade:** 1º **Linha de frente/incidentes** (`Incidente`) → 2º **Features** (`Story`) → 3º **Refatoração** (`Story`, menos importante). Mapeamento e JQL: ver `coletor`, "Registro de boards".
  - **Features × Refatoração** (ambos `Story`) são separados **pelo título**: **Refatoração** = título contém "Refatoração" (`summary ~ "Refatoração"`); **Features** = o complemento (`summary !~ ...`). Blocos distintos, sem sobreposição. Se um card cair no board errado → refino do filtro (com OK do Ronan); **nunca inventar** outro critério. Ver `coletor`, "Registro de boards".

---

## 2. Fluxo de promoção de branches (Sync) — passo a passo

Governança do `repos.yaml`, **guiada pela documentação**:

- **Lê o doc da versão no Notion** e **descomenta as linhas já existentes de** `repos.yaml` **apenas os repositórios que constam em "Repositórios para Deploy"** — ativando **só `name` + `repository`**; **os `triggers:` ficam comentados** (triggers são do **Passo 3**/prod, disparados só após OK do PO/QA — o `make run` do Passo 1/2 **não os usa**). **Tudo que não corresponder → comenta de volta** (não entra no `make run`). **Nunca reescreve/reformata/gera o arquivo nem altera `defaults`/`cloud_build`; só alterna o `#`. Passa pelo gate `tools/optimus_yaml_gate.py` (exit 1 → restaura backup e para).** **Repo faltando no YAML → para e reporta** (Ronan adiciona).
- **Editar o `repos.yaml` é autônomo** (guiado pela doc do Notion): **não pergunta a cada alteração**, **não pede OK para ler/editar** — só interrompe/reporta em caso de **discrepância** (repo faltando no YAML, doc ambígua). O `make dry-run` também é autônomo (simulação); o **gate humano** é **todo `make run`**: Passo 1, master (Passo 2) e triggers (Passo 3).

**Driver único (`tools/optimus_sync.py`) — sintaxe completa.** Toda ação no sync roda por ele; ele
encadeia GATE-YAML → GATE-PROMO → GATE-TRIGGERS → `make`, e em falha restaura o backup e documenta em
`erros/` sozinho (exit 1 = pare):
```
python3 tools/optimus_sync.py backup                                             # ANTES de editar o YAML
python3 tools/optimus_sync.py dry-run  --step <passo1|passo2|pos-deploy> --pr-title "<título>"
python3 tools/optimus_sync.py run      --step <passo1|passo2|pos-deploy> --pr-title "<título>"   # só sob OK do Ronan
python3 tools/optimus_sync.py dry-run-triggers                                   # Passo 3
python3 tools/optimus_sync.py run-triggers                                       # Passo 3 — só sob OK do Ronan
```
Ao mudar de passo, ajuste **`source` E `targets`** no YAML antes do `dry-run`. O GATE-PROMO só aprova os
pares da whitelist (`tools/promotion.json`) e bloqueia `prerelease→master`, self-sync, branch desconhecida
e passo divergente (criado após o incidente **2026-08-04**). O GATE-TRIGGERS exige triggers comentados
fora do Passo 3 e presentes/sem órfão no Passo 3 (incidente **2026-08-12**).

**Fluxo (NUNCA direto pra master; `make run` sempre com `target` explícito):**

- **Passo 1** — `source: prerelease` → `target: teste_regressivo` (pré-prod): ajusta o YAML, **GATE-PROMO
  `--step passo1`**, `make dry-run` e **parseia**; **erro (exit 1) → documenta em `erros/` e para**; **limpo (exit 0) → emite a mensagem `Confira` e para**. **O `make run`** (abre os PRs) só **sob OK explícito do Ronan**, depois da mensagem. Merge é do Ronan.
- **Passo 2** — `source: teste_regressivo` → `target: master` (prod): **só sob comando/override explícito do Ronan**. Por padrão o Optimus Prime edita o YAML (**troca `source` para `teste_regressivo` E `targets` para `master`**), roda **GATE-PROMO `--step passo2`** e `make dry-run`; o **`make run` de master só quando o Ronan mandar explicitamente**.
- **Passo 3** — **`make run-triggers`** (dispara os triggers Cloud Build → deploy nos ambientes dos clientes; **NÃO recebe `PR_TITLE`**). O Optimus Prime pode **disparar** sob **comando explícito** do Ronan; **quais** triggers vêm de **instrução do Ronan + os `triggers:` do `repos.yaml`** (ainda **não** estão no Notion). A **aprovação do build no GCP é do Ronan**, após OK do QA. Ex. (autocadastro-front): `neoenergia-front-autocadastro`, `vli-front-autocadastro`.
- **Pós-deploy (sync de volta)** — depois do deploy, sincroniza **master → develop, stage, prerelease**: edita o YAML (`source: master`, `targets: [develop, stage, prerelease]`), `make dry-run` → OK → **`make run PR_TITLE="Sync Master"`** (título **padrão** desse passo). Cria os PRs; **merges do Ronan**.

**Governança:** master/prod, merges e aprovação de build = **sempre do Ronan**; o Optimus Prime **pergunta antes** de master (Passo 2) e das triggers (Passo 3).

---

## 3. Mensagem única de retorno (elaboração)

No `executar`, ao concluir **todo o escopo autônomo** — cards conferidos → Notion montado e conferido com **TODOS** os links reais → `repos.yaml` editado → `make dry-run` do Passo 1 **limpo** — o Optimus emite **exatamente uma** mensagem de fechamento, começando pela linha exata:

```
Optimus Prime retornando com o resultado = Confira
```

- É a **única saída conversacional de fechamento**: execução **silenciosa**, sem relatórios verbosos nem perguntas de "posso avançar?" pelo caminho. Só **card genuinamente ambíguo** (passo 3) e **paradas por erro** (documenta em `erros/` e para) interrompem.
- **Na mesma** mensagem, logo abaixo da linha, listar os artefatos para o Ronan conferir: **URL da página no Notion**, **repos ativados no `repos.yaml`** e o **resultado do `make dry-run`** do Passo 1.
- **Contrato de confiança:** o Optimus só emite essa linha depois de ter **lido, conferido e montado certo**; o Ronan **confere depois** da mensagem (a linha é o sinal de "escopo autônomo concluído").
- **O `make run` do Passo 1** (abre os PRs pré-prod) só roda **depois**, sob **OK explícito do Ronan**.
- No alvo **`todos os boards`**, o escopo autônomo **termina no Notion** → a mensagem sai **por board**, ao fim de cada bloco (o Sync fica fora do loop).
- **`verificar`** (dry) **não** emite essa linha — entrega só o relatório/plano.

---

## 4. Configuração atual — MCPs + `make` do sync-repos-from-master

- **Skills irmãs** (delegar, nunca reimplementar): `coletor`, `validador`, `montador` (+ `notificador` quando existir).
- **MCPs:** Atlassian (leitura de cards, `read:jira-work`) e Notion (base "Versões - NewContract").
- **Deploy tool:** `sync-repos-from-master` — **repo separado** (não faz parte deste repo). Caminho via env **`SYNC_REPO_PATH`**; default: repo-irmão **`../sync-repos-from-master`**. Makefile. Comandos:
  - `make dry-run [PR_TITLE="..."]` / `make dry-run-triggers` → **simulação segura** (sempre antes).
  - `make run PR_TITLE="..."` → cria/atualiza **PRs** conforme `source`/`target` do YAML. **Convenção do `PR_TITLE`:** promoção de release = `[Hotfix]`/`[Release] <versão>`; **pós-deploy** (master → develop/stage/prerelease) = **`Sync Master`** (padrão).
  - `make run-triggers` → dispara os **triggers Cloud Build** (deploy nos ambientes dos clientes). **NÃO recebe `PR_TITLE`.** Disparado pelo Optimus Prime **sob comando explícito do Ronan**; a **aprovação do build no GCP** é do Ronan (após OK do QA).
  - Saída é **`chave=valor` parseável**; **exit code 0 = ok, 1 = erro** (usar para o gate).
  - **Branches (confirmar grafia exata):** `prerelease` → `teste_regressivo` → `master`. `make run` **sempre com `target` explícito**; trocar `source`/`targets` por passo é via **edição do YAML** (comentar/descomentar), ativando **só os repos da doc do Notion**.
- **`repos.yaml`** (na raiz do sync tool): manter **`auto_merge=false`**; **descomente** só os repos da doc. **Edição = só toggle de `#`; nunca reescrever.**

---

## 5. Documentação de erro / refino

- Cada erro → um arquivo **`erros/AAAA-MM-DD-<slug>.md`** no repo: comando + parâmetros, exit code, `motivo` (da saída chave=valor), trecho de stdout/stderr, etapa/skill onde ocorreu, e **hipótese**.
- O **resumo da execução** referencia os erros do dia.
- **Refino:** o Ronan revisa o `.md`; **só com o OK dele** a skill/comando que causou o erro é atualizada, e a melhoria é registrada. Erros viram base para deixar a esteira correta, limpa, segura e rápida.

---

## 6. Evolução / próximos papéis (este escopo vai crescer)

- Skill **`notificador`** de verdade (envio a dev/PO/QA por canal oficial).
- **Leitura diária multi-board** (incidents + features + refatoração): varrer cards em "Teste regressivo"/"Pronto para deploy" com conclusão correta e montar todo dia (amplia o `coletor`).
- Estudar (com o Ronan) se um dia o Optimus Prime poderá mergear/deployar com segurança.
- Trocar as ferramentas sem mudar o papel: reescrever apenas "Configuração atual".
- **Lean Loop (redução de custo):** mover I/O pesado (coleta do Jira, escrita dos `execucoes/*.json`) para passos determinísticos estilo `make` (como o Sync já é), deixando o LLM só para julgamento. Ver plano com o Ronan.
