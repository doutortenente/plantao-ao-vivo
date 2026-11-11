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
  - série `anterior => atual`: o anterior vem do último valor de cada analito em `laboratorio_anterior`
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
# milhar com ponto (150.000) | decimal com ponto (1.7, 7.31, -2.5: 1 ou 2 casas não é milhar) | inteiro ou vírgula
NUMERO = re.compile(r"(?<![\w,.])((?<!-)[<>]\s*)?(\d{1,3}(?:\.\d{3})+(?:,\d+)?|-?\d+\.\d{1,2}|-?\d+(?:,\d+)?)(?![\w])")
NOME_INICIO = re.compile(r"^\s*([A-Za-zÀ-ú][A-Za-zÀ-ú0-9 .\-()]{0,40}?)\s*(?:[:.]{1,}|\s{2,}|\s(?=[<>]?\s*-?\d))")
# resultado em texto: o primeiro número da linha seria o da faixa de referência
RESULTADO_EM_TEXTO = re.compile(r"(?i)\b(hemolis\w*|pendente\w*|n[ãa]o\s+reagente|reagente|coagulad\w*|"
                                r"insuficiente|cancelad\w*|n[ãa]o\s+realizad\w*|inconclusiv\w*|aguardando|"
                                r"em\s+andamento|lip[êe]mic\w*|ict[ée]ric\w*)\b")
# unidade do laudo em outra escala que a UNIDADE fixa do bloco (o valor sairia 10× ou 1000× errado)
OUTRA_ESCALA = {
    "HB": r"g\s*/\s*l\b|mmol", "UR": r"m?mol|[µu]mol|mg\s*/\s*l\b", "CR": r"m?mol|[µu]mol|mg\s*/\s*l\b",
    "PLAQ": r"x\s*10|10\s*\^|10\s*[³3]\s*/|mil\b", "LEUCO": r"x\s*10|10\s*\^|10\s*[³3]\s*/|mil\b",
}


def _br(numero):
    """Decimal com ponto (1.7) vira vírgula (1,7), o padrão do BRIEFING; milhar (150.000) fica."""
    return numero.replace(".", ",") if re.fullmatch(r"-?\d+\.\d{1,2}", numero) else numero


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
        em_texto = RESULTADO_EM_TEXTO.search(linha, m.end())
        if em_texto:
            avisos.append(f"lab: {sigla} com resultado em texto (\"{em_texto.group(0)}\"): sem valor, ler no PDF")
            continue
        num = NUMERO.search(linha, m.end())
        if not num:
            avisos.append(f"lab: {sigla} sem número legível na linha \"{linha.strip()[:60]}\"")
            continue
        valor = ((num.group(1) or "").replace(" ", "") + " " if num.group(1) else "") + _br(num.group(2))
        valor = valor.strip()
        resto = linha[num.end():].lstrip()
        if sigla in OUTRA_ESCALA and re.match(OUTRA_ESCALA[sigla], resto, re.I):
            avisos.append(f"lab: {sigla} {valor} com unidade \"{resto.split('  ')[0].strip()}\" no laudo (o bloco "
                          f"escreve {UNIDADE[sigla]}): sem valor, ler no PDF")
            continue
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
                ant[sigla] = ((ult[0] or "").replace(" ", "") + " " if ult[0] else "") + _br(ult[1])
    return ant


def montar(valores, ant=None):
    """Linhas no formato do BRIEFING §1, com série anterior => atual onde houver anterior. UR e CR seriais na mesma
    linha dos eletrólitos, e eletrólitos só com o valor atual (pedido de 02/11/2026)."""
    ant = ant or {}

    def s(k):
        if k not in valores:
            return None
        v = valores[k] if k not in ant or ant[k] == "" else f"{ant[k]} => {valores[k]}"
        return f"{k}: {v}" + (f" {UNIDADE[k]}" if k in UNIDADE else "")
    linhas = []
    grupo = [x for x in (s("HB"), s("HT"), s("PLAQ")) if x]
    if grupo:
        linhas.append(" | ".join(grupo))
    if "LEUCO" in valores:
        dif = f" (seg {valores['SEG']} % / bast {valores['BAST']} %)" if "SEG" in valores and "BAST" in valores else ""
        linhas.append(s("LEUCO") + dif)
    atual = lambda k: f"{k}: {valores[k]}" if k in valores else None  # eletrólito: sem série
    grupo = [x for x in [s("UR"), s("CR")] + [atual(k) for k in ("NA", "K", "MG", "CAI", "P")] if x]
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
