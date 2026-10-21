# -*- coding: utf-8 -*-
"""Tokens do papel (evolução, ficha-cola, admissão) — um lugar só para os dois geradores.

Os nomes seguem o design system "Plantão ao Vivo" (família Papel): papel-cinza -> PAPEL_CINZA, etc.
Mudou aqui, muda na evolução e na ficha-cola juntas. Valores aprovados em 11-12/10/2026 (docs/formato-entrega.md);
as exceções de tamanho (8, 9, 13, 20 pt) foram aprovadas como exceção ao "TNR 10 em tudo" em 19/10/2026.
"""

FONTE = "Times New Roman"

# ── tamanhos (pt) ───────────────────────────────────────────────────────────
CORPO = 10            # papel-corpo
AJUSTE = (10, 9.5, 9)  # papel-ajuste-1/2: o corpo da ficha desce nesta ordem quando a folha não cabe
NOME = 13             # papel-nome (ficha)
LEITO = 20            # papel-leito (número na caixa)
LEITO_ROTULO = 8      # papel-leito-rotulo ("LEITO")
PAUTA = 6             # run invisível de cada linha de anotação
ESPACADOR = 2         # parágrafo que só carrega um fio
# rótulos de 9 pt (papel-sub) são sempre CORPO_ATUAL - 1, por isso não têm constante

# ── entrelinha (múltiplo do Word) ────────────────────────────────────────────
ENTRELINHA_EVOLUCAO = 1.08
ENTRELINHA_FICHA = 1.05
ENTRELINHA_ADMISSAO = 1.0

# ── cores (só fios; texto é sempre preto) ────────────────────────────────────
PAPEL_TINTA = "000000"
PAPEL_CINZA = "A6A6A6"            # fios guia das grades e divisória interna (dislexia)
PAPEL_CINZA_ANOTACAO = "8C8C8C"   # linhas de anotação e intercorrências
PAPEL_CINZA_SECAO = "808080"      # fio sob título de seção da evolução

# ── espessura dos fios (w:sz, em 1/8 pt) ─────────────────────────────────────
FIO_GUIA = 2      # 0,25 pt
FIO_SECAO = 4     # 0,5 pt
FIO_TITULO = 8    # 1 pt
FIO_CAIXA = 12    # 1,5 pt

# ── página (cm) ─────────────────────────────────────────────────────────────
A4_CURTO, A4_LONGO = 21.0, 29.7
MARGEM_EVOLUCAO_LATERAL, MARGEM_EVOLUCAO_VERTICAL = 2.0, 1.8
MARGEM_FICHA_LATERAL, MARGEM_FICHA_TOPO, MARGEM_FICHA_PE = 1.0, 0.8, 0.7
DISTANCIA_CABECALHO = 0.3
FOLGA_MEDICAO = 1.5   # somada ao pé só na medição: o Word renderiza mais alto que o LibreOffice
MARGEM_ADMISSAO_ESQ, MARGEM_ADMISSAO_DIR, MARGEM_ADMISSAO_VERTICAL = 1.25, 1.34, 2.5

# ── grade da ficha-cola (cm) ────────────────────────────────────────────────
LARGURA_UTIL = 27.7                   # W
COL_CONTROLES, COL_PRESCRICAO = 8.3, 11.0   # WL, WM (WR = o resto)
CAIXA_LEITO, CABECALHO_DIREITA = 2.0, 4.4
FAIXA_CONTROLES = 13.3
GRADE_ROTULO, GRADE_CELULA = 2.1, 1.4
RX_ROTULO = 2.35
