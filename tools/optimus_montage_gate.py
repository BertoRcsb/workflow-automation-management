#!/usr/bin/env python3
"""optimus_montage_gate.py - GATE-MONTAGEM deterministico (fecha o buraco de 2026-08-19).

A montagem era a UNICA etapa da esteira sem verificacao em codigo: os gates do
montador (CONJUNTO/MOLDE/LINKS/IDEMPOT) eram prosa auto-certificada pelo modelo mais
barato. Em 2026-08-19 o montador reportou tudo "PASSOU" mas criou a pagina 1.121.1
ORFA (fora da base, sem Tipo), com Participantes vazios. Este gate le o conteudo REAL
da pagina (saida do notion-fetch salva em disco pelo montador/Optimus) e falha fechado.

Uso:
    python3 tools/optimus_montage_gate.py \
        --page-json <notion_fetch_salvo.json> \
        --gates <gates.json> \
        --roster tools/deploy_roster.json \
        --version 1.121.1 --tipo Hotfix \
        --data-source 23e19d89-2318-81ff-812d-000b6afb6b5a \
        [--assignees "Nome A,Nome B"]

Saida chave=valor + exit code (0 = ok / 1 = falha), no padrao dos gates.
O LLM nao decide se "passou" - le a saida deste script.
"""
import argparse
import json
import sys

COLUNAS = ["Item", "Pull Requests", "Tem Ação de Banco ?", "Tem Ação de Infra ?", "Merge Realizado ?"]


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def page_text(page_json):
    """Extrai o texto/markdown da pagina de varias formas de saida do notion-fetch."""
    if isinstance(page_json, str):
        return page_json
    if isinstance(page_json, dict):
        for key in ("text", "content", "output"):
            if isinstance(page_json.get(key), str):
                return page_json[key]
    return json.dumps(page_json, ensure_ascii=False)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--page-json", required=True)
    ap.add_argument("--gates", required=True)
    ap.add_argument("--roster", required=True)
    ap.add_argument("--version", required=True)
    ap.add_argument("--tipo", required=True, choices=["Release", "Hotfix"])
    ap.add_argument("--data-source", required=True)
    ap.add_argument("--assignees", default="")
    args = ap.parse_args(argv[1:])

    fails = []

    try:
        text = page_text(load_json(args.page_json))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ok=false etapa=GATE-MONTAGEM motivo=page_json_ilegivel detalhe={exc!r}")
        return 1

    try:
        gates = load_json(args.gates)
        roster = load_json(args.roster)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ok=false etapa=GATE-MONTAGEM motivo=insumo_ilegivel detalhe={exc!r}")
        return 1

    ds = args.data_source.replace("-", "")
    text_nodash = text.replace("-", "")

    # 1. Pagina DENTRO da base (nao orfa). O fetch de pagina-linha traz o
    #    ancestor parent-data-source collection://<data_source>.
    if ds not in text_nodash:
        fails.append("pagina_orfa_ou_fora_da_base(sem_parent_data_source)")

    # 2. Propriedades da base: Tipo e Versao (title). Numa pagina orfa so ha
    #    {"title": ...} e estes checks caem juntos, reforcando o item 1.
    if f'"Tipo":"{args.tipo}"' not in text.replace(" ", ""):
        fails.append(f"tipo_incorreto(esperado={args.tipo})")
    if f'"Versão":"{args.version}"' not in text.replace(" ", ""):
        fails.append(f"versao_property_ausente(esperado={args.version})")

    # 3. Colunas da tabela, exatas.
    for col in COLUNAS:
        if col not in text:
            fails.append(f"coluna_ausente({col})")

    # 4. Cada card aprovado presente + celula de PR do contrato presente.
    rows = gates.get("rows", [])
    if not rows:
        fails.append("gates_sem_rows")
    for row in rows:
        cid = row.get("card_id", "")
        if cid and cid not in text:
            fails.append(f"card_ausente({cid})")
        pr_cell = (row.get("pull_requests") or "").strip()
        # confere so os URLs (o texto do link pode variar por escaping do Notion)
        for token in pr_cell.split("<br>"):
            token = token.strip()
            if token.startswith("[") and "](" in token:
                url = token.split("](", 1)[1].rstrip(")")
                if url and url not in text:
                    fails.append(f"pr_url_ausente({cid}:{url})")

    # 5. Participantes: elenco canonico presente e NAO vazio.
    for papel, nomes in roster.items():
        if papel.startswith("_"):
            continue
        if papel not in text:
            fails.append(f"participante_papel_ausente({papel})")
            continue
        for nome in nomes:
            if nome not in text:
                fails.append(f"participante_nome_ausente({papel}:{nome})")

    # 6. Sobreaviso = assignees dos cards aprovados.
    assignees = [a.strip() for a in args.assignees.split(",") if a.strip()]
    if assignees and "sobreaviso" not in text.lower():
        fails.append("bloco_sobreaviso_ausente")
    for nome in assignees:
        if nome not in text:
            fails.append(f"sobreaviso_assignee_ausente({nome})")

    # 7. Microformatacao canonica (incidente 2026-08-19: blocos como H2 e papeis
    #    sem {color=brown}). Sintaxe literal confirmada nas paginas 1.118.1/1.120.0.
    obrigatorios = [
        "**Testes regressivos**",
        "**Ambientes**",
        "**Repositórios para Deploy:**",
        '## <span underline="true">Participantes do Deploy:</span>',
    ]
    for tok in obrigatorios:
        if tok not in text:
            fails.append(f"microformato_ausente({tok})")
    if "- [ ] Prod" not in text and "- [x] Prod" not in text:
        fails.append("ambiente_prod_ausente")
    papeis = [p for p in roster if not p.startswith("_")] + ["Desenvolvedores sobreaviso"]
    for papel in papeis:
        if f'**{papel}:** {{color="brown"}}' not in text:
            fails.append(f"papel_sem_negrito_marrom({papel})")
        for h in ("## ", "### "):
            if f"{h}{papel}" in text:
                fails.append(f"papel_como_heading_proibido({h.strip()} {papel})")
    for bloco in ("Testes regressivos", "Ambientes", "Repositórios para Deploy"):
        for h in ("## ", "### "):
            if f"{h}{bloco}" in text:
                fails.append(f"bloco_como_heading_proibido({h.strip()} {bloco})")
    # nomes com ponto final, como nas paginas reais
    todos_nomes = [n for ns in roster.values() if isinstance(ns, list) for n in ns] + assignees
    for nome in todos_nomes:
        if nome in text and f"{nome}." not in text:
            fails.append(f"nome_sem_ponto_final({nome})")

    if fails:
        print(f"ok=false etapa=GATE-MONTAGEM version={args.version} tipo={args.tipo} falhas={len(fails)}")
        for f in fails:
            print(f"  falha={f}")
        return 1

    print(f"ok=true etapa=GATE-MONTAGEM version={args.version} tipo={args.tipo} "
          f"cards={len(rows)} participantes_ok=true na_base=true")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
