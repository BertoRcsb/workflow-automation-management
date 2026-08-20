#!/usr/bin/env python3
"""optimus_next_version.py - GATE-VER-1/2/3: versao-alvo deterministica.

Recebe o dump da consulta ao Notion (JSON ou texto qualquer contendo as versoes
existentes; aceita varios arquivos, um por pagina da consulta), extrai todos os
tokens semver X.Y.Z, calcula a MAIOR por ordenacao NUMERICA (GATE-VER-1: nunca
por data de criacao) e propoe a proxima release X.(Y+1).0. GATE-VER-2
(anti-colisao): falha se a proposta ja existir na base (numeracao
dessincronizada -> decisao do Ronan). GATE-VER-3 (completude): falha se o dump
terminar com "has_more": true - a consulta veio paginada e faltam paginas;
refazer com cursor ate has_more=false. O LLM nao calcula versao de cabeca - le
a saida deste script.

Uso:
    python3 tools/optimus_next_version.py <dump_notion.json> [dump2.json ...]
    ... | python3 tools/optimus_next_version.py -

Saida em chave=valor + exit code (0 = ok / 1 = falha), no padrao dos gates.
"""
import re
import sys

SEMVER = re.compile(r"\b(\d+)\.(\d+)\.(\d+)\b")
HAS_MORE = re.compile(r'"has_more"\s*:\s*(true|false)')


def extract_versions(text):
    """Todas as versoes X.Y.Z do texto, como tuplas de int, dedupe."""
    return sorted({tuple(int(g) for g in m.groups()) for m in SEMVER.finditer(text)})


def fmt(v):
    return ".".join(str(n) for n in v)


def main(argv):
    if len(argv) < 2:
        print("ok=false motivo=uso_invalido esperado='<dump_notion.json> [dump2 ...]|-'")
        return 1
    chunks = []
    for arg in argv[1:]:
        src = sys.stdin if arg == "-" else open(arg, encoding="utf-8")
        try:
            chunks.append(src.read())
        except OSError as exc:
            print(f"ok=false motivo=leitura_falhou detalhe={exc!r}")
            return 1
        finally:
            if src is not sys.stdin:
                src.close()
    text = "\n".join(chunks)

    flags = HAS_MORE.findall(text)
    if flags and flags[-1] == "true":  # GATE-VER-3
        print("ok=false motivo=dump_paginado_incompleto has_more=true")
        print("acao=refazer_consulta_paginando_ate_has_more_false")
        return 1

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

    aviso = "" if flags else " aviso=has_more_ausente_no_dump"
    print(f"ok=true maior={fmt(maior)} proxima={fmt(proxima)} versoes_na_base={len(versions)}{aviso}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
