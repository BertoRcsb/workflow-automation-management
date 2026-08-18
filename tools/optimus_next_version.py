#!/usr/bin/env python3
"""optimus_next_version.py - GATE-VER-1/2: versao-alvo deterministica.

Recebe o dump da consulta ao Notion (JSON ou texto qualquer contendo as versoes
existentes), extrai todos os tokens semver X.Y.Z, calcula a MAIOR por ordenacao
NUMERICA (GATE-VER-1: nunca por data de criacao) e propoe a proxima release
X.(Y+1).0. GATE-VER-2 (anti-colisao): falha se a proposta ja existir na base
(numeracao dessincronizada -> decisao do Ronan). O LLM nao calcula versao de
cabeca - le a saida deste script.

Uso:
    python3 tools/optimus_next_version.py <dump_notion.json>
    ... | python3 tools/optimus_next_version.py -

Saida em chave=valor + exit code (0 = ok / 1 = falha), no padrao dos gates.
"""
import re
import sys

SEMVER = re.compile(r"\b(\d+)\.(\d+)\.(\d+)\b")


def extract_versions(text):
    """Todas as versoes X.Y.Z do texto, como tuplas de int, dedupe."""
    return sorted({tuple(int(g) for g in m.groups()) for m in SEMVER.finditer(text)})


def fmt(v):
    return ".".join(str(n) for n in v)


def main(argv):
    if len(argv) != 2:
        print("ok=false motivo=uso_invalido esperado='<dump_notion.json>|-'")
        return 1
    src = sys.stdin if argv[1] == "-" else open(argv[1], encoding="utf-8")
    try:
        text = src.read()
    except OSError as exc:
        print(f"ok=false motivo=leitura_falhou detalhe={exc!r}")
        return 1
    finally:
        if src is not sys.stdin:
            src.close()

    versions = extract_versions(text)
    if not versions:
        print("ok=false motivo=nenhuma_versao_encontrada_no_dump")
        return 1

    maior = versions[-1]
    proxima = (maior[0], maior[1] + 1, 0)
    existentes = set(versions)

    if proxima in existentes:  # GATE-VER-2
        print(f"ok=false motivo=colisao_numeracao_dessincronizada maior={fmt(maior)} proposta={fmt(proxima)}")
        print("acao=parar_e_pedir_decisao_do_ronan")
        return 1

    print(f"ok=true maior={fmt(maior)} proxima={fmt(proxima)} versoes_na_base={len(versions)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
