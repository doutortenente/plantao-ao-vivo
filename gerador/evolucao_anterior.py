#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
evolucao_anterior.py — lê a evolução anterior (.docx ou .txt) e devolve, por leito, o que o plantão copia dela.

  exame_fisico          → cópia literal (o Dr. altera ao "canetar"; só sai o que ficou falso)
  plano_anterior        → o motor alerta droga que o plano mandou suspender e continua prescrita
  laboratorio_anterior  → o anterior da série "anterior -> atual" (labs.py)

Leitos: linha "LEITO 99 …" ou "02 - NOME" (formato da admissão). Seções pelos títulos do BRIEFING (e "Exame Físico
Geral" da admissão). Leito sem exame físico reconhecido vira aviso: aí o Claude lê na mão.

Uso: python3 gerador/evolucao_anterior.py anterior.docx   → JSON {"leitos": {...}, "avisos": [...]}
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

LEITO = re.compile(r"^\s*(?:LEITO\s+(\d{1,3})\b|(\d{2,3})\s+[-–—]\s+[A-ZÀ-Ú])")
SECOES = {
    "exame_fisico": re.compile(r"^exame fisico( geral)?$"),
    "plano_anterior": re.compile(r"^plano terapeutico( e condutas)?$"),
    "laboratorio_anterior": re.compile(r"^laboratorio$"),
}


def _norm(txt):
    s = unicodedata.normalize("NFD", txt.strip().lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def _titulo(linha):
    """Nome da seção se a linha for um título ('Exame físico:'), senão None. Outro título fecha a seção."""
    s = linha.strip()
    if not s.endswith(":") or len(s) > 60 or not s[0].isalpha():
        return None
    base = _norm(s[:-1])
    for chave, rx in SECOES.items():
        if rx.match(base):
            return chave
    return "outra"


def linhas_do_arquivo(caminho):
    caminho = Path(caminho)
    if caminho.suffix.lower() == ".docx":
        from docx import Document
        doc = Document(str(caminho))
        return [p.text for p in doc.paragraphs]
    return caminho.read_text(encoding="utf-8").splitlines()


def ler(linhas):
    """{leito: {exame_fisico, plano_anterior, laboratorio_anterior}}, avisos."""
    leitos, avisos = {}, []
    atual, secao = None, None
    for linha in linhas:
        m = LEITO.match(linha)
        if m:
            atual = (m.group(1) or m.group(2)).zfill(2)
            leitos[atual] = {k: [] for k in SECOES}
            secao = None
            continue
        if atual is None:
            continue
        t = _titulo(linha)
        if t:
            secao = t if t != "outra" else None
            continue
        if secao and linha.strip():
            leitos[atual][secao].append(linha.strip())
    for n, dados in leitos.items():
        if not dados["exame_fisico"]:
            avisos.append(f"L{n}: exame físico da evolução anterior não reconhecido — copiar na mão")
        if not dados["plano_anterior"]:
            avisos.append(f"L{n}: plano da evolução anterior não reconhecido — o alerta de suspensos não roda")
    if not leitos:
        avisos.append("nenhum leito reconhecido na evolução anterior (cabeçalho 'LEITO XX' ou 'XX - NOME')")
    return leitos, avisos


def main():
    leitos, avisos = ler(linhas_do_arquivo(sys.argv[1]))
    print(json.dumps({"leitos": leitos, "avisos": avisos}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
