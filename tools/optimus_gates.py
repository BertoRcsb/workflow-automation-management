#!/usr/bin/env python3
"""optimus_gates.py - validador v2 + D1/D2 + GATE-CROSSCHECK, deterministico.

Uso:
    python3 tools/optimus_gates.py <contrato.json> <rules.json> [epic_status.json] > gates.json

epic_status.json (opcional): { "PB-236": {"completo": false}, ... }  (completude do epico)
Sai com exit code 1 se GATE-CROSSCHECK falhar (algo foi "esquecido").
"""
import json, sys


def montador_pr_cell(card):
    prs = card["links"]["pull_requests"]
    if prs:
        return "<br>".join(f"[{p['label']}]({p['url']})" for p in prs)
    if card["deploy_fields"]["apenas_proc"]:
        return "• APENAS PROC"  # "• APENAS PROC"
    return ""


def eligibility_v2(card, rules):
    ps = card["parse_status"]
    df = card["deploy_fields"]
    if ps["parse_failed"]:
        return ("parse_failed", "parse_failed: ADF com conteudo mas 0 URLs; re-extrair")
    has_code = ps["pr_url_count"] > 0 and ps["repo_url_count"] > 0
    if has_code:
        return ("aprovado", "PR + repositorio")
    if df["acao_dados"] == "Sim" and ps["pr_url_count"] == 0 and ps["repo_url_count"] == 0:
        owner = (card.get("owner") or {}).get("name")
        if owner in rules.get("db_owners", []):
            return ("aprovado", "so-banco legitimo (owner de banco)")
        return ("ambiguo", "acao_dados=Sim sem PR/repo e owner nao e de banco: decidir")
    return ("reprovado", "sem PR, sem repo, sem acao de dados")


def apply_d1(approved, cards_by_id, rules, epic_status):
    """Exclui filhos de epico all-or-nothing/incompleto. Retorna (mantidos, excluidos)."""
    allon = set(rules.get("epicos_all_or_nothing", []))
    excluded = []
    kept = []
    for cid in approved:
        epic = (cards_by_id[cid].get("epic") or {})
        ek = epic.get("key")
        reason = None
        if ek in allon:
            reason = f"D1: epico {ek} all-or-nothing incompleto"
        elif ek and epic_status.get(ek, {}).get("completo") is False:
            reason = f"D1: epico {ek} incompleto"
        if reason:
            excluded.append({"card_id": cid, "reason": reason})
        else:
            kept.append(cid)
    return kept, excluded


def apply_d2(approved, cards_by_id):
    """PR compartilhada parcial -> excluir os aprovados que a usam. Fixpoint."""
    final = set(approved)
    excluded = []
    changed = True
    while changed:
        changed = False
        usage = {}
        for cid, card in cards_by_id.items():
            for p in card["links"]["pull_requests"]:
                usage.setdefault(p["url"], set()).add(cid)
        for url, users in usage.items():
            if len(users) <= 1:
                continue
            inside = users & final
            outside = users - final
            if inside and outside:
                for cid in list(inside):
                    final.discard(cid)
                    excluded.append({"card_id": cid, "reason": f"D2: PR {url} compartilhada parcial"})
                    changed = True
    return [c for c in approved if c in final], excluded


def crosscheck(cards_by_id, final_approved):
    """Falha dura: nunca 'APENAS PROC' onde ha PR; nunca aprovar parse_failed."""
    errors = []
    for cid, card in cards_by_id.items():
        cell = montador_pr_cell(card)
        pc = card["parse_status"]["pr_url_count"]
        rc = card["parse_status"]["repo_url_count"]
        if cell == "• APENAS PROC" and pc > 0:
            errors.append(f"{cid}: celula 'APENAS PROC' mas pr_url_count={pc}")
        if card["deploy_fields"]["apenas_proc"] and (pc > 0 or rc > 0):
            errors.append(f"{cid}: apenas_proc=true com links reais (pr={pc}, repo={rc})")
        if card["parse_status"]["parse_failed"] and cid in final_approved:
            errors.append(f"{cid}: aprovado com parse_failed=true")
    return errors


def main():
    if len(sys.argv) < 3:
        raise SystemExit("uso: optimus_gates.py <contrato.json> <rules.json> [epic_status.json]")
    contract = json.load(open(sys.argv[1], encoding="utf-8"))
    rules = json.load(open(sys.argv[2], encoding="utf-8"))
    epic_status = {}
    if len(sys.argv) > 3:
        try:
            epic_status = json.load(open(sys.argv[3], encoding="utf-8"))
        except FileNotFoundError:
            epic_status = {}

    cards_by_id = {c["card_id"]: c for c in contract}
    aprovado, reprovado, ambiguo, parse_failed = [], [], [], []
    for c in contract:
        verdict, reason = eligibility_v2(c, rules)
        rec = {"card_id": c["card_id"], "reason": reason}
        {"aprovado": aprovado, "reprovado": reprovado,
         "ambiguo": ambiguo, "parse_failed": parse_failed}[verdict].append(rec)

    approved_ids = [r["card_id"] for r in aprovado]
    kept1, exc_d1 = apply_d1(approved_ids, cards_by_id, rules, epic_status)
    kept2, exc_d2 = apply_d2(kept1, cards_by_id)
    final_approved = set(kept2)

    errors = crosscheck(cards_by_id, final_approved)

    rows = []
    for cid in kept2:
        c = cards_by_id[cid]
        rows.append({
            "card_id": cid,
            "item": f"[{cid} - {c['title']}]({c['links']['jira']}) · {c['status']}",
            "pull_requests": montador_pr_cell(c),
            "acao_banco": c["deploy_fields"]["acao_dados"] or "—",
            "acao_infra": "—",
            "merge": c["deploy_fields"]["merge_realizado"] or "—",
            "repos": c["links"]["repositories"],
        })

    out = {
        "aprovados_finais": kept2,
        "rows": rows,
        "reprovados": reprovado,
        "ambiguos": ambiguo,
        "parse_failed": parse_failed,
        "excluidos_d1": exc_d1,
        "excluidos_d2": exc_d2,
        "errors": errors,
    }
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
