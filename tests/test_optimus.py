import json
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))
from optimus_extract import build_contract, extract_field_urls, norm_pr, walk_urls
import optimus_gates as G


def test_pb_5528_two_prs_two_repos():
    """PB-5528: 2 inlineCards em 12400, 2 em 12399. Espera 2 PRs, 2 repos, parse_failed=False."""
    issue = {
        "key": "PB-5528",
        "fields": {
            "summary": "Test issue",
            "issuetype": {"name": "Task"},
            "status": {"name": "In Progress"},
            "assignee": {"displayName": "John Doe", "accountId": "123"},
            "customfield_12400": {
                "version": 1,
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "inlineCard",
                                "attrs": {"url": "https://bitbucket.org/bernhoeft/newcontract-front/pull-requests/1112"}
                            }
                        ]
                    },
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "inlineCard",
                                "attrs": {"url": "https://bitbucket.org/bernhoeft/sla-api/pull-requests/195"}
                            }
                        ]
                    }
                ]
            },
            "customfield_12399": {
                "version": 1,
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "inlineCard",
                                "attrs": {"url": "https://bitbucket.org/bernhoeft/newcontract-front"}
                            }
                        ]
                    },
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "inlineCard",
                                "attrs": {"url": "https://bitbucket.org/bernhoeft/sla-api"}
                            }
                        ]
                    }
                ]
            }
        }
    }
    contract = build_contract(issue)
    assert contract["parse_status"]["pr_url_count"] == 2
    assert contract["parse_status"]["repo_url_count"] == 2
    assert contract["parse_status"]["parse_failed"] is False
    assert contract["deploy_fields"]["apenas_proc"] is False
    cell = G.montador_pr_cell(contract)
    assert "sla-api #195" in cell
    assert "newcontract-front #1112" in cell
    assert "<br>" in cell


def test_pb_5085_three_prs():
    """PB-5085: 3 PRs esperadas (autocadastro-api #348, autocadastro-front #228, newcontract-front #1178)."""
    issue = {
        "key": "PB-5085",
        "fields": {
            "summary": "Test issue",
            "issuetype": {"name": "Task"},
            "status": {"name": "In Progress"},
            "assignee": {"displayName": "John Doe", "accountId": "123"},
            "customfield_12400": {
                "version": 1,
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "inlineCard",
                                "attrs": {"url": "https://bitbucket.org/bernhoeft/newcontract-front/pull-requests/1178"}
                            }
                        ]
                    },
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "inlineCard",
                                "attrs": {"url": "https://bitbucket.org/bernhoeft/autocadastro-front/pull-requests/228"}
                            }
                        ]
                    },
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "inlineCard",
                                "attrs": {"url": "https://bitbucket.org/bernhoeft/autocadastro-api/pull-requests/348"}
                            }
                        ]
                    }
                ]
            }
        }
    }
    contract = build_contract(issue)
    assert contract["parse_status"]["pr_url_count"] == 3
    cell = G.montador_pr_cell(contract)
    assert "autocadastro-api #348" in cell
    assert "autocadastro-front #228" in cell
    assert "newcontract-front #1178" in cell


def test_pb_4969_two_prs():
    """PB-4969: 2 PRs (centraldocumentos-api #96, front #1180). Normaliza /src/master/ fora do repo."""
    issue = {
        "key": "PB-4969",
        "fields": {
            "summary": "Test issue",
            "issuetype": {"name": "Task"},
            "status": {"name": "In Progress"},
            "assignee": {"displayName": "John Doe", "accountId": "123"},
            "customfield_12400": {
                "version": 1,
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "inlineCard",
                                "attrs": {"url": "https://bitbucket.org/bernhoeft/centraldocumentos-api/src/master/"}
                            }
                        ]
                    },
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "inlineCard",
                                "attrs": {"url": "https://bitbucket.org/bernhoeft/front/pull-requests/1180"}
                            }
                        ]
                    }
                ]
            }
        }
    }
    contract = build_contract(issue)
    assert contract["parse_status"]["pr_url_count"] == 1
    cell = G.montador_pr_cell(contract)
    assert "front #1180" in cell


def test_markdown_regression_parse_failed():
    """Regressão markdown: campo string com inlineCard renderizado sem URL -> parse_failed=True."""
    issue = {
        "key": "PB-TEST",
        "fields": {
            "summary": "Test issue",
            "issuetype": {"name": "Task"},
            "status": {"name": "In Progress"},
            "assignee": {"displayName": "John Doe", "accountId": "123"},
            "customfield_12400": "[Card]"
        }
    }
    contract = build_contract(issue)
    assert contract["parse_status"]["pr_url_count"] == 0
    assert contract["parse_status"]["parse_failed"] is True


def test_db_owner_apenas_proc():
    """Só-banco legítimo: acao_dados=Sim, 0 PR, owner 'Alexandre Bolonhini' -> apenas_proc=True."""
    issue = {
        "key": "PB-5778",
        "fields": {
            "summary": "Test issue",
            "issuetype": {"name": "Task"},
            "status": {"name": "In Progress"},
            "assignee": {"displayName": "Alexandre Bolonhini", "accountId": "123"},
            "customfield_12297": {"value": "Sim"},
            "customfield_12400": None,
            "customfield_12399": None
        }
    }
    contract = build_contract(issue)
    assert contract["deploy_fields"]["apenas_proc"] is True
    assert contract["parse_status"]["parse_failed"] is False
    cell = G.montador_pr_cell(contract)
    assert cell == "• APENAS PROC"
    rules = {"db_owners": ["Alexandre Bolonhini", "Alexandre Rudoi"]}
    verdict, _ = G.eligibility_v2(contract, rules)
    assert verdict == "aprovado"


def test_eligibility_approval_with_code():
    """Elegibilidade: PR + repositorio -> aprovado."""
    contract = {
        "card_id": "PB-TEST",
        "deploy_fields": {"acao_dados": None},
        "parse_status": {"parse_failed": False, "pr_url_count": 1, "repo_url_count": 1},
        "links": {"pull_requests": [{"label": "test #1", "url": "https://..."}]}
    }
    rules = {}
    verdict, _ = G.eligibility_v2(contract, rules)
    assert verdict == "aprovado"


def test_eligibility_rejection_no_data():
    """Elegibilidade: sem PR, sem repo, sem acao de dados -> reprovado."""
    contract = {
        "card_id": "PB-TEST",
        "deploy_fields": {"acao_dados": None},
        "parse_status": {"parse_failed": False, "pr_url_count": 0, "repo_url_count": 0},
        "links": {"pull_requests": []}
    }
    rules = {"db_owners": []}
    verdict, _ = G.eligibility_v2(contract, rules)
    assert verdict == "reprovado"


def test_d1_epic_all_or_nothing():
    """D1: card com epic.key='PB-5768' -> excluido com reason contendo 'D1: epico PB-5768'."""
    cards = {
        "PB-CHILD": {
            "card_id": "PB-CHILD",
            "epic": {"key": "PB-5768", "summary": "Refactoring"},
            "deploy_fields": {},
            "parse_status": {},
            "links": {"pull_requests": []}
        }
    }
    rules = {"epicos_all_or_nothing": ["PB-5768"]}
    kept, excluded = G.apply_d1(["PB-CHILD"], cards, rules, {})
    assert len(kept) == 0
    assert len(excluded) == 1
    assert "D1: epico PB-5768" in excluded[0]["reason"]


def test_d2_partial_shared_pr():
    """D2: dois cards compartilham PR; um aprovado, outro não -> exclui o aprovado."""
    cards = {
        "PB-A": {
            "card_id": "PB-A",
            "links": {"pull_requests": [{"label": "shared", "url": "https://shared"}]}
        },
        "PB-B": {
            "card_id": "PB-B",
            "links": {"pull_requests": [{"label": "shared", "url": "https://shared"}]}
        }
    }
    kept, excluded = G.apply_d2(["PB-A"], cards)
    assert len(kept) == 0
    assert len(excluded) == 1
    assert "D2:" in excluded[0]["reason"]


def test_crosscheck_parse_failed_approved():
    """GATE-CROSSCHECK: card com parse_failed=true não deve estar nos aprovados."""
    cards = {
        "PB-BAD": {
            "card_id": "PB-BAD",
            "deploy_fields": {"apenas_proc": False},
            "parse_status": {"parse_failed": True, "pr_url_count": 0, "repo_url_count": 0},
            "links": {"pull_requests": []}
        }
    }
    errors = G.crosscheck(cards, {"PB-BAD"})
    assert len(errors) == 1
    assert "parse_failed=true" in errors[0]
    assert "PB-BAD" in errors[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
