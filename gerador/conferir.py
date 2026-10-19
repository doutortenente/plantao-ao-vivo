#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conferir.py — confere a entrega depois de gerar (o que antes era feito no olho).

Erros (a entrega não pode sair assim):
  - ficha-cola com nº de páginas diferente do nº de leitos (1 folha por leito);
  - run fora de Times New Roman, tamanho fora da lista aprovada, ou com cor;
  - "(revisar)" no texto; "–"/"—" entre números (Máx - Mín usa " - "); setas ↑ ↓ na evolução.
Avisos: "→" no texto; LibreOffice ausente (sem PDF não dá para contar páginas).

Também gera o PDF da evolução e um PNG por página em <saida>/paginas/, para olhar todas as folhas.

Uso:
  python3 gerador/conferir.py <evolucoes.docx> <ficha-cola.docx> --leitos N
O gerar_docx.py chama conferir() sozinho no fim.
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import estilo as E  # noqa: E402
import office  # noqa: E402

from docx import Document  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402

# Tamanhos aprovados (pt). Evolução: só o corpo. Ficha: corpo nos 3 degraus do ajuste, rótulos (corpo - 1),
# células da grade de controles (corpo + 1) e as exceções fixas aprovadas em 19/10/2026.
TAM_EVOLUCAO = {E.CORPO}
TAM_FICHA = ({t for t in E.AJUSTE} | {t - 1 for t in E.AJUSTE} | {t + 1 for t in E.AJUSTE}
             | {E.NOME, E.LEITO, E.LEITO_ROTULO, E.PAUTA, E.ESPACADOR})

TRAVESSAO_NUMEROS = re.compile(r"\d\s*[–—]\s*\d")
SETAS_PROIBIDAS = re.compile(r"[↑↓]")


def _texto_paragrafos(doc):
    for p in doc.element.body.iter(qn("w:p")):
        yield "".join(t.text or "" for t in p.iter(qn("w:t")))


def conferir_docx(caminho, tamanhos, evolucao=False):
    """Erros e avisos de fonte, tamanho, cor e texto de um .docx."""
    erros, avisos = [], []
    nome = Path(caminho).name
    doc = Document(str(caminho))
    if doc.styles["Normal"].font.name != E.FONTE:
        erros.append(f"{nome}: estilo Normal em {doc.styles['Normal'].font.name}, não {E.FONTE}")
    fontes, tams, cor = set(), set(), 0
    for r in doc.element.body.iter(qn("w:r")):
        rpr = r.find(qn("w:rPr"))
        if rpr is None:
            continue
        rf = rpr.find(qn("w:rFonts"))
        if rf is not None and rf.get(qn("w:ascii")) not in (None, E.FONTE):
            fontes.add(rf.get(qn("w:ascii")))
        sz = rpr.find(qn("w:sz"))
        if sz is not None and "".join(t.text or "" for t in r.iter(qn("w:t"))):
            tams.add(int(sz.get(qn("w:val"))) / 2)
        if rpr.find(qn("w:color")) is not None:
            cor += 1
    if fontes:
        erros.append(f"{nome}: fonte fora do padrão: {', '.join(sorted(fontes))}")
    fora = sorted(t for t in tams if t not in tamanhos)
    if fora:
        erros.append(f"{nome}: tamanho fora da lista aprovada: {', '.join(f'{t:g} pt' for t in fora)}")
    if cor:
        erros.append(f"{nome}: {cor} trecho(s) com cor (destaque é só negrito)")
    for txt in _texto_paragrafos(doc):
        if "(revisar)" in txt.lower():
            erros.append(f"{nome}: \"(revisar)\" no texto: {txt[:80]}")
        if TRAVESSAO_NUMEROS.search(txt):
            erros.append(f"{nome}: travessão entre números (use \" - \"): {txt[:80]}")
        if evolucao and SETAS_PROIBIDAS.search(txt):
            erros.append(f"{nome}: seta ↑/↓ no texto: {txt[:80]}")
        if "→" in txt:
            avisos.append(f"{nome}: seta → no texto: {txt[:80]}")
    return erros, avisos


def para_pdf(docx):
    return office.para_pdf(docx)


def paginas(pdf):
    out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, check=True).stdout
    return int(re.search(r"Pages:\s+(\d+)", out).group(1))


def fotos(pdf, pasta, dpi=80):
    pasta.mkdir(parents=True, exist_ok=True)
    for velho in pasta.glob(f"{pdf.stem}-*.png"):
        velho.unlink()
    subprocess.run(["pdftoppm", "-r", str(dpi), "-png", str(pdf), str(pasta / pdf.stem)], check=True,
                   capture_output=True, timeout=300)
    return sorted(pasta.glob(f"{pdf.stem}-*.png"))


def conferir(evolucoes, ficha, n_leitos):
    """Confere os dois Word. Devolve (erros, avisos, pngs)."""
    erros, avisos, pngs = [], [], []
    for caminho, tam, evo in ((evolucoes, TAM_EVOLUCAO, True), (ficha, TAM_FICHA, False)):
        e, a = conferir_docx(caminho, tam, evolucao=evo)
        erros += e; avisos += a
    if not ((shutil.which("soffice") or shutil.which("libreoffice")) and shutil.which("pdfinfo")):
        avisos.append("sem LibreOffice/pdfinfo: páginas não contadas e sem PDF para olhar")
        return erros, avisos, pngs
    pasta = Path(ficha).parent / "paginas"
    pdf_evo = para_pdf(evolucoes)
    pdf_ficha = Path(ficha).with_suffix(".pdf")
    if not pdf_ficha.exists():
        pdf_ficha = para_pdf(ficha)
    n = paginas(pdf_ficha)
    if n != n_leitos:
        erros.append(f"ficha-cola com {n} página(s) para {n_leitos} leito(s): tem de ser 1 folha por leito")
    if shutil.which("pdftoppm"):
        pngs = fotos(pdf_evo, pasta) + fotos(pdf_ficha, pasta)
    return erros, avisos, pngs


def relatorio(erros, avisos, pngs):
    linhas = ["", "Conferência: " + ("OK" if not erros else f"{len(erros)} erro(s)")]
    linhas += [f"- ERRO: {e}" for e in erros] + [f"- aviso: {a}" for a in avisos]
    if pngs:
        linhas.append(f"- páginas para olhar: {pngs[0].parent} ({len(pngs)} PNG)")
    return "\n".join(linhas)


def main():
    ap = argparse.ArgumentParser(description="Confere evolução e ficha-cola geradas.")
    ap.add_argument("evolucoes"); ap.add_argument("ficha")
    ap.add_argument("--leitos", type=int, required=True)
    a = ap.parse_args()
    erros, avisos, pngs = conferir(a.evolucoes, a.ficha, a.leitos)
    print(relatorio(erros, avisos, pngs))
    sys.exit(4 if erros else 0)


if __name__ == "__main__":
    main()
