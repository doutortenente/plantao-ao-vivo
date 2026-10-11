#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
processar.py — trabalhador da esteira do plantão (roda no GitHub Actions).

Entrada (variáveis de ambiente):
  RECORD_ID  ID da linha na tabela "Plantão × Leito" do Airtable.
  AIRTABLE_TOKEN  token do Airtable (segredo do repositório, passado só ele ao job).
  SEGREDOS        (legado, opcional) JSON com os segredos; usado só se AIRTABLE_TOKEN faltar.

Estágio atual (teste 2): baixa os anexos da linha e confere o tamanho de cada um.
Ainda NÃO lê o scan nem monta o bloco. O resultado vai para os campos Status e Avisos.
Só biblioteca padrão.
"""
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

BASE = "apppxhq0Qx7nqm14E"
TABELA = "tblgiiRmOyXmSLWu1"
CAMPO = {
    "status": "fldMKAeMcwDEIYrWP",
    "avisos": "fldyWHVHultgXHW9Z",
    "controles": "fldUP6tJBs4wom2Ua",
    "prescricao": "fld5klIen8VvLQ7wd",
    "exames": "fldsV1WHG8CUtENpR",
    "evolucoes_anteriores": "fldZjS4XF50inBZO6",
}
ANEXOS = ("controles", "prescricao", "exames")
PASTA = Path("entrada")


def segredo(nome):
    bruto = os.environ.get("SEGREDOS", "")
    valor = (json.loads(bruto) if bruto else {}).get(nome) or os.environ.get(nome)
    if not valor:
        sys.exit(f"falta o segredo {nome}")
    return valor


def airtable(metodo, record_id, token, corpo=None):
    url = f"https://api.airtable.com/v0/{BASE}/{TABELA}/{record_id}?returnFieldsByFieldId=true"
    dados = json.dumps(corpo).encode() if corpo is not None else None
    req = urllib.request.Request(url, data=dados, method=metodo, headers={
        "Authorization": "Bearer " + token, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def gravar(record_id, token, **campos):
    airtable("PATCH", record_id, token, {"fields": {CAMPO[k]: v for k, v in campos.items()}})


def nome_seguro(nome):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", nome)[:120] or "arquivo"


def baixar(url, destino):
    destino.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with urllib.request.urlopen(url, timeout=300) as r, open(destino, "wb") as f:
        while True:
            bloco = r.read(1 << 20)
            if not bloco:
                break
            f.write(bloco)
            total += len(bloco)
    return total


def main():
    record_id = os.environ.get("RECORD_ID", "")
    if not re.fullmatch(r"rec[A-Za-z0-9]{14}", record_id):
        sys.exit("RECORD_ID inválido")
    token = segredo("AIRTABLE_TOKEN")

    gravar(record_id, token, status="lendo")
    linhas, falhas = [], 0
    try:
        campos = airtable("GET", record_id, token).get("fields", {})
        for chave in ANEXOS:
            for i, anexo in enumerate(campos.get(CAMPO[chave], []), 1):
                esperado = anexo.get("size")
                destino = PASTA / chave / f"{i:02d}_{nome_seguro(anexo.get('filename', ''))}"
                try:
                    baixado = baixar(anexo["url"], destino)
                except Exception as e:  # falha de rede ou link vencido
                    falhas += 1
                    linhas.append(f"{chave} {i}: FALHOU ao baixar ({type(e).__name__})")
                    continue
                ok = esperado is None or baixado == esperado
                falhas += 0 if ok else 1
                linhas.append(
                    f"{chave} {i}: {anexo.get('filename')} | {baixado / 1e6:.2f} MB baixados"
                    + ("" if ok else f" | DIFERE do tamanho informado ({esperado} bytes)"))
        texto_ant = campos.get(CAMPO["evolucoes_anteriores"]) or ""
        linhas.append(f"evoluções anteriores: {len(texto_ant)} caracteres")
        if not any(l.split(" ")[0] in ANEXOS for l in linhas):
            linhas.insert(0, "nenhum anexo na linha")
    except Exception as e:
        falhas += 1
        linhas.append(f"erro: {type(e).__name__}: {e}")

    cabecalho = "TESTE 2 (só baixa os anexos; ainda não lê o scan nem monta o bloco)"
    gravar(record_id, token, status="falhou" if falhas else "pronto",
           avisos=cabecalho + "\n" + "\n".join(linhas))
    print("\n".join(linhas))
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
