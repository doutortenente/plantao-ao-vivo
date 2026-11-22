# Formato de entrega — evolução e ficha-cola (Word)

Vigente desde 11/10/2026. Substitui o `claude/doc-plantao-formato.md` do projeto "Plantão ao vivo" (27/09/2026),
que previa Google Doc gerado de HTML, Arial 10 e caixas cinzas — formato abandonado.
Gerador: `gerador/gerar_docx.py`. Texto clínico: `docs/BRIEFING.md`.

## Comum aos dois

- Times New Roman 10 em TUDO (inclusive cabeçalho e títulos). Rótulos, títulos, flags `[Nx < 50]` e alertas em
  negrito. Sem cor nenhuma — nada de vermelho (pedido de 11/10/2026).
- Sem cor e sem ícone. Evolução: preto no branco, filete fino sob títulos. Ficha-cola (opção A, 07/11/2026): faixa
  cinza nos títulos, linha sim, linha não em cinza, alerta e alergia em caixa. O cinza é só de fundo; o texto é
  sempre preto.
- Impressora do plantão não faz frente e verso: cada página é uma folha.
- Nome do arquivo: `DD-MM-AA-utiN-<classe-do-documento>.<tipo>` — ex.: `11-10-26-uti2-evolucoes-diurno.docx` e
  `11-10-26-uti2-ficha-cola-diurno.docx` (o turno vem de `meta.turno`) (mesmo padrão dos arquivos de entrada, como `11-10-26-uti2-controles.pdf`).

## Evolução (retrato, 1 leito por página)

Cabeçalho: `LEITO XX  NOME COMPLETO` e, embaixo, `idade/sexo · dia de UTI · Evolução <turno> <UTI> · data`.

Seções, nesta ordem e só estas:

1. Sinais vitais + balanço 24 h — numa linha só, itens separados por " | ", sem "Ingesta hídrica" (02/11/2026)
2. Laboratório — séries com " => "; UR e CR seriais na linha dos eletrólitos, que vão sem série (02/11/2026)
3. Exame físico — copiado da evolução anterior (ele altera ao "canetar")
4. Evolução / Eventos 24 h — só fato que não está nos vitais e no laboratório
5. Impressão / Problemas ativos — a leitura do caso
6. Plano terapêutico e Condutas — ordens curtas, sem justificativa

Sem "Terapias vigentes" desde 21/11/2026: a ficha-cola já traz a prescrição (o campo `terapias` continua no JSON, para
os dias de ATB e as checagens, mas não é impresso).

Uma página por leito não é obrigatória na evolução (a regra de 1 folha é da ficha-cola).

## Ficha-cola (paisagem, 1 folha por leito — obrigatório)

Modelo aprovado em 12/10/2026 (plantão UTI 2 de 11/10). Gerador: `gerador/ficha_cola.py`, a partir do bloco
`ficha` de cada leito (`gerador/schema-plantao.md`). 6 leitos = 6 folhas.

- Cabeçalho: caixa `LEITO XX` | nome em destaque; na linha seguinte (mesmo parágrafo, 9 pt) `D3 UTI`, `Idade:`,
  `Sexo:`, `Peso:` e `Altura:` **sempre** (bloco `peso` do JSON, sem fonte/data no cabeçalho; ausente = `?`;
  peso e altura independentes); depois `HD:` e `Disp.:`
  (dispositivo com data) | `ALERGIA:` em caixa preta, caixa alta e negrito, se houver (sem alergia: `Alergia: nega`,
  sem caixa) e turno/data.
  Hipóteses diagnósticas (**HD:**) ficam no cabeçalho, não em coluna própria (JSON: `leito.hd`).
- Coluna 1 — CONTROLES: sinais vitais em grade de 2 colunas (PAS/FR, PAD/SpO2, PAM/TAX, FC), Máx - Mín, alerta
  `[Nx<lim]` em negrito na mesma linha; Dx (glicemia) em linha própria; BALANÇO em grade (Diurese, perdas, BH; sem
  Ganhos; com
  peso, `Débito  0,38 ml/kg/h em 12 h  KDIGO 2`, flag em negrito; Evac.); LABORATÓRIO, um grupo por linha, e com
  peso a linha `ClCr 26 ml/min (Cockcroft-Gault)` do motor. Linha sim, linha não em cinza nos vitais, no balanço e
  no laboratório (guia de leitura — o Dr. é disléxico); flag e BH em caixinha (07/11/2026).
- Prescrição INTEIRA (22/11/2026): todo item que o paciente está recebendo, um por linha, por sistema, inclusive pele,
  tópicos e sintomáticos (a regra de 11/10/2026 que tirava esses itens acabou). PROFILAXIA = TEV + LAMG: o gerador
  move para lá IBP/anti-H2 escrito em outro sistema. ACM ("a critério médico" = a princípio suspenso) e SUSPENSOS
  saem da coluna 2 e vão para a coluna 3, abaixo das PENDÊNCIAS, com o título "ACM · a princípio suspenso".
- Coluna 2 — PRESCRIÇÃO em 2 blocos: INFUSÕES E TERAPIAS (DVA, sedação, ATB com D e início, VM/O2, dieta/NPT —
  em TNE, a linha DIETA leva também a água pela sonda, com volume e horários: `Fresubin HP Energy 60 ml/h SNE ·
  Água 200 ml 6/6 h` (02/11/2026) —,
  TRS) e POR SISTEMAS (Neuro, CV, Resp, TGI, Renal, Endócrino, Analgesia, Profilaxia, SN, Suspensos), rótulo à
  esquerda em coluna cinza, fio cinza de 0,5 pt entre sistemas, nome da droga em negrito. Profilaxia = só TEV/LAMG. DVA, SEDAÇÃO e BNM das bombas
  saem do motor (`infusoes_continuas`), uma linha por bomba com o que corre agora: `Hyponor 16 mg/250 ml · 2 ml/h
  · 0,03 mcg/kg/min` (a sequência das vazões fica na evolução). Em VM com altura, a linha VM ganha `VC 6 - 8 ml/kg
  (PP 46 kg): 276 - 368 ml`. Sem aferição de glicemia (Dx/HGT 6/6 h) e sem escala de correção (insulina
  "conforme Dx", G50% se Dx < 70): o gerador tira esses trechos (02/11/2026). Toda a prescrição sai sem os
  horários de administração ("=> 10-16-22-04"): droga, dose, via e frequência bastam; o gerador tira (02/11/2026).
- Coluna 3 — PENDÊNCIAS (□), ACM (e SE NECESSÁRIO quando a folha não comporta), EXAMES, ANOTAÇÕES / NOVOS EXAMES
  (linhas, quantas couberem). As pendências saem do plano das evoluções anteriores dele e das condutas que ele ditar.
- LABORATÓRIO da ficha (22/11/2026): série de 72 h, "Hb 9,6 => 7,8 => 8,3", eletrólitos também em série, dois exames
  afins por linha quando cabem (`gerador/labs_72h.py`); título com as datas ("LABORATÓRIO 20/11 => 21/11 => 22/11").
- Faixa de baixo (07/11/2026, no lugar da grade CONTROLES DO PLANTÃO): EXAME FÍSICO sob as colunas 1 e 2, em 6
  quadros por sistema na ordem da evolução (NEURO, RESPIRATÓRIO, HEMODINÂMICA, RENAL · METABÓLICO, TGI · NUTRIÇÃO,
  INFECTO · PELE), com □ para marcar e ____ para escrever, e a hora na faixa | INTERCORRÊNCIAS, CONDUTAS E PASSAGEM
  sob a coluna 3 (6 linhas). Sem faixa de bundle (FAST HUGS BID) no pé dos quadros: ele mandou tirar.
- Fora: subtítulos explicativos, rodapé de fontes, frase de comentário. Dúvida de leitura vai para o "Conferir" do chat.
- Tamanho: corpo 10 pt. Em cada tamanho (10, depois 9,5, depois 9 pt) o ajuste corta primeiro as linhas de anotação
  (14 até 0); depois deixa o exame compacto (os mesmos campos com menos folga e 4 linhas de intercorrências); só então
  a fonte desce. Se nem assim cabe (22/11/2026: a prescrição não perde item), o ajuste tenta variantes, nesta ordem:
  menos ar entre as linhas; SN na coluna 3; as duas. Se nada couber, o gerador acusa erro: encurtar o texto das
  pendências e dos exames, nunca tirar item da prescrição. Mede com 1,5 cm de folga no pé (o Word renderiza mais alto que o LibreOffice — sem folga, a folha
  estourava para 2 páginas no Word).
- Entrega: `.docx` + `.pdf` (o PDF é o que imprime igual em qualquer computador).
- O XML é reordenado no padrão OOXML (`sanear`) porque o Word é estrito e o LibreOffice não.

## Conferência antes de entregar

- `gerador/conferir.py` roda sozinho no fim do `gerar_docx.py`: PDF dos dois Word, nº de páginas da ficha-cola =
  nº de leitos, Times New Roman, tamanhos da lista aprovada (10/9,5/9 e as exceções 8, 13, 20 pt e rótulos de
  corpo - 1), nenhuma cor, nenhum `(revisar)`, nenhum travessão entre números, nenhuma seta ↑/↓ na evolução.
  Erro = código de saída 4: não entregar. Sem LibreOffice também é erro (sem PDF não se contam as folhas); com
  `--sem-ajuste`, a ficha ainda é medida uma vez com a folga de 1,5 cm.
- Os `ALERTA:` de segurança (alergia × prescrição, TEV, duplicidade, suspenso) saem no topo do "Conferir".
- Olhar TODAS as páginas (PNG em `saida/paginas/`), não uma amostra.
