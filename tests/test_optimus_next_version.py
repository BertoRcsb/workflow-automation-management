"""Testes de tools/optimus_next_version.py (GATE-VER-1/2)."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "optimus_next_version.py"


def run(stdin_text):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "-"],
        input=stdin_text, capture_output=True, text=True,
    )


def test_maior_numerico_nao_lexicografico():
    # 1.9.0 < 1.10.0 numericamente (lexicografico erraria)
    r = run('{"v": ["1.9.0", "1.10.0", "1.2.3"]}')
    assert r.returncode == 0
    assert "maior=1.10.0" in r.stdout and "proxima=1.11.0" in r.stdout


def test_hotfix_nao_muda_a_proxima_release():
    r = run("1.118.0 1.119.0 1.119.1 1.115.1")
    assert r.returncode == 0
    assert "maior=1.119.1" in r.stdout and "proxima=1.120.0" in r.stdout


def test_dump_sem_versao_falha():
    r = run("nenhuma versao aqui")
    assert r.returncode == 1 and "nenhuma_versao_encontrada" in r.stdout


def test_dedup_e_ordenacao():
    r = run("1.119.0 1.119.0 1.118.0")
    assert r.returncode == 0
    assert "versoes_na_base=2" in r.stdout
