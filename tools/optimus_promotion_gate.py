#!/usr/bin/env python3
"""optimus_promotion_gate.py - GATE-PROMO: valida a promocao de branches do Sync.

Le o `defaults.source` e `defaults.targets` efetivos (linhas NAO comentadas) do
`repos.yaml` do sync-repos-from-master e garante que o par `source -> targets` e
uma promocao SEGURA e permitida (whitelist em tools/promotion.json). Bloqueia a
causa-raiz do incidente 2026-08-04: `source: prerelease -> target: master`
(promocao direta pra prod, pulando o teste regressivo).

Invariantes duras (qualquer falha -> exit 1):
  1. source e todos os targets sao branches conhecidas.
  2. source nao vazio; ao menos um target ativo.
  3. source nao pode estar entre os targets (sem self-sync).
  4. o par (source, targets) tem de casar com UM passo declarado (whitelist);
     targets efetivos devem ser subconjunto dos targets do passo.
  5. prod (master) so recebe de `prod_requires_source` (teste_regressivo) -
     defesa em profundidade contra o "nunca direto pra master".
  6. se --step for informado, o passo detectado tem de ser exatamente ele
     (pega "quis Passo 2 mas o YAML ainda esta no source do Passo 1").

Uso:
    python3 tools/optimus_promotion_gate.py <repos.yaml> [--step passo1|passo2|pos-deploy] [--rules tools/promotion.json]

Saida em chave=valor + exit code (0 = ok / 1 = violacao), no padrao dos outros gates.
"""
import json
import os
import sys

DEFAULT_RULES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "promotion.json")


def _strip_comment(value):
    """Remove comentario inline YAML (' # ...') e aspas simples do valor escalar."""
    # corta a partir de um '#' precedido de espaco (comentario inline)
    for i in range(1, len(value)):
        if value[i] == "#" and value[i - 1] in " \t":
            value = value[:i]
            break
    return value.strip().strip("'\"")


def parse_defaults(path):
    """Extrai (source, targets) EFETIVOS do bloco `defaults:` do repos.yaml.

    Considera apenas linhas nao comentadas (primeiro caractere nao-espaco != '#').
    Parser deterministico para o formato fixo do catalogo (sem dependencia de PyYAML).
    Retorna (source|None, [targets], [avisos]).
    """
    source = None
    source_count = 0
    targets = []
    warnings = []

    in_defaults = False
    in_targets = False
    targets_indent = None

    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            stripped = line.strip()
            if not stripped:
                continue
            is_comment = stripped.startswith("#")
            indent = len(line) - len(line.lstrip(" "))

            # Fronteiras do bloco defaults: (chave de topo, coluna 0, nao-comentario).
            if not is_comment and indent == 0:
                key = stripped.split(":", 1)[0]
                in_defaults = key == "defaults"
                in_targets = False
                continue

            if not in_defaults:
                continue

            if is_comment:
                continue  # linhas comentadas nunca contam como valor efetivo

            # Dentro de targets: itens de lista mais indentados que a chave `targets:`.
            if in_targets:
                if stripped.startswith("- "):
                    targets.append(_strip_comment(stripped[2:]))
                    continue
                if stripped == "-":
                    warnings.append("target_vazio")
                    continue
                # qualquer outra chave encerra a lista de targets
                in_targets = False

            if stripped.startswith("source:"):
                val = _strip_comment(stripped.split(":", 1)[1])
                if val:
                    source = val
                    source_count += 1
                continue

            if stripped.startswith("targets:"):
                rest = _strip_comment(stripped.split(":", 1)[1])
                in_targets = True
                targets_indent = indent
                if rest and rest not in ("[]", "|", ">"):
                    warnings.append("targets_inline_nao_suportado")
                continue

    if source_count > 1:
        warnings.append("multiplas_linhas_source_ativas")
    return source, targets, warnings


def detect_step(source, targets, rules):
    """Retorna (step_name|None, motivo). Casa (source, targets) com um passo da whitelist."""
    tset = set(targets)
    matches = []
    for name, spec in rules.get("steps", {}).items():
        if spec.get("source") != source:
            continue
        allowed = set(spec.get("targets", []))
        if tset and tset.issubset(allowed):
            matches.append(name)
    if len(matches) == 1:
        return matches[0], "ok"
    if len(matches) > 1:
        return None, f"ambiguo:{','.join(sorted(matches))}"
    return None, "nenhum_passo_casa"


def evaluate(path, expected_step, rules):
    """Aplica as invariantes. Retorna (ok:bool, motivo:str, detalhes:dict)."""
    source, targets, warnings = parse_defaults(path)
    branches = set(rules.get("branches", []))
    prod_targets = set(rules.get("prod_targets", []))
    prod_src = rules.get("prod_requires_source")

    detalhes = {"source": source, "targets": ",".join(targets) or "-"}
    if warnings:
        detalhes["avisos"] = ",".join(warnings)

    if "multiplas_linhas_source_ativas" in warnings:
        return False, "multiplas_linhas_source_ativas", detalhes
    if not source:
        return False, "source_ausente", detalhes
    if not targets:
        return False, "targets_ausentes", detalhes
    if source not in branches:
        return False, f"source_desconhecido:{source}", detalhes
    desconhecidos = [t for t in targets if t not in branches]
    if desconhecidos:
        return False, f"target_desconhecido:{','.join(desconhecidos)}", detalhes
    if source in targets:
        return False, "source_igual_ao_target", detalhes

    # Defesa em profundidade: prod so recebe da fonte permitida (nunca direto pra master).
    for t in targets:
        if t in prod_targets and source != prod_src:
            return False, f"promocao_direta_pra_prod:{source}->{t}_exige_source={prod_src}", detalhes

    step, motivo = detect_step(source, targets, rules)
    if step is None:
        return False, f"promocao_fora_da_whitelist:{motivo}", detalhes
    detalhes["passo_detectado"] = step

    if expected_step and step != expected_step:
        return False, f"passo_diverge:esperado={expected_step}_detectado={step}", detalhes

    return True, f"promocao_segura:{step}", detalhes


def main(argv):
    args = argv[1:]
    if not args:
        print("ok=false motivo=uso_invalido esperado='<repos.yaml> [--step ...] [--rules ...]'")
        return 1
    path = None
    expected_step = None
    rules_path = DEFAULT_RULES
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--step":
            i += 1
            expected_step = args[i] if i < len(args) else None
        elif a == "--rules":
            i += 1
            rules_path = args[i] if i < len(args) else rules_path
        elif path is None:
            path = a
        i += 1

    if not path:
        print("ok=false motivo=repos_yaml_nao_informado")
        return 1
    try:
        rules = json.load(open(rules_path, encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"ok=false motivo=rules_invalido detalhe={exc!r}")
        return 1

    ok, motivo, detalhes = evaluate(path, expected_step, rules)
    campos = " ".join(f"{k}={v}" for k, v in detalhes.items())
    print(f"ok={'true' if ok else 'false'} motivo={motivo} {campos}".rstrip())
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
