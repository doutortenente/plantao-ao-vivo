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

1. `gerador/preparar.py` arruma a pasta de entrada: inventário, recortes das folhas, labs em texto e evolução
   anterior.
2. O Claude lê o material (skill `skills/plantao/SKILL.md`, doutrina em `skills/controles-vitais-janela/`), ou a
   página `extracao-web` exporta o JSON.
3. O Claude monta um JSON no contrato `gerador/schema-plantao.md` com os números **crus** (células, séries).
4. O motor `skills/sasi-ingest-export/scripts/build_passagem.py` faz toda a conta e cruza a prescrição
   (`checagens.py`):
   - Máx - Mín, flags e balanço pela soma das células;
   - dias de ATB (início = D0) e de UTI (admissão = D1).
5. `gerador/gerar_docx.py` gera os dois Word.
   - Antes de gerar, valida o JSON (`validar.py`).
   - Ajusta a ficha-cola para 1 folha por leito.
   - Depois confere os dois Word (`conferir.py`), guarda a versão anterior e rascunha a mensagem do chat
     (`entrega.py`).

```
python3 gerador/preparar.py entrada/ --saida saida/preparo     # opcional
python3 gerador/gerar_docx.py plantao.json --saida saida/       # saída ≠ 0 = não entregar
python3 gerador/gerar_admissao.py nota.txt saida/               # admissão (A4)
python3 gerador/validar.py plantao.json                         # só validar
```

Esteira (opcional): uma linha do Airtable dispara `.github/workflows/plantao.yml`, que lê os scans com a API do
Claude e devolve a ficha-cola na linha (`esteira/README.md`).

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
  gerar_docx.py                 gera evolução + ficha-cola (chama validar, conferir e entrega)
  ficha_cola.py                 a ficha-cola (modelo de 12/10/2026) e o ajuste em 1 folha
  estilo.py                     fonte, tamanhos, cinzas, fios e margens (tokens do design system)
  validar.py / conferir.py      antes de gerar / depois de gerar
  entrega.py                    histórico, diff por leito e rascunho do chat (mensagem.md)
  preparar.py                   pasta de entrada: inventário, recortes, labs em texto
  evolucao_anterior.py          exame físico, plano e labs da evolução de ontem
  gerar_admissao.py             nota de admissão em A4
  office.py                     LibreOffice com perfil próprio por processo
  schema-plantao.md             contrato do JSON
  exemplo/plantao-exemplo.json  caso fictício para teste
  requirements.txt
extracao-web/                   página-artefato que lê os scans no navegador e exporta o JSON (ver README dela)
esteira/                        esteira Airtable → GitHub Actions: leitura com a API do Claude (ver README dela)
.github/workflows/              testes.yml (a cada push e PR) e plantao.yml (esteira, disparo manual)
tests/                          motor, checagens, dias, janela, validar, conferir, gerador, esteira, página, doutrina…
```

## Requisitos

- Python 3.10+ e `pip install -r gerador/requirements.txt` (python-docx). Para a esteira:
  `pip install -r esteira/requirements.txt` (acrescenta o SDK `anthropic`).
- LibreOffice (`soffice`) e poppler-utils (`pdfinfo`, `pdftoppm`, `pdftotext`) para o ajuste da ficha-cola, a
  conferência e o preparo. Sem LibreOffice, `--sem-ajuste` gera os Word, mas a conferência dá erro: sem PDF não se
  contam as folhas.
- Testes: `python3 -m unittest discover -s tests`. O teste da página `extracao-web` precisa de node e playwright;
  sem eles, é pulado.

## Dados de paciente

Os plantões do dia não são versionados: a pasta `saida/`, os Word gerados e os JSON de plantão (`DD-MM-AA-utiN-plantao.json`)
estão no `.gitignore`. O único JSON versionado é o exemplo fictício. As amostras OCR em
`skills/controles-vitais-janela/references/amostras/` são folhas reais de 2026 (as mesmas do `claude-workspace`),
mantidas como referência de layout.
