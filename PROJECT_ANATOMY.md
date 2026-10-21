# Project Anatomy: plantao-ao-vivo
Generated: 2026-10-19 | 83 files | ~157.3K tokens if all read

## Structure
| Path | Lines | ~Tokens | Type |
|------|-------|---------|------|
| skills/sasi-ingest-export/scripts/build_passagem.py | 633 | 7.1K | source |
| skills/hemodinamica-calculada/scripts/calc_hemo.py | 588 | 6.0K | source |
| gerador/ficha_cola.py | 475 | 5.0K | source |
| tests/test_esteira.py | 412 | 5.2K | source |
| esteira/montar.py | 369 | 4.6K | source |
| esteira/processar.py | 286 | 3.3K | source |
| skills/sasi-ingest-export/scripts/checagens.py | 269 | 3.1K | source |
| gerador/validar.py | 259 | 3.2K | source |
| gerador/gerar_docx.py | 237 | 2.8K | source |
| gerador/preparar.py | 223 | 2.6K | source |
| tests/test_checagens.py | 183 | 2.2K | source |
| esteira/leitura.py | 157 | 1.9K | source |
| skills/sasi-ingest-export/scripts/labs.py | 154 | 1.8K | source |
| gerador/conferir.py | 146 | 1.5K | source |
| gerador/gerar_admissao.py | 132 | 1.4K | source |
| tests/test_dias.py | 122 | 1.6K | source |
| gerador/entrega.py | 113 | 1.2K | source |
| tests/test_validar.py | 111 | 1.3K | source |
| tests/test_conferir.py | 100 | 1.0K | source |
| tests/test_pagina.py | 95 | 1.1K | source |
| gerador/evolucao_anterior.py | 90 | 803 | source |
| tests/test_doutrina.py | 84 | 1.0K | source |
| tests/test_motor.py | 77 | 813 | source |
| tests/test_gerador.py | 63 | 686 | source |
| tests/test_janela.py | 58 | 661 | source |
| tests/test_admissao.py | 57 | 617 | source |
| tests/test_entrega.py | 57 | 678 | source |
| tests/pagina/teste_pagina.js | 56 | 854 | source |
| tests/test_evolucao_anterior.py | 56 | 520 | source |
| gerador/estilo.py | 52 | 621 | source |
| tests/test_preparar.py | 52 | 620 | source |
| tests/test_labs.py | 49 | 483 | source |
| gerador/office.py | 28 | 261 | source |
| gerador/exemplo/plantao-exemplo.json | 308 | 1.9K | config |
| skills/sasi-ingest-export/assets/payload-example.json | 254 | 1.5K | config |
| .github/workflows/plantao.yml | 65 | 557 | config |
| .github/workflows/testes.yml | 48 | 323 | config |
| skills/controles-vitais-janela/references/amostras/prescricao-uti2-2026-06-21.md | 1421 | 6.7K | docs |
| skills/controles-vitais-janela/references/amostras/sinais-uti2-2026-06-21.md | 426 | 3.2K | docs |
| skills/controles-vitais-janela/SKILL.md | 339 | 3.9K | docs |
| skills/sasi-ingest-export/SKILL.md | 301 | 4.6K | docs |
| skills/sasi-ingest-export/references/06-api-automation-prompts.md | 273 | 2.3K | docs |
| skills/sasi-ingest-export/references/01-schema-eventos-clinicos.md | 266 | 2.1K | docs |
| skills/sasi-ingest-export/references/02-extraction-dictionary.md | 237 | 2.7K | docs |
| skills/admissao-uti/SKILL.md | 206 | 2.9K | docs |
| skills/hemodinamica-calculada/references/01-formulas-cutoffs.md | 175 | 2.0K | docs |
| skills/sasi-ingest-export/references/03-clinical-sanity-checks.md | 167 | 2.3K | docs |
| skills/sasi-ingest-export/references/00-estilo-texto-clinico.md | 159 | 2.0K | docs |
| skills/analise-ecott/SKILL.md | 158 | 2.5K | docs |
| skills/hemodinamica-calculada/SKILL.md | 141 | 2.0K | docs |
| docs/BRIEFING.md | 133 | 1.4K | docs |
| skills/sasi-ingest-export/references/05-export-passagem-turno.md | 126 | 1.4K | docs |
| skills/analise-ecott/references/01-modo-A-pocus.md | 116 | 1.0K | docs |
| skills/analise-ecott/references/02-modo-B-laudo-formal.md | 114 | 1.0K | docs |
| gerador/schema-plantao.md | 113 | 1.9K | docs |
| extracao-web/README.md | 112 | 1.6K | docs |
| skills/analise-ecott/references/03-red-flags.md | 110 | 1.2K | docs |
| docs/DECISOES.md | 108 | 1.9K | docs |
| skills/analise-ecott/references/05-nota-template.md | 108 | 959 | docs |
| skills/hemodinamica-calculada/references/04-schema-supabase.md | 107 | 1.0K | docs |
| skills/hemodinamica-calculada/references/02-estimativa-vsve.md | 100 | 952 | docs |
| README.md | 96 | 1.4K | docs |
| skills/sasi-ingest-export/references/04-export-evolucao-template.md | 93 | 1.1K | docs |
| skills/sasi-ingest-export/references/07-export-prescricao-ordenada.md | 82 | 961 | docs |
| esteira/doutrina-leitura.md | 80 | 1.4K | docs |
| esteira/README.md | 72 | 939 | docs |
| skills/hemodinamica-calculada/references/03-perfis-choque-conduta.md | 72 | 1.0K | docs |
| skills/analise-ecott/references/04-protocolos-focados.md | 69 | 760 | docs |
| skills/plantao/SKILL.md | 69 | 1.3K | docs |
| skills/controles-vitais-janela/references/mapa-folha.md | 66 | 703 | docs |
| docs/instrucoes-projeto.md | 64 | 1.1K | docs |
| docs/formato-entrega.md | 63 | 1.0K | docs |
| skills/sasi-ingest-export/references/08-p0-banco-10ago.md | 63 | 976 | docs |
| skills/controles-vitais-janela/references/exemplo-resolvido.md | 61 | 494 | docs |
| CLAUDE.md | 58 | 890 | docs |
| skills/controles-vitais-janela/references/amostras/folha-uti2-2026-05-10.md | 55 | 526 | docs |
| esteira/requirements.txt | 3 | 39 | docs |
| gerador/requirements.txt | 1 | 4 | docs |
| extracao-web/extracao-controles-labs-prescricao.html | 1080 | 15.3K | other |
| tests/fixtures/leitura-ficticia.json | 512 | 1.9K | other |
| tests/fixtures/admissao-ficticia.txt | 43 | 287 | other |
| tests/fixtures/laudo-ficticio.txt | 29 | 319 | other |
| .gitignore | 17 | 64 | other |

## Summary
- Source: 33 files, ~66.5K tokens
- Config: 4 files, ~4.4K tokens
- Docs: 41 files, ~68.4K tokens
- Other: 5 files, ~17.9K tokens

## Heaviest files (read these with offset/limit)
1. extracao-web/extracao-controles-labs-prescricao.html — 1080 lines (~15.3K tokens)
2. skills/sasi-ingest-export/scripts/build_passagem.py — 633 lines (~7.1K tokens)
3. skills/controles-vitais-janela/references/amostras/prescricao-uti2-2026-06-21.md — 1421 lines (~6.7K tokens)
4. skills/hemodinamica-calculada/scripts/calc_hemo.py — 588 lines (~6.0K tokens)
5. tests/test_esteira.py — 412 lines (~5.2K tokens)
6. gerador/ficha_cola.py — 475 lines (~5.0K tokens)
