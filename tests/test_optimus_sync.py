"""Testes do driver tools/optimus_sync.py (coreografia do Sync em um comando).

Usa um sync falso (repos.yaml minimo + Makefile stub) em tmp_path; o driver e
invocado como subprocesso, igual ao uso real. Artefatos (backup, erros/) vao
para o WORKFLOW real, entao cada teste limpa o que criou.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DRIVER = ROOT / "tools" / "optimus_sync.py"

REPOS_YAML_PASSO1 = """\
defaults:
  provider: bitbucket
  source:  prerelease
#  source:  teste_regressivo
  targets:
    - teste_regressivo
#    - master
  auto_merge: false

cloud_build:
  defaults:
     project_id: fake

repositories:
  - name: repo-a
    repository: bernhoeft/repo-a
#    triggers:
#      - name: cliente-repo-a
#  - name: repo-b
#    repository: bernhoeft/repo-b
"""

MAKEFILE = """\
dry-run:
\t@echo "acao=dry-run pr_title=$(PR_TITLE)"
run:
\t@echo "acao=run pr_title=$(PR_TITLE)"
dry-run-triggers:
\t@echo "acao=dry-run-triggers"
"""


@pytest.fixture
def fake_sync(tmp_path):
    (tmp_path / "repos.yaml").write_text(REPOS_YAML_PASSO1, encoding="utf-8")
    (tmp_path / "Makefile").write_text(MAKEFILE, encoding="utf-8")
    yield tmp_path
    # limpa artefatos que o driver escreve no workflow real
    bak = ROOT / "execucoes" / "repos.yaml.optimus-bak"
    if bak.exists():
        bak.unlink()
    for f in (ROOT / "erros").glob("*-sync-passo*"):
        f.unlink()


def drive(fake_sync, *args):
    env = dict(os.environ, SYNC_REPO_PATH=str(fake_sync))
    return subprocess.run(
        [sys.executable, str(DRIVER), *args],
        capture_output=True, text=True, env=env, cwd=ROOT,
    )


def test_backup_cria_copia(fake_sync):
    r = drive(fake_sync, "backup")
    assert r.returncode == 0 and "ok=true" in r.stdout
    assert (ROOT / "execucoes" / "repos.yaml.optimus-bak").exists()


def test_dry_run_exige_backup_antes(fake_sync):
    r = drive(fake_sync, "dry-run", "--step", "passo1")
    assert r.returncode == 1 and "backup_ausente" in r.stdout


def test_happy_path_passo1(fake_sync):
    drive(fake_sync, "backup")
    r = drive(fake_sync, "dry-run", "--step", "passo1", "--pr-title", "9.9.9")
    assert r.returncode == 0, r.stdout
    assert "GATE-YAML: ok=true" in r.stdout
    assert "promocao_segura:passo1" in r.stdout
    assert "pr_title=9.9.9" in r.stdout
    assert "ok=true acao=dry-run step=passo1" in r.stdout


def test_passo_divergente_bloqueia(fake_sync):
    drive(fake_sync, "backup")
    r = drive(fake_sync, "dry-run", "--step", "passo2")
    assert r.returncode == 1
    assert "passo_diverge" in r.stdout and "erro_doc=" in r.stdout


def test_conteudo_alterado_restaura_backup(fake_sync):
    drive(fake_sync, "backup")
    yaml = fake_sync / "repos.yaml"
    yaml.write_text(yaml.read_text().replace("auto_merge: false", "auto_merge: true"), encoding="utf-8")
    r = drive(fake_sync, "dry-run", "--step", "passo1")
    assert r.returncode == 1
    assert "conteudo_alterado_alem_de_comentarios" in r.stdout
    assert "backup_restaurado=true" in r.stdout
    assert "auto_merge: false" in yaml.read_text()  # restaurado


def test_trigger_ativo_fora_do_passo3_bloqueia(fake_sync):
    drive(fake_sync, "backup")
    yaml = fake_sync / "repos.yaml"
    yaml.write_text(
        yaml.read_text()
        .replace("#    triggers:", "    triggers:")
        .replace("#      - name: cliente-repo-a", "      - name: cliente-repo-a"),
        encoding="utf-8",
    )
    r = drive(fake_sync, "dry-run", "--step", "passo1")
    assert r.returncode == 1 and "triggers_ativos_fora_do_passo3" in r.stdout


def test_passo3_sem_trigger_bloqueia(fake_sync):
    r = drive(fake_sync, "dry-run-triggers")
    assert r.returncode == 1 and "nenhum_trigger_ativo_para_passo3" in r.stdout


def test_passo3_com_trigger_passa(fake_sync):
    yaml = fake_sync / "repos.yaml"
    yaml.write_text(
        yaml.read_text()
        .replace("#    triggers:", "    triggers:")
        .replace("#      - name: cliente-repo-a", "      - name: cliente-repo-a"),
        encoding="utf-8",
    )
    r = drive(fake_sync, "dry-run-triggers")
    assert r.returncode == 0, r.stdout
    assert "acao=dry-run-triggers" in r.stdout
