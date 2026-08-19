"""Regras do placeholder ("APENAS PROC"/"N/A") no extrator — confirmadas pelo Ronan em 2026-08-18.

1. Texto puro sem URL nos campos de PR/repo NAO e parse_failed: e sem_link, e o texto
   literal vai preservado no contrato (sera reescrito no Notion como esta).
2. acao_dados=Sim NAO implica ausencia de PR: se houver qualquer link, captura TODOS
   e apenas_proc fica False.
3. parse_failed continua reservado para falha real: campo COM URL que a normalizacao perdeu.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))
from optimus_extract import build_contract
import optimus_gates as G

RULES = {"db_owners": ["Maria Banco"]}


def adf(*nodes):
    return {"version": 1, "type": "doc",
            "content": [{"type": "paragraph", "content": list(nodes)}]}


def text(t):
    return {"type": "text", "text": t}


def card_link(url):
    return {"type": "inlineCard", "attrs": {"url": url}}


def make_issue(pr_field=None, repo_field=None, acao_dados=None, owner="John Doe"):
    return {
        "key": "PB-6096",
        "fields": {
            "summary": "Card de teste",
            "issuetype": {"name": "Task"},
            "status": {"name": "Teste regressivo"},
            "assignee": {"displayName": owner, "accountId": "1"},
            "customfield_12400": pr_field,
            "customfield_12399": repo_field,
            "customfield_12297": {"value": acao_dados} if acao_dados else None,
        },
    }


def test_apenas_proc_placeholder_nao_e_parse_failed():
    """PB-6096 (1.120.0): 'APENAS PROC' sem inlineCard = sem_link + apenas_proc, nunca falha."""
    c = build_contract(make_issue(pr_field=adf(text("APENAS PROC")),
                                  repo_field=adf(text("APENAS PROC")),
                                  acao_dados="Sim"))
    ps = c["parse_status"]
    assert ps["parse_failed"] is False
    assert ps["pr_sem_link"] is True and ps["repo_sem_link"] is True
    assert ps["pr_field_text"] == "APENAS PROC"
    assert c["deploy_fields"]["apenas_proc"] is True


def test_placeholder_texto_preservado_para_notion():
    """O texto literal das abas vai no contrato para ser reescrito no Notion como esta."""
    c = build_contract(make_issue(pr_field=adf(text("N/A")),
                                  repo_field=adf(text("Não tem."))))
    ps = c["parse_status"]
    assert ps["parse_failed"] is False
    assert ps["pr_field_text"] == "N/A"
    assert ps["repo_field_text"] == "Não tem."
    assert c["deploy_fields"]["apenas_proc"] is False


def test_acao_dados_sim_com_pr_captura_tudo():
    """acao_dados=Sim NAO implica sem PR: com links, captura todos e apenas_proc=False."""
    c = build_contract(make_issue(
        pr_field=adf(card_link("https://bitbucket.org/bernhoeft/sla-api/pull-requests/195"),
                     card_link("https://bitbucket.org/bernhoeft/newcontract-front/pull-requests/1112")),
        repo_field=adf(card_link("https://bitbucket.org/bernhoeft/sla-api")),
        acao_dados="Sim"))
    assert c["parse_status"]["parse_failed"] is False
    assert c["parse_status"]["pr_url_count"] == 2
    # 2026-08-19: repos derivam das PRs (sla-api + newcontract-front) alem do campo (sla-api).
    # O comportamento antigo (repo so do campo) perderia newcontract-front no repos.yaml.
    assert c["parse_status"]["repo_url_count"] == 2
    assert c["deploy_fields"]["apenas_proc"] is False
    verdict, _ = G.eligibility_v2(c, RULES)
    assert verdict == "aprovado"


def test_texto_apenas_proc_misturado_com_link_nunca_vira_apenas_proc():
    """Texto 'APENAS PROC' junto de um inlineCard: links vencem, apenas_proc=False."""
    c = build_contract(make_issue(
        pr_field=adf(text("APENAS PROC"),
                     card_link("https://bitbucket.org/bernhoeft/sla-api/pull-requests/195")),
        repo_field=adf(card_link("https://bitbucket.org/bernhoeft/sla-api")),
        acao_dados="Sim"))
    assert c["deploy_fields"]["apenas_proc"] is False
    assert c["parse_status"]["parse_failed"] is False
    assert c["parse_status"]["pr_url_count"] == 1


def test_url_que_a_normalizacao_perde_continua_parse_failed():
    """Falha real: campo de PR com URL que nao e PR (repo cru) -> parse_failed, gate bloqueia."""
    c = build_contract(make_issue(
        pr_field=adf(card_link("https://bitbucket.org/bernhoeft/sla-api")),
        repo_field=adf(card_link("https://bitbucket.org/bernhoeft/sla-api"))))
    assert c["parse_status"]["parse_failed"] is True
    verdict, _ = G.eligibility_v2(c, RULES)
    assert verdict == "parse_failed"


def test_so_banco_owner_de_banco_aprova_e_outros_ambiguo():
    """Placeholder so-banco: db_owner aprova; outro owner vira ambiguo (fica de fora, documentado)."""
    banco = build_contract(make_issue(pr_field=adf(text("APENAS PROC")),
                                      acao_dados="Sim", owner="Maria Banco"))
    outro = build_contract(make_issue(pr_field=adf(text("APENAS PROC")),
                                      acao_dados="Sim", owner="John Doe"))
    assert G.eligibility_v2(banco, RULES)[0] == "aprovado"
    assert G.eligibility_v2(outro, RULES)[0] == "ambiguo"


def test_crosscheck_nunca_apenas_proc_com_pr():
    """GATE-CROSSCHECK: apenas_proc=true com qualquer link real = falha dura."""
    c = build_contract(make_issue(
        pr_field=adf(card_link("https://bitbucket.org/bernhoeft/sla-api/pull-requests/195")),
        repo_field=adf(card_link("https://bitbucket.org/bernhoeft/sla-api")),
        acao_dados="Sim"))
    c["deploy_fields"]["apenas_proc"] = True  # corrupcao simulada
    errors = G.crosscheck({c["card_id"]: c}, [c["card_id"]])
    assert any("apenas_proc" in e for e in errors)


def test_residuo_de_link_renderizado_e_falha_real():
    """'[Card]' (smart link renderizado sem URL) continua parse_failed — link perdido."""
    c = build_contract(make_issue(pr_field=adf(text("[Card]"))))
    assert c["parse_status"]["parse_failed"] is True
    assert G.eligibility_v2(c, RULES)[0] == "parse_failed"
