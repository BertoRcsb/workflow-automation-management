#!/usr/bin/env python3
"""optimus_yaml_gate.py — Gate deterministico do repos.yaml.

Garante que a edicao do repos.yaml pelo Optimus foi APENAS comentar/descomentar
linhas que ja existiam: nenhum valor alterado, nenhuma linha adicionada/removida,
nenhuma reordenacao. Uso:

    python3 tools/optimus_yaml_gate.py <antes.yaml> <depois.yaml>

Saida em chave=valor + exit code (0 = ok / 1 = violacao), no padrao dos outros gates.
"""
import re
import sys


def logical_lines(path):
    """Linhas 'logicas' do arquivo: sem indentacao, sem '#' de comentario, sem
    espacos nas bordas; linhas vazias descartadas. Comentar/descomentar NAO muda
    esta lista; qualquer edicao de conteudo (valor/linha nova/remocao/reordem) muda."""
    out = []
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            norm = re.sub(r"^\s*#*\s*", "", raw).rstrip()
            if norm:
                out.append(norm)
    return out


def _is_source_scalar(l):
    """Verifica se a linha eh uma source: COM valor (defaults.source).
    A chave-pai `source:` do cloud_build (sem valor) nao conta."""
    return l.startswith("source:") and l.strip() != "source:"


def _partition_source(lines):
    """Separa a linha `source:` COM VALOR (defaults.source) do resto das linhas logicas."""
    src = [l for l in lines if _is_source_scalar(l)]
    rest = [l for l in lines if not _is_source_scalar(l)]
    return src, rest


def main(argv):
    if len(argv) != 3:
        print("ok=false motivo=uso_invalido esperado='antes.yaml depois.yaml'")
        return 1
    before, after = argv[1], argv[2]
    a = logical_lines(before)
    b = logical_lines(after)
    if a == b:
        print("ok=true motivo=somente_comentarios_alterados")
        return 0
    # Excecao controlada: a UNICA linha de conteudo que muda por passo e o escalar
    # `defaults.source` (Passo 1/2/pos-deploy). Todo o resto (repos, defaults,
    # cloud_build) permanece imutavel. A SEGURANCA do novo valor de source e
    # responsabilidade do GATE-PROMO (tools/optimus_promotion_gate.py), nao deste.
    src_a, rest_a = _partition_source(a)
    src_b, rest_b = _partition_source(b)
    if rest_a == rest_b and len(src_a) == 1 and len(src_b) == 1 and src_a != src_b:
        print("ok=true motivo=comentarios_e_source_alterados")
        print(f"source_antes={src_a[0]!r} source_depois={src_b[0]!r}")
        print("nota=validar o par source->target com o GATE-PROMO")
        return 0
    # Encontrar a primeira divergencia para reportar.
    n = min(len(a), len(b))
    idx = next((i for i in range(n) if a[i] != b[i]), n)
    print("ok=false motivo=conteudo_alterado_alem_de_comentarios")
    print(f"linhas_antes={len(a)} linhas_depois={len(b)} primeira_divergencia_idx={idx}")
    if idx < len(a):
        print(f"antes={a[idx]!r}")
    if idx < len(b):
        print(f"depois={b[idx]!r}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
