# Backup imutavel do repos.yaml (sync-repos-from-master)

Este `repos.yaml` e o CATALOGO CANONICO e IMUTAVEL. Fonte da verdade para restaurar o
`repos.yaml` de trabalho em /home/ronan/sync-repos-from-master/repos.yaml.

Regras:
- Este arquivo NUNCA e editado pelo Optimus Prime.
- So CRESCE: quando surgir um repo/trigger novo, o usuário adiciona aqui (comentado).
- Todos os repos/triggers ficam COMENTADOS por padrao.
- O Optimus so alterna o '#' no arquivo de TRABALHO (a copia no sync-repos-from-master),
  nunca aqui.

Restaurar o arquivo de trabalho a partir deste backup:
    cp reference/sync-repos-from-master/repos.yaml /home/ronan/sync-repos-from-master/repos.yaml

Conteudo = o repos.yaml REAL do sync-repos-from-master, fornecido pelo usuário (o mais proximo do
original). Substitui a reconstrucao anterior (que era inferida dos execucoes/*.json e tinha lacunas:
faltavam bi-api e catraca; contractweb-api/analysis-api/relatorios/sla-api estavam sem triggers).
