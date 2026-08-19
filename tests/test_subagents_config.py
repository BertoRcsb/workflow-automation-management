#!/usr/bin/env python3
"""Testes de configuração dos subagentes canônicos."""

import json
import os
import sys
from pathlib import Path

def test_four_canonical_subagents_exist():
    """Validar que os 4 subagentes canônicos existem."""
    agents_dir = '.claude/agents'
    required_agents = ['coletor', 'validador', 'montador', 'notificador-sandbox']

    for agent in required_agents:
        filepath = os.path.join(agents_dir, f'{agent}.md')
        assert os.path.isfile(filepath), f"Subagente {agent} não encontrado em {filepath}"

    print(f"✓ 4 subagentes canônicos existem: {', '.join(required_agents)}")


def test_no_auditor_release():
    """Validar que auditor-release NÃO existe."""
    filepath = '.claude/agents/auditor-release.md'
    assert not os.path.isfile(filepath), f"auditor-release.md não deve existir: {filepath}"
    print("✓ auditor-release.md não existe")


def test_no_guard_scripts():
    """Validar que scripts de guard não existem."""
    guard_scripts = [
        'tools/optimus_agent_guard.py',
        'tools/optimus_handoff.py',
        'tools/optimus_release_audit.py',
        'tools/optimus_sync_guard.py',
    ]

    for script in guard_scripts:
        assert not os.path.isfile(script), f"Script {script} não deve existir"

    print(f"✓ Scripts de guard foram removidos: {len(guard_scripts)} validados")


def test_subagent_frontmatter():
    """Validar frontmatter YAML dos 4 subagentes."""
    agents = ['coletor', 'validador', 'montador', 'notificador-sandbox']

    for agent_name in agents:
        filepath = f'.claude/agents/{agent_name}.md'
        with open(filepath, 'r') as f:
            content = f.read()

        # Verificar que começa com ---
        assert content.startswith('---'), f"{agent_name}: sem frontmatter"

        # Verificar campos obrigatórios
        assert f'name: {agent_name}' in content, f"{agent_name}: sem 'name' correto"
        assert 'description:' in content, f"{agent_name}: sem 'description'"
        assert 'model: haiku' in content, f"{agent_name}: sem 'model: haiku'"
        assert 'permissionMode: dontAsk' in content, \
            f"{agent_name}: deve executar ferramentas permitidas sem prompts intermediários"

        # Verificar que validador, montador e notificador têm Agent explicitamente proibido
        if agent_name in ['validador', 'montador', 'notificador-sandbox']:
            assert 'Agent' in content, f"{agent_name}: Agent não está listado em disallowedTools"

        # Verificar que não tem hooks de guard
        assert 'optimus_agent_guard' not in content, f"{agent_name}: ainda tem referência a optimus_agent_guard"
        assert 'optimus_handoff' not in content, f"{agent_name}: ainda tem referência a optimus_handoff"

        print(f"✓ {agent_name}: frontmatter válido")


def test_optimus_prime_no_auditor():
    """Validar que optimus-prime.md não menciona auditor-release."""
    with open('.claude/commands/optimus-prime.md', 'r') as f:
        content = f.read()

    assert 'auditor-release' not in content.lower(), \
        "optimus-prime.md ainda menciona auditor-release"
    assert 'optimus_handoff' not in content, \
        "optimus-prime.md ainda menciona optimus_handoff"

    print("✓ optimus-prime.md sem referências a auditor-release ou optimus_handoff")


def test_settings_no_guard_permissions():
    """Validar que settings.local.json não tem permissões para scripts removidos."""
    with open('.claude/settings.local.json', 'r') as f:
        settings = json.load(f)

    all_rules = settings.get('permissions', {}).get('allow', [])

    dangerous_patterns = [
        'optimus_agent_guard',
        'optimus_handoff',
        'optimus_release_audit',
        'optimus_sync_guard',
    ]

    for rule in all_rules:
        for pattern in dangerous_patterns:
            assert pattern not in rule, \
                f"Permissão para script removido encontrada: {rule}"

    print("✓ settings.local.json sem permissões para scripts removidos")


def test_four_subagents_have_agent_disabled():
    """Validar que validador, montador e notificador proíbem Agent."""
    restricted_agents = ['validador', 'montador', 'notificador-sandbox']

    for agent in restricted_agents:
        filepath = f'.claude/agents/{agent}.md'
        with open(filepath, 'r') as f:
            content = f.read()

        assert 'disallowedTools' in content, \
            f"{agent}: não tem disallowedTools"
        assert 'Agent' in content, \
            f"{agent}: Agent não está em disallowedTools"

    print("✓ Validador, Montador e Notificador proíbem Agent")


def test_old_test_file_removed():
    """Validar que test_optimus_security.py foi removido."""
    filepath = 'tests/test_optimus_security.py'
    assert not os.path.isfile(filepath), \
        f"test_optimus_security.py (da tentativa anterior) não deve existir"

    print("✓ test_optimus_security.py foi removido")


def test_optimus_autonomy_contract():
    """Modo + alvo autorizam a esteira até o dry-run, sem plano ou microaprovação."""
    command = open('.claude/commands/optimus-prime.md', encoding='utf-8').read()
    skill = open('.claude/skills/orquestrador/SKILL.md', encoding='utf-8').read()

    assert 'Autonomia operacional obrigatória' in command
    assert 'não apresente plano antes de trabalhar' in command
    assert 'primeiro gate conversacional' in command.lower()
    assert 'Somente quatro subagentes' in skill
    assert 'refinamento automático obrigatório para `parse_failed`' in skill
    assert '**apresenta ANTES o que vai fazer**' not in skill


def test_pipeline_permissions_do_not_ask():
    """Ações canônicas não podem cair no prompt de permissão do Claude Code."""
    settings = json.load(open('.claude/settings.local.json', encoding='utf-8'))
    ask = settings['permissions'].get('ask', [])
    deny = settings['permissions'].get('deny', [])

    assert not any('dry-run' in rule for rule in ask)
    assert not any('repos.yaml' in rule for rule in ask)
    assert set(ask) == {
        'Bash(git add *)',
        'Bash(git commit *)',
        'Bash(python3 tools/optimus_sync.py run *)',
        'Bash(python3 tools/optimus_sync.py run-triggers)',
    }
    assert 'Bash(make -C /home/ronan/sync-repos-from-master *)' in deny
    assert 'Write(//home/ronan/sync-repos-from-master/**)' in deny


if __name__ == '__main__':
    os.chdir(Path(__file__).resolve().parents[1])

    tests = [
        test_four_canonical_subagents_exist,
        test_no_auditor_release,
        test_no_guard_scripts,
        test_subagent_frontmatter,
        test_optimus_prime_no_auditor,
        test_settings_no_guard_permissions,
        test_four_subagents_have_agent_disabled,
        test_old_test_file_removed,
        test_optimus_autonomy_contract,
        test_pipeline_permissions_do_not_ask,
    ]

    failed = 0
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1

    print(f"\n{len(tests) - failed}/{len(tests)} testes passaram")
    sys.exit(0 if failed == 0 else 1)
