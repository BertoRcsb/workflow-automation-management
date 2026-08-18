#!/usr/bin/env python3
"""optimus_extract.py - contrato normalizado (spec §7) a partir do JSON CRU de issues do Jira.

O LLM NAO interpreta ADF: busca via MCP (getJiraIssue com responseContentFormat="adf"),
salva o cru e roda este script. Deterministico, stdlib apenas, sem rede.

Uso:
    python3 tools/optimus_extract.py <raw_issues.json> [remote_links.json] > contrato.json

Entrada: um issue, uma lista de issues, ou {"issues":[...]} (formato do searchJiraIssuesUsingJql).
remote_links.json (opcional): { "PB-5528": ["https://.../pull-requests/195", ...], ... }
"""
import json, sys
from urllib.parse import urlsplit, unquote

PR_FIELD = "customfield_12400"
REPO_FIELD = "customfield_12399"
ACAO_DADOS_FIELD = "customfield_12297"
MERGE_FIELD = "customfield_12401"
PRODUTO_FIELD = "customfield_11993"


def walk_urls(node, out):
    """Anda o ADF recursivamente e coleta URL de cards/links e URLs cruas em texto."""
    if isinstance(node, dict):
        t = node.get("type")
        attrs = node.get("attrs") or {}
        if t in ("inlineCard", "blockCard", "embedCard", "smartCard"):
            u = attrs.get("url")
            if u:
                out.append(u)
        if t == "text":
            for m in (node.get("marks") or []):
                if m.get("type") == "link":
                    href = (m.get("attrs") or {}).get("href")
                    if href:
                        out.append(href)
            txt = (node.get("text") or "").strip()
            if txt.startswith(("http://", "https://")):
                out.append(txt)
        for v in node.values():
            walk_urls(v, out)
    elif isinstance(node, list):
        for v in node:
            walk_urls(v, out)


def extract_text_from_adf(field):
    """Extrai texto literal do ADF."""
    if not field or not isinstance(field, dict):
        return ""
    texts = []
    if 'content' in field:
        for item in field['content']:
            if isinstance(item, dict) and 'content' in item:
                for subitem in item['content']:
                    if isinstance(subitem, dict) and 'text' in subitem:
                        texts.append(subitem['text'])
    return ' '.join(texts).strip()


def field_has_real_content(field):
    """Verifica se o field tem conteúdo REAL (não é "Não tem" / "N/A" / vazio)."""
    if not field:
        return False
    if isinstance(field, str):
        text = field.strip()
        return text and text not in ("N/A", "Não tem.", "Não tem")
    if isinstance(field, dict):
        text = extract_text_from_adf(field)
        # Se o único conteúdo é "Não tem" ou "N/A", considerar como sem conteúdo real
        return text and text not in ("N/A", "Não tem.", "Não tem")
    return bool(field)


def field_has_content(field):
    """Compatibilidade: verifica se field tem qualquer conteúdo (até "Não tem")."""
    if not field:
        return False
    if isinstance(field, str):
        return bool(field.strip())
    if isinstance(field, dict):
        return bool(field.get("content"))
    return bool(field)


def dedup(seq):
    seen, out = set(), []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def norm_pr(url):
    parts = [unquote(p) for p in urlsplit(url).path.split("/") if p]
    if "pull-requests" in parts:
        i = parts.index("pull-requests")
        repo = parts[i - 1] if i >= 1 else "?"
        num = parts[i + 1] if i + 1 < len(parts) else "?"
        workspace = parts[0] if parts else "bernhoeft"
        canon = f"https://bitbucket.org/{workspace}/{repo}/pull-requests/{num}"
        return {"repo": repo, "num": num, "url": canon, "label": f"{repo} #{num}"}
    return None


def norm_repo(url):
    parts = [unquote(p) for p in urlsplit(url).path.split("/") if p]
    if len(parts) >= 2:
        return {"repo": parts[1], "url": f"https://bitbucket.org/{parts[0]}/{parts[1]}"}
    return None


def extract_field_urls(field):
    urls = []
    walk_urls(field, urls)
    return dedup(urls)


def select_value(field):
    if field is None:
        return None
    if isinstance(field, str):
        return field
    if isinstance(field, dict):
        return field.get("value")
    if isinstance(field, list) and field:
        f0 = field[0]
        return f0.get("value") if isinstance(f0, dict) else f0
    return None


def build_contract(issue, remote_pr_urls=None):
    key = issue.get("key")
    f = issue.get("fields") or {}
    pr_field = f.get(PR_FIELD)
    repo_field = f.get(REPO_FIELD)

    pr_raw = extract_field_urls(pr_field)
    for u in (remote_pr_urls or []):
        if "pull-requests" in u:
            pr_raw.append(u)
    pr_raw = dedup(pr_raw)

    repo_raw = [u for u in extract_field_urls(repo_field) if "pull-requests" not in u]

    prs = dedup_by(
        [p for p in (norm_pr(u) for u in pr_raw) if p], key="url"
    )
    prs.sort(key=lambda p: p["url"])
    repos = dedup_by(
        [r for r in (norm_repo(u) for u in repo_raw) if r], key="url"
    )
    repos.sort(key=lambda r: r["url"])

    pr_parse_failed = field_has_real_content(pr_field) and len(prs) == 0
    repo_parse_failed = field_has_real_content(repo_field) and len(repos) == 0
    parse_failed = bool(pr_parse_failed or repo_parse_failed)

    acao_dados = select_value(f.get(ACAO_DADOS_FIELD))
    merge = select_value(f.get(MERGE_FIELD))
    produto = select_value(f.get(PRODUTO_FIELD))
    apenas_proc = (
        acao_dados == "Sim" and len(prs) == 0 and len(repos) == 0 and not parse_failed
    )

    parent = f.get("parent") or {}
    epic = None
    if parent and isinstance(parent, dict):
        epic = {"key": parent.get("key"), "summary": (parent.get("fields") or {}).get("summary")}
    assignee = f.get("assignee") or {}
    if assignee and isinstance(assignee, str):
        assignee = {}

    return {
        "card_id": key,
        "title": f.get("summary"),
        "issue_type": (f.get("issuetype") or {}).get("name"),
        "status": (f.get("status") or {}).get("name"),
        "owner": {"name": assignee.get("displayName"), "account_id": assignee.get("accountId")},
        "product": produto,
        "epic": epic,
        "summary": f.get("summary"),
        "links": {
            "jira": f"https://bernhoeft.atlassian.net/browse/{key}",
            "repositories": [r["url"] for r in repos],
            "pull_requests": [{"label": p["label"], "url": p["url"]} for p in prs],
        },
        "parse_status": {
            "parse_failed": parse_failed,
            "pr_url_count": len(prs),
            "repo_url_count": len(repos),
        },
        "deploy_fields": {
            "acao_dados": acao_dados, "acao_infra": None, "merge_realizado": merge,
            "apenas_proc": apenas_proc, "proc_name": None,
        },
    }


def dedup_by(items, key):
    seen, out = set(), []
    for it in items:
        if it[key] not in seen:
            seen.add(it[key])
            out.append(it)
    return out


def load_issues(path):
    data = json.load(open(path, encoding="utf-8"))
    if isinstance(data, dict):
        if "issues" in data:
            return data["issues"]
        if "key" in data:
            return [data]
    if isinstance(data, list):
        return data
    raise SystemExit("entrada invalida: esperado issue, lista, ou {issues:[]}")


def load_remote(path):
    if not path:
        return {}
    try:
        return json.load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        return {}


def main():
    if len(sys.argv) < 2:
        raise SystemExit("uso: optimus_extract.py <raw_issues.json> [remote_links.json]")
    issues = load_issues(sys.argv[1])
    remote = load_remote(sys.argv[2] if len(sys.argv) > 2 else None)
    contract = [build_contract(i, remote.get(i.get("key"))) for i in issues]
    json.dump(contract, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
