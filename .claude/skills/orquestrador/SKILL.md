---
name: orquestrador
description: >-
  Use quando o usuário quer conduzir a esteira de release notes de ponta a ponta
  — coordenar coletor → validador → montador → notificador e acionar o deploy via
  sync-repos-from-master, com segurança por ação e aprovação humana. Gatilhos:
  "Optimus Prime", "Optimus Prime iniciar", "Optimus Prime verificar", "Optimus Prime executar",
  "Optimus Prime verificar todos os boards", "Optimus Prime iniciar todos os boards", "iniciar
  deploy", "montar e preparar a release", "rodar a esteira". Contexto atual: MCPs
  Atlassian + Notion e comandos `make` do sync-repos-from-master; papel agnóstico.
---

# Orquestrador — "Optimus Prime"

O **maestro** da esteira: governa as skills (`coletor` → `validador` → `montador`
→ `notificador`) e o **`sync-repos-from-master`**, cuidando das transições, dos
**gates de segurança** e da **rastreabilidade**. É acionado pelo comando **"Optimus
Prime"**. **Agnóstico de ferramenta**: hoje orquestra MCPs + `make`, mas o papel
não muda se as ferramentas mudarem — para trocar, reescreva só "Configuração atual".

> Fonte da verdade do projeto: `spec/spec.md`. Esta skill é a versão operacional/executável deste papel.

## Responsabilidade (única)
- **Coordenar** os papéis na ordem certa e passar o contrato normalizado (§7) entre eles.
- Impor **segurança por ação** e **aprovação humana** nos passos que mudam algo.
- **Consolidar** o resultado (resumo §9) e **documentar erros** para refino.
- **Não** faz o trabalho dos outros papéis (não coleta/valida/monta/notifica por conta
  própria — sempre delega às skills). **Não** mergeia nem faz deploy real (é do Ronan).

## Modos (verificar / executar)
- **`verificar`** — **apresenta ANTES o que vai fazer** (todos os passos + os comandos que rodaria),
  **sem executar NENHUM comando** que mude algo: `coletor` (leitura) → `validador` → **rascunho**
  (aprovados × reprovados) → simula o Notion e mostra o alvo do Sync (`repos.yaml` + `make dry-run`).
  Entrega só **relatório/plano**.
- **`executar`** (board único) — roda a esteira **autônoma até o `make dry-run` do Sync Passo 1**:
  versão-alvo (automática) → `coletor` → `validador` → `montador` **cria/atualiza o Notion (real) sem
  pedir aprovação** → `notificador` (sandbox) → **Sync** (edita o `repos.yaml` e roda `make dry-run`).
  Ao terminar (dry-run limpo), emite a **mensagem única `Confira`** e **para**. **A única pausa antes
  disso é card genuinamente ambíguo** (ver passo 3). **O `make run` do Passo 1** (abre os PRs pré-prod),
  merge, **master (Passo 2)** e **triggers (Passo 3)** seguem **sob comando explícito do Ronan**. No alvo
  **`todos os boards`**, a varredura ainda **termina no Notion** (Sync por-board e explícito, depois).

> **"Optimus Prime iniciar"** (ou só **"iniciar"**) = modo **`executar`**.

### Alvo da varredura: um board × "todos os boards"
O **alvo** é parâmetro (separado do modo). Sem alvo, o Optimus **pergunta** qual board.
- **`<board>`** (incidentes | features | refatoração) — roda **um** board (comportamento de sempre).
- **`todos os boards`** — varre os três **em sequência, na ordem de prioridade do registro do
  `coletor` (incidentes SEMPRE 1º)**. Cada board é **totalmente isolado**: sua própria coleta →
  validação → versão-alvo → **sua própria página no Notion** (release/hotfix por board). **NUNCA**
  se misturam cards de boards diferentes (invariante §5.1 — a varredura reforça a regra, não a viola).
  - A varredura **termina no Notion**: o **Sync** (`repos.yaml` + `make run`) **não** entra no loop —
    segue **por-board e explícito**, como hoje (deploys em dias diferentes, incidentes primeiro).
  - **Board sem mapeamento** → **pula e reporta** naquele bloco; os demais seguem normalmente. Definir
    filtro = descoberta via MCP + OK do Ronan (ver `coletor`, "Registro de boards"). **Nunca inventar JQL.**
  - Combina com os dois modos: **`verificar todos os boards`** (dry, só relatório — um bloco por board)
    e **`iniciar todos os boards`** (executa até o Notion de cada board, com os gates por ação).
  - **Ordem/prioridade:** 1º **Linha de frente/incidentes** (`Incidente`) → 2º **Features** (`Story`)
    → 3º **Refatoração** (`Story`, menos importante). Mapeamento e JQL: ver `coletor`, "Registro de boards".
  - **Features × Refatoração** (ambos `Story`) são separados **pelo título**: **Refatoração** = título
    contém "Refatoração" (`summary ~ "Refatoração"`); **Features** = o complemento (`summary !~ ...`).
    Blocos distintos, sem sobreposição. Se um card cair no board errado → refino do filtro (com OK do
    Ronan); **nunca inventar** outro critério. Ver `coletor`, "Registro de boards".

## Sequência e gates (base spec §6)
> No alvo **`todos os boards`**, os passos **1–5 e 7 rodam por board** (em ordem de prioridade,
> incidentes 1º), **isolados**; o passo **6 (Sync)** fica **fora do loop** (por-board e explícito, depois).
> A versão-alvo é atribuída **automaticamente por board** como **`Release` sequencial** (`X.(Y+1).0`);
> **incidente NÃO é hotfix por padrão** (é release comum) — hotfix só quando o Ronan avisar.

1. **Versão-alvo (automática):** lê a última versão no Notion e atribui a **próxima `X.(Y+1).0` como
   `Release`** por board, em ordem de prioridade (incidentes 1º). **Incidente NÃO é hotfix por padrão**
   (é release comum); **hotfix só quando o Ronan avisar**. Não pausa.
2. **Coletor** → cards do Jira normalizados (§7).  · gate: erro de leitura → documenta e **para**.
3. **Validador** → aprovados × reprovados (regra v2 + heurística "só-banco"). **Segue sozinho nos casos
   claros** (sem checkpoint de rascunho). · **pausa SÓ em card genuinamente ambíguo** (heurística
   só-banco não fecha, ou dado divergente tipo repo≠PR): aí pergunta ao Ronan — **nunca inventa**.
4. **Montador** → **cria/atualiza a página no Notion no molde sem pedir OK** e **re-verifica via
   re-fetch** (colunas iguais às versões anteriores).  · gate: divergência no re-fetch → documenta e **para**.
5. **Notificador (sandbox)** → gera as mensagens de pendência/deploy p/ dev/PO/QA; **mostra só
   pro Ronan** (envio automático pendente até a skill `notificador` existir).
6. **Sync (`sync-repos-from-master`)** — governança do `repos.yaml`, **guiada pela documentação**:
   - **Lê o doc da versão no Notion** e ativa no `repos.yaml` **apenas os repositórios que constam em
     "Repositórios para Deploy"** — ativando **só `name` + `repository`**; **os `triggers:` ficam
     comentados** (triggers são do **Passo 3**/prod, disparados só após OK do PO/QA — o `make run` do
     Passo 1/2 **não os usa**). **Tudo que não corresponder → comenta de volta** (não entra no
     `make run`). **Repo faltando no YAML → para e reporta** (Ronan adiciona).
   - **Editar o `repos.yaml` é autônomo** (guiado pela doc do Notion): **não pergunta a cada alteração**,
     **não pede OK para ler/editar** — só interrompe/reporta em caso de **discrepância** (repo faltando no
     YAML, doc ambígua). O `make dry-run` também é autônomo (simulação); o **gate humano** é **todo `make
     run`**: Passo 1, master (Passo 2) e triggers (Passo 3).
   - **Fluxo de promoção (NUNCA direto pra master; `make run` sempre com `target` explícito):**
     - **Passo 1** — `source: prerelease` → `target: teste_regressivo` (pré-prod): ajusta o YAML,
       `make dry-run` e **parseia**; **erro (exit 1) → documenta em `erros/` e para**; **limpo (exit 0) →
       emite a mensagem `Confira` e para**. **O `make run`** (abre os PRs) só **sob OK explícito do
       Ronan**, depois da mensagem. Merge é do Ronan.
     - **Passo 2** — `source: teste_regressivo` → `target: master` (prod): **só sob comando/override
       explícito do Ronan**. Por padrão o Optimus Prime edita o YAML e roda `make dry-run`; o **`make run`
       de master só quando o Ronan mandar explicitamente**.
     - **Passo 3** — **`make run-triggers`** (dispara os triggers Cloud Build → deploy nos ambientes
       dos clientes; **NÃO recebe `PR_TITLE`**). O Optimus Prime pode **disparar** sob **comando
       explícito** do Ronan; **quais** triggers vêm de **instrução do Ronan + os `triggers:` do
       `repos.yaml`** (ainda **não** estão no Notion). A **aprovação do build no GCP é do Ronan**,
       após OK do QA. Ex. (autocadastro-front): `neoenergia-front-autocadastro`, `vli-front-autocadastro`.
     - **Pós-deploy (sync de volta)** — depois do deploy, sincroniza **master → develop, stage,
       prerelease**: edita o YAML (`source: master`, `targets: [develop, stage, prerelease]`),
       `make dry-run` → OK → **`make run PR_TITLE="Sync Master"`** (título **padrão** desse passo).
       Cria os PRs; **merges do Ronan**.
   - **Governança:** master/prod, merges e aprovação de build = **sempre do Ronan**; o Optimus Prime
     **pergunta antes** de master (Passo 2) e das triggers (Passo 3).
7. **Fechamento** → salva o resumo consolidado (§9) em `execucoes/` (trilha de auditoria em disco) e
   emite ao Ronan **uma única mensagem de fechamento** (ver "Mensagem única de retorno").

## Mensagem única de retorno (contrato de confiança)
No `executar`, ao concluir **todo o escopo autônomo** — cards conferidos → Notion montado e conferido com
**TODOS** os links reais → `repos.yaml` editado → `make dry-run` do Passo 1 **limpo** — o Optimus emite
**exatamente uma** mensagem de fechamento, começando pela linha exata:

```
Optimus Prime retornando com o resultado = Confira
```

- É a **única saída conversacional de fechamento**: execução **silenciosa**, sem relatórios verbosos nem
  perguntas de "posso avançar?" pelo caminho. Só **card genuinamente ambíguo** (passo 3) e **paradas por
  erro** (documenta em `erros/` e para) interrompem.
- **Na mesma** mensagem, logo abaixo da linha, listar os artefatos para o Ronan conferir: **URL da página
  no Notion**, **repos ativados no `repos.yaml`** e o **resultado do `make dry-run`** do Passo 1.
- **Contrato de confiança:** o Optimus só emite essa linha depois de ter **lido, conferido e montado
  certo**; o Ronan **confere depois** da mensagem (a linha é o sinal de "escopo autônomo concluído").
- **O `make run` do Passo 1** (abre os PRs pré-prod) só roda **depois**, sob **OK explícito do Ronan**.
- No alvo **`todos os boards`**, o escopo autônomo **termina no Notion** → a mensagem sai **por board**,
  ao fim de cada bloco (o Sync fica fora do loop).
- **`verificar`** (dry) **não** emite essa linha — entrega só o relatório/plano.

## Configuração atual — MCPs + `make` do sync-repos-from-master
- **Skills irmãs** (delegar, nunca reimplementar): `coletor`, `validador`, `montador`
  (+ `notificador` quando existir).
- **MCPs:** Atlassian (leitura de cards, `read:jira-work`) e Notion (base "Versões - NewContract").
- **Deploy tool:** `sync-repos-from-master` — **repo separado** (não faz parte deste repo). Caminho via
  env **`SYNC_REPO_PATH`**; default: repo-irmão **`../sync-repos-from-master`**. Makefile. Comandos:
  - `make dry-run [PR_TITLE="..."]` / `make dry-run-triggers` → **simulação segura** (sempre antes).
  - `make run PR_TITLE="..."` → cria/atualiza **PRs** conforme `source`/`target` do YAML. **Convenção do
    `PR_TITLE`:** promoção de release = `[Hotfix]`/`[Release] <versão>`; **pós-deploy** (master →
    develop/stage/prerelease) = **`Sync Master`** (padrão).
  - `make run-triggers` → dispara os **triggers Cloud Build** (deploy nos ambientes dos clientes).
    **NÃO recebe `PR_TITLE`.** Disparado pelo Optimus Prime **sob comando explícito do Ronan**; a
    **aprovação do build no GCP** é do Ronan (após OK do QA).
  - Saída é **`chave=valor` parseável**; **exit code 0 = ok, 1 = erro** (usar para o gate).
  - **Branches (confirmar grafia exata):** `prerelease` → `teste_regressivo` → `master`. `make run`
    **sempre com `target` explícito**; trocar `source`/`targets` por passo é via **edição do YAML**
    (comentar/descomentar), ativando **só os repos da doc do Notion**.
- **`repos.yaml`** (na raiz do sync tool): manter **`auto_merge=false`**; descomentar só o repo alvo.

## Modelo & custo (troca automática por skill)
A esteira é **majoritariamente mecânica** (orquestrar MCPs + parsear/escrever) → **roda no modelo mais
barato por padrão (ex.: Haiku)**. Só **um ponto exige julgamento fino**: validar **card ambíguo**.
- **Padrão barato:** `coletor` e `montador` (trabalho mecânico) ficam no modelo barato.
- **Escala só na ambiguidade:** ao bater num card ambíguo (heurística só-banco não fecha, ou repo ≠ PR),
  o Optimus **pausa e pede o veredito ao Ronan** — que decide ali (ou sobe pra um modelo mais forte, se quiser).
- **Como a skill "troca" de modelo:** cada skill declara seu **"Modelo sugerido"** (padrão = barato); a
  escalada é **explícita** (a pausa do card ambíguo). *(Evolução opcional: delegar as etapas mecânicas a
  um subagente no modelo barato, mantendo o julgamento no principal — só quando não arriscar o funcionamento.)*
- **Regra de ouro:** **desempenho atual vem primeiro.** Economizar modelo/token **nunca** pode quebrar
  ou degradar a esteira; na dúvida, **mantém como está**.

## Guardrails (diretrizes inquebráveis)
- **MERGE é só do Ronan** — Optimus Prime **nunca** mergeia (garantia: `auto_merge=false`).
- **Master/prod = governança do Ronan.** **Sempre pergunte/confirme antes** de ir pra master
  (Passo 2) e antes de disparar triggers (Passo 3). Pode **disparar** triggers sob comando explícito,
  mas a **aprovação do build no GCP é do Ronan** (após OK do QA).
- **Autonomia até o `make dry-run` do Sync Passo 1** (board único): no `executar`, os passos rodam **sem
  aprovação humana** — inclui criar a doc no Notion, editar o `repos.yaml` e rodar o `make dry-run` do
  Passo 1 — e terminam na mensagem `Confira`. **O `make run` do Passo 1 (abre os PRs) é sob OK explícito
  do Ronan.** **Única pausa antes disso:** card genuinamente ambíguo (passo 3). No alvo `todos os boards`,
  ainda **termina no Notion**.
- **Segurança por ação:** toda ação do `sync-repos-from-master` roda antes em **dry-run** (parseia saída
  + exit code); erro → documenta e **para**. **Todo `make run` (Passo 1 e Passo 2) e triggers (Passo 3):**
  limpo → mostra e espera **comando explícito** do Ronan antes do real. O `make dry-run` e a edição do
  `repos.yaml` são autônomos.
- **Todo erro documentado**; refino de skill/comando **só com aprovação do Ronan** (sem correção
  silenciosa). Ver [[regra-nao-executar-sozinho]].
- **Não inventar dado ausente** (§11); privilégio mínimo (Jira leitura; Notion só a base).
- **Hotfix** → identificar e **devolver ao Ronan** para ele conduzir.
- **Um board por vez** — coletar de UM board (incidentes/features/refatoração) por execução;
  **nunca misturar** numa release. Misturar só com **OK explícito do Ronan**.
- **`verificar` nunca executa** — só apresenta o plano (o que faria); execução real só em
  `executar`/`iniciar`.
- **Execução silenciosa + mensagem única:** no `executar`, nada de relatórios verbosos ou "posso
  avançar?" pelo caminho; ao fim do escopo autônomo, **uma só** mensagem — `Optimus Prime retornando com
  o resultado = Confira` + os links dos artefatos (ver "Mensagem única de retorno").

## Documentação de erro / refino
- Cada erro → um arquivo **`erros/AAAA-MM-DD-<slug>.md`** no repo: comando + parâmetros, exit code,
  `motivo` (da saída chave=valor), trecho de stdout/stderr, etapa/skill onde ocorreu, e **hipótese**.
- O **resumo da execução** referencia os erros do dia.
- **Refino:** o Ronan revisa o `.md`; **só com o OK dele** a skill/comando que causou o erro é
  atualizada, e a melhoria é registrada. Erros viram base para deixar a esteira correta, limpa,
  segura e rápida.

## Evolução / próximos papéis (este escopo vai crescer)
- Skill **`notificador`** de verdade (envio a dev/PO/QA por canal oficial).
- **Leitura diária multi-board** (incidents + features + refatoração): varrer cards em "Teste
  regressivo"/"Pronto para deploy" com conclusão correta e montar todo dia (amplia o `coletor`).
- Estudar (com o Ronan) se um dia o Optimus Prime poderá mergear/deployar com segurança.
- Trocar as ferramentas sem mudar o papel: reescrever apenas "Configuração atual".
