# Site Curriculo Portfolio

## Project

This repository contains the personal portfolio of Aglalberto.

The main website is the professional portfolio/CV.

A new immersive autobiographical experience is being developed at:

`/aboutme`

## About Me experience

For every task related to `/aboutme`, read and follow:

@docs/aboutme-creative-brief.md

The creative brief is the source of truth for:
- narrative
- visual direction
- personal history
- professional behavior
- interaction design
- responsive behavior
- motion design
- accessibility
- performance
- copywriting

## Core principles

- Do not turn `/aboutme` into another résumé.
- The page should communicate who Aglalberto is and what it feels like to work with him.
- Treat personal photographs and historical assets as narrative evidence.
- Maintain factual accuracy. Never invent autobiographical information.
- Desktop and mobile may use different compositions and animation choreography.
- Performance, especially mobile performance, is a priority.
- Motion must support the narrative rather than exist only as decoration.
- PT-BR and English must both be supported.

## Technology

The existing site uses:
- HTML
- CSS
- Vanilla JavaScript

Keep this fundamental stack.

GSAP / ScrollTrigger are permitted where justified.

Three.js / WebGL may only be used when the narrative benefit clearly outweighs the performance cost.

## Working behavior

Do not assume the first visual result is definitive.

For meaningful implementations:

1. Understand the existing code.
2. Review the creative brief.
3. Inspect available assets.
4. Implement a complete first version.
5. Critically review the result as a Senior Product Designer and Senior Frontend Engineer.
6. Perform at least one meaningful refinement pass.
7. Test desktop and mobile.
8. Review accessibility and performance.
9. Only then consider the task complete.

Do not redesign unrelated parts of the existing portfolio unless explicitly requested.
## Textos e idiomas (i18n)

Todos os textos do portfólio ficam em `locales/pt-BR.json` e `locales/en.json`.
`/` é a página em português e `/en/` a página em inglês.

Para mudar um texto:
1. Edite o JSON (as duas versões).
2. Rode `python3 scripts/build-i18n.py`: ele reescreve `index.html` e gera `en/index.html` e `sitemap.xml`.
3. Suba os arquivos gerados junto.

Não edite `en/index.html` à mão. No HTML, os elementos usam `data-i18n`, `data-i18n-html`,
`data-i18n-list`, `data-i18n-type`, `data-i18n-attr` e `data-i18n-href` com a chave do JSON.
Novo idioma: crie `locales/<código>.json` com as mesmas chaves e acrescente-o em `LANGS`
(scripts/build-i18n.py) e `PATHS` (runtime no `<head>` do index.html).
