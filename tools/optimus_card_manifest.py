#!/usr/bin/env python3
"""Manifesto determinístico do fan-out de coleta.

O LLM não decide escopo nem concorrência: este script fatia as chaves da JQL em lotes
e fixa caminhos e params.

Uso:
    python3 tools/optimus_card_manifest.py <busca-jql.json> <board> <data> [workers.json]

Entrada: resultado da JQL (aceita {"issues":[...]}, lista de issues, ou um issue único).
Saída: JSON no stdout com schema_version, run_id, board, data, total_cards, fanout, params,
       keys[], e batches[] (se fanout=true).
"""
import json
import sys
import os

def load_issues(input_file):
    """Carrega issues com tolerância (lista, {"issues":[...]} ou um issue único)."""
    with open(input_file, 'r') as f:
        data = json.load(f)

    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if "issues" in data:
            return data["issues"]
        if "key" in data:
            return [data]
    raise ValueError("Formato não reconhecido; espera lista, {'issues':[...]} ou um issue")

def main():
    if len(sys.argv) < 4:
        print("erro=uso", file=sys.stderr)
        sys.exit(1)

    jql_file = sys.argv[1]
    board = sys.argv[2]
    data = sys.argv[3]
    workers_json = sys.argv[4] if len(sys.argv) > 4 else os.path.join(
        os.path.dirname(__file__), "workers.json"
    )

    # Validação de entrada
    if not board or not data:
        print("erro=argumento_vazio", file=sys.stderr)
        sys.exit(1)

    try:
        issues = load_issues(jql_file)
    except Exception:
        print("erro=entrada_invalida", file=sys.stderr)
        sys.exit(1)

    # Extrair chaves
    keys = []
    seen = set()
    duplicados = []

    for issue in issues:
        if not isinstance(issue, dict) or "key" not in issue:
            print("erro=item_sem_key", file=sys.stderr)
            sys.exit(1)
        key = issue["key"]
        if key in seen:
            duplicados.append(key)
        seen.add(key)
        keys.append(key)

    if duplicados:
        print(f"erro=chave_duplicada chaves={','.join(duplicados)}", file=sys.stderr)
        sys.exit(1)

    # Carregar config
    try:
        with open(workers_json, 'r') as f:
            cfg = json.load(f)
    except Exception:
        print("erro=config_invalida", file=sys.stderr)
        sys.exit(1)

    fanout_threshold = cfg.get("fanout_threshold", 8)
    batch_size = cfg.get("batch_size", 1)
    max_workers = cfg.get("max_workers", 5)

    total_cards = len(keys)
    fanout = total_cards > fanout_threshold

    # Construir saída
    result = {
        "schema_version": "1.0",
        "run_id": f"{data}-{board}",
        "board": board,
        "data": data,
        "total_cards": total_cards,
        "fanout": fanout,
        "params": {
            "fanout_threshold": fanout_threshold,
            "batch_size": batch_size,
            "max_workers": max_workers
        },
        "keys": keys,
        "batches": []
    }

    if fanout:
        # Fatiamento em lotes
        n_batches = (total_cards + batch_size - 1) // batch_size
        batch_id_width = max(2, len(str(n_batches)))

        for i in range(n_batches):
            start = i * batch_size
            end = min(start + batch_size, total_cards)
            batch_keys = keys[start:end]
            batch_id = f"b{str(i+1).zfill(batch_id_width)}"

            batch = {
                "batch_id": batch_id,
                "keys": batch_keys,
                "raw_path": f"execucoes/{data}-{board}-lote-{batch_id}-raw.json",
                "remote_path": f"execucoes/{data}-{board}-lote-{batch_id}-remote.json",
                "contrato_path": f"execucoes/{data}-{board}-lote-{batch_id}-contrato.json"
            }
            result["batches"].append(batch)

    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
