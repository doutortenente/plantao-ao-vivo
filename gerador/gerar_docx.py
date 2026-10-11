#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gerar_docx.py — gera os dois Word do plantão a partir de UM arquivo JSON.

  1. DD-MM-AA-utiN-evolucoes-<turno>.docx   (retrato, 1 leito por página)
     Só os blocos que mudam no dia, na ordem do docs/BRIEFING.md.
  2. DD-MM-AA-utiN-ficha-cola-<turno>.docx  (paisagem, 1 FOLHA por leito)
     Esquerda: sinais vitais + balanço + laboratório. Direita: prescrição por
     classe, uma droga por linha ("Nome (genérico) dose => horários").
     Embaixo: linhas para anotação. Nunca passa de uma folha por leito.

Fonte Times New Roman 10 em tudo; destaque só por negrito (rótulos, flags, alertas). Sem cor.
Toda conta (Máx - Mín, flags, balanço) vem do motor:
skills/sasi-ingest-export/scripts/build_passagem.py

Uso:
  python3 gerador/gerar_docx.py plantao.json --saida pasta/
  python3 gerador/gerar_docx.py plantao.json --saida pasta/ --sem-ajuste   # não chama o LibreOffice

O ajuste automático (padrão) usa o LibreOffice para medir quantas linhas de
anotação cabem em cada folha da ficha-cola. Sem LibreOffice, usa 3 linhas.
Contrato do JSON: gerador/schema-plantao.md
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "skills" / "sasi-ingest-export" / "scripts"))
import build_passagem as motor  # noqa: E402

from docx import Document  # noqa: E402
from docx.enum.section import WD_ORIENT  # noqa: E402
from docx.enum.text import WD_TAB_ALIGNMENT, WD_TAB_LEADER  # noqa: E402
from docx.oxml import OxmlElement  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.shared import Cm, Pt, RGBColor  # noqa: E402

FONTE = "Times New Roman"
TAM = 10
RED = None  # sem cor: destaque só por negrito (pedido de 11/10/2026)
FLAG = re.compile(r"(\[[^\]]*x [<>][^\]]*\])")
VITAIS = ("PAS", "PAD", "PAM", "FC", "FR", "SpO2", "Sup O2", "TAX", "Dx")


# ── utilidades de formatação ─────────────────────────────────────────────────
def base(doc, entrelinha=1.08):
    st = doc.styles["Normal"]
    st.font.name = FONTE
    st.font.size = Pt(TAM)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), FONTE)
    pf = st.paragraph_format
    pf.space_before = Pt(0); pf.space_after = Pt(0); pf.line_spacing = entrelinha


_ATUAL = {"tam": TAM}  # tamanho corrente (a ficha pode reduzir 0,5 pt num leito que não cabe)


def T(p, texto, negrito=False, cor=None, tam=None):
    r = p.add_run(texto)
    r.bold = negrito
    if cor is not None:
        r.font.color.rgb = cor
    r.font.size = Pt(tam or _ATUAL["tam"])
    return r


def com_flags(p, texto, tam=None):
    for parte in FLAG.split(texto):
        if parte:
            if FLAG.fullmatch(parte):
                T(p, parte, True, RED, tam)
            else:
                T(p, parte, False, None, tam)


def filete(p, sz=6, cor="000000"):
    pPr = p._p.get_or_add_pPr()
    b = OxmlElement("w:pBdr"); e = OxmlElement("w:bottom")
    for k, v in (("val", "single"), ("sz", str(sz)), ("space", "1"), ("color", cor)):
        e.set(qn("w:" + k), v)
    b.append(e); pPr.append(b)


def rotulo_valor(p, linha, tam=None):
    m = re.match(r"^(-\s)?([^:]{1,40}):(.*)$", linha)
    if m:
        T(p, (m.group(1) or "") + m.group(2) + ":", True, None, tam)
        com_flags(p, m.group(3), tam)
    else:
        com_flags(p, linha, tam)


def separar_pipes(linhas):
    out = []
    for l in linhas:
        if not l.strip():
            continue
        partes = [x.strip() for x in l.split(" | ")]
        out += partes if all(re.match(r"^[^:]{1,40}:", x) for x in partes) else [l]
    return out


# ── EVOLUÇÕES ────────────────────────────────────────────────────────────────
def gerar_evolucoes(plantao, caminho):
    meta = plantao.get("meta", {})
    doc = Document(); base(doc)
    s = doc.sections[0]
    s.page_height, s.page_width = Cm(29.7), Cm(21.0)
    s.left_margin = s.right_margin = Cm(2.0)
    s.top_margin = s.bottom_margin = Cm(1.8)
    for i, leito in enumerate(plantao["leitos"]):
        r = motor.compute_leito(leito, meta)
        p = doc.add_paragraph()
        if i:
            p.paragraph_format.page_break_before = True
        T(p, f"LEITO {leito['leito']}  ", True, tam=TAM)
        T(p, leito.get("nome", ""), True, tam=TAM)
        p2 = doc.add_paragraph()
        info = [leito.get("idade_sexo"), leito.get("dia_uti"),
                f"Evolução {meta.get('turno', '')} {meta.get('unidade', '')}".strip(), meta.get("data")]
        T(p2, "  ·  ".join(x for x in info if x))
        filete(p2, 8); p2.paragraph_format.space_after = Pt(6)
        for titulo, linhas in r["secoes"]:
            h = doc.add_paragraph()
            h.paragraph_format.space_before = Pt(9); h.paragraph_format.space_after = Pt(3)
            h.paragraph_format.keep_with_next = True
            T(h, titulo, True, tam=TAM); filete(h, 4, "808080")
            plano = titulo.startswith("Plano")
            for l in linhas:
                if not l.strip():
                    continue
                q = doc.add_paragraph(); q.paragraph_format.space_after = Pt(1.5)
                if re.match(r"^(\d+\.\s|-\s)", l):
                    q.paragraph_format.left_indent = Cm(0.5); q.paragraph_format.first_line_indent = Cm(-0.5)
                if plano and l.startswith("- "):
                    q.paragraph_format.left_indent = Cm(0.9); q.paragraph_format.first_line_indent = Cm(-0.4)
                m_num = re.match(r"^(\d+\.\s[^:]{1,40}:)(.*)$", l) if plano else re.match(r"^(\d+\.\s)(.*)$", l)
                if titulo.startswith(("Evolução",)):
                    com_flags(q, l)
                elif m_num and (plano or titulo.startswith("Impressão")):
                    T(q, m_num.group(1), True); T(q, m_num.group(2))
                elif plano or titulo.startswith("Impressão"):
                    T(q, l)
                else:
                    rotulo_valor(q, l)
    doc.save(caminho)


# ── FICHA-COLA ───────────────────────────────────────────────────────────────
def _sem_recuo(t):
    tblPr = t._tbl.tblPr; ind = OxmlElement("w:tblInd")
    ind.set(qn("w:w"), "108"); ind.set(qn("w:type"), "dxa"); tblPr.append(ind)


def _tabela_lisa(t):
    _sem_recuo(t)
    tblPr = t._tbl.tblPr; b = OxmlElement("w:tblBorders")
    for e in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement("w:" + e)
        if e == "insideV":
            el.set(qn("w:val"), "single"); el.set(qn("w:sz"), "6"); el.set(qn("w:color"), "000000")
        else:
            el.set(qn("w:val"), "nil")
        b.append(el)
    tblPr.append(b)


def _larguras(t, ws):
    tblPr = t._tbl.tblPr; lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
    t.autofit = False
    for i, gc in enumerate(t._tbl.tblGrid.findall(qn("w:gridCol"))):
        gc.set(qn("w:w"), str(ws[i].twips))
    for row in t.rows:
        for i, w in enumerate(ws):
            row.cells[i].width = w


def _margens(cell, esq, dir_):
    tcPr = cell._tc.get_or_add_tcPr(); m = OxmlElement("w:tcMar")
    for k, v in (("left", esq), ("right", dir_), ("top", 0), ("bottom", 0)):
        e = OxmlElement("w:" + k); e.set(qn("w:w"), str(v)); e.set(qn("w:type"), "dxa"); m.append(e)
    tcPr.append(m)


def _par(cell):
    p = cell.paragraphs[-1]
    return p if (not p.runs and p.text == "") else cell.add_paragraph()


def _titulo_col(cell, texto, primeiro=False):
    p = _par(cell)
    if not primeiro:
        p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    T(p, texto, True, tam=TAM); filete(p, 4)


def _kv(cell, linha, tab):
    p = _par(cell); p.paragraph_format.space_after = Pt(1)
    m = re.match(r"^(Gaso[^)]*\)|[^:]{1,40}):\s*(.*)$", linha)
    if not m:
        com_flags(p, linha); return
    rot, val = m.group(1), m.group(2)
    if len(rot) <= (6 if tab < Cm(1.8) else 10):
        p.paragraph_format.tab_stops.add_tab_stop(tab)
        p.paragraph_format.left_indent = tab; p.paragraph_format.first_line_indent = -tab
        T(p, rot, True); T(p, "\t")
    else:
        T(p, rot + ": ", True)
    com_flags(p, val)


def _item_rx(cell, texto, largura):
    q = _par(cell)
    q.paragraph_format.left_indent = Cm(0.8); q.paragraph_format.first_line_indent = Cm(-0.4)
    q.paragraph_format.space_after = Pt(1)
    alerta = bool(re.search(r"SUSPENSO|duplicidade", texto))
    cor = None
    droga, _, hora = texto.partition("=>")
    droga = droga.rstrip()
    m = re.match(r"^([^(]+?)(\s\(.*?\))(.*)$", droga)
    if m and len(m.group(1)) < 24:
        T(q, m.group(1), True, cor); T(q, m.group(2)); T(q, m.group(3), alerta, cor)
    else:
        mb = re.match(r"^(\D+?)(\s[\d<].*)?$", droga)
        if mb and len(mb.group(1)) < 26 and not alerta:
            T(q, mb.group(1), True); T(q, mb.group(2) or "")
        else:
            T(q, droga, alerta, cor)
    if hora.strip():
        q.paragraph_format.tab_stops.add_tab_stop(largura - Cm(0.45), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        hm = re.match(r"^([\d\-:h ]+?)(\s*\(.*\))?$", hora.strip())
        if hm:
            T(q, "\t"); T(q, hm.group(1).strip() + " h", True); T(q, hm.group(2) or "")
        else:
            T(q, "\t"); T(q, hora.strip(), True)


# ── grade compacta (rótulo | valor | rótulo | valor) para a coluna esquerda ─
CINZA = "BFBFBF"


def _grade(cell, itens, largura):
    """itens: lista de (rótulo, valor). Valor longo ocupa a linha inteira."""
    if not itens:
        return
    curto = all(len(r) <= 5 for r, _ in itens if len(r) <= 9)
    lw = 1.3 if curto else 2.1
    wl = Cm(lw); wv = Cm((largura.cm - 2 * lw) / 2)
    linhas, par = [], []
    for rot, val in itens:
        longo = len(rot) > 9 or len(val) > (26 if lw > 1.5 else 30)
        if longo:
            if par: linhas.append(par); par = []
            linhas.append([(rot, val, True)])
        else:
            par.append((rot, val, False))
            if len(par) == 2: linhas.append(par); par = []
    if par: linhas.append(par)
    t = cell.add_table(rows=len(linhas), cols=4)
    tblPr = t._tbl.tblPr; b = OxmlElement("w:tblBorders")
    for e in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement("w:" + e)
        if e in ("insideH", "bottom", "top"):
            el.set(qn("w:val"), "single"); el.set(qn("w:sz"), "4"); el.set(qn("w:color"), CINZA)
        else:
            el.set(qn("w:val"), "nil")
        b.append(el)
    tblPr.append(b)
    _larguras(t, [wl, wv, wl, wv])
    for r_i, linha in enumerate(linhas):
        cells = t.rows[r_i].cells
        for c in cells: _margens(c, 40, 40)
        if linha[0][2]:  # linha inteira
            m = cells[0].merge(cells[3])
            p = m.paragraphs[0]; p.paragraph_format.space_before = Pt(1); p.paragraph_format.space_after = Pt(1)
            if linha[0][0]:
                T(p, linha[0][0] + ": ", True)
            com_flags(p, linha[0][1])
            continue
        for k, (rot, val, _) in enumerate(linha):
            pr = cells[2 * k].paragraphs[0]; pv = cells[2 * k + 1].paragraphs[0]
            for p in (pr, pv): p.paragraph_format.space_before = Pt(1); p.paragraph_format.space_after = Pt(1)
            T(pr, rot, True); com_flags(pv, val)
    # parágrafo depois da tabela aninhada (exigência do Word) — mínimo
    q = cell.add_paragraph(); q.paragraph_format.line_spacing = Pt(1)
    q.paragraph_format.space_after = Pt(0); T(q, "", tam=1)


def _pares(linhas):
    out = []
    for l in linhas:
        m = re.match(r"^(Gaso[^)]*\)|[^:]{1,40}):\s*(.*)$", l)
        rot, val = (m.group(1), m.group(2)) if m else ("", l)
        rot = {"Ingesta hídrica": "Ingesta", "Resíduo gástrico": "Resíduo"}.get(rot, rot)
        out.append((rot, val))
    return out


# Item 4 (11/10/2026): a ficha-cola mostra só o que muda decisão. Saem tópicos de pele, colírios,
# lágrima artificial, simeticona e a classe SN. A evolução e a prescrição real não são afetadas.
CLASSES_OMITIR = {"SN", "SINTOMÁTICOS", "OFTALMO", "PELE", "TÓPICOS"}
ITENS_OMITIR = re.compile(
    r"\b(col[íi]rio|lacrima|lumigan|brixag|ephynal|hirudoid|brava|comfeel|com feel|primoderm|primo derme|"
    r"rio ?hex|riohex|luftal|simeticona|dersani|fresubin creme|fresubin protein|resource fiber|complexo b|"
    r"shilley heparinizado|água( mineral)? \d+ ?ml)\b", re.I)


def filtrar_prescricao(prescricao):
    out = []
    for bloco in prescricao:
        if bloco["classe"].strip().upper() in CLASSES_OMITIR:
            continue
        itens = []
        for item in bloco["itens"]:
            partes = [x for x in item.split(" | ") if not ITENS_OMITIR.search(x)]
            partes = ["; ".join(p for p in x.split("; ") if not ITENS_OMITIR.search(p)) for x in partes]
            partes = [x for x in partes if x.strip()]
            if partes:
                itens.append(" | ".join(partes))
        if itens:
            out.append({"classe": bloco["classe"], "itens": itens})
    return out


def gerar_ficha(plantao, caminho, linhas_notas=None):
    meta = plantao.get("meta", {})
    linhas_notas = linhas_notas or {}
    doc = Document(); base(doc, 1.0)
    s = doc.sections[0]; s.orientation = WD_ORIENT.LANDSCAPE
    s.page_width, s.page_height = Cm(29.7), Cm(21.0)
    s.left_margin = s.right_margin = Cm(1.2); s.top_margin = Cm(0.8); s.bottom_margin = Cm(0.6)
    W = 29.7 - 2.4
    for i, leito in enumerate(plantao["leitos"]):
        cfg = linhas_notas.get(leito["leito"], (3, TAM))
        if not isinstance(cfg, tuple):
            cfg = (cfg, TAM)
        n_notas, _ATUAL["tam"] = cfg[0], cfg[1]
        col_chk = cfg[2] if len(cfg) > 2 else "auto"
        r = motor.compute_leito(leito, meta)
        secoes = dict(r["secoes"])
        p = doc.add_paragraph()
        if i:
            p.paragraph_format.page_break_before = True
        T(p, f"LEITO {leito['leito']}   ", True, tam=TAM)
        T(p, f"{leito.get('nome', '')}, {leito.get('idade_sexo', '')}".strip(", "), True, tam=TAM)
        extra = [x for x in (leito.get("dia_uti"), f"{meta.get('data', '')} {meta.get('turno', '')}".strip()) if x]
        T(p, "   ·   " + "   ·   ".join(extra), tam=TAM)
        if leito.get("diagnostico"):
            T(doc.add_paragraph(), leito["diagnostico"], tam=TAM)
        p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(2)
        alergia = leito.get("alergia", "?")
        T(p, "Alergia: ", True, tam=TAM)
        T(p, alergia, True, None, TAM)
        dieta = leito.get("dieta_ficha") or leito.get("dieta")
        if dieta:
            T(p, "      Dieta: ", True, tam=TAM); T(p, dieta, tam=TAM)
        if leito.get("dispositivos"):
            q = doc.add_paragraph(); q.paragraph_format.space_before = Pt(1)
            q.paragraph_format.left_indent = Cm(2.3); q.paragraph_format.first_line_indent = Cm(-2.3)
            T(q, "Dispositivos/ATB: ", True); T(q, leito["dispositivos"])
            p = q
        alertas = leito.get("alertas", [])
        if alertas:
            for a in alertas:
                q = doc.add_paragraph(); q.paragraph_format.left_indent = Cm(0.35)
                q.paragraph_format.first_line_indent = Cm(-0.35); q.paragraph_format.space_before = Pt(1)
                T(q, "! ", True); T(q, a, True)
            p = doc.paragraphs[-1]
        p.paragraph_format.space_after = Pt(3)
        filete(p, 8)

        t = doc.add_table(rows=1, cols=2); _tabela_lisa(t)
        wl, wr = Cm(11.3), Cm(W - 11.3); _larguras(t, [wl, wr])
        E, D = t.rows[0].cells; _margens(E, 0, 220); _margens(D, 220, 0)

        jan_tit, jan_linhas = r["secoes"][0]
        todas = separar_pipes(jan_linhas)
        vit = [l for l in todas if l.split(":")[0] in VITAIS]
        bal = [l for l in todas if l not in vit]
        janela = leito.get("janela") or meta.get("janela", "24 h")
        larg_e = Cm(11.3 - 0.4)
        _titulo_col(E, f"SINAIS VITAIS {janela}", primeiro=True)
        _grade(E, _pares(vit), larg_e)
        _titulo_col(E, f"BALANÇO {janela}")
        _grade(E, _pares(bal), larg_e)
        lab = secoes.get("Laboratório:", [])
        if lab:
            _titulo_col(E, "LABORATÓRIO")
            _grade(E, _pares(separar_pipes(lab)), larg_e)

        _titulo_col(D, f"PRESCRIÇÃO {meta.get('data_prescricao', meta.get('data', ''))}".strip(), primeiro=True)
        n_rx = 0
        for bloco in filtrar_prescricao(leito.get("prescricao", [])):
            q = _par(D); q.paragraph_format.space_before = Pt(5); q.paragraph_format.space_after = Pt(1)
            T(q, bloco["classe"].upper(), True, tam=TAM)
            for item in bloco["itens"]:
                for x in item.split(" | "):
                    _item_rx(D, x, wr); n_rx += 1
            n_rx += 2
        checklist = leito.get("checklist", [])
        if checklist:
            n_esq = len(vit) // 2 + len(bal) // 2 + len(lab) + 6
            C = {"E": E, "D": D}.get(col_chk) or (E if n_esq <= n_rx else D)
            _titulo_col(C, "CHECKLIST DO PLANTÃO")
            for item in checklist:
                q = _par(C); q.paragraph_format.space_after = Pt(2)
                q.paragraph_format.left_indent = Cm(0.55); q.paragraph_format.first_line_indent = Cm(-0.55)
                T(q, "☐  "); T(q, item)
        n = n_notas
        if n:
            p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(8)
            T(p, "Anotações", True, tam=TAM)
            for k in range(n):
                q = doc.add_paragraph(); q.paragraph_format.space_before = Pt(12)
                T(q, " ", tam=8); filete(q, 4, "9A9A9A")
                pPr = q._p.get_or_add_pPr(); ind = OxmlElement("w:ind")
                ind.set(qn("w:right"), str(k % 2)); pPr.append(ind)  # evita o Word fundir as bordas
    _ATUAL["tam"] = TAM
    doc.save(caminho)


# ── ajuste automático (quantas linhas de anotação cabem em 1 folha) ─────────
def _paginas(docx_path):
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    out = Path(docx_path).parent
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(out), str(docx_path)],
                   check=True, capture_output=True, timeout=180)
    pdf = Path(docx_path).with_suffix(".pdf")
    dados = pdf.read_bytes()
    n = len(re.findall(rb"/Type\s*/Page[^s]", dados))
    pdf.unlink()
    return n


def ajustar_linhas(plantao):
    if not (shutil.which("soffice") or shutil.which("libreoffice")):
        return {}
    res = {}
    with tempfile.TemporaryDirectory() as tmp:
        for leito in plantao["leitos"]:
            um = {"meta": plantao.get("meta", {}), "leitos": [leito]}
            res[leito["leito"]] = (0, TAM)
            achou = False
            melhor = None
            for col in ("E", "D"):
                for n in range(8, -1, -1):
                    f = Path(tmp) / "x.docx"
                    gerar_ficha(um, f, {leito["leito"]: (n, TAM, col)})
                    if _paginas(f) == 1:
                        if melhor is None or n > melhor[0]:
                            melhor = (n, TAM, col)
                        break
            if melhor:
                res[leito["leito"]] = melhor; achou = True
            if not achou:
                print(f"AVISO: leito {leito['leito']} não coube em 1 folha nem sem anotações — encurte a prescrição.",
                      file=sys.stderr)
    return res


def nome_arquivo(meta, classe, tipo):
    """Padrão DD-MM-AA-utiN-<classe>.<tipo>, ex.: 11-10-26-uti2-ficha-cola-diurno.docx"""
    d = re.match(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", meta.get("data", ""))
    data = f"{int(d.group(1)):02d}-{int(d.group(2)):02d}-{d.group(3)[-2:]}" if d else "sem-data"
    uti = re.sub(r"\s+", "", meta.get("unidade", "uti")).lower()
    return f"{data}-{uti}-{classe}.{tipo}"


def main():
    ap = argparse.ArgumentParser(description="Gera evolução + ficha-cola (.docx) do plantão.")
    ap.add_argument("json")
    ap.add_argument("--saida", default="saida")
    ap.add_argument("--sem-ajuste", action="store_true")
    a = ap.parse_args()
    plantao = json.loads(Path(a.json).read_text(encoding="utf-8"))
    meta = plantao.get("meta", {})
    pasta = Path(a.saida); pasta.mkdir(parents=True, exist_ok=True)
    turno = re.sub(r"\s+", "-", meta.get("turno", "").strip().lower())
    sufixo = f"-{turno}" if turno else ""
    evo = pasta / nome_arquivo(meta, "evolucoes" + sufixo, "docx")
    cola = pasta / nome_arquivo(meta, "ficha-cola" + sufixo, "docx")
    gerar_evolucoes(plantao, evo)
    linhas = {} if a.sem_ajuste else ajustar_linhas(plantao)
    gerar_ficha(plantao, cola, linhas)
    print(evo); print(cola)
    _, avisos = motor.build(plantao)
    if avisos:
        print("\nRodapé (conferir — fora do bloco):")
        for w in avisos:
            print("- " + w)


if __name__ == "__main__":
    main()
