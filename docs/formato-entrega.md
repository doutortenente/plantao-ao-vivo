# Formato de entrega — evolução e ficha-cola (Word)

Vigente desde 11/10/2026. Substitui o `claude/doc-plantao-formato.md` do projeto "Plantão ao vivo" (27/09/2026),
que previa Google Doc gerado de HTML, Arial 10 e caixas cinzas — formato abandonado.
Gerador: `gerador/gerar_docx.py`. Texto clínico: `docs/BRIEFING.md`.

## Comum aos dois

- Times New Roman 10. Rótulos em negrito (`PAS:`, `HB:`, títulos de seção). Flags `[Nx < 50]` em vermelho.
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

- Topo: `LEITO XX  NOME, idade/sexo · dia de UTI · data turno`; diagnóstico; `Alergia:` (vermelho se houver) e
  `Dieta:`.
- Coluna esquerda: TODOS os sinais vitais da janela (Máx - Mín + flags), o balanço completo e o laboratório.
- Coluna direita: prescrição por classe (ATB, DVA, SEDAÇÃO/ANALGESIA, CV, HPB, TGI...), uma droga por linha:
  `Nome (genérico) dose via frequência ........ horários h` — nome em negrito, horário alinhado à direita.
  Item suspenso ou duplicado em vermelho.
- ATENÇÃO: até 3 alertas, em vermelho, na coluna que tiver espaço.
- Embaixo: linhas para anotação — quantas couberem.
- Se o leito não cabe: o gerador reduz as linhas de anotação, depois a fonte em 0,5 pt (até 9). Se ainda assim não
  couber, avisa — aí encurtar a prescrição juntando itens na mesma linha com "; ".

## Conferência antes de entregar

- Converter para PDF e contar páginas da ficha-cola (= nº de leitos).
- Abrir 1 página de cada arquivo e olhar.
