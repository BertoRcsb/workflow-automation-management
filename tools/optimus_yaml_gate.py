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
