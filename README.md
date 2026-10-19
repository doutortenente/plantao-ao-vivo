# plantao-ao-vivo

Material do plantão de UTI → evolução do dia e ficha-cola, em Word, prontos para imprimir.

Repositório independente: tudo que o fluxo precisa está aqui dentro, em arquivos reais (sem symlink).
Montado em 11/10/2026 a partir de `doutortenente/claude-workspace` (pastas `EXTRACAO-CLINICA-SASI/`,
`extracao-plantao/`, `skills-que-prestam/01-pacote-skills-medicas/` e `.github/workflows/plantao*`), com as
correções listadas em `docs/DECISOES.md`.

## O que entra e o que sai

| Entra | Sai |
|---|---|
| Evoluções anteriores (docx/txt) | `DD-MM-AA-utiN-evolucoes-<turno>.docx` (ex.: `11-10-26-uti2-evolucoes-diurno.docx`) — por leito, só os 7 blocos que mudam |
| Folhas de controle (scan PDF) | `DD-MM-AA-utiN-ficha-cola-<turno>.docx` — 1 folha paisagem por leito |
| Prescrições do dia (scan PDF) | Rodapé "Conferir" (ilegíveis e divergências) — no chat, fora do bloco |
| Laudos de laboratório (PDF) | Alertas e bloco final de conduta — no chat |

## Fluxo

1. O Claude lê o material (skill `skills/plantao/SKILL.md`, doutrina em `skills/controles-vitais-janela/`).
2. Monta um JSON no contrato `gerador/schema-plantao.md` com os números **crus** (células, séries).
3. O motor `skills/sasi-ingest-export/scripts/build_passagem.py` faz toda a conta: Máx - Mín, flags, balanço
   pela soma das células.
4. `gerador/gerar_docx.py` gera os dois Word (Times New Roman 10) e ajusta a ficha-cola para caber em 1 folha
   por leito.

```
python3 gerador/gerar_docx.py plantao.json --saida saida/
```

## Estrutura

```
CLAUDE.md                       instruções para o Claude rodar o plantão (leia primeiro)
docs/
  BRIEFING.md                   formato do texto clínico — fonte única
  formato-entrega.md            como ficam os dois Word
  DECISOES.md                   decisões do operador e correções feitas neste repo
  instrucoes-projeto.md         texto das instruções do projeto no claude.ai (versionado)
skills/
  plantao/                      orquestrador do plantão
  controles-vitais-janela/      transcrição das folhas de controle (+ referências e amostras)
  sasi-ingest-export/           ingest SASI, templates e o MOTOR (scripts/build_passagem.py)
  hemodinamica-calculada/       calculadora hemodinâmica por eco (scripts/calc_hemo.py)
  admissao-uti/                 nota de admissão
  analise-ecott/                leitura de ecocardiograma
gerador/
  gerar_docx.py                 gera evolução + ficha-cola
  schema-plantao.md             contrato do JSON
  exemplo/plantao-exemplo.json  caso fictício para teste
  requirements.txt
extracao-web/                   página-artefato que lê os scans no navegador (ver README dela)
esteira/processar.py            esteira Airtable → GitHub Actions (estágio de teste)
.github/workflows/              testes.yml (a cada push e PR) e plantao.yml (esteira, disparo manual)
tests/test_motor.py             testes do motor
```

## Requisitos

- Python 3.10+ e `pip install -r gerador/requirements.txt` (python-docx).
- LibreOffice (`soffice`) e `pdfinfo` (poppler-utils) para o ajuste automático da ficha-cola. Sem eles, use
  `--sem-ajuste` (6 linhas de anotação e 4 de intercorrências em 10 pt; a folha pode estourar se a prescrição for
  longa).
- Testes: `python3 -m unittest discover -s tests`.

## Dados de paciente

Os plantões do dia não são versionados: a pasta `saida/`, os Word gerados e os JSON de plantão (`DD-MM-AA-utiN-plantao.json`)
estão no `.gitignore`. O único JSON versionado é o exemplo fictício. As amostras OCR em
`skills/controles-vitais-janela/references/amostras/` são folhas reais de 2026 (as mesmas do `claude-workspace`),
mantidas como referência de layout.
