# Diagramas exportados — Apresentação

Imagens dos 11 diagramas Mermaid de [`../APRESENTACAO.md`](../APRESENTACAO.md), prontas para slides.

- **`.svg`** — vetorial, escala sem perder qualidade (preferir em slides/impressão).
- **`.png`** — rasterizado 2x, fundo branco (para ferramentas que não aceitam SVG).
- **`.mmd`** — fonte Mermaid de cada diagrama (regenerar com o comando abaixo).

| # | Seção | Arquivo |
|---|---|---|
| 1 | Sumário executivo | `01-sumario-executivo` |
| 2 | O problema | `02-problema` |
| 3 | Arquitetura em camadas | `03-arquitetura-camadas` |
| 4 | Papéis da esteira | `04-papeis` |
| 5 | Fluxo de execução | `05-fluxo-execucao` |
| 6 | Varredura "todos os boards" | `06-varredura-boards` |
| 7 | Regra de elegibilidade v2 | `07-regra-elegibilidade` |
| 8 | Promoção de branches e deploy | `08-promocao-branches` |
| 9 | Governança e segurança | `09-governanca-seguranca` |
| 10 | Ciclo E2E — Hotfix 1.111.2 | `10-ciclo-e2e-hotfix` |
| 11 | Roadmap / evolução | `11-roadmap` |

## Regenerar

Do diretório do repositório, com `node`/`npx` disponíveis:

```bash
cd docs/diagramas
for f in *.mmd; do
  npx -y @mermaid-js/mermaid-cli -i "$f" -o "${f%.mmd}.svg" -b white -p .puppeteer.json
  npx -y @mermaid-js/mermaid-cli -i "$f" -o "${f%.mmd}.png" -b white -s 2 -p .puppeteer.json
done
```

Os `.mmd` são extraídos dos blocos ```` ```mermaid ```` de `../APRESENTACAO.md`, na ordem das seções.
