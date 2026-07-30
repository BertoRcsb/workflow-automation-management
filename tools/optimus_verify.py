#!/usr/bin/env python3
"""optimus_verify.py - auditoria passo a passo (read-only). Prova o fix ponta a ponta.

Uso:
    python3 tools/optimus_verify.py <raw_issues.json> <rules.json> [remote_links.json] [epic_status.json]

Imprime, por card: pr_url_count | celula que iria pro Notion | veredito | motivo.
E o bloco de exclusoes D1/D2 com o motivo CORRETO. Exit 1 se GATE-CROSSCHECK falhar.
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from optimus_extract import build_contract, load_issues, load_remote  # noqa: E402
import optimus_gates as G  # noqa: E402


def main():
    if len(sys.argv) < 3:
        raise SystemExit("uso: optimus_verify.py <raw_issues.json> <rules.json> [remote_links.json] [epic_status.json]")
    issues = load_issues(sys.argv[1])
    rules = json.load(open(sys.argv[2], encoding="utf-8"))
    remote = load_remote(sys.argv[3] if len(sys.argv) > 3 else None)
    epic_status = {}
    if len(sys.argv) > 4:
        try:
            epic_status = json.load(open(sys.argv[4], encoding="utf-8"))
        except FileNotFoundError:
            pass

    contract = [build_contract(i, remote.get(i.get("key"))) for i in issues]
    by_id = {c["card_id"]: c for c in contract}

    print(f"{'CARD':<10} {'PRs':>3} {'PARSE_FAIL':>10}  CELULA_NOTION")
    print("-" * 80)
    for c in contract:
        ps = c["parse_status"]
        cell = G.montador_pr_cell(c)
        print(f"{c['card_id']:<10} {ps['pr_url_count']:>3} {str(ps['parse_failed']):>10}  {cell}")

    aprov = []
    for c in contract:
        v, r = G.eligibility_v2(c, rules)
        if v == "aprovado":
            aprov.append(c["card_id"])
    k1, d1 = G.apply_d1(aprov, by_id, rules, epic_status)
    k2, d2 = G.apply_d2(k1, by_id)
    errors = G.crosscheck(by_id, set(k2))

    print("\nEXCLUSOES D1:", json.dumps(d1, ensure_ascii=False))
    print("EXCLUSOES D2:", json.dumps(d2, ensure_ascii=False))
    print("APROVADOS FINAIS:", k2)
    print("\nGATE-CROSSCHECK:", "OK" if not errors else "FALHOU")
    for e in errors:
        print("  -", e)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
