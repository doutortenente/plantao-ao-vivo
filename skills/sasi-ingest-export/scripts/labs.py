#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
labs.py — lê o laudo de laboratório em PDF por programa (BETA) e monta a seção Laboratório do BRIEFING.

Estado: beta até ser calibrado com o primeiro laudo real (o layout do laboratório ainda não foi visto).
O Claude confere o resultado contra o PDF: o que divergir vale o PDF e vai para o Conferir.

Como lê:
  - `pdftotext -layout`; cada linha que começa com um analito conhecido (LAB_ALIAS) dá um valor: o PRIMEIRO
    número depois do nome (o resto da linha costuma ser a faixa de referência);
  - bloco de "AMOSTRA MAQUINA" (circuito de diálise) é ignorado até a próxima amostra;
  - série `anterior -> atual`: o anterior vem do último valor de cada analito em `laboratorio_anterior`
    (as linhas de Laboratório da evolução anterior, no formato do BRIEFING);
  - analito repetido no laudo com valores diferentes, ou linha de analito sem número: aviso.

Uso:
  python3 skills/sasi-ingest-export/scripts/labs.py laudo.pdf [--anterior "HB: 11,2 g/dl | HT: 33 %" ...]
"""
import argparse
import re
import subprocess
import sys
import unicodedata

# nome no laudo (sem acento, maiúsculo, só letras e números) → sigla do BRIEFING
LAB_ALIAS = {
    "HB": "HB", "HGB": "HB", "HEMOGLOBINA": "HB", "HT": "HT", "HCT": "HT", "HEMATOCRITO": "HT",
    "PLAQ": "PLAQ", "PLAQUETAS": "PLAQ", "PLT": "PLAQ", "CONTAGEMDEPLAQUETAS": "PLAQ",
    "LEUCO": "LEUCO", "LEUCOCITOS": "LEUCO", "LEUC": "LEUCO", "LEUCOGRAMA": "LEUCO", "GLOBULOSBRANCOS": "LEUCO",
    "SEGMENTADOS": "SEG", "SEG": "SEG", "NEUTROFILOSSEGMENTADOS": "SEG", "BASTONETES": "BAST", "BAST": "BAST",
    "UR": "UR", "UREIA": "UR", "CR": "CR", "CREATININA": "CR", "CREAT": "CR",
    "NA": "NA", "SODIO": "NA", "K": "K", "POTASSIO": "K", "MG": "MG", "MAGNESIO": "MG",
    "CAI": "CAI", "CALCIOIONICO": "CAI", "CAIONICO": "CAI", "CALCIOIONIZADO": "CAI", "P": "P", "FOSFORO": "P",
    "PH": "pH", "PCO2": "pCO2", "PO2": "pO2", "HCO3": "HCO3", "BICARBONATO": "HCO3", "BE": "BE", "SBE": "BE",
    "EXCESSODEBASE": "BE", "SATO2": "SatO2", "LACTATO": "Lactato", "LAC": "Lactato", "ACIDOLATICO": "Lactato",
    "PCR": "PCR", "PROTEINACREATIVA": "PCR", "PROTEINACREATIVAPCR": "PCR", "TROPONINA": "Troponina",
    "TROPONINAI": "Troponina", "DDIMERO": "D-dímero", "INR": "INR", "RNI": "INR",
}
UNIDADE = {"HB": "g/dl", "HT": "%", "PLAQ": "/mm3", "LEUCO": "/mm3", "UR": "mg/dl", "CR": "mg/dl"}
NUMERO = re.compile(r"(?<![\w,.])([<>]\s*)?(\d{1,3}(?:\.\d{3})+(?:,\d+)?|-?\d+(?:,\d+)?)(?![\w])")
NOME_INICIO = re.compile(r"^\s*([A-Za-zÀ-ú][A-Za-zÀ-ú0-9 .\-()]{0,40}?)\s*(?:[:.]{1,}|\s{2,}|\s(?=[<>]?\s*-?\d))")


def _chave(nome):
    s = unicodedata.normalize("NFD", nome.upper())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return LAB_ALIAS.get(re.sub(r"[^A-Z0-9]", "", s))


def texto_do_pdf(caminho):
    return subprocess.run(["pdftotext", "-layout", str(caminho), "-"], capture_output=True, text=True,
                          check=True).stdout


def extrair(texto):
    """{sigla: valor (texto do laudo)} + avisos. Primeiro número depois do nome do analito."""
    valores, avisos, ignorar = {}, [], False
    for linha in texto.splitlines():
        sem = unicodedata.normalize("NFD", linha.upper())
        sem = "".join(c for c in sem if unicodedata.category(c) != "Mn")
        if "AMOSTRA" in sem:
            ignorar = "MAQUINA" in sem
            continue
        if ignorar:
            continue
        m = NOME_INICIO.match(linha)
        if not m:
            continue
        sigla = _chave(m.group(1))
        if not sigla:
            continue
        num = NUMERO.search(linha, m.end())
        if not num:
            avisos.append(f"lab: {sigla} sem número legível na linha \"{linha.strip()[:60]}\"")
            continue
        valor = ((num.group(1) or "").replace(" ", "") + " " if num.group(1) else "") + num.group(2)
        valor = valor.strip()
        if sigla in valores and valores[sigla] != valor:
            avisos.append(f"lab: {sigla} aparece com {valores[sigla]} e {valor} no laudo — ficou o primeiro")
            continue
        valores[sigla] = valor
    return valores, avisos


def anteriores(linhas):
    """Último valor de cada analito nas linhas de Laboratório da evolução anterior."""
    ant = {}
    for linha in linhas or []:
        for parte in re.split(r"\s\|\s|\s/\s", re.sub(r"^\s*Gaso\s*\w?:\s*", "", linha)):
            m = re.match(r"^\s*([A-Za-zÀ-ú0-9\-]+)\s*:?\s*(.+)$", parte.strip())
            if not m:
                continue
            sigla = _chave(m.group(1)) or (m.group(1) if m.group(1) in UNIDADE.values() else None)
            nums = NUMERO.findall(m.group(2).split("(")[0])
            if sigla and nums:
                ult = nums[-1]
                ant[sigla] = ((ult[0] or "").replace(" ", "") + " " if ult[0] else "") + ult[1]
    return ant


def montar(valores, ant=None):
    """Linhas no formato do BRIEFING §1, com série anterior -> atual onde houver anterior."""
    ant = ant or {}

    def s(k):
        if k not in valores:
            return None
        v = valores[k] if k not in ant or ant[k] == "" else f"{ant[k]} -> {valores[k]}"
        return f"{k}: {v}" + (f" {UNIDADE[k]}" if k in UNIDADE else "")
    linhas = []
    grupo = [x for x in (s("HB"), s("HT"), s("PLAQ")) if x]
    if grupo:
        linhas.append(" | ".join(grupo))
    if "LEUCO" in valores:
        dif = f" (seg {valores['SEG']} % / bast {valores['BAST']} %)" if "SEG" in valores and "BAST" in valores else ""
        linhas.append(s("LEUCO") + dif)
    for k in ("UR", "CR"):
        if s(k):
            linhas.append(s(k))
    grupo = [x for x in (s(k) for k in ("NA", "K", "MG", "CAI", "P")) if x]
    if grupo:
        linhas.append(" | ".join(grupo))
    gaso = [f"{k} {valores[k]}" for k in ("pH", "pCO2", "pO2", "HCO3", "BE", "SatO2", "Lactato") if k in valores]
    if gaso:
        linhas.append("Gaso: " + " / ".join(gaso))
    outros = [f"{k} {valores[k]}" for k in ("PCR", "Troponina", "D-dímero", "INR") if k in valores]
    if outros:
        linhas.append("Outros: " + " / ".join(outros))
    return linhas


def ler_laudo(texto, laboratorio_anterior=None):
    """(linhas de Laboratório, avisos) a partir do texto do laudo."""
    valores, avisos = extrair(texto)
    if not valores:
        avisos.append("lab: nenhum analito reconhecido — layout novo, ler o PDF na mão e calibrar labs.py")
    return montar(valores, anteriores(laboratorio_anterior)), avisos


def main():
    ap = argparse.ArgumentParser(description="Lê laudo de laboratório (PDF ou .txt) — BETA")
    ap.add_argument("laudo")
    ap.add_argument("--anterior", nargs="*", default=[], help="linhas de Laboratório da evolução anterior")
    a = ap.parse_args()
    texto = texto_do_pdf(a.laudo) if a.laudo.lower().endswith(".pdf") else open(a.laudo, encoding="utf-8").read()
    linhas, avisos = ler_laudo(texto, a.anterior)
    print("\n".join(linhas))
    for av in avisos:
        print("aviso: " + av, file=sys.stderr)


if __name__ == "__main__":
    main()
