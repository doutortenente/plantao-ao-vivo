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

Modelo aprovado em 12/10/2026 (plantão UTI 2 de 11/10). Gerador: `gerador/ficha_cola.py`, a partir do bloco
`ficha` de cada leito (`gerador/schema-plantao.md`). 6 leitos = 6 folhas.

- Cabeçalho: caixa `LEITO XX` | nome em destaque + idade/sexo + dia de UTI; embaixo `Dx:` (problemas ativos
  separados por " · ") e `Disp.:` (dispositivo com data) | `Alergia:` (caixa alta e negrito se houver) e turno/data.
  Diagnósticos ficam no cabeçalho, não em coluna própria.
- Coluna 1 — CONTROLES: sinais vitais em grade de 2 colunas (PAS/FR, PAD/SpO2, PAM/TAX, FC), Máx - Mín, alerta
  `[Nx<lim]` em negrito na mesma linha; Dx em linha própria; BALANÇO em grade (Ganhos, Diurese, perdas, BH, Evac.);
  LABORATÓRIO, um grupo por linha. Fios cinza finos entre linhas (guia de leitura — o Dr. é disléxico).
- Coluna 2 — PRESCRIÇÃO em 2 blocos: INFUSÕES E TERAPIAS (DVA, sedação, ATB com D e início, VM/O2, dieta/NPT,
  TRS) e POR SISTEMAS (Neuro, CV, Resp, TGI, Renal, Endócrino, Analgesia, Profilaxia, SN, Suspensos), rótulo à
  esquerda, fio entre sistemas, nome da droga em negrito. Profilaxia = só TEV/LAMG.
- Coluna 3 — PENDÊNCIAS (☐), EXAMES, ANOTAÇÕES / NOVOS EXAMES (linhas, quantas couberem).
- Faixa de baixo: grade CONTROLES DO PLANTÃO (Hora, PA (PAM), FC, SpO2/FiO2, Diurese, Dx × 8) | INTERCORRÊNCIAS,
  CONDUTAS E PASSAGEM.
- Fora: subtítulos explicativos, rodapé de fontes, frase de comentário. Dúvida de leitura vai para o "Conferir" do chat.
- Tamanho: corpo 10 pt; o ajuste desce para 9,5/9 pt e corta linhas de anotação até caber, medindo com 1,5 cm de
  folga no pé (o Word renderiza mais alto que o LibreOffice — sem folga, a folha estourava para 2 páginas no Word).
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
