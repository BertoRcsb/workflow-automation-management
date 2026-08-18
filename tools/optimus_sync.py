#!/usr/bin/env python3
"""optimus_sync.py - driver unico da coreografia do Sync (um comando por etapa).

Encadeia, na ordem certa e com tratamento de erro, o que antes era prosa nas skills:
backup -> GATE-YAML -> GATE-PROMO -> GATE-TRIGGERS -> make. Em falha de gate de
edicao, restaura o backup; em qualquer falha, documenta em erros/ e para (exit 1).
O LLM lembra de DOIS comandos (backup antes de editar; a acao depois) e le a saida.

Uso (cwd = workflow-automation-management; NUNCA cd no sync):
    python3 tools/optimus_sync.py backup
    python3 tools/optimus_sync.py dry-run  --step <passo1|passo2|pos-deploy> [--pr-title "..."]
    python3 tools/optimus_sync.py run      --step <passo1|passo2|pos-deploy> --pr-title "..."
    python3 tools/optimus_sync.py dry-run-triggers
    python3 tools/optimus_sync.py run-triggers

Governanca inalterada: `run` e `run-triggers` continuam sendo executados SO sob
comando explicito do Ronan - o script nao decide, so garante os gates.

Saida em chave=valor + exit code (0 = ok / 1 = falha), no padrao dos gates.
"""
import datetime
import os
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


def _run(cmd, **kw):
    """Roda um comando capturando stdout+stderr. Retorna (exit_code, saida)."""
    proc = subprocess.run(cmd, capture_output=True, text=True, **kw)
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

    code, out = _run(make_cmd)
    if code != 0:
        return fail(slug + "-make", f"make {action}", make_cmd, code, out, restore=False)
    print(out)
    print(f"ok=true acao={action}" + (f" step={step}" if step else ""))
    return 0


def main(argv):
    args = argv[1:]
    if not args:
        print("ok=false motivo=uso_invalido esperado='backup | dry-run | run | dry-run-triggers | run-triggers'")
        return 1
    action = args[0]
    step = None
    pr_title = None
    i = 1
    while i < len(args):
        if args[i] == "--step" and i + 1 < len(args):
            i += 1
            step = args[i]
        elif args[i] == "--pr-title" and i + 1 < len(args):
            i += 1
            pr_title = args[i]
        i += 1

    if action == "backup":
        return cmd_backup()
    if action in PR_ACTIONS | TRIGGER_ACTIONS:
        return cmd_action(action, step, pr_title)
    print(f"ok=false motivo=acao_desconhecida:{action}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
