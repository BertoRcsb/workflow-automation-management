import subprocess
import sys
from pathlib import Path

GATE = Path(__file__).resolve().parents[1] / "tools" / "optimus_yaml_gate.py"


def run_gate(tmp_path, before_text, after_text):
    before = tmp_path / "antes.yaml"
    after = tmp_path / "depois.yaml"
    before.write_text(before_text, encoding="utf-8")
    after.write_text(after_text, encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(GATE), str(before), str(after)],
        capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout


BASE = """repos:
  # - name: contractweb-v3
  #   repository: bernhoeft/contractweb-v3
  # - name: bernhoeft-grt-login-api
  #   repository: bernhoeft/bernhoeft-grt-login-api
"""


def test_descomentar_repo_passa(tmp_path):
    after = BASE.replace(
        "  # - name: contractweb-v3\n  #   repository: bernhoeft/contractweb-v3\n",
        "  - name: contractweb-v3\n    repository: bernhoeft/contractweb-v3\n",
    )
    code, out = run_gate(tmp_path, BASE, after)
    assert code == 0, out


def test_mudar_valor_falha(tmp_path):
    after = BASE.replace("bernhoeft/contractweb-v3", "bernhoeft/OUTRO-repo")
    code, out = run_gate(tmp_path, BASE, after)
    assert code == 1, out


def test_linha_nova_falha(tmp_path):
    after = BASE + "  - name: repo-inventado\n    repository: bernhoeft/repo-inventado\n"
    code, out = run_gate(tmp_path, BASE, after)
    assert code == 1, out


def test_remover_linha_falha(tmp_path):
    after = BASE.replace(
        "  # - name: bernhoeft-grt-login-api\n  #   repository: bernhoeft/bernhoeft-grt-login-api\n",
        "",
    )
    code, out = run_gate(tmp_path, BASE, after)
    assert code == 1, out
