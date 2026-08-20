#!/usr/bin/env python3
"""Testes para optimus_card_manifest.py (fan-out determinístico)."""

import json
import subprocess
import sys
import os
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "optimus_card_manifest.py"

def test_abaixo_do_limiar_sem_fanout(tmp_path):
    """Abaixo do limiar: fanout=false, batches=[]."""
    jql_file = tmp_path / "jql.json"
    workers_file = tmp_path / "workers.json"

    # 3 cards, threshold 8
    jql_file.write_text(json.dumps({"issues": [
        {"key": "PB-1"}, {"key": "PB-2"}, {"key": "PB-3"}
    ]}))
    workers_file.write_text(json.dumps({
        "fanout_threshold": 8, "batch_size": 1, "max_workers": 5
    }))

    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(jql_file), "features", "2026-08-20", str(workers_file)],
        capture_output=True, text=True
    )

    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert data["fanout"] == False
    assert data["batches"] == []
    assert data["keys"] == ["PB-1", "PB-2", "PB-3"]
    assert data["total_cards"] == 3
    print("✓ test_abaixo_do_limiar_sem_fanout")

def test_acima_do_limiar_gera_lotes(tmp_path):
    """Acima do limiar: fanout=true, lotes com batch_id b01..b10."""
    jql_file = tmp_path / "jql.json"
    workers_file = tmp_path / "workers.json"

    keys = [f"PB-{5800+i}" for i in range(10)]
    jql_file.write_text(json.dumps({"issues": [{"key": k} for k in keys]}))
    workers_file.write_text(json.dumps({
        "fanout_threshold": 8, "batch_size": 1, "max_workers": 5
    }))

    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(jql_file), "features", "2026-08-20", str(workers_file)],
        capture_output=True, text=True
    )

    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["fanout"] == True
    assert len(data["batches"]) == 10
    assert data["batches"][0]["batch_id"] == "b01"
    assert data["batches"][9]["batch_id"] == "b10"
    assert data["batches"][0]["keys"] == ["PB-5800"]
    assert all(b["keys"] == [keys[i]] for i, b in enumerate(data["batches"]))
    assert data["batches"][0]["raw_path"] == "execucoes/2026-08-20-features-lote-b01-raw.json"
    print("✓ test_acima_do_limiar_gera_lotes")

def test_batch_size_maior(tmp_path):
    """batch_size=4: 10 cards viram 3 lotes com 4/4/2 keys."""
    jql_file = tmp_path / "jql.json"
    workers_file = tmp_path / "workers.json"

    keys = [f"PB-{5800+i}" for i in range(10)]
    jql_file.write_text(json.dumps({"issues": [{"key": k} for k in keys]}))
    workers_file.write_text(json.dumps({
        "fanout_threshold": 8, "batch_size": 4, "max_workers": 5
    }))

    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(jql_file), "features", "2026-08-20", str(workers_file)],
        capture_output=True, text=True
    )

    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert len(data["batches"]) == 3
    assert len(data["batches"][0]["keys"]) == 4
    assert len(data["batches"][1]["keys"]) == 4
    assert len(data["batches"][2]["keys"]) == 2
    print("✓ test_batch_size_maior")

def test_chave_duplicada_falha(tmp_path):
    """Chave duplicada: exit 1, erro=chave_duplicada no stderr."""
    jql_file = tmp_path / "jql.json"
    workers_file = tmp_path / "workers.json"

    jql_file.write_text(json.dumps({"issues": [
        {"key": "PB-1"}, {"key": "PB-2"}, {"key": "PB-1"}
    ]}))
    workers_file.write_text(json.dumps({
        "fanout_threshold": 8, "batch_size": 1, "max_workers": 5
    }))

    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(jql_file), "features", "2026-08-20", str(workers_file)],
        capture_output=True, text=True
    )

    assert result.returncode == 1
    assert "erro=chave_duplicada" in result.stderr
    assert result.stdout == ""
    print("✓ test_chave_duplicada_falha")

def test_determinismo(tmp_path):
    """Duas execuções com input idêntico: stdout byte-idêntico."""
    jql_file = tmp_path / "jql.json"
    workers_file = tmp_path / "workers.json"

    keys = [f"PB-{5800+i}" for i in range(15)]
    jql_file.write_text(json.dumps({"issues": [{"key": k} for k in keys]}))
    workers_file.write_text(json.dumps({
        "fanout_threshold": 8, "batch_size": 1, "max_workers": 5
    }))

    result1 = subprocess.run(
        [sys.executable, str(SCRIPT), str(jql_file), "features", "2026-08-20", str(workers_file)],
        capture_output=True, text=True
    )
    result2 = subprocess.run(
        [sys.executable, str(SCRIPT), str(jql_file), "features", "2026-08-20", str(workers_file)],
        capture_output=True, text=True
    )

    assert result1.stdout == result2.stdout
    print("✓ test_determinismo")

if __name__ == "__main__":
    os.chdir(Path(__file__).resolve().parents[1])

    tests = [
        test_abaixo_do_limiar_sem_fanout,
        test_acima_do_limiar_gera_lotes,
        test_batch_size_maior,
        test_chave_duplicada_falha,
        test_determinismo,
    ]

    import tempfile
    failed = 0
    for test in tests:
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                test(Path(tmpdir))
        except Exception as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1

    print(f"\n{len(tests) - failed}/{len(tests)} testes passaram")
    sys.exit(0 if failed == 0 else 1)
