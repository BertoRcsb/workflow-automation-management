"""Regras de 2026-08-19 — repo derivado da PR, motivos fieis e prosseguir deterministico.

Incidentes-modelo da execucao `executar incidentes` (Release 1.122.0):
1. PB-5728: 6 PRs reprovadas como "sem PR, sem repo" — repo agora deriva da URL da PR e o
   motivo do gate sai dos contadores reais (nunca generico).
2. PB-6257: URL de PR no campo Repositorio gerava parse_failed falso — agora e interpretada
   (PR + repo derivado) com aviso nao-bloqueante repo_field_com_pr.
3. Bloqueio fabricado "nunca deploy isolado": prosseguir = aprovados nao-vazio e sem errors,
   calculado em codigo — nao existe limiar minimo de aprovados.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))
from optimus_extract import build_contract
import optimus_gates as G

RULES = {"db_owners": ["Maria Banco"], "epicos_all_or_nothing": ["PB-5768"]}


def adf(*nodes):
    return {"version": 1, "type": "doc",
            "content": [{"type": "paragraph", "content": list(nodes)}]}


def text(t):
    return {"type": "text", "text": t}


def card_link(url):
    return {"type": "inlineCard", "attrs": {"url": url}}


def make_issue(key="PB-9999", pr_field=None, repo_field=None, acao_dados=None,
               owner="John Doe", parent=None):
    return {
        "key": key,
        "fields": {
            "summary": "Card de teste",
            "issuetype": {"name": "Incidente"},
            "status": {"name": "Teste regressivo"},
            "assignee": {"displayName": owner, "accountId": "1"},
            "parent": parent,
            "customfield_12400": pr_field,
            "customfield_12399": repo_field,
            "customfield_12297": {"value": acao_dados} if acao_dados else None,
        },
    }


def test_repo_deriva_da_pr_com_campo_repo_vazio():
    """PB-5728: PRs validas com campo Repositorio vazio = aprovado (repo derivado da URL)."""
    c = build_contract(make_issue(
        pr_field=adf(card_link("https://bitbucket.org/bernhoeft/sla-api/pull-requests/210"),
                     card_link("https://bitbucket.org/bernhoeft/login-api/pull-requests/393"))))
    ps = c["parse_status"]
    assert ps["parse_failed"] is False
    assert ps["pr_url_count"] == 2
    assert ps["repo_url_count"] == 2
    assert c["links"]["repositories"] == [
        "https://bitbucket.org/bernhoeft/login-api",
        "https://bitbucket.org/bernhoeft/sla-api",
    ]
    verdict, reason = G.eligibility_v2(c, RULES)
    assert verdict == "aprovado"
    assert "pr=2" in reason and "repo=2" in reason


def test_pb5728_aprovado_pela_v2_e_excluido_por_d1_com_motivo_correto():
    """O veredito certo do PB-5728 e exclusao D1 (epico all-or-nothing), nao reprova por 'sem PR'."""
    c = build_contract(make_issue(
        key="PB-5728",
        pr_field=adf(card_link("https://bitbucket.org/bernhoeft/contractweb-v3/pull-requests/5297")),
        parent={"key": "PB-5768", "fields": {"summary": "Refatoracao Melhorias Onda 1"}}))
    verdict, _ = G.eligibility_v2(c, RULES)
    assert verdict == "aprovado"
    kept, excluded = G.apply_d1(["PB-5728"], {"PB-5728": c}, RULES, {})
    assert kept == []
    assert excluded[0]["reason"] == "D1: epico PB-5768 all-or-nothing incompleto"


def test_url_de_pr_no_campo_repo_e_interpretada_nao_parse_failed():
    """PB-6257: campo Repositorio com a URL da propria PR = aprovado + flag repo_field_com_pr."""
    pr = "https://bitbucket.org/bernhoeft/bernhoeft-grt-contractweb-front/pull-requests/1296/overview"
    c = build_contract(make_issue(pr_field=adf(card_link(pr)), repo_field=adf(card_link(pr))))
    ps = c["parse_status"]
    assert ps["parse_failed"] is False
    assert ps["repo_field_com_pr"] is True
    assert ps["pr_url_count"] == 1
    assert ps["repo_url_count"] == 1
    assert c["links"]["repositories"] == [
        "https://bitbucket.org/bernhoeft/bernhoeft-grt-contractweb-front"]
    verdict, _ = G.eligibility_v2(c, RULES)
    assert verdict == "aprovado"


def test_pr_somente_no_campo_repo_tambem_e_interpretada():
    """PR presente apenas no campo Repositorio (campo de PR vazio) vira PR + repo derivado."""
    c = build_contract(make_issue(
        repo_field=adf(card_link("https://bitbucket.org/bernhoeft/bar/pull-requests/9"))))
    ps = c["parse_status"]
    assert ps["parse_failed"] is False
    assert ps["repo_field_com_pr"] is True
    assert ps["pr_url_count"] == 1 and ps["repo_url_count"] == 1
    assert c["links"]["pull_requests"][0]["label"] == "bar #9"


def test_derivacao_nao_mascara_residuo_perdido_no_campo_repo():
    """Residuo '[Card]' sem URL no campo repo segue falha real, mesmo com PR valida no campo PR."""
    c = build_contract(make_issue(
        pr_field=adf(card_link("https://bitbucket.org/bernhoeft/foo/pull-requests/1")),
        repo_field=adf(text("[Card]"))))
    assert c["parse_status"]["parse_failed"] is True
    verdict, _ = G.eligibility_v2(c, RULES)
    assert verdict == "parse_failed"


def test_motivo_de_reprova_nunca_mente_sobre_os_contadores():
    """Motivo sai dos contadores reais: 'sem PR' so quando pr=0 (incidente PB-5728)."""
    so_repo = build_contract(make_issue(
        repo_field=adf(card_link("https://bitbucket.org/bernhoeft/foo"))))
    verdict, reason = G.eligibility_v2(so_repo, RULES)
    assert verdict == "reprovado"
    assert "sem PR, sem repo" not in reason
    assert "pr=0" in reason and "repo=1" in reason

    vazio = build_contract(make_issue())
    verdict, reason = G.eligibility_v2(vazio, RULES)
    assert verdict == "reprovado"
    assert "sem PR, sem repo, sem acao de dados" in reason


def test_prosseguir_e_avisos_no_gates_json(tmp_path):
    """prosseguir = aprovados nao-vazio e errors vazio; 1 aprovado E deploy valido; avisos fluem."""
    import json
    import subprocess
    pr = "https://bitbucket.org/bernhoeft/foo/pull-requests/1"
    contract = [build_contract(make_issue(key="PB-1", pr_field=adf(card_link(pr)),
                                          repo_field=adf(card_link(pr)))),
                build_contract(make_issue(key="PB-2"))]
    cpath = tmp_path / "contrato.json"
    rpath = tmp_path / "rules.json"
    cpath.write_text(json.dumps(contract), encoding="utf-8")
    rpath.write_text(json.dumps(RULES), encoding="utf-8")
    tools = os.path.join(os.path.dirname(__file__), '..', 'tools')
    out = subprocess.run(
        [sys.executable, os.path.join(tools, "optimus_gates.py"), str(cpath), str(rpath)],
        capture_output=True, text=True)
    assert out.returncode == 0
    g = json.loads(out.stdout)
    assert g["prosseguir"] is True
    assert g["aprovados_finais"] == ["PB-1"]
    assert g["avisos"][0]["card_id"] == "PB-1"

    # Sem aprovados -> prosseguir=False (o criterio e codigo, nao juizo do LLM).
    cpath.write_text(json.dumps([build_contract(make_issue(key="PB-2"))]), encoding="utf-8")
    out = subprocess.run(
        [sys.executable, os.path.join(tools, "optimus_gates.py"), str(cpath), str(rpath)],
        capture_output=True, text=True)
    g = json.loads(out.stdout)
    assert g["prosseguir"] is False
