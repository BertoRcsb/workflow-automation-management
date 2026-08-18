# Roadmap — evolução dos papéis (fonte única)

> Consolidação das seções "Evolução / próximos papéis" que ficavam dentro de cada skill (removidas de
> lá: skill é instrução executável, não backlog). Toda mudança de skill/comando = **só com OK do usuário**.

## Coletor
- Ler PR do **painel Development** quando o campo estiver vazio (complementa a "PR por referência de card").
- Extrair o **nome do proc** da descrição (cards só-banco).
- Incluir `issuetype = Bug` na coleta (hoje fora do mapeamento — pendente de OK).
- Outras fontes/ciclos: outros projetos, issue types, Bitbucket/GitHub direto.

## Validador
- **Revalidar** cards corrigidos.
- **Categorias** (correção · banco · infra · melhoria · alteração técnica · pós-deploy).
- Regras distintas por **tipo de ciclo**.
- Refino do falso-positivo de `parse_failed` para placeholders sem inlineCard ("APENAS PROC"/"N/A")
  — aplicar só após concluir a 1.120.0, com OK do usuário.

## Montador
- **Categorias** na tabela/release.
- **Nome do proc** nas linhas só-banco.
- Preencher **Merge / Infra** quando a origem do dado estiver definida.

## Orquestrador / esteira
- Skill **`notificador`** de verdade (envio a dev/PO/QA por canal oficial — hoje sandbox).
- **Leitura diária multi-board** com montagem automática.
- **Paralelismo** entre subagentes independentes.
- Estudar (com o usuário) se um dia o Optimus poderá mergear/deployar com segurança.
- **Lean Loop (redução de custo):** mover I/O pesado (coleta do Jira, escrita dos `execucoes/*.json`)
  para passos determinísticos estilo `make`, deixando o LLM só para julgamento.
- GATE-CONJUNTO e GATE-LINKS como código (ver `GATES.md`).
- Integração com CI/CD (hoje manual via usuário).

## Princípio de troca de ferramenta
Cada papel é agnóstico: trocar Jira/Notion/sync = reescrever só a seção "Configuração atual" da skill,
nunca o papel.
