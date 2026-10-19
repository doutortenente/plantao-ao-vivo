#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validar.py — confere o JSON do plantão ANTES de gerar (o checklist do docs/BRIEFING.md §5 em código).

Erros (o gerar_docx.py não gera):
  - campo que o gerador exige e falta (antes dava KeyError no meio da ficha-cola);
  - item de balanço fora do dicionário do motor (CANON): sairia fora da conta e o BH ficaria errado;
  - "(revisar)" em qualquer texto (proibido no bloco colável).
Avisos (vão para o "Conferir"):
  - "?" em texto livre; PROFILAXIA com item que não é TEV/LAMG; item que não vai na ficha (colírio, pele…);
  - setas na Impressão; plano sem linha de Profilaxias; menos itens de plano que problemas na Impressão;
  - pendências fora de 3 a 7; mais de 3 alertas.

Uso: python3 gerador/validar.py plantao.json   (o gerar_docx.py chama validar() sozinho)
"""
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "skills" / "sasi-ingest-export" / "scripts"))
import build_passagem as motor  # noqa: E402

META_OBRIGATORIO = ("unidade", "data", "turno", "data_prescricao")
LEITO_OBRIGATORIO = ("leito", "nome", "idade_sexo", "dia_uti")
FICHA_OBRIGATORIO = ("janela_controles", "janela_balanco", "alergia", "dx", "disp", "infusoes", "sistemas",
                     "vigiar", "lab")

# O que não vai para a ficha-cola (decisão de 11/10/2026): pele, colírios, lágrima, simeticona…
CLASSES_FORA_DA_FICHA = {"SINTOMÁTICOS", "OFTALMO", "PELE", "TÓPICOS"}
ITENS_FORA_DA_FICHA = re.compile(
    r"\b(col[íi]rio|lacrima|lumigan|brixag|ephynal|hirudoid|brava|comfeel|com feel|primoderm|primo derme|"
    r"rio ?hex|riohex|luftal|simeticona|dersani|fresubin creme|fresubin protein|resource fiber|complexo b|"
    r"shilley heparinizado|água( mineral)? \d+ ?ml)\b", re.I)

# PROFILAXIA na ficha = só TEV e LAMG (docs/formato-entrega.md).
PROFILAXIA_TEV_LAMG = re.compile(
    r"enoxaparina|clexane|heparina|\bhnf\b|fondaparinux|arixtra|dalteparina|fragmin|compress[ãa]o pneum|"
    r"\bcpi\b|meia|pantopra|pantozol|omepra|esomepra|nexium|lansopra|ranitidina|famotidina|sucralfato|\bibp\b|"
    r"\btev\b|\blamg\b", re.I)
SETAS = re.compile(r"[↑↓→]|(?<![<>=!])=(?![=>])")


def _textos(valor):
    """Todas as strings dentro de um valor JSON."""
    if isinstance(valor, str):
        yield valor
    elif isinstance(valor, dict):
        for v in valor.values():
            yield from _textos(v)
    elif isinstance(valor, list):
        for v in valor:
            yield from _textos(v)


def validar_leito(leito, meta):
    erros, avisos = [], []
    L = f"L{leito.get('leito', '?')}"
    for k in LEITO_OBRIGATORIO:
        if not leito.get(k):
            erros.append(f"{L}: falta `{k}`")
    ficha = leito.get("ficha")
    if not isinstance(ficha, dict):
        erros.append(f"{L}: falta o bloco `ficha`")
        ficha = {}
    for k in FICHA_OBRIGATORIO:
        if k not in ficha:
            erros.append(f"{L}: falta `ficha.{k}`")

    for lado in ("ganhos", "perdas"):
        for item in leito.get(lado, []):
            if motor.classify(item.get("nome", "")) is None:
                erros.append(f"{L}: item de balanço \"{item.get('nome')}\" fora do dicionário do motor (CANON): "
                             "ficaria fora da conta e o BH sairia errado. Use um nome conhecido "
                             "(ex.: \"soro EV\", \"diurese SVD\") ou acrescente o termo ao CANON.")

    for campo, valor in leito.items():
        for txt in _textos(valor):
            if "(revisar)" in txt.lower():
                erros.append(f"{L}: \"(revisar)\" em `{campo}`: dúvida vai para o Conferir, nunca para o bloco")
    for campo in ("laboratorio", "terapias", "exame_fisico", "evolucao", "impressao", "conduta", "ficha"):
        for txt in _textos(leito.get(campo, [])):
            if re.search(r"(?<![\w])\?(?![\w])", txt):
                avisos.append(f"{L}: \"?\" em `{campo}`: {txt[:70]}")

    for rot, itens in ficha.get("infusoes", []) + ficha.get("sistemas", []):
        if rot.strip().upper() in CLASSES_FORA_DA_FICHA:
            avisos.append(f"{L}: classe {rot} não vai na ficha-cola")
        for it in itens:
            if ITENS_FORA_DA_FICHA.search(it):
                avisos.append(f"{L}: \"{it[:50]}\" não vai na ficha-cola (pele, colírio, simeticona e afins)")
            if rot.strip().upper() == "PROFILAXIA" and not PROFILAXIA_TEV_LAMG.search(it):
                avisos.append(f"{L}: PROFILAXIA só tem TEV e LAMG; \"{it[:50]}\" vai em outro sistema")

    for linha in leito.get("impressao", []):
        if SETAS.search(linha):
            avisos.append(f"{L}: seta ou \"=\" na Impressão (escrever a tendência em palavras): {linha[:70]}")
    conduta = leito.get("conduta", [])
    if conduta and not any("profilax" in c.lower() for c in conduta):
        avisos.append(f"{L}: plano sem a linha de Profilaxias (TEV, LAMG, cabeceira)")
    n_imp = len([x for x in leito.get("impressao", []) if x.strip()])
    n_plano = len([c for c in conduta if re.match(r"^\d+\.", c.strip())])
    if conduta and n_plano < n_imp:
        avisos.append(f"{L}: {n_imp} problema(s) na Impressão e só {n_plano} item(ns) no plano")
    n_vig = len(ficha.get("vigiar", []))
    if ficha and not 3 <= n_vig <= 7:
        avisos.append(f"{L}: {n_vig} pendência(s) na ficha (o combinado é de 3 a 7)")
    if len(leito.get("alertas", [])) > 3:
        avisos.append(f"{L}: {len(leito['alertas'])} alertas (até 3, frases curtas)")
    return erros, avisos


def validar(plantao):
    """Devolve (erros, avisos) do plantão inteiro."""
    erros, avisos = [], []
    meta = plantao.get("meta", {})
    for k in META_OBRIGATORIO:
        if not meta.get(k):
            erros.append(f"meta: falta `{k}`")
    leitos = plantao.get("leitos", [])
    if not leitos:
        erros.append("nenhum leito no JSON")
    vistos = set()
    for leito in leitos:
        n = leito.get("leito")
        if n in vistos:
            erros.append(f"L{n}: leito repetido no JSON")
        vistos.add(n)
        e, a = validar_leito(leito, meta)
        erros += e; avisos += a
    return erros, avisos


def main():
    plantao = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    erros, avisos = validar(plantao)
    for e in erros:
        print("ERRO: " + e)
    for a in avisos:
        print("aviso: " + a)
    print("Validação: " + ("OK" if not erros else f"{len(erros)} erro(s)"))
    sys.exit(2 if erros else 0)


if __name__ == "__main__":
    main()
