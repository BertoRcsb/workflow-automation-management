#!/usr/bin/env python3
"""optimus_triggers_gate.py - GATE-TRIGGERS: valida o estado dos blocos `triggers:`.

Os `triggers:` do `repos.yaml` do sync-repos-from-master so devem estar ATIVOS
(descomentados) quando a operacao for o Passo 3 (`make dry-run-triggers` /
`make run-triggers`). Em qualquer operacao de sync de PRs (Passo 1, Passo 2,
pos-deploy: `make dry-run` / `make run`) os triggers TEM de estar comentados -
senao um disparo acidental sobe build em ambiente de cliente fora de hora.

Nem o GATE-YAML nem o GATE-PROMO enxergam isso: o GATE-YAML trata o toggle de
`triggers:` como "so comentario" (legitimo) e o GATE-PROMO so olha source/targets.
Este gate cobre a lacuna (incidente 2026-08-12: `newcontract-front` ficou com
triggers ativos no Passo 2, resquicio do hotfix 1.118.1).

Invariantes:
  --expect none    (Passo 1/2/pos-deploy): exit 1 se HOUVER qualquer trigger ativo.
  --expect present (Passo 3):              exit 1 se NAO houver trigger ativo,
                                           ou se houver trigger orfao (ativo sob
                                           um repo comentado).

Parser deterministico (sem PyYAML), no estilo dos outros gates. Distingue o
`- name:` de repo (indent 2) do `- name:` de trigger (indent >= 6) e o header
`triggers:` (indent 4). Para linhas comentadas, remove 1 `#` de comando e conta
a indentacao logica, de forma que a estrutura comentada tambem seja legivel.

Uso:
    python3 tools/optimus_triggers_gate.py <repos.yaml> --expect <none|present>

Saida em chave=valor + exit code (0 = ok / 1 = violacao), no padrao dos outros gates.
"""
import sys


def _parse_line(raw):
    """Retorna (commented, indent_logico, texto_strip) de uma linha do catalogo.

    Para linhas comentadas remove UM '#' de comando antes de medir a indentacao,
    de modo que `#  - name:` (repo) e `#      - name:` (trigger) fiquem distinguiveis
    pela indentacao logica, igual as linhas ativas.
    """
    lstripped = raw.lstrip()
    if lstripped.startswith("#"):
        commented = True
        body = lstripped[1:]  # remove o '#' de comando
    else:
        commented = False
        body = raw
    indent = len(body) - len(body.lstrip(" "))
    return commented, indent, body.strip()


def scan(path):
    """Varre o repos.yaml e devolve (triggers_ativos, repos_com_trigger_ativo, orfaos).

    - trigger ativo = header `triggers:` OU item `- name:` (indent >= 6) NAO comentado.
    - repo corrente = ultimo header `- name:` (indent 2), com seu estado (ativo/comentado).
    - orfao = trigger ativo cujo repo corrente esta comentado.
    """
    ativos = 0
    repos_ativos_com_trigger = []
    orfaos = []
    repo_atual = None
    repo_atual_ativo = None

    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line.strip():
                continue
            commented, indent, text = _parse_line(line)

            # Header de repo (indent 2): abre um novo contexto de repositorio.
            if text.startswith("- name:") and indent == 2:
                repo_atual = text.split(":", 1)[1].strip()
                repo_atual_ativo = not commented
                continue

            # Trigger: header `triggers:` (indent 4) ou item `- name:` (indent >= 6).
            eh_trigger = text == "triggers:" or (text.startswith("- name:") and indent >= 6)
            if eh_trigger and not commented:
                ativos += 1
                if repo_atual_ativo is False and repo_atual not in orfaos:
                    orfaos.append(repo_atual)
                if text.startswith("- name:") and repo_atual_ativo and repo_atual not in repos_ativos_com_trigger:
                    repos_ativos_com_trigger.append(repo_atual)

    return ativos, repos_ativos_com_trigger, orfaos


def evaluate(path, expect):
    ativos, repos, orfaos = scan(path)
    det = {"triggers_ativos": ativos, "repos": ",".join(repos) or "-"}
    if orfaos:
        det["orfaos"] = ",".join(orfaos)

    if expect == "none":
        if ativos > 0:
            return False, "triggers_ativos_fora_do_passo3", det
        return True, "sem_triggers_ativos", det

    if expect == "present":
        if ativos == 0:
            return False, "nenhum_trigger_ativo_para_passo3", det
        if orfaos:
            return False, "trigger_orfao_sob_repo_comentado", det
        return True, "triggers_ativos_ok", det

    return False, f"expect_invalido:{expect}", det


def main(argv):
    args = argv[1:]
    path = None
    expect = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--expect":
            i += 1
            expect = args[i] if i < len(args) else None
        elif path is None:
            path = a
        i += 1

    if not path or expect not in ("none", "present"):
        print("ok=false motivo=uso_invalido esperado='<repos.yaml> --expect <none|present>'")
        return 1

    ok, motivo, det = evaluate(path, expect)
    campos = " ".join(f"{k}={v}" for k, v in det.items())
    print(f"ok={'true' if ok else 'false'} motivo={motivo} expect={expect} {campos}".rstrip())
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
