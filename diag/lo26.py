#!/usr/bin/env python3
"""Diagnóstico temporário (ramo diag/lo26-ficha, não vai para a main): mede a ficha-cola no LibreOffice desta
máquina, para comparar o 24.2 daqui com o 26.2 do runner do GitHub.

Uso: python diag/lo26.py <pasta-saida>
"""
import copy
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "gerador"))
sys.path.insert(0, str(RAIZ / "tests"))
import estilo as E  # noqa: E402
import ficha_cola  # noqa: E402
import office  # noqa: E402
import test_ficha_exame as T  # noqa: E402

SAIDA = Path(sys.argv[1])
SAIDA.mkdir(parents=True, exist_ok=True)
CABECALHOS = ("CONTROLES", "BALANÇO", "LABORATÓRIO", "PRESCRIÇÃO", "PENDÊNCIAS", "EXAME", "NEURO", "RENAL",
              "INTERCORRÊNCIAS")
WORD = re.compile(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>')


def medir(nome, plantao, cfg, folga):
    docx = SAIDA / f"{nome}.docx"
    ficha_cola.gerar(plantao, docx, cfg, folga=folga)
    pdf = office.para_pdf(docx, SAIDA)
    subprocess.run(["pdftoppm", "-r", "50", "-png", str(pdf), str(SAIDA / nome)], check=True)
    html = subprocess.run(["pdftotext", "-bbox-layout", str(pdf), "-"], capture_output=True, text=True).stdout
    paginas = html.split("<page ")[1:]
    achados, fim = {}, 0.0
    for i, pag in enumerate(paginas, 1):
        for m in WORD.finditer(pag):
            y0, y1, w = float(m.group(2)), float(m.group(4)), m.group(5)
            for c in CABECALHOS:
                if w.startswith(c) and c not in achados:
                    achados[c] = f"p{i} y={y0:.1f}"
            if i == len(paginas):
                fim = max(fim, y1)
    print(f"{nome}: {len(paginas)} página(s); fim do texto na última = {fim:.1f} pt")
    print("   " + " | ".join(f"{c} {achados.get(c, '-')}" for c in CABECALHOS))


exemplo, _ = ficha_cola.motor.preparar(copy.deepcopy(T.EXEMPLO))
pesado, _ = ficha_cola.motor.preparar(T.leito_pesado())
for nome, pl, cfg in (("exemplo", exemplo, {}), ("pesado", pesado, {"99": (0, ficha_cola.N_INTER_COMPACTO, 9, True)})):
    for folga in (0, E.FOLGA_MEDICAO):
        medir(f"{nome}-folga{folga:g}", copy.deepcopy(pl), cfg, folga)
