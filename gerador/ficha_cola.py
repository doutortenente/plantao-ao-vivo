# -*- coding: utf-8 -*-
"""Ficha-cola (modelo aprovado em 12/10/2026, opção A em 07/11/2026) — 1 folha paisagem por leito.
Cabeçalho: leito + nome + idade/sexo + Peso/Altura + HD + dispositivos | alergia (em caixa) + plantão.
Corpo: CONTROLES + LAB | PRESCRIÇÃO (infusões/terapias + por sistemas) | PENDÊNCIAS + EXAMES + ANOTAÇÕES.
Rodapé de trabalho: EXAME FÍSICO em 6 quadros por sistema | intercorrências.
Times New Roman, texto sempre preto. Para a leitura (o Dr. é disléxico): título em faixa cinza, linha sim, linha
não em cinza, alerta em caixinha e fios cinza entre as linhas da prescrição."""
import json, re, subprocess, sys, tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "skills" / "sasi-ingest-export" / "scripts"))
import build_passagem as motor  # noqa: E402
import estilo as E  # noqa: E402
import office  # noqa: E402

from docx import Document  # noqa: E402
from docx.enum.section import WD_ORIENT  # noqa: E402
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_ROW_HEIGHT_RULE, WD_TABLE_ALIGNMENT  # noqa: E402
from docx.enum.text import WD_BREAK, WD_TAB_ALIGNMENT  # noqa: E402
from docx.oxml import OxmlElement  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.shared import Cm, Pt  # noqa: E402

FONTE = E.FONTE
S = {"tam": E.CORPO, "ls": E.ENTRELINHA_FICHA}
CINZA = E.PAPEL_CINZA
CFG = {"tam": E.CORPO}


def T(p, txt, b=False, tam=None, it=False):
    r = p.add_run(txt); r.bold = b; r.italic = it
    r.font.size = Pt(tam or CFG["tam"]); r.font.name = FONTE
    r._element.rPr.rFonts.set(qn("w:eastAsia"), FONTE)
    return r


def rico(p, txt, tam=None, b_all=False):
    for i, parte in enumerate(re.split(r"\*\*", txt)):
        if parte:
            T(p, parte, b=b_all or i % 2 == 1, tam=tam)


def borda_p(p, lado="bottom", sz=6, cor=E.PAPEL_TINTA):
    pPr = p._p.get_or_add_pPr()
    b = pPr.find(qn("w:pBdr"))
    if b is None:
        b = OxmlElement("w:pBdr"); pPr.append(b)
    e = OxmlElement(f"w:{lado}")
    for k, v in (("val", "single"), ("sz", str(sz)), ("space", "1"), ("color", cor)):
        e.set(qn("w:" + k), v)
    b.append(e)


def tab(p, pos_cm, align="left"):
    p.paragraph_format.tab_stops.add_tab_stop(
        Cm(pos_cm), WD_TAB_ALIGNMENT.RIGHT if align == "right" else WD_TAB_ALIGNMENT.LEFT)


def tabela(doc_or_cell, rows, cols, larguras, bordas=None):
    t = doc_or_cell.add_table(rows=rows, cols=cols)
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    t.autofit = False
    tblPr = t._tbl.tblPr
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
    tb = OxmlElement("w:tblBorders")
    for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{lado}")
        v = (bordas or {}).get(lado)
        if v:
            e.set(qn("w:val"), "single"); e.set(qn("w:sz"), str(v[0])); e.set(qn("w:color"), v[1])
        else:
            e.set(qn("w:val"), "nil")
        tb.append(e)
    tblPr.append(tb)
    grid = t._tbl.tblGrid
    for i, gc in enumerate(grid.findall(qn("w:gridCol"))):
        gc.set(qn("w:w"), str(int(larguras[i] * 567)))
    for row in t.rows:
        for i, c in enumerate(row.cells):
            c.width = Cm(larguras[i])
    return t


def margens(cell, top=0, left=0, bottom=0, right=0):
    tcPr = cell._tc.get_or_add_tcPr()
    m = OxmlElement("w:tcMar")
    for k, v in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        e = OxmlElement(f"w:{k}"); e.set(qn("w:w"), str(v)); e.set(qn("w:type"), "dxa"); m.append(e)
    tcPr.append(m)


def borda_cel(cell, **lados):
    tcPr = cell._tc.get_or_add_tcPr()
    b = OxmlElement("w:tcBorders")
    for lado, (sz, cor) in lados.items():
        e = OxmlElement(f"w:{lado}")
        e.set(qn("w:val"), "single"); e.set(qn("w:sz"), str(sz)); e.set(qn("w:color"), cor)
        b.append(e)
    tcPr.append(b)


# ── cinza e caixa (opção A, 07/11/2026): só fundo e fio; o texto continua preto ──────────────────────────
def sombra(pr, cor):
    """Fundo cinza (w:shd) num pPr ou tcPr; o sanear() põe na ordem do OOXML."""
    shd = OxmlElement("w:shd")
    for k, v in (("val", "clear"), ("color", "auto"), ("fill", cor)):
        shd.set(qn("w:" + k), v)
    pr.append(shd)


def recuo(p, pt):
    f = p.paragraph_format
    f.left_indent = f.right_indent = Pt(pt)


def moldura(p, cor, sz=E.FIO_SECAO, folga=2):
    """Borda nos 4 lados do parágrafo, afastada `folga` pt do texto; o recuo traz a moldura de volta para a
    largura da coluna."""
    pPr = p._p.get_or_add_pPr()
    b = OxmlElement("w:pBdr")
    for lado, esp in (("top", 1), ("left", folga), ("bottom", 1), ("right", folga)):
        e = OxmlElement(f"w:{lado}")
        for k, v in (("val", "single"), ("sz", str(sz)), ("space", str(esp)), ("color", cor)):
            e.set(qn("w:" + k), v)
        b.append(e)
    pPr.append(b)
    recuo(p, folga + sz / 8)
    return p


def faixa(p, cor, folga=2):
    """Faixa cinza de ponta a ponta da coluna, com folga em volta do texto (a borda tem a cor do fundo)."""
    moldura(p, cor, folga=folga)
    sombra(p._p.get_or_add_pPr(), cor)
    return p


def caixinha(run):
    """Alerta em caixinha: borda fina no próprio trecho (flag de sinal vital, KDIGO, BH)."""
    b = OxmlElement("w:bdr")
    for k, v in (("val", "single"), ("sz", str(E.FIO_SECAO)), ("space", "1"), ("color", E.PAPEL_TINTA)):
        b.set(qn("w:" + k), v)
    run._element.get_or_add_rPr().append(b)
    return run


def zebra(g, comeco=0):
    """Linha sim, linha não em cinza (guia de leitura), contando a partir de `comeco`."""
    for i, tr in enumerate(g._tbl.tr_lst):
        if (i + comeco) % 2 == 0:
            for tc in tr.tc_lst:
                sombra(tc.get_or_add_tcPr(), E.PAPEL_CINZA_ZEBRA)



W = E.LARGURA_UTIL
WL, WM = E.COL_CONTROLES, E.COL_PRESCRICAO
WR = W - WL - WM


def P(cell, first=False, after=1.5, before=0):
    if first and len(cell.paragraphs) == 1 and not cell.paragraphs[0].text:
        p = cell.paragraphs[0]
    else:
        p = cell.add_paragraph()
    f = p.paragraph_format
    f.space_before = Pt(before); f.space_after = Pt(after); f.line_spacing = S["ls"]
    return p


def t(p, txt, b=False, tam=None):
    return T(p, txt, b=b, tam=tam or S["tam"])


def rk(p, txt, tam=None):
    rico(p, txt, tam=tam or S["tam"])


def sec(cell, txt, first=False, before=5, folga=2):
    p = P(cell, first=first, after=3, before=0 if first else before)
    p.paragraph_format.keep_with_next = True
    faixa(p, E.PAPEL_CINZA_FAIXA, folga)
    t(p, txt, b=True, tam=S["tam"])
    return p


def subsec(cell, txt, before=5):
    p = P(cell, after=2, before=before)
    p.paragraph_format.keep_with_next = True
    faixa(p, E.PAPEL_CINZA_SUB)
    t(p, txt, b=True, tam=S["tam"] - 1)
    return p


def encolher(p):
    """Parágrafo vazio que o Word exige depois de tabela dentro de célula: quase sem altura."""
    pPr = p._p.get_or_add_pPr()
    rPr = OxmlElement("w:rPr"); sz = OxmlElement("w:sz"); sz.set(qn("w:val"), "2"); rPr.append(sz)
    pPr.append(rPr)
    from docx.enum.text import WD_LINE_SPACING
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    p.paragraph_format.line_spacing = Pt(1)
    p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(0)


def grade(cell_or_doc, rows, cols, larg, linhas=True, fio=E.FIO_GUIA):
    bd = {"insideH": (fio, CINZA), "bottom": (fio, CINZA), "top": (fio, CINZA)} if linhas else None
    g = tabela(cell_or_doc, rows, cols, larg, bd)
    if hasattr(cell_or_doc, "paragraphs"):
        encolher(cell_or_doc.paragraphs[-1])
    for r in g.rows:
        for c in r.cells:
            margens(c, 10, 40, 10, 40)
            c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    return g


def droga(p, item):
    """Nome comercial/rotulo em negrito, resto normal. Itens com ** já marcados ficam como vieram."""
    if "**" in item:
        rk(p, item); return
    partes = item.split(" · ")
    for i, seg in enumerate(partes):
        if i:
            t(p, "  ·  ")
        m = re.match(r"^(.{2,28}?)(\s\(|\s\d|\s=>|:|$)(.*)$", seg)
        if m and not re.match(r"^\d", seg):
            t(p, m.group(1), b=True); t(p, m.group(2) + m.group(3))
        else:
            t(p, seg)


# ── dados do cabeçalho: uma fonte só ────────────────────────────────────────
# alergia, HD (diagnóstico) e dispositivos moram no leito; o bloco `ficha` só sobrescreve
# quando precisa de um texto mais curto. Divergência entre os dois vira erro/aviso no gerador/validar.py.
CABECALHO = {"alergia": "alergia", "hd": "hd", "disp": "dispositivos"}


def idade_sexo_ficha(txt):
    """Linhas do cabeçalho: idade legível e sexo por extenso (o JSON continua 90F)."""
    idade, sexo = motor.PESO.idade_sexo(txt)
    if idade is None:
        bruto = str(txt or "?").strip() or "?"
        return bruto, "?"
    sexo_txt = {"M": "masculino", "F": "feminino"}.get(sexo, sexo or "?")
    return f"{idade} anos", sexo_txt


def rotulo_cabecalho(celula, rotulo, after=0):
    """Parágrafo com gancho à esquerda (`Idade:`, `Peso:`…); devolve o parágrafo para o valor."""
    q = P(celula, after=after)
    q.paragraph_format.left_indent = Cm(0.75)
    q.paragraph_format.first_line_indent = Cm(-0.75)
    t(q, f"{rotulo}:  ", b=True)
    return q


def peso_altura_ficha(leito):
    """Peso e altura só para o cabeçalho: leem o bloco `peso` do JSON, sem fonte/data; não dependem do motor."""
    p = leito.get("peso")
    if not isinstance(p, dict):
        return "?", "?"

    def _campo(chave, unidade):
        bruto = p.get(chave)
        if bruto in (None, "", "?"):
            return "?"
        n = motor.PESO._num(bruto)
        if n is None or n <= 0:
            return "?"
        return f"{motor._fmt(n)} {unidade}"

    return _campo("kg", "kg"), _campo("altura_cm", "cm")


def dado(leito, chave):
    v = leito["ficha"].get(chave)
    return v if v not in (None, "") else (leito.get(CABECALHO[chave]) or "")


def janelas(leito, meta, jan=None):
    """Títulos de CONTROLES e BALANÇO. Sem `janela_controles`/`janela_balanco` no bloco, saem da janela que o motor
    conferiu (24 h = 07 - 05 h)."""
    f = leito["ficha"]
    jan = jan or leito.get("janela") or meta.get("janela") or "24 h"
    d = motor._data(meta.get("data"))
    padrao_c = f"{d:%d/%m}  ·  07 - 05 h" if jan == "24 h" and d else (jan if jan != "24 h" else "07 - 05 h")
    padrao_b = "07 - 05 h" if jan == "24 h" else jan
    return f.get("janela_controles") or padrao_c, f.get("janela_balanco") or padrao_b


# ── colunas ────────────────────────────────────────────────────────────────
def linhas_controle(r, leito):
    calculadas = set(r.get("calculadas") or [])  # peso, débito e bombas: a ficha mostra do jeito dela
    jan_linhas = [l for l in r["secoes"][0][1] if l not in calculadas]
    out = []
    for l in jan_linhas:
        out += [x.strip() for x in l.split(" | ")] if " | " in l else [l]
    infus = set(leito.get("outros_balanco", []))
    vit, bal = {}, []
    for l in out:
        if l in infus:
            continue
        m = re.match(r"^([^:]{1,30}):\s*(.*)$", l)
        if not m:
            continue
        rot, resto = m.group(1), m.group(2)
        flags = re.findall(r"\[([^\]]+)\]", resto)
        val = re.sub(r"\s*\[[^\]]+\]", "", resto).strip()
        val = re.sub(r"\s*(mmHg|bpm|rpm|ºC|mg/dl)$", "", val)
        val = re.sub(r"\s*%(\s*\(.*\))?$", " %", val) if rot == "SpO2" else val
        flag = "  ".join(f.replace(" ", "") for f in flags)
        if rot in ("PAS", "PAD", "PAM", "FC", "FR", "SpO2", "TAX", "Dx"):
            vit[rot] = (val, flag)
        elif rot in ("Dieta", "Sup O2"):
            continue
        else:
            rot = {"Ingesta hídrica": "Ganhos", "Resíduo gástrico": "Resíduo", "UF (CVVHDF)": "UF",
                   "Débito SNG": "SNG"}.get(rot, rot)
            if rot == "Ganhos":
                continue
            v = val.replace(" ml", "")
            if rot == "BH":
                v = v.replace("+ ", "+").replace("- ", "-")
            bal.append((rot, v))
    return vit, bal


def col_controles(C, r, leito, jan_c, jan_b):
    sec(C, f"CONTROLES  {jan_c}", first=True)
    vit, bal = linhas_controle(r, leito)
    pares = [("PAS", "FR"), ("PAD", "SpO2"), ("PAM", "TAX"), ("FC", None)]
    w = [1.0, 1.75, 1.3] * 2
    g = grade(C, len(pares), 6, w, linhas=False)  # a zebra faz o papel do fio entre as linhas
    for i, (a, b) in enumerate(pares):
        for j, k in enumerate((a, b)):
            if not k or k not in vit:
                continue
            val, fl = vit[k]
            c0, c1, c2 = g.rows[i].cells[j * 3: j * 3 + 3]
            t(P(c0, True, 0), k, b=True)
            t(P(c1, True, 0), val, b=bool(fl))
            if fl:
                q = P(c2, True, 0); q.alignment = 2; caixinha(t(q, fl, b=True, tam=S["tam"] - 1))
    for row in g.rows:
        borda_cel(row.cells[3], left=(E.FIO_SECAO, CINZA))
    zebra(g)
    if "Dx" in vit:
        val, fl = vit["Dx"]
        g2 = grade(C, 1, 3, [1.05, 5.1, 2.15], linhas=False)
        t(P(g2.rows[0].cells[0], True, 0), "Dx", b=True)
        t(P(g2.rows[0].cells[1], True, 0), val, b=bool(fl))
        if fl:
            q = P(g2.rows[0].cells[2], True, 0); q.alignment = 2; caixinha(t(q, fl, b=True, tam=S["tam"] - 1))
        zebra(g2, comeco=len(pares))  # continua a alternância dos vitais

    subsec(C, f"BALANÇO  {jan_b}")
    curtos = [(k, v) for k, v in bal if k != "Evacuação"]
    evac = [v for k, v in bal if k == "Evacuação"]
    deb = r.get("debito")
    n = (len(curtos) + 1) // 2
    g3 = grade(C, n + (1 if deb else 0) + (1 if evac else 0), 4, [1.55, 2.6, 1.55, 2.6], linhas=False)
    for i, (k, v) in enumerate(curtos):
        row, off = i // 2, (i % 2) * 2
        c0, c1 = g3.rows[row].cells[off], g3.rows[row].cells[off + 1]
        t(P(c0, True, 0), k, b=True)
        valor = t(P(c1, True, 0), v + ("" if k in ("Evacuação",) else " ml"), b=(k == "BH"))
        if k == "BH":
            caixinha(valor)
    for row in g3.rows[:n]:
        borda_cel(row.cells[2], left=(E.FIO_SECAO, CINZA))
    extra = n
    if deb:  # débito urinário do motor (peso + horas do balanço), com o KDIGO como flag
        rr = g3.rows[extra].cells; extra += 1
        t(P(rr[0], True, 0), "Débito", b=True)
        m = rr[1].merge(rr[3]); q = P(m, True, 0)
        t(q, f"{deb['ml_kg_h']} ml/kg/h em {deb['horas']} h")
        if deb["kdigo"]:
            t(q, "   "); caixinha(t(q, f"KDIGO {deb['kdigo']}", b=True, tam=S["tam"] - 1))
    if evac:
        rr = g3.rows[extra].cells
        t(P(rr[0], True, 0), "Evac.", b=True)
        m = rr[1].merge(rr[3]); t(P(m, True, 0), evac[0])
    zebra(g3)

    sec(C, leito["ficha"].get("lab_titulo", "LABORATÓRIO"), before=8)
    lab = [linha.replace(" | ", "   |   ") for linha in leito["ficha"]["lab"]]
    if r.get("clcr") is not None:
        lab.append(f"ClCr {r['clcr']} ml/min (Cockcroft-Gault)")
    for i, linha in enumerate(lab):  # linha sim, linha não em cinza; a borda branca alinha as linhas brancas
        q = P(C, after=1)
        if i % 2 == 0:
            faixa(q, E.PAPEL_CINZA_ZEBRA)
        else:
            moldura(q, E.PAPEL_FOLHA)
        rk(q, linha)


# 02/11/2026: aferição de glicemia (Dx/HGT 6/6 h) e escala de correção (insulina "conforme Dx", G50% se Dx < 70)
# não vão na ficha-cola. Sai o trecho (" · "), e o rótulo que ficar vazio some.
GLICEMIA_CORRECAO = re.compile(
    r"conforme\s+(o\s+)?(dx|dextro|hgt|glicemia)|\bG\s?50\s?%|glicose\s+50\s?%.*\bdx\b|dextrostix|\bhgt\b|"
    r"glicemia\s+capilar|\bdx\s+\d+\s*/\s*\d+\s*h", re.I)


def sem_glicemia(linhas):
    out = []
    for rot, itens in linhas:
        novos = []
        for it in itens:
            segs = [s for s in it.split(" · ") if not GLICEMIA_CORRECAO.search(s.replace("**", ""))]
            if segs:
                novos.append(" · ".join(segs))
        if novos:
            out.append([rot, novos])
    return out


# 02/11/2026: a prescrição da ficha-cola sai sem os horários ("=> 10-16-22-04"): a frequência basta, horário é
# ruído. O JSON pode trazer os horários (a evolução e o motor não dependem deles); quem tira é a ficha.
HORARIOS = re.compile(r"\s*=>\s*\d{1,2}(?::\d{2})?(?:\s*-\s*\d{1,2}(?::\d{2})?)*\s*(?=\*\*\s*$|$)")


def sem_horarios(linhas):
    return [[rot, [" · ".join(HORARIOS.sub("", s) for s in it.split(" · ")) for it in itens]] for rot, itens in linhas]


def bloco_rx(C, linhas, w_rot=E.RX_ROTULO):
    linhas = sem_horarios(sem_glicemia(linhas))
    g = grade(C, len(linhas), 2, [w_rot, WM - 0.6 - w_rot], fio=E.FIO_SECAO)
    for i, (rot, itens) in enumerate(linhas):
        c0, c1 = g.rows[i].cells
        c0.vertical_alignment = c1.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
        sombra(c0._tc.get_or_add_tcPr(), E.PAPEL_CINZA_ZEBRA)  # coluna de rótulo em cinza: âncora do olho
        t(P(c0, True, 0), rot, b=True, tam=S["tam"] - 1)
        for j, it in enumerate(itens):
            q = P(c1, first=(j == 0), after=0.5)
            if rot in ("VM", "O2", "TRS"):
                rk(q, it)
            else:
                droga(q, it)


def infusoes_da_ficha(r, f):
    """Linhas de INFUSÕES E TERAPIAS: as do motor (DVA, SEDAÇÃO, BNM, de `infusoes_continuas`) no topo, mescladas na
    linha manual do mesmo rótulo (droga fora da tabela fica ali, depois das calculadas); o VC alvo vai na linha VM."""
    manuais = [[rot, list(itens)] for rot, itens in f["infusoes"]]
    geradas = {}
    for it in r.get("infusoes") or []:
        geradas.setdefault(it["grupo"], []).append(it["ficha"])
    linhas = []
    if geradas:  # sem bomba calculada, as linhas ficam como vieram
        for grupo in motor.bic.GRUPOS:  # DVA, SEDAÇÃO, BNM no topo, nessa ordem, com as manuais do mesmo rótulo
            mesma = [x for x in manuais if x[0].strip().upper() == grupo]
            itens = geradas.get(grupo, []) + [i for x in mesma for i in x[1]]
            if itens:
                linhas.append([grupo, itens])
            manuais = [x for x in manuais if x not in mesma]
    linhas += manuais
    if r.get("vc"):
        vc = f"VC 6 - 8 ml/kg (PP {round(r['pp'])} kg): {r['vc'][0]} - {r['vc'][1]} ml"
        vm = next((x for x in linhas if x[0].strip().upper() == "VM"), None)
        if vm:
            vm[1].append(vc)
        else:
            linhas.append(["VM", [vc]])
    return linhas


def col_rx(C, leito, meta, r=None):
    f = leito["ficha"]
    sec(C, f"PRESCRIÇÃO  {meta['data_prescricao']}", first=True)
    subsec(C, "INFUSÕES E TERAPIAS", before=1)
    bloco_rx(C, infusoes_da_ficha(r or {}, f))
    subsec(C, "POR SISTEMAS", before=4)
    bloco_rx(C, f["sistemas"])


def col_acao(C, leito, n_anot):
    f = leito["ficha"]
    sec(C, "PENDÊNCIAS", first=True)
    for it in f["vigiar"]:
        q = P(C, after=2.5)
        q.paragraph_format.left_indent = Cm(0.55); q.paragraph_format.first_line_indent = Cm(-0.55)
        t(q, "☐  "); rk(q, it)
    if f.get("exames"):
        sec(C, "EXAMES")
        for it in f["exames"]:
            q = P(C, after=2)
            q.paragraph_format.left_indent = Cm(0.3); q.paragraph_format.first_line_indent = Cm(-0.3)
            t(q, "– "); rk(q, it)
    sec(C, "ANOTAÇÕES / NOVOS EXAMES")
    linhas(C, n_anot)


def linhas(cell, n):
    for k in range(n):
        q = P(cell, after=0, before=11)
        t(q, " ", tam=E.PAUTA); borda_p(q, "bottom", E.FIO_SECAO, E.PAPEL_CINZA_ANOTACAO)
        q.paragraph_format.right_indent = Cm(0.01 * (k % 2))


# ── exame físico (opção A, aprovada em 07/11/2026) ───────────────────────────────────────────────────────
# 6 quadros por sistema, na ordem da evolução, para canetar à beira-leito: ☐ marca, ____ escreve.
# Sem a faixa de bundle (FAST HUGS BID) no pé dos quadros: ele mandou tirar em 07/11/2026.
EXAME = (
    ("NEURO", ("RASS ____  alvo ____   CAM-ICU ☐ +  ☐ −",
               "ECG ____   Pupilas ☐ iso  ☐ aniso  ☐ FR",
               "Dor ____   Déficit focal ☐ não  ☐ sim")),
    ("RESPIRATÓRIO", ("☐ AA  ☐ CN  ☐ VNI  ☐ CNAF  ☐ TOT/TQT",
                      "FiO2 ____  PEEP ____  Pplat ____  ΔP ____",
                      "MV ____________   ☐ crep  ☐ sib  ☐ roncos")),
    ("HEMODINÂMICA", ("Ritmo ☐ sinusal  ☐ FA  ____________",
                      "TEC ____ s   Mottling ____   ☐ extrem. frias",
                      "Bulhas ________________   ☐ sopro")),
    ("RENAL · METABÓLICO", ("Diurese ____ ml/kg/h   BH acum. ________",
                            "TRS ☐ não  ☐ sim  ____________",
                            "Glicemia ____ a ____   ☐ hipo (< 70)")),
    ("TGI · NUTRIÇÃO", ("Abdome ☐ flácido  ☐ distendido  ☐ doloroso",
                        "RHA ☐ +  ☐ −   Evacuação última ______",
                        "Dieta ____ % da meta   Resíduo ____")),
    ("INFECTO · PELE", ("Tmáx ____   Foco ________________",
                        "LPP ☐ não  ☐ sim  ________   Edema ____",
                        "Mobilização ____   Panturrilhas ☐ livres")),
)
N_INTER = 6  # linhas de intercorrências ao lado do exame: em 10, 9,5 e 9 pt ficam mais baixas que os quadros
N_INTER_COMPACTO = 4  # com o exame compacto: senão as intercorrências é que seguram a altura da faixa


def exame(cell, compacto=False):
    """EXAME FÍSICO: faixa com a hora e 2 linhas de 3 quadros (cabeçalho cinza, 3 linhas para canetar).
    Compacto (folha cheia, último recurso antes de baixar a fonte): os mesmos campos, com menos folga."""
    p = sec(cell, "EXAME FÍSICO", first=True)
    tab(p, E.FAIXA_EXAME - 0.4, "right")
    t(p, "\thora  ________", tam=S["tam"] - 1)
    q, v = E.QUADRO_EXAME, E.VAO_EXAME
    g = tabela(cell, 5, 5, [q, v, q, v, q])  # linhas: cabeçalho, quadro, vão, cabeçalho, quadro
    encolher(cell.paragraphs[-1])
    vao = g.rows[2]
    vao.height, vao.height_rule = Cm(0.08 if compacto else 0.15), WD_ROW_HEIGHT_RULE.EXACTLY
    for k, row in enumerate(g.rows):
        for j, c in enumerate(row.cells):
            if k == 2 or j in (1, 3):  # vãos: sem borda, sem margem, sem altura própria
                margens(c, 0, 0, 0, 0); encolher(c.paragraphs[0])
    fio = (E.FIO_SECAO, E.PAPEL_TINTA)
    for i, (titulo, itens) in enumerate(EXAME):
        lin, col = 3 * (i // 3), 2 * (i % 3)
        cab, corpo = g.rows[lin].cells[col], g.rows[lin + 1].cells[col]
        borda_cel(cab, top=fio, left=fio, bottom=fio, right=fio)
        borda_cel(corpo, left=fio, bottom=fio, right=fio)
        sombra(cab._tc.get_or_add_tcPr(), E.PAPEL_CINZA_SUB)
        m = 0 if compacto else 10
        margens(cab, m, 60, m, 40); margens(corpo, 0, 60, 2 * m + 20, 40)
        t(P(cab, True, 0), titulo, b=True, tam=S["tam"] - 1)
        for j, item in enumerate(itens):
            t(P(corpo, first=(j == 0), after=0, before=1 if compacto else 4.5), item, tam=S["tam"] - 1)


# ── página ─────────────────────────────────────────────────────────────────
def pagina(doc, meta, leito, n_anot, n_inter, primeiro, compacto=False):
    r = motor.compute_leito(leito, meta)
    if not primeiro:
        q = doc.add_paragraph(); q.paragraph_format.page_break_before = True
        q.paragraph_format.space_after = Pt(0); t(q, " ", tam=E.ESPACADOR)

    wbox, wdir = E.CAIXA_LEITO, E.CABECALHO_DIREITA
    h = tabela(doc, 1, 3, [wbox, W - wbox - wdir, wdir])
    a, b, c = h.rows[0].cells
    for cc in (a, b, c):
        cc.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    caixa = (E.FIO_CAIXA, E.PAPEL_TINTA)
    borda_cel(a, top=caixa, left=caixa, bottom=caixa, right=caixa)
    margens(a, 20, 40, 20, 40); margens(b, 0, 200, 0, 100); margens(c, 0, 100, 0, 0)
    q = P(a, True, 0); q.alignment = 1; t(q, "LEITO", b=True, tam=E.LEITO_ROTULO)
    q = P(a, after=0); q.alignment = 1; t(q, leito["leito"], b=True, tam=E.LEITO)
    nome = leito["nome"].title().replace(" Da ", " da ").replace(" De ", " de ")
    idade, sexo = idade_sexo_ficha(leito["idade_sexo"])
    peso, altura = peso_altura_ficha(leito)
    demo = S["tam"] - 1  # 9 pt nas linhas do nome: mesmo truque do modelo antigo (tudo no 1º parágrafo)
    q = P(b, True, 0)
    t(q, nome, b=True, tam=E.NOME)
    q.add_run().add_break(WD_BREAK.LINE)
    uti = leito["dia_uti"].split(" (")[0]
    t(q, f"     {uti}     ", tam=demo)
    t(q, "Idade:  ", b=True, tam=demo)
    t(q, idade, tam=demo)
    t(q, "     Sexo:  ", b=True, tam=demo)
    t(q, sexo, tam=demo)
    t(q, "     Peso:  ", b=True, tam=demo)
    t(q, peso, tam=demo)
    t(q, "     Altura:  ", b=True, tam=demo)
    t(q, altura, tam=demo)
    rk(rotulo_cabecalho(b, "HD", after=0), dado(leito, "hd"), tam=demo)
    rk(rotulo_cabecalho(b, "Disp.", after=1), dado(leito, "disp"), tam=demo)
    al = dado(leito, "alergia")
    q = P(c, True, 3)
    if al.strip().lower() in ("", "nega"):
        t(q, "Alergia:  ", b=True); t(q, al.strip().lower())
    else:  # alergia em caixa preta: salta aos olhos
        moldura(q, E.PAPEL_TINTA, E.FIO_CAIXA)
        t(q, f"ALERGIA:  {al.upper()}", b=True)
    q = P(c, after=0); t(q, f"{meta['turno'].capitalize()}  ·  {meta['data']}")
    q.paragraph_format.left_indent = Pt(2 + E.FIO_CAIXA / 8)  # alinhado ao texto da caixa
    q = doc.add_paragraph(); q.paragraph_format.space_after = Pt(4); q.paragraph_format.space_before = Pt(2)
    t(q, " ", tam=E.ESPACADOR); borda_p(q, "bottom", E.FIO_CAIXA)

    body = tabela(doc, 1, 3, [WL, WM, WR], {"insideV": (E.FIO_SECAO, E.PAPEL_TINTA)})
    esq, meio, dir_ = body.rows[0].cells
    margens(esq, 0, 0, 0, 150); margens(meio, 0, 150, 0, 150); margens(dir_, 0, 150, 0, 0)
    col_controles(esq, r, leito, *janelas(leito, meta, r["janela"]))
    col_rx(meio, leito, meta, r)
    col_acao(dir_, leito, n_anot)

    q = doc.add_paragraph(); q.paragraph_format.space_before = Pt(6); q.paragraph_format.space_after = Pt(4)
    t(q, " ", tam=E.ESPACADOR); borda_p(q, "bottom", E.FIO_TITULO)
    wl = E.FAIXA_EXAME  # o exame fica sob as colunas 1 e 2; as intercorrências, sob a coluna 3
    bt = tabela(doc, 1, 2, [wl, W - wl], {"insideV": (E.FIO_SECAO, E.PAPEL_TINTA)})
    L, R = bt.rows[0].cells
    margens(L, 0, 0, 0, 150); margens(R, 0, 150, 0, 0)
    exame(L, compacto)
    # 225,8 pt de texto em 8,4 cm: com a folga de 2 pt a faixa quebrava em 2 linhas; com 1 pt sobram 1,8 pt
    sec(R, "INTERCORRÊNCIAS, CONDUTAS E PASSAGEM", first=True, folga=1)
    linhas(R, n_inter)


ORDEM = {
    "pPr": "pStyle keepNext keepLines pageBreakBefore framePr widowControl numPr suppressLineNumbers pBdr shd tabs "
           "suppressAutoHyphens kinsoku wordWrap overflowPunct topLinePunct autoSpaceDE autoSpaceDN bidi "
           "adjustRightInd snapToGrid spacing ind contextualSpacing mirrorIndents suppressOverlap jc textDirection "
           "textAlignment textboxTightWrap outlineLvl divId cnfStyle rPr sectPr pPrChange",
    "tcPr": "cnfStyle tcW gridSpan hMerge vMerge tcBorders shd noWrap tcMar textDirection tcFitText vAlign hideMark "
            "headers cellIns cellDel cellMerge tcPrChange",
    "tblPr": "tblStyle tblpPr tblOverlap bidiVisual tblStyleRowBandSize tblStyleColBandSize tblW jc tblCellSpacing "
             "tblInd tblBorders shd tblLayout tblCellMar tblLook tblCaption tblDescription tblPrChange",
}


def sanear(doc):
    """Reordena pPr/tcPr/tblPr na ordem do schema OOXML (o Word é estrito; o LibreOffice não)."""
    for tag, ordem in ORDEM.items():
        pos = {qn("w:" + n): i for i, n in enumerate(ordem.split())}
        for el in doc.element.body.iter(qn("w:" + tag)):
            filhos = list(el)
            vistos, unicos = set(), []
            for f in filhos:
                if f.tag in vistos and f.tag != qn("w:tab"):
                    el.remove(f); continue
                vistos.add(f.tag); unicos.append(f)
            for f in unicos:
                el.remove(f)
            for f in sorted(unicos, key=lambda x: pos.get(x.tag, 999)):
                el.append(f)


def gerar(plantao, caminho, cfg=None, folga=0.0):
    meta = plantao["meta"]
    doc = Document()
    st = doc.styles["Normal"]; st.font.name = FONTE; st.font.size = Pt(E.CORPO)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), FONTE)
    st.paragraph_format.space_after = Pt(0); st.paragraph_format.space_before = Pt(0)
    s = doc.sections[0]; s.orientation = WD_ORIENT.LANDSCAPE
    s.page_width, s.page_height = Cm(E.A4_LONGO), Cm(E.A4_CURTO)
    s.left_margin = s.right_margin = Cm(E.MARGEM_FICHA_LATERAL); s.top_margin = Cm(E.MARGEM_FICHA_TOPO)
    s.bottom_margin = Cm(E.MARGEM_FICHA_PE + folga)
    s.header_distance = s.footer_distance = Cm(E.DISTANCIA_CABECALHO)
    for i, leito in enumerate(plantao["leitos"]):
        n_anot, n_inter, tam, *compacto = (cfg or {}).get(leito["leito"], (6, N_INTER, E.CORPO, False))
        S["tam"] = tam
        pagina(doc, meta, leito, n_anot, n_inter, i == 0, compacto=bool(compacto and compacto[0]))
    body = doc.element.body
    if body[0].tag == qn("w:p") and not "".join(body[0].itertext()).strip():
        body.remove(body[0])
    S["tam"] = E.CORPO
    sanear(doc)
    doc.save(caminho)


def n_paginas(docx):
    pdf = office.para_pdf(docx, timeout=180)
    out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
    return int(re.search(r"Pages:\s+(\d+)", out).group(1))


def ajustar(plantao, folga=E.FOLGA_MEDICAO):
    """Devolve (cfg por leito, leitos que não couberam nem em 9 pt sem anotações)."""
    res, nao_coube = {}, []
    with tempfile.TemporaryDirectory() as tmp:
        for leito in plantao["leitos"]:
            um = {"meta": plantao["meta"], "leitos": [leito]}
            achou = None
            # Em cada tamanho: primeiro descem as anotações (as intercorrências ficam ao lado do exame e não
            # aumentam a folha); depois o exame fica compacto, com 4 intercorrências; só então a fonte desce.
            for tam in E.AJUSTE:
                for compacto, n_inter in ((False, N_INTER), (True, N_INTER_COMPACTO)):
                    for n_anot in (14, 12, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0):
                        fx = Path(tmp) / "x.docx"
                        tentativa = (n_anot, n_inter, tam, compacto)
                        gerar(um, fx, {leito["leito"]: tentativa}, folga=folga)
                        if n_paginas(fx) == 1:
                            achou = tentativa; break
                    if achou:
                        break
                if achou:
                    break
            res[leito["leito"]] = achou or (0, N_INTER_COMPACTO, 9, True)
            if not achou:
                nao_coube.append(leito["leito"])
            print(leito["leito"], res[leito["leito"]], "OK" if achou else "NAO COUBE", file=sys.stderr)
    return res, nao_coube


if __name__ == "__main__":
    pl, _ = motor.preparar(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))  # dias de ATB e de UTI
    cfg, nao_coube = ajustar(pl)
    gerar(pl, sys.argv[2], cfg)
    print(sys.argv[2])
    if nao_coube:
        sys.exit("NAO COUBE em 1 folha: leito(s) " + ", ".join(nao_coube))
