#!/usr/bin/env python3
"""Testes para optimus_card_aggregate.py (agregação determinística)."""

import json
import subprocess
import sys
import os
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "optimus_card_aggregate.py"
EXTRACT = Path(__file__).resolve().parents[1] / "tools" / "optimus_extract.py"

# Helpers de ADF (copiados de test_optimus_extract_placeholder.py)
def adf(*nodes):
    return {"version": 1, "type": "doc",
            "content": [{"type": "paragraph", "content": list(nodes)}]}

def text(t):
    return {"type": "text", "text": t}

def card_link(url):
    return {"type": "inlineCard", "attrs": {"url": url}}

def make_issue(key="PB-1", pr_field=None, repo_field=None, acao_dados=None):
    return {
        "key": key,
        "fields": {
            "summary": f"Card {key}",
            "issuetype": {"name": "Task"},
            "status": {"name": "Teste regressivo"},
            "assignee": {"displayName": "John Doe", "accountId": "1"},
            "customfield_12400": pr_field or adf(card_link("https://bitbucket.org/bernhoeft/api/pull-requests/1")),
            "customfield_12399": repo_field or adf(card_link("https://bitbucket.org/bernhoeft/api")),
            "customfield_12297": {"value": acao_dados} if acao_dados else None,
            "customfield_12401": None,
            "customfield_11993": None,
            "parent": None,
        },
    }

def test_equivalencia_com_monolitico(tmp_path):
    """Contrato monolítico == agregado de fragmentos por card."""
    # Criar 3 issues de teste
    issues_mono = [
        make_issue(key="PB-5801"),
        make_issue(key="PB-5802"),
        make_issue(key="PB-5803"),
    ]

    # Salvar raw monolítico
    raw_mono_file = tmp_path / "raw-mono.json"
    raw_mono_file.write_text(json.dumps(issues_mono))

    # Rodar extract monolítico
    result_mono = subprocess.run(
        [sys.executable, str(EXTRACT), str(raw_mono_file)],
        capture_output=True, text=True
    )
    assert result_mono.returncode == 0
    contrato_mono = json.loads(result_mono.stdout)

    # Criar manifesto sintético (fanout=true, 3 lotes)
    manifesto = {
        "schema_version": "1.0",
        "run_id": "2026-08-20-features",
        "board": "features",
        "data": "2026-08-20",
        "total_cards": 3,
        "fanout": True,
        "params": {"fanout_threshold": 8, "batch_size": 1, "max_workers": 5},
        "keys": ["PB-5801", "PB-5802", "PB-5803"],
        "batches": [
            {"batch_id": "b01", "keys": ["PB-5801"],
             "raw_path": str(tmp_path / "raw-b01.json"),
             "remote_path": str(tmp_path / "remote-b01.json"),
             "contrato_path": str(tmp_path / "contrato-b01.json")},
            {"batch_id": "b02", "keys": ["PB-5802"],
             "raw_path": str(tmp_path / "raw-b02.json"),
             "remote_path": str(tmp_path / "remote-b02.json"),
             "contrato_path": str(tmp_path / "contrato-b02.json")},
            {"batch_id": "b03", "keys": ["PB-5803"],
             "raw_path": str(tmp_path / "raw-b03.json"),
             "remote_path": str(tmp_path / "remote-b03.json"),
             "contrato_path": str(tmp_path / "contrato-b03.json")},
        ]
    }

    # Rodar extract por card e salvar contratos
    for i, issue in enumerate(issues_mono):
        raw_file = tmp_path / f"raw-b{i+1:02d}.json"
        raw_file.write_text(json.dumps([issue]))

        result = subprocess.run(
            [sys.executable, str(EXTRACT), str(raw_file)],
            capture_output=True, text=True
        )
        assert result.returncode == 0

        contrato_file = tmp_path / f"contrato-b{i+1:02d}.json"
        contrato_file.write_text(result.stdout)

    # Salvar manifesto
    manifesto_file = tmp_path / "manifesto.json"
    manifesto_file.write_text(json.dumps(manifesto))

    # Rodar aggregate
    result_agg = subprocess.run(
        [sys.executable, str(SCRIPT), str(manifesto_file)],
        capture_output=True, text=True
    )
    assert result_agg.returncode == 0

    # Equivalência BYTE a BYTE com o contrato monolítico (mesma serialização)
    assert result_agg.stdout == result_mono.stdout
    assert json.loads(result_agg.stdout) == contrato_mono
    print("✓ test_equivalencia_com_monolitico")

def test_lote_ausente_falha(tmp_path):
    """Lote ausente: exit 1, stderr com lotes_ausentes e faltantes."""
    manifesto = {
        "schema_version": "1.0",
        "run_id": "2026-08-20-features",
        "board": "features",
        "data": "2026-08-20",
        "total_cards": 2,
        "fanout": True,
        "keys": ["PB-1", "PB-2"],
        "batches": [
            {"batch_id": "b01", "keys": ["PB-1"],
             "raw_path": str(tmp_path / "raw-b01.json"),
             "remote_path": str(tmp_path / "remote-b01.json"),
             "contrato_path": str(tmp_path / "contrato-b01.json")},
            {"batch_id": "b02", "keys": ["PB-2"],
             "raw_path": str(tmp_path / "raw-b02.json"),
             "remote_path": str(tmp_path / "remote-b02.json"),
             "contrato_path": str(tmp_path / "contrato-b02.json")},
        ]
    }

    # Criar apenas b01, não b02
    manifesto_file = tmp_path / "manifesto.json"
    manifesto_file.write_text(json.dumps(manifesto))

    contrato_b01 = [{"card_id": "PB-1", "title": "Card 1"}]
    contrato_b01_file = tmp_path / "contrato-b01.json"
    contrato_b01_file.write_text(json.dumps(contrato_b01))

    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(manifesto_file)],
        capture_output=True, text=True
    )

    assert result.returncode == 1
    assert "lotes_ausentes=" in result.stderr
    assert "faltantes=" in result.stderr
    assert result.stdout == ""
    print("✓ test_lote_ausente_falha")

def test_intruso_falha(tmp_path):
    """Card fora do manifesto: exit 1, intruso no stderr."""
    manifesto = {
        "schema_version": "1.0",
        "run_id": "2026-08-20-features",
        "board": "features",
        "data": "2026-08-20",
        "total_cards": 1,
        "fanout": True,
        "keys": ["PB-1"],
        "batches": [
            {"batch_id": "b01", "keys": ["PB-1"],
             "raw_path": str(tmp_path / "raw-b01.json"),
             "remote_path": str(tmp_path / "remote-b01.json"),
             "contrato_path": str(tmp_path / "contrato-b01.json")},
        ]
    }

    manifesto_file = tmp_path / "manifesto.json"
    manifesto_file.write_text(json.dumps(manifesto))

    # Contrato com card FORA do manifesto
    contrato_b01 = [
        {"card_id": "PB-1", "title": "Card 1"},
        {"card_id": "PB-999", "title": "Intruso"}
    ]
    contrato_b01_file = tmp_path / "contrato-b01.json"
    contrato_b01_file.write_text(json.dumps(contrato_b01))

    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(manifesto_file)],
        capture_output=True, text=True
    )

    assert result.returncode == 1
    assert "intrusos=" in result.stderr
    print("✓ test_intruso_falha")

def test_duplicado_falha(tmp_path):
    """Mesma chave em dois lotes: exit 1, duplicado no stderr."""
    manifesto = {
        "schema_version": "1.0",
        "run_id": "2026-08-20-features",
        "board": "features",
        "data": "2026-08-20",
        "total_cards": 1,
        "fanout": True,
        "keys": ["PB-1"],
        "batches": [
            {"batch_id": "b01", "keys": ["PB-1"],
             "raw_path": str(tmp_path / "raw-b01.json"),
             "remote_path": str(tmp_path / "remote-b01.json"),
             "contrato_path": str(tmp_path / "contrato-b01.json")},
            {"batch_id": "b02", "keys": [],
             "raw_path": str(tmp_path / "raw-b02.json"),
             "remote_path": str(tmp_path / "remote-b02.json"),
             "contrato_path": str(tmp_path / "contrato-b02.json")},
        ]
    }

    manifesto_file = tmp_path / "manifesto.json"
    manifesto_file.write_text(json.dumps(manifesto))

    # b01 e b02 têm PB-1
    contrato_b01 = [{"card_id": "PB-1", "title": "Card 1 - batch 1"}]
    contrato_b02 = [{"card_id": "PB-1", "title": "Card 1 - batch 2"}]

    (tmp_path / "contrato-b01.json").write_text(json.dumps(contrato_b01))
    (tmp_path / "contrato-b02.json").write_text(json.dumps(contrato_b02))

    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(manifesto_file)],
        capture_output=True, text=True
    )

    assert result.returncode == 1
    assert "duplicados=" in result.stderr
    print("✓ test_duplicado_falha")

def test_override_substitui(tmp_path):
    """Override de refino-1 substitui por card_id, mantém ordem."""
    manifesto = {
        "schema_version": "1.0",
        "run_id": "2026-08-20-features",
        "board": "features",
        "data": "2026-08-20",
        "total_cards": 2,
        "fanout": True,
        "keys": ["PB-1", "PB-2"],
        "batches": [
            {"batch_id": "b01", "keys": ["PB-1"],
             "raw_path": str(tmp_path / "raw-b01.json"),
             "remote_path": str(tmp_path / "remote-b01.json"),
             "contrato_path": str(tmp_path / "contrato-b01.json")},
            {"batch_id": "b02", "keys": ["PB-2"],
             "raw_path": str(tmp_path / "raw-b02.json"),
             "remote_path": str(tmp_path / "remote-b02.json"),
             "contrato_path": str(tmp_path / "contrato-b02.json")},
        ]
    }

    manifesto_file = tmp_path / "manifesto.json"
    manifesto_file.write_text(json.dumps(manifesto))

    contrato_b01 = [{"card_id": "PB-1", "title": "Card 1 - original", "status": "broken"}]
    contrato_b02 = [{"card_id": "PB-2", "title": "Card 2"}]

    (tmp_path / "contrato-b01.json").write_text(json.dumps(contrato_b01))
    (tmp_path / "contrato-b02.json").write_text(json.dumps(contrato_b02))

    # Override para PB-1
    override = [{"card_id": "PB-1", "title": "Card 1 - corrigido", "status": "ok"}]
    override_file = tmp_path / "refino-1-contrato.json"
    override_file.write_text(json.dumps(override))

    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(manifesto_file), str(override_file)],
        capture_output=True, text=True
    )

    assert result.returncode == 0
    agregado = json.loads(result.stdout)

    # Ordem: PB-1 (do override), PB-2 (original)
    assert len(agregado) == 2
    assert agregado[0]["card_id"] == "PB-1"
    assert agregado[0]["title"] == "Card 1 - corrigido"
    assert agregado[1]["card_id"] == "PB-2"
    print("✓ test_override_substitui")

if __name__ == "__main__":
    os.chdir(Path(__file__).resolve().parents[1])

    tests = [
        test_equivalencia_com_monolitico,
        test_lote_ausente_falha,
        test_intruso_falha,
        test_duplicado_falha,
        test_override_substitui,
    ]

    import tempfile
    failed = 0
    for test in tests:
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                test(Path(tmpdir))
        except Exception as e:
            print(f"✗ {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\n{len(tests) - failed}/{len(tests)} testes passaram")
    sys.exit(0 if failed == 0 else 1)
