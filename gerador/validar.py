#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validar.py — confere o JSON do plantão ANTES de gerar (o checklist do docs/BRIEFING.md §5 em código).

Erros (o gerar_docx.py não gera):
  - campo que o gerador exige e falta (antes dava KeyError no meio da ficha-cola); `meta.data` fora de dd/mm/aaaa
    (sem ela o motor não conta os dias); campo com tipo errado (lista onde é texto, linha da ficha fora de
    [rótulo, [itens]]) — antes estourava no meio da ficha, com a evolução já gravada;
  - alergia diferente entre o leito e o bloco `ficha` (a ficha imprimiria a errada);
  - item de balanço fora do dicionário do motor (CANON): sairia fora da conta e o BH ficaria errado;
  - "(revisar)" em qualquer texto que vai para o bloco ou para a ficha (`avisos` e `alertas` podem).
Avisos (vão para o "Conferir"):
  - "?" em texto livre, colado a número ("1?00 mg") ou no D do ATB ("D?"), e no cabeçalho (alergia, Dx, disp.);
  - PROFILAXIA com item que não é TEV/LAMG; item que não vai na ficha (colírio, pele…);
  - Dx ou dispositivos diferentes entre leito e ficha; número do lab da ficha que não está em `laboratorio`;
    ATB da ficha que não está nas terapias (e vice-versa);
  - setas na Impressão; plano sem linha de Profilaxias; menos itens de plano que problemas na Impressão;
  - pendências fora de 3 a 7; mais de 3 alertas.

Uso: python3 gerador/validar.py plantao.json   (o gerar_docx.py chama validar() sozinho, depois do motor.preparar)
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
FICHA_OBRIGATORIO = ("infusoes", "sistemas", "vigiar", "lab")
# cabeçalho da ficha: no leito (fonte única) ou sobrescrito no bloco `ficha` (texto mais curto)
CABECALHO = {"alergia": "alergia", "dx": "diagnostico", "disp": "dispositivos"}

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
DUVIDA = re.compile(r"(?<![\w])\?(?![\w])|\d\?|\?\d|\bD\?")  # "?" sozinho, colado a número, ou "D?"
DATA = re.compile(r"^\s*\d{2}/\d{2}/\d{4}\s*$")
TEXTO = ("leito", "nome", "idade_sexo", "dia_uti", "alergia", "diagnostico", "dispositivos", "dieta", "sup_o2",
         "evacuacao", "admissao_uti", "iniciais", "janela")
LISTA = ("laboratorio", "terapias", "exame_fisico", "evolucao", "impressao", "conduta", "alertas", "avisos",
         "outros_balanco", "plano_anterior")
FORA_DO_BLOCO = ("avisos", "alertas")  # rodapé e chat: aqui "(revisar)" não faz mal


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


def _tipos(leito, ficha, L):
    """Erros de tipo: o gerador espera texto em uns campos, lista de textos em outros."""
    erros = []
    for k in TEXTO:
        if k in leito and leito[k] is not None and not isinstance(leito[k], str):
            erros.append(f"{L}: `{k}` tem de ser texto, veio {type(leito[k]).__name__}")
    for k in LISTA:
        v = leito.get(k)
        if v is not None and not (isinstance(v, list) and all(isinstance(x, str) for x in v)):
            erros.append(f"{L}: `{k}` tem de ser lista de textos")
    for k in ("infusoes", "sistemas"):
        v = ficha.get(k)
        if v is None:
            continue
        ok = isinstance(v, list) and all(
            isinstance(x, list) and len(x) == 2 and isinstance(x[0], str) and x[0].strip()
            and isinstance(x[1], list) and all(isinstance(i, str) for i in x[1]) for x in v)
        if not ok:
            erros.append(f"{L}: `ficha.{k}` tem de ser [[\"RÓTULO\", [\"item\", …]], …] (item único também vai "
                         "numa lista)")
    for k in ("vigiar", "exames", "lab"):
        v = ficha.get(k)
        if v is not None and not (isinstance(v, list) and all(isinstance(x, str) for x in v)):
            erros.append(f"{L}: `ficha.{k}` tem de ser lista de textos")
    for k in ("alergia", "dx", "disp", "janela_controles", "janela_balanco", "lab_titulo"):
        if ficha.get(k) is not None and not isinstance(ficha[k], str):
            erros.append(f"{L}: `ficha.{k}` tem de ser texto")
    return erros


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
    tipo = _tipos(leito, ficha, L)
    if tipo:
        return erros + tipo, avisos  # o resto das checagens supõe os tipos certos
    e, a = _coerencia(leito, ficha, L)
    erros += e; avisos += a

    for lado in ("ganhos", "perdas"):
        for item in leito.get(lado, []):
            if motor.classify(item.get("nome", "")) is None:
                erros.append(f"{L}: item de balanço \"{item.get('nome')}\" fora do dicionário do motor (CANON): "
                             "ficaria fora da conta e o BH sairia errado. Use um nome conhecido "
                             "(ex.: \"soro EV\", \"diurese SVD\") ou acrescente o termo ao CANON.")

    for campo, valor in leito.items():
        if campo in FORA_DO_BLOCO:
            continue
        for txt in _textos(valor):
            if "(revisar)" in txt.lower():
                erros.append(f"{L}: \"(revisar)\" em `{campo}`: dúvida vai para o Conferir, nunca para o bloco")
    for campo in ("alergia", "diagnostico", "dispositivos", "dia_uti", "laboratorio", "terapias", "exame_fisico",
                  "evolucao", "impressao", "conduta", "ficha"):
        for txt in _textos(leito.get(campo, [])):
            if DUVIDA.search(txt):
                avisos.append(f"{L}: \"?\" em `{campo}`: {txt[:70]}")

    for rot, itens in (ficha.get("infusoes") or []) + (ficha.get("sistemas") or []):
        if rot.strip().upper() in CLASSES_FORA_DA_FICHA:
            avisos.append(f"{L}: classe {rot} não vai na ficha-cola")
        for it in itens:
            if ITENS_FORA_DA_FICHA.search(it):
                avisos.append(f"{L}: \"{it[:50]}\" não vai na ficha-cola (pele, colírio, simeticona e afins)")
            if rot.strip().upper() == "PROFILAXIA" and not PROFILAXIA_TEV_LAMG.search(it):
                avisos.append(f"{L}: PROFILAXIA só tem TEV e LAMG; \"{it[:50]}\" vai em outro sistema")

    for linha in leito.get("impressao") or []:
        if SETAS.search(linha):
            avisos.append(f"{L}: seta ou \"=\" na Impressão (escrever a tendência em palavras): {linha[:70]}")
    conduta = leito.get("conduta") or []
    if conduta and not any("profilax" in c.lower() for c in conduta):
        avisos.append(f"{L}: plano sem a linha de Profilaxias (TEV, LAMG, cabeceira)")
    n_imp = len([x for x in (leito.get("impressao") or []) if x.strip()])
    n_plano = len([c for c in conduta if re.match(r"^\d+\.", c.strip())])
    if conduta and n_plano < n_imp:
        avisos.append(f"{L}: {n_imp} problema(s) na Impressão e só {n_plano} item(ns) no plano")
    n_vig = len(ficha.get("vigiar") or [])
    if ficha and not 3 <= n_vig <= 7:
        avisos.append(f"{L}: {n_vig} pendência(s) na ficha (o combinado é de 3 a 7)")
    if len(leito.get("alertas") or []) > 3:
        avisos.append(f"{L}: {len(leito['alertas'])} alertas (até 3, frases curtas)")
    return erros, avisos


def _norm(txt):
    return re.sub(r"[\s·,;|]+", " ", str(txt).replace("**", "")).strip().lower()


NUMERO = re.compile(r"\d+(?:[.,]\d+)*")
NOME_DROGA = re.compile(r"^\s*\**([A-Za-zÀ-ú][A-Za-zÀ-ú-]+)")


def _atbs(texto):
    """Nomes de droga (comercial e genérico entre parênteses) de um texto de ATB."""
    nomes = set()
    for generico in re.findall(r"\(([A-Za-zÀ-ú][A-Za-zÀ-ú +-]+)\)", texto):
        nomes.update(g.strip().lower() for g in generico.split("+") if g.strip())
    sem_parenteses = re.sub(r"\([^)]*\)", " ", texto)
    for parte in re.split(r"[;·]|\s\+\s", sem_parenteses):
        m = NOME_DROGA.match(parte.replace("ATB:", ""))
        if m:
            nomes.add(m.group(1).lower())
    return nomes


def _coerencia(leito, ficha, L):
    """Cópias do mesmo dado no leito e no bloco `ficha` têm de bater."""
    erros, avisos = [], []
    for chave, campo in CABECALHO.items():
        no_leito, na_ficha = leito.get(campo), ficha.get(chave)
        if not no_leito and not na_ficha:
            erros.append(f"{L}: falta `{campo}` (ou `ficha.{chave}`)" +
                         (": se não houver alergia, escreva \"nega\"; se não souber, \"?\"" if chave == "alergia" else ""))
        elif no_leito and na_ficha and _norm(no_leito) != _norm(na_ficha):
            msg = f"{campo} diverge: leito \"{no_leito}\" × ficha \"{na_ficha}\" (a ficha imprime o da ficha)"
            (erros if chave == "alergia" else avisos).append(f"{L}: {msg}")
    lab_txt = " ".join(leito.get("laboratorio") or [])
    numeros_lab = set(NUMERO.findall(lab_txt))
    faltam = [n for linha in (ficha.get("lab") or []) for n in NUMERO.findall(linha.replace("**", ""))
              if n not in numeros_lab]
    if lab_txt and faltam:
        avisos.append(f"{L}: lab da ficha com número que não está em `laboratorio`: {', '.join(dict.fromkeys(faltam))}")
    atb_ficha = set().union(*[_atbs(it) for rot, its in (ficha.get("infusoes") or []) + (ficha.get("sistemas") or [])
                              if rot.strip().upper() == "ATB" for it in its]) if ficha else set()
    atb_terapia = set().union(*[_atbs(t) for t in (leito.get("terapias") or []) if t.strip().upper().startswith("ATB")])
    if atb_ficha and atb_terapia and not atb_ficha & atb_terapia:
        avisos.append(f"{L}: ATB da ficha ({', '.join(sorted(atb_ficha))}) não bate com as terapias "
                      f"({', '.join(sorted(atb_terapia))})")
    elif atb_ficha and atb_terapia:
        so_terapia = {n for n in atb_terapia if n not in atb_ficha}
        so_ficha = {n for n in atb_ficha if n not in atb_terapia}
        # nomes que aparecem só de um lado e não são o genérico do outro
        if so_terapia and so_ficha:
            avisos.append(f"{L}: ATB diferente entre ficha ({', '.join(sorted(so_ficha))}) e terapias "
                          f"({', '.join(sorted(so_terapia))})")
    return erros, avisos


def validar(plantao):
    """Devolve (erros, avisos) do plantão inteiro."""
    erros, avisos = [], []
    meta = plantao.get("meta", {})
    for k in META_OBRIGATORIO:
        if not meta.get(k):
            erros.append(f"meta: falta `{k}`")
    if meta.get("data") and not (isinstance(meta["data"], str) and DATA.match(meta["data"])):
        erros.append(f"meta: `data` tem de ser dd/mm/aaaa (veio \"{meta['data']}\"): sem o ano o motor não conta "
                     "os dias de ATB e de UTI")
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
    plantao, avisos_dias = motor.preparar(plantao)  # como no gerar_docx: dia_uti pode vir de admissao_uti
    erros, avisos = validar(plantao)
    avisos = avisos_dias + avisos
    for e in erros:
        print("ERRO: " + e)
    for a in avisos:
        print("aviso: " + a)
    print("Validação: " + ("OK" if not erros else f"{len(erros)} erro(s)"))
    sys.exit(2 if erros else 0)


if __name__ == "__main__":
    main()
