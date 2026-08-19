#!/usr/bin/env python3
"""optimus_sync.py - driver unico da coreografia do Sync (um comando por etapa).

Encadeia, na ordem certa e com tratamento de erro, o que antes era prosa nas skills:
backup -> GATE-YAML -> GATE-PROMO -> GATE-TRIGGERS -> make. Em falha de gate de
edicao, restaura o backup; em qualquer falha, documenta em erros/ e para (exit 1).
O LLM lembra de DOIS comandos (backup antes de editar; a acao depois) e le a saida.

Uso (cwd = workflow-automation-management; NUNCA cd no sync):
    python3 tools/optimus_sync.py backup
    python3 tools/optimus_sync.py configure --step <passo1|passo2|pos-deploy> --repos <nome1,nome2,...>
    python3 tools/optimus_sync.py dry-run  --step <passo1|passo2|pos-deploy> [--pr-title "..."]
    python3 tools/optimus_sync.py run      --step <passo1|passo2|pos-deploy> --pr-title "..."
    python3 tools/optimus_sync.py dry-run-triggers
    python3 tools/optimus_sync.py run-triggers

`configure` (incidente 2026-08-19: edicao manual do YAML pelo LLM deletou linhas e
quebrou o GATE-YAML) edita o repos.yaml DETERMINISTICAMENTE: faz backup, ajusta o
escalar defaults.source e alterna APENAS o `#` das linhas de targets e dos pares
name+repository (triggers sempre comentados), lendo source/targets canonicos de
tools/promotion.json. Nunca cria/remove/reescreve linha; repo fora do catalogo =
exit 1 (o usuario adiciona). Ao final valida a si mesmo com o GATE-YAML.
O LLM NAO edita o repos.yaml na mao: usa configure.

Governanca inalterada: `run` e `run-triggers` continuam sendo executados SO sob
comando explicito do Ronan - o script nao decide, so garante os gates.

Saida em chave=valor + exit code (0 = ok / 1 = falha), no padrao dos gates.
"""
import datetime
import json
import os
import re
import shutil
import subprocess
import sys

WORKFLOW_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(WORKFLOW_ROOT, "tools")
BACKUP = os.path.join(WORKFLOW_ROOT, "execucoes", "repos.yaml.optimus-bak")

# Gates de PR-sync (dry-run/run): triggers TEM de estar comentados (--expect none).
# Gates de triggers (Passo 3): triggers TEM de estar ativos (--expect present).
PR_ACTIONS = {"dry-run", "run"}
TRIGGER_ACTIONS = {"dry-run-triggers", "run-triggers"}
STEPS = ("passo1", "passo2", "pos-deploy")


def sync_repo_path():
    return os.environ.get(
        "SYNC_REPO_PATH",
        os.path.join(os.path.dirname(WORKFLOW_ROOT), "sync-repos-from-master"),
    )


def repos_yaml():
    return os.path.join(sync_repo_path(), "repos.yaml")


def _run(cmd, clean_env=False, **kw):
    """Roda um comando capturando stdout+stderr. Retorna (exit_code, saida).

    clean_env=True remove o venv do workflow do ambiente (VIRTUAL_ENV + PATH):
    sem isso, o `poetry run` do sync resolve para o venv ERRADO e o make falha
    com ModuleNotFoundError (incidente 2026-08-19). Determinismo > herdar shell.
    """
    env = None
    if clean_env:
        env = dict(os.environ)
        venv = env.pop("VIRTUAL_ENV", None)
        env.pop("PYTHONPATH", None)
        if venv:
            partes = [p for p in env.get("PATH", "").split(os.pathsep) if not p.startswith(venv)]
            env["PATH"] = os.pathsep.join(partes)
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env, **kw)
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out.strip()


def document_error(slug, etapa, cmd, code, saida):
    """Escreve erros/AAAA-MM-DD-<slug>.md no formato da REFERENCE secao 5."""
    dia = datetime.date.today().isoformat()
    erros_dir = os.path.join(WORKFLOW_ROOT, "erros")
    os.makedirs(erros_dir, exist_ok=True)
    path = os.path.join(erros_dir, f"{dia}-{slug}.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(f"# Erro no Sync - {etapa}\n\n")
        fh.write(f"- **Data:** {dia}\n")
        fh.write(f"- **Etapa:** {etapa}\n")
        fh.write(f"- **Comando:** `{' '.join(cmd)}`\n")
        fh.write(f"- **Exit code:** {code}\n\n")
        fh.write("## Saida\n\n```\n")
        fh.write(saida[-4000:] + "\n")
        fh.write("```\n\n## Hipotese\n\n(preencher na analise)\n")
    return os.path.relpath(path, WORKFLOW_ROOT)


def restore_backup():
    if os.path.exists(BACKUP):
        shutil.copyfile(BACKUP, repos_yaml())
        return True
    return False


def fail(slug, etapa, cmd, code, saida, restore):
    restored = restore_backup() if restore else False
    err_path = document_error(slug, etapa, cmd, code, saida)
    print(saida)
    print(f"ok=false etapa={etapa} exit={code} backup_restaurado={str(restored).lower()} erro_doc={err_path}")
    return 1


def gate(nome, cmd, slug, restore):
    """Roda um gate; falha -> restaura (se aplicavel), documenta e encerra com 1."""
    code, out = _run(cmd)
    if code != 0:
        return fail(slug, nome, cmd, code, out, restore)
    print(f"{nome}: {out}")
    return None


def cmd_backup():
    yaml = repos_yaml()
    if not os.path.exists(yaml):
        print(f"ok=false motivo=repos_yaml_nao_encontrado path={yaml}")
        return 1
    os.makedirs(os.path.dirname(BACKUP), exist_ok=True)
    shutil.copyfile(yaml, BACKUP)
    print(f"ok=true backup={os.path.relpath(BACKUP, WORKFLOW_ROOT)} origem={yaml}")
    return 0


# ---------------------------------------------------------------------------
# configure: edicao deterministica do repos.yaml (incidente 2026-08-19 - o LLM
# editava na mao, deletou linhas do bloco targets e quebrou o GATE-YAML).
# Regras identicas as do gate: so alterna '#' de linhas existentes + escalar
# defaults.source. Nunca cria, remove ou reescreve linha.
# ---------------------------------------------------------------------------

RE_SOURCE = re.compile(r"^(\s*source:\s+)(\S+)(\s*)$")           # defaults.source (com valor inline)
RE_TARGETS_HDR = re.compile(r"^\s*targets:\s*$")                  # header do bloco (descomentado)
RE_TARGET_ITEM = re.compile(r"^\s*#?\s*-\s+(\S+)\s*$")            # item do bloco targets
RE_REPO_NAME = re.compile(r"^#?\s{0,3}- name:\s*(\S+)\s*$")       # entrada de repo (indent raso)
RE_REPO_URL = re.compile(r"^#?\s{0,4}repository:\s*(\S+)\s*$")    # repository da entrada
RE_TRIGGERS_HDR = re.compile(r"^#?\s*triggers:\s*$")              # header de triggers
RE_TRIGGER_ITEM = re.compile(r"^#?\s{4,}- name:\s*\S+\s*$")       # item de trigger (indent fundo)


def _uncomment(line):
    """Remove o PRIMEIRO '#' da linha (toggle), preservando o resto."""
    return line.replace("#", "", 1) if "#" in line else line


def _comment(line):
    """Prefixa '#' na linha ativa (toggle)."""
    return line if line.lstrip().startswith("#") else "#" + line


def _load_step_config(step):
    with open(os.path.join(TOOLS, "promotion.json"), encoding="utf-8") as fh:
        promo = json.load(fh)
    cfg = promo.get("steps", {}).get(step)
    if not cfg:
        return None
    return cfg["source"], list(cfg["targets"])


def cmd_configure(step, repos_csv):
    yaml = repos_yaml()
    py = sys.executable or "python3"
    if step not in STEPS:
        print(f"ok=false motivo=step_invalido esperado={'|'.join(STEPS)}")
        return 1
    if not repos_csv:
        print("ok=false motivo=repos_ausentes esperado=--repos nome1,nome2 (da doc do Notion)")
        return 1
    if not os.path.exists(yaml):
        print(f"ok=false motivo=repos_yaml_nao_encontrado path={yaml}")
        return 1
    cfg = _load_step_config(step)
    if cfg is None:
        print(f"ok=false motivo=step_sem_config_em_promotion_json step={step}")
        return 1
    source_alvo, targets_alvo = cfg
    pedidos = {r.strip() for r in repos_csv.split(",") if r.strip()}

    # backup automatico ANTES de editar (mesmo arquivo que o dry-run/run espera)
    os.makedirs(os.path.dirname(BACKUP), exist_ok=True)
    shutil.copyfile(yaml, BACKUP)

    with open(yaml, encoding="utf-8") as fh:
        lines = fh.read().splitlines(keepends=True)

    out = []
    source_ok = False
    targets_vistos = set()
    repos_vistos = set()
    repos_ativados = []
    repos_desativados = []
    in_targets = False
    in_repos = False
    entrada_ativa = False  # a entrada de repo corrente deve ficar ativa?

    for line in lines:
        body = line.rstrip("\n")
        nl = line[len(body):]

        # --- escalar defaults.source (primeira ocorrencia com valor inline) ---
        m = RE_SOURCE.match(body)
        if m and not source_ok and not in_repos:
            out.append(f"{m.group(1)}{source_alvo}{m.group(3)}{nl}")
            source_ok = True
            continue

        # --- bloco targets (toggle de '#' por item) ---
        if not in_repos and RE_TARGETS_HDR.match(body):
            in_targets = True
            out.append(line)
            continue
        if in_targets:
            m = RE_TARGET_ITEM.match(body)
            if m:
                branch = m.group(1)
                targets_vistos.add(branch)
                out.append((_uncomment(body) if branch in targets_alvo else _comment(body)) + nl)
                continue
            in_targets = False  # primeira linha fora do padrao encerra o bloco

        # --- secao repos ---
        if body.strip() == "repos:":
            in_repos = True
            out.append(line)
            continue
        if in_repos:
            m = RE_REPO_NAME.match(body)
            if m:
                nome = m.group(1)
                repos_vistos.add(nome)
                entrada_ativa = nome in pedidos
                (repos_ativados if entrada_ativa else repos_desativados).append(nome)
                out.append((_uncomment(body) if entrada_ativa else _comment(body)) + nl)
                continue
            if RE_REPO_URL.match(body):
                out.append((_uncomment(body) if entrada_ativa else _comment(body)) + nl)
                continue
            if RE_TRIGGERS_HDR.match(body) or RE_TRIGGER_ITEM.match(body):
                out.append(_comment(body) + nl)  # triggers SEMPRE comentados (Passo 3 e via run-triggers)
                continue

        out.append(line)

    # --- validacoes fail-closed (antes de escrever) ---
    faltando_repos = pedidos - repos_vistos
    faltando_targets = [t for t in targets_alvo if t not in targets_vistos]
    problemas = []
    if not source_ok:
        problemas.append("source_nao_encontrado")
    if faltando_targets:
        problemas.append(f"target_fora_do_catalogo:{','.join(faltando_targets)}")
    if faltando_repos:
        problemas.append(f"repo_fora_do_catalogo:{','.join(sorted(faltando_repos))}")
    if problemas:
        print(f"ok=false etapa=configure motivo={' '.join(problemas)}")
        print("acao=parar_e_reportar (nunca criar linhas; o usuario adiciona no catalogo)")
        return 1

    with open(yaml, "w", encoding="utf-8") as fh:
        fh.writelines(out)

    # --- auto-verificacao com o GATE-YAML (mesma regra do dry-run/run) ---
    code, gout = _run([py, os.path.join(TOOLS, "optimus_yaml_gate.py"), BACKUP, yaml])
    if code != 0:
        return fail(f"sync-{step}-configure-gate-yaml", "GATE-YAML(configure)",
                    ["configure"], code, gout, restore=True)

    print(f"GATE-YAML: {gout}")
    print(f"ok=true acao=configure step={step} source={source_alvo} targets={','.join(targets_alvo)}")
    print(f"repos_ativos={','.join(repos_ativados) or '-'}")
    print(f"repos_desativados={len(repos_desativados)}")
    return 0


def cmd_action(action, step, pr_title):
    yaml = repos_yaml()
    py = sys.executable or "python3"

    if action in PR_ACTIONS:
        if step not in STEPS:
            print(f"ok=false motivo=step_invalido esperado={'|'.join(STEPS)}")
            return 1
        if not os.path.exists(BACKUP):
            print("ok=false motivo=backup_ausente rode='optimus_sync.py backup' ANTES de editar o repos.yaml")
            return 1
        slug = f"sync-{step}-{action}"
        # GATE-YAML: edicao foi so toggle de '#' (+ escalar defaults.source por passo).
        r = gate("GATE-YAML", [py, os.path.join(TOOLS, "optimus_yaml_gate.py"), BACKUP, yaml],
                 slug + "-gate-yaml", restore=True)
        if r is not None:
            return r
        # GATE-PROMO: par source->targets na whitelist e no passo esperado.
        r = gate("GATE-PROMO", [py, os.path.join(TOOLS, "optimus_promotion_gate.py"), yaml, "--step", step],
                 slug + "-gate-promo", restore=True)
        if r is not None:
            return r
        # GATE-TRIGGERS: nenhum trigger ativo fora do Passo 3.
        r = gate("GATE-TRIGGERS", [py, os.path.join(TOOLS, "optimus_triggers_gate.py"), yaml, "--expect", "none"],
                 slug + "-gate-triggers", restore=False)
        if r is not None:
            return r
        make_cmd = ["make", "-C", sync_repo_path(), action]
        if pr_title:
            make_cmd.append(f"PR_TITLE={pr_title}")
    else:  # TRIGGER_ACTIONS (Passo 3): sem PR_TITLE, sem --step
        slug = f"sync-passo3-{action}"
        # GATE-PROMO sem --step: valida que o par do YAML segue na whitelist.
        r = gate("GATE-PROMO", [py, os.path.join(TOOLS, "optimus_promotion_gate.py"), yaml],
                 slug + "-gate-promo", restore=False)
        if r is not None:
            return r
        # GATE-TRIGGERS: triggers presentes e sem orfao.
        r = gate("GATE-TRIGGERS", [py, os.path.join(TOOLS, "optimus_triggers_gate.py"), yaml, "--expect", "present"],
                 slug + "-gate-triggers", restore=False)
        if r is not None:
            return r
        make_cmd = ["make", "-C", sync_repo_path(), action]

    code, out = _run(make_cmd, clean_env=True)
    if code != 0:
        return fail(slug + "-make", f"make {action}", make_cmd, code, out, restore=False)
    print(out)
    print(f"ok=true acao={action}" + (f" step={step}" if step else ""))
    return 0


def main(argv):
    args = argv[1:]
    if not args:
        print("ok=false motivo=uso_invalido esperado='backup | configure | dry-run | run | dry-run-triggers | run-triggers'")
        return 1
    action = args[0]
    step = None
    pr_title = None
    repos_csv = None
    i = 1
    while i < len(args):
        if args[i] == "--step" and i + 1 < len(args):
            i += 1
            step = args[i]
        elif args[i] == "--pr-title" and i + 1 < len(args):
            i += 1
            pr_title = args[i]
        elif args[i] == "--repos" and i + 1 < len(args):
            i += 1
            repos_csv = args[i]
        i += 1

    if action == "backup":
        return cmd_backup()
    if action == "configure":
        return cmd_configure(step, repos_csv)
    if action in PR_ACTIONS | TRIGGER_ACTIONS:
        return cmd_action(action, step, pr_title)
    print(f"ok=false motivo=acao_desconhecida:{action}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
