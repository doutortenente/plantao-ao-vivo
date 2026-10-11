# Formato de entrega — evolução e ficha-cola (Word)

Vigente desde 11/10/2026. Substitui o `claude/doc-plantao-formato.md` do projeto "Plantão ao vivo" (27/09/2026),
que previa Google Doc gerado de HTML, Arial 10 e caixas cinzas — formato abandonado.
Gerador: `gerador/gerar_docx.py`. Texto clínico: `docs/BRIEFING.md`.

## Comum aos dois

- Times New Roman 10 em TUDO (inclusive cabeçalho e títulos). Rótulos, títulos, flags `[Nx < 50]` e alertas em
  negrito. Sem cor nenhuma — nada de vermelho (pedido de 11/10/2026).
- Sem caixas coloridas, sem faixas, sem ícone. Preto no branco, filete fino sob títulos.
- Impressora do plantão não faz frente e verso: cada página é uma folha.
- Nome do arquivo: `DD-MM-AA-utiN-<classe-do-documento>.<tipo>` — ex.: `11-10-26-uti2-evolucoes-diurno.docx` e
  `11-10-26-uti2-ficha-cola-diurno.docx` (o turno vem de `meta.turno`) (mesmo padrão dos arquivos de entrada, como `11-10-26-uti2-controles.pdf`).

## Evolução (retrato, 1 leito por página)

Cabeçalho: `LEITO XX  NOME COMPLETO` e, embaixo, `idade/sexo · dia de UTI · Evolução <turno> <UTI> · data`.

Seções, nesta ordem e só estas:

1. Sinais vitais + balanço 24 h
2. Laboratório
3. Terapias vigentes
4. Exame físico — copiado da evolução anterior (ele altera ao "canetar")
5. Evolução / Eventos 24 h
6. Impressão / Problemas ativos
7. Plano terapêutico e Condutas — enriquecido, sem prolixidade

Uma página por leito não é obrigatória na evolução (a regra de 1 folha é da ficha-cola).

## Ficha-cola (paisagem, 1 folha por leito — obrigatório)

Modelo: a cola que o Dr. faz à mão. 6 leitos = 6 folhas, sem segunda página quase vazia.

- Topo: `LEITO XX  NOME, idade/sexo · dia de UTI · data turno`; diagnóstico; `Alergia:` e
  `Dieta:`.
- Coluna esquerda: TODOS os sinais vitais e o balanço, um parâmetro por linha com rótulo alinhado (sem linhas de
  grade); laboratório compacto, um grupo por linha com rótulos em negrito.
- Coluna direita: prescrição por classe (ATB, DVA, SEDAÇÃO/ANALGESIA, CV, HPB, TGI...), uma droga por linha:
  `Nome (genérico) dose via frequência ........ horários h` — nome em negrito, horário alinhado à direita.
  Item suspenso ou duplicado em negrito.
- Linha `Dispositivos/ATB:` logo abaixo de Alergia/Dieta: dispositivo com data de inserção e ATB com dia e início.
- Alertas: até 3, em negrito, logo abaixo do cabeçalho.
- CHECKLIST DO PLANTÃO: 3 a 5 tarefas com caixinha (☐), tiradas do plano — na coluna que tiver espaço.
- Prescrição enxuta: a ficha não mostra classe SN, colírios, lágrima artificial, cremes/tópicos de pele, simeticona,
  módulos de proteína/fibra, água de SNE e complexo B (lista em `gerador/gerar_docx.py`, `ITENS_OMITIR`).
- Embaixo: linhas para anotação — quantas couberem.
- Se o leito não cabe: o gerador reduz as linhas de anotação, e a fonte fica em 10. Se não
  couber, avisa — aí encurtar a prescrição juntando itens na mesma linha com "; ".

## Conferência antes de entregar

- Converter para PDF e contar páginas da ficha-cola (= nº de leitos).
- Abrir 1 página de cada arquivo e olhar.
