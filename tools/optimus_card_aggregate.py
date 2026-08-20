#!/usr/bin/env python3
"""Agrega contratos por lote do fan-out no contrato único.

Fail-closed: qualquer card do manifesto ausente/duplicado/intruso bloqueia.

Uso:
    python3 tools/optimus_card_aggregate.py <manifesto.json> [override-1.json ...]

Entrada: manifesto.json (saída de optimus_card_manifest.py) + overrides opcionais.
Saída: array JSON agregado na ordem de manifest.keys (stdout), ou erro (exit 1).
"""
import json
import sys

def main():
    if len(sys.argv) < 2:
        print("erro=uso", file=sys.stderr)
        sys.exit(1)

    manifesto_file = sys.argv[1]
    override_files = sys.argv[2:] if len(sys.argv) > 2 else []

    # Carregar manifesto
    try:
        with open(manifesto_file, 'r') as f:
            manifesto = json.load(f)
    except Exception:
        print("erro=manifesto_invalido", file=sys.stderr)
        sys.exit(1)

    if not manifesto.get("fanout"):
        print("erro=manifesto_sem_fanout", file=sys.stderr)
        sys.exit(1)

    if not manifesto.get("batches"):
        print("erro=manifesto_vazio", file=sys.stderr)
        sys.exit(1)

    manifest_keys = set(manifesto["keys"])

    # Carregar contratos dos lotes
    contracts_by_id = {}
    lotes_ausentes = []
    duplicados = []
    intrusos = []
    formato_invalido = []

    for batch in manifesto["batches"]:
        contrato_path = batch["contrato_path"]
        batch_id = batch["batch_id"]

        try:
            with open(contrato_path, 'r') as f:
                contrato = json.load(f)
        except FileNotFoundError:
            lotes_ausentes.append(batch_id)
            continue
        except Exception:
            lotes_ausentes.append(batch_id)
            continue

        if not isinstance(contrato, list):
            formato_invalido.append(f"{batch_id}: não é array")
            continue

        for card in contrato:
            if not isinstance(card, dict) or "card_id" not in card:
                formato_invalido.append(f"{batch_id}: card sem card_id")
                continue

            card_id = card["card_id"]

            if card_id not in manifest_keys:
                intrusos.append(card_id)
                continue

            if card_id in contracts_by_id:
                duplicados.append(card_id)
                continue

            contracts_by_id[card_id] = card

    # Carregar overrides
    for override_file in override_files:
        try:
            with open(override_file, 'r') as f:
                override = json.load(f)
        except Exception:
            formato_invalido.append(f"override {override_file}: ilegível")
            continue

        if not isinstance(override, list):
            formato_invalido.append(f"override {override_file}: não é array")
            continue

        for card in override:
            if not isinstance(card, dict) or "card_id" not in card:
                formato_invalido.append(f"override {override_file}: card sem card_id")
                continue

            card_id = card["card_id"]

            if card_id not in manifest_keys:
                intrusos.append(card_id)
                continue

            contracts_by_id[card_id] = card

    # Verificar faltantes
    faltantes = list(manifest_keys - set(contracts_by_id.keys()))

    # Relatório de erros
    errors = []
    if lotes_ausentes:
        errors.append(f"lotes_ausentes={','.join(lotes_ausentes)}")
    if faltantes:
        errors.append(f"faltantes={','.join(sorted(faltantes))}")
    if duplicados:
        errors.append(f"duplicados={','.join(duplicados)}")
    if intrusos:
        errors.append(f"intrusos={','.join(intrusos)}")
    if formato_invalido:
        errors.append(f"formato_invalido={';'.join(formato_invalido[:3])}")

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        sys.exit(1)

    # Agregado na ordem de manifest.keys
    agregado = []
    for key in manifesto["keys"]:
        if key in contracts_by_id:
            agregado.append(contracts_by_id[key])

    n_overrides = len(override_files)
    print(json.dumps(agregado, ensure_ascii=False, indent=2))
    print(f"total={len(agregado)} lotes={len(manifesto['batches'])} overrides={n_overrides}", file=sys.stderr)

if __name__ == "__main__":
    main()
