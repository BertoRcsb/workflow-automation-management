"""Testes de tools/optimus_next_version.py (GATE-VER-1/2/3)."""
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


def run_files(*paths):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, paths)],
        capture_output=True, text=True,
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


def test_dump_paginado_incompleto_falha():
    # GATE-VER-3: pagina unica com has_more=true = faltam paginas
    r = run('{"results": [{"Versao": "1.121.1"}], "has_more": true}')
    assert r.returncode == 1
    assert "dump_paginado_incompleto" in r.stdout
    assert "refazer_consulta_paginando_ate_has_more_false" in r.stdout


def test_paginas_concatenadas_completas_ok():
    # duas paginas em ordem: a ultima tem has_more=false -> completo
    dump = (
        '{"results": [{"Versao": "1.121.0"}], "has_more": true}\n'
        '{"results": [{"Versao": "1.122.0"}], "has_more": false}'
    )
    r = run(dump)
    assert r.returncode == 0
    assert "maior=1.122.0" in r.stdout and "proxima=1.123.0" in r.stdout
    assert "aviso=has_more_ausente_no_dump" not in r.stdout


def test_multiplos_arquivos_mesclados(tmp_path):
    p1 = tmp_path / "p1.json"
    p2 = tmp_path / "p2.json"
    p1.write_text('{"results": ["1.121.0", "1.121.1"], "has_more": true}', encoding="utf-8")
    p2.write_text('{"results": ["1.122.0"], "has_more": false}', encoding="utf-8")
    r = run_files(p1, p2)
    assert r.returncode == 0
    assert "maior=1.122.0" in r.stdout and "proxima=1.123.0" in r.stdout
    assert "versoes_na_base=3" in r.stdout


def test_dump_sem_has_more_ok_com_aviso():
    # compat: dump texto/reformatado sem has_more segue valendo, com aviso
    r = run("1.119.0 1.120.0")
    assert r.returncode == 0
    assert "aviso=has_more_ausente_no_dump" in r.stdout


def test_incidente_2026_08_20_pagina_parcial_bloqueada():
    # pagina 1 sem a 1.122.0 (que estava na pagina ausente): antes propunha
    # 1.122.0 (colisao real invisivel ao GATE-VER-2); agora GATE-VER-3 bloqueia
    r = run('{"results": [{"Versao": "1.121.0"}, {"Versao": "1.121.1"}], "has_more": true}')
    assert r.returncode == 1
    assert "dump_paginado_incompleto" in r.stdout
    assert "proxima=" not in r.stdout
