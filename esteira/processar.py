#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
processar.py — trabalhador da esteira do plantão (roda no GitHub Actions, workflow plantao.yml).

Entrada (variáveis de ambiente):
  RECORD_ID             ID da linha na tabela "Plantão × Leito" do Airtable (uma linha = um leito).
  AIRTABLE_TOKEN        token do Airtable (segredo do repositório).
  ANTHROPIC_API_KEY     (opcional) liga a leitura automática. Sem ela, a esteira só baixa e confere os anexos.
  AIRTABLE_CAMPO_SAIDA  (opcional) ID do campo de anexos onde voltam a ficha (.docx + .pdf) e o JSON rascunho.
  DATA_PLANTAO, TURNO   (opcionais) data dd/mm/aaaa e turno; sem elas, a data sai da prescrição e o turno é diurno.
  SEGREDOS              (legado, opcional) JSON com os segredos; usado só se AIRTABLE_TOKEN faltar.

Com a chave (etapa 3):
  1. baixa os anexos (controles, prescrição, exames) e as evoluções anteriores (texto);
  2. recorta cada página em JPEG (preparar.recortes_para_leitura) e lê com a API do Claude (leitura.py);
     laudo de laboratório com texto vai pelo labs.py, sem API;
  3. monta o JSON do plantão do leito (montar.py) e roda motor.preparar → validar → ficha-cola (ajuste em 1 folha)
     → PDF → conferência (fonte, tamanho, cor, 1 folha);
  4. devolve na linha: ficha .docx + .pdf e o JSON rascunho (campo de saída) e o "Conferir" (campo Avisos).
A evolução (Impressão, Plano) continua no chat, a partir do JSON rascunho.

O log do Actions é público: aqui só saem contagens e o status, nunca nome, nome de arquivo ou dado clínico.
"""
import base64
import datetime as dt
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "esteira"))
sys.path.insert(0, str(RAIZ / "gerador"))
sys.path.insert(0, str(RAIZ / "skills" / "sasi-ingest-export" / "scripts"))

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
SAIDA = Path("saida-esteira")
ANEXO_MAX = 5_000_000  # limite do uploadAttachment do Airtable
TIPOS = {".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
         ".pdf": "application/pdf", ".json": "application/json"}


def segredo(nome):
    bruto = os.environ.get("SEGREDOS", "")
    valor = os.environ.get(nome) or (json.loads(bruto) if bruto else {}).get(nome)
    if not valor:
        sys.exit(f"falta o segredo {nome}")
    return valor


def _pedido(url, token, metodo, corpo=None, timeout=60):
    dados = json.dumps(corpo).encode() if corpo is not None else None
    req = urllib.request.Request(url, data=dados, method=metodo, headers={
        "Authorization": "Bearer " + token, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def airtable(metodo, record_id, token, corpo=None):
    url = f"https://api.airtable.com/v0/{BASE}/{TABELA}/{record_id}?returnFieldsByFieldId=true"
    return _pedido(url, token, metodo, corpo)


def gravar(record_id, token, **campos):
    airtable("PATCH", record_id, token, {"fields": {CAMPO[k]: v for k, v in campos.items()}})


def enviar_anexo(record_id, token, campo, arquivo):
    """Sobe um arquivo para o campo de anexos (endpoint uploadAttachment do Airtable, até 5 MB)."""
    arquivo = Path(arquivo)
    if arquivo.stat().st_size > ANEXO_MAX:
        raise ValueError(f"{arquivo.suffix}: passa de 5 MB")
    url = f"https://content.airtable.com/v0/{BASE}/{record_id}/{campo}/uploadAttachment"
    return _pedido(url, token, "POST", {"contentType": TIPOS[arquivo.suffix.lower()], "filename": arquivo.name,
                                        "file": base64.b64encode(arquivo.read_bytes()).decode("ascii")}, 120)


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


def baixar_anexos(campos, pasta):
    """Baixa os anexos da linha. Devolve ({chave: [arquivos]}, linhas do relatório, nº de falhas)."""
    arquivos, linhas, falhas = {k: [] for k in ANEXOS}, [], 0
    for chave in ANEXOS:
        for i, anexo in enumerate(campos.get(CAMPO[chave], []), 1):
            esperado = anexo.get("size")
            destino = pasta / chave / f"{i:02d}_{nome_seguro(anexo.get('filename', ''))}"
            try:
                baixado = baixar(anexo["url"], destino)
            except Exception as e:  # falha de rede ou link vencido
                falhas += 1
                linhas.append(f"{chave} {i}: FALHOU ao baixar ({type(e).__name__})")
                continue
            ok = esperado is None or baixado == esperado
            falhas += 0 if ok else 1
            linhas.append(f"{chave} {i}: {anexo.get('filename')} | {baixado / 1e6:.2f} MB baixados"
                          + ("" if ok else f" | DIFERE do tamanho informado ({esperado} bytes)"))
            if ok:
                arquivos[chave].append(destino)
    if not any(arquivos.values()) and not falhas:
        linhas.insert(0, "nenhum anexo na linha")
    return arquivos, linhas, falhas


def _texto_do_pdf(pdf):
    try:
        return subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True,
                              check=True, timeout=120).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def ler_documentos(cli, arquivos, pasta):
    """{"controles"|"prescricao"|"labs": leitura, "labs_texto": texto} + erros + avisos."""
    import leitura
    import preparar
    leituras, erros, avisos = {"labs_texto": None}, [], []
    for chave, tipo in (("controles", "controles"), ("prescricao", "prescricao"), ("exames", "labs")):
        pdfs = [a for a in arquivos.get(chave, []) if a.suffix.lower() == ".pdf"]
        outros = [a for a in arquivos.get(chave, []) if a.suffix.lower() != ".pdf"]
        if outros:  # foto do celular etc.: a ficha sairia sem o documento, com cara de pronta
            erros.append(f"{chave}: {len(outros)} anexo(s) que não são PDF não foram lidos: mandar em PDF ou ler "
                         "no chat")
        if tipo == "labs":
            texto = "\n".join(t for t in (_texto_do_pdf(p) for p in pdfs) if len(re.sub(r"\W", "", t)) >= 50)
            if texto:
                leituras["labs_texto"] = texto
                pdfs = [p for p in pdfs if len(re.sub(r"\W", "", _texto_do_pdf(p))) < 50]  # só os escaneados
        if not pdfs:
            if tipo != "labs":  # sem a folha ou sem a prescrição não há ficha
                erros.append(f"{chave}: sem anexo em PDF: ficha não gerada")
            elif not leituras["labs_texto"]:
                avisos.append(f"{chave}: sem anexo em PDF")
            continue
        paginas = []
        try:
            for i, pdf in enumerate(pdfs):
                paginas += [(len(paginas) + p, imgs) for p, imgs in
                            preparar.recortes_para_leitura(pdf, pasta / "recortes" / chave / f"{i:02d}")]
        except Exception as e:  # PDF corrompido, poppler que falha: o documento não é lido, os outros seguem
            erros.append(f"{chave}: PDF não recortado ({type(e).__name__}): não lido")
            continue
        try:
            leituras[tipo], _ = leitura.ler(cli, tipo, paginas)
        except leitura.LeituraFalhou as e:
            erros.append(f"{chave}: não lido ({e})")
    return leituras, erros, avisos


def gerar_ficha(plantao, pasta):
    """Ficha-cola do leito. Devolve ([docx, pdf] ou [], erros, avisos do Conferir)."""
    import build_passagem as motor
    import conferir
    import ficha_cola
    import gerar_docx
    import office
    import validar
    prep, _ = motor.preparar(plantao)
    erros, avisos_v = validar.validar(prep)
    _, avisos_m = motor.build(plantao)
    avisos = sorted(avisos_v + avisos_m, key=lambda w: "ALERTA:" not in w)
    if erros:
        return [], erros, avisos
    meta, leito = prep["meta"], prep["leitos"][0]
    turno = re.sub(r"\s+", "-", meta.get("turno", "").strip().lower())
    nome = nome_seguro(gerar_docx.nome_arquivo(meta, f"ficha-cola-{turno}-leito{leito['leito']}", "docx")
                       .replace(".docx", f"-{dt.datetime.now():%H%M}.docx"))
    cola = pasta / nome
    cfg, nao_coube = ficha_cola.ajustar(prep)
    ficha_cola.gerar(prep, cola, cfg)
    pdf = office.para_pdf(cola, pasta)
    e, a = conferir.conferir_docx(cola, conferir.TAM_FICHA)
    n = conferir.paginas(pdf)
    if n != 1:
        e.append(f"ficha-cola com {n} página(s): tem de ser 1 folha")
    if nao_coube:
        e.append("a ficha não coube em 1 folha nem em 9 pt sem anotações: encurtar no chat")
    return [cola, pdf], e, avisos + a


def relatorio(arquivos_ok, erros, avisos, linhas_anexos, gerados):
    """Texto do campo Avisos: o "Conferir" da linha."""
    alertas = [a for a in avisos if "ALERTA:" in a]
    resto = [a for a in avisos if "ALERTA:" not in a]
    partes = ["LEITURA AUTOMÁTICA (rascunho: conferir no chat antes de imprimir)",
              "Ficha-cola: " + ("gerada, 1 folha" if gerados else "NÃO gerada")]
    for titulo, itens in (("ERROS", erros), ("ALERTAS", alertas), ("CONFERIR", resto), ("ANEXOS", linhas_anexos)):
        if itens:
            partes += ["", titulo] + [f"- {x}" for x in itens]
    if arquivos_ok:
        partes += ["", "Devolvidos: " + ", ".join(Path(a).name for a in arquivos_ok)]
    return "\n".join(partes)


def etapa3(cli, campos, arquivos, pasta, contexto):
    """Lê, monta, gera e confere. Devolve (arquivos para devolver, erros, avisos)."""
    import montar
    leituras, erros, avisos = ler_documentos(cli, arquivos, pasta)
    plantao, erros_m = montar.montar(leituras, dict(contexto, evolucao_anterior=campos.get(
        CAMPO["evolucoes_anteriores"]) or None))
    erros += erros_m
    meta, leito = plantao["meta"], plantao["leitos"][0]
    rascunho = pasta / nome_seguro(f"{meta['data'].replace('/', '-') or 'sem-data'}-leito{leito['leito']}-"
                                   f"rascunho-{dt.datetime.now():%H%M}.json")
    rascunho.write_text(json.dumps(plantao, ensure_ascii=False, indent=2), encoding="utf-8")
    if erros:  # leitura falhou ou identificação não bate: o rascunho volta, a ficha não sai
        return [rascunho], erros, avisos + [f"L{leito['leito']}: {a}" for a in leito.get("avisos", [])]
    try:
        gerados, e, a = gerar_ficha(plantao, pasta)
    except Exception as ex:  # LibreOffice, poppler: o rascunho volta assim mesmo
        return [rascunho], [f"ficha não gerada ({type(ex).__name__}: {ex})"], avisos
    if e:  # ficha reprovada na conferência não volta: não pode ser impressa por engano
        return [rascunho], erros + e, avisos + a
    return gerados + [rascunho], erros, avisos + a


def _interrompido(*_):
    raise KeyboardInterrupt


def main():
    signal.signal(signal.SIGTERM, _interrompido)  # cancelamento do Actions: o status volta "falhou", não "lendo"
    record_id = os.environ.get("RECORD_ID", "")
    if not re.fullmatch(r"rec[A-Za-z0-9]{14}", record_id):
        sys.exit("RECORD_ID inválido")
    token = segredo("AIRTABLE_TOKEN")
    campo_saida = os.environ.get("AIRTABLE_CAMPO_SAIDA", "").strip()
    contexto = {"data": os.environ.get("DATA_PLANTAO", "").strip() or None,
                "turno": os.environ.get("TURNO", "").strip() or "diurno", "hoje": dt.date.today()}

    gravar(record_id, token, status="lendo")
    erros, avisos, linhas, devolvidos, gerados, falhas = [], [], [], [], False, 0
    pasta = Path(tempfile.mkdtemp(prefix="plantao-", dir=os.environ.get("RUNNER_TEMP") or None))
    try:
        import leitura
        campos = airtable("GET", record_id, token).get("fields", {})
        arquivos, linhas, falhas = baixar_anexos(campos, pasta / PASTA)
        texto_ant = campos.get(CAMPO["evolucoes_anteriores"]) or ""
        linhas.append(f"evoluções anteriores: {len(texto_ant)} caracteres")
        cli = leitura.cliente()
        if cli is None:
            avisos.append("leitura automática desligada (falta o segredo ANTHROPIC_API_KEY): só baixou os anexos")
        elif falhas:
            erros.append("anexo não baixado inteiro: leitura não feita (dispare de novo)")
        elif not re.fullmatch(r"fld[A-Za-z0-9]{14}", campo_saida):  # antes de ler: a leitura custa
            erros.append("falta a variável AIRTABLE_CAMPO_SAIDA (ID do campo de anexos): leitura não feita, "
                         "não haveria onde devolver a ficha")
        else:
            arquivos_out, erros, avisos = etapa3(cli, campos, arquivos, pasta / SAIDA, contexto)
            gerados = any(a.suffix == ".pdf" for a in arquivos_out) and not erros
            for arq in arquivos_out:
                try:
                    enviar_anexo(record_id, token, campo_saida, arq)
                    devolvidos.append(arq)
                except Exception as e:
                    erros.append(f"não consegui devolver {arq.suffix} ({type(e).__name__})")
    except (Exception, KeyboardInterrupt) as e:  # KeyboardInterrupt: job cancelado ou estourou o tempo
        erros.append("interrompido antes do fim (job cancelado ou tempo esgotado): disparar de novo"
                     if isinstance(e, KeyboardInterrupt) else f"erro: {type(e).__name__}: {e}")
    finally:
        status = "falhou" if (erros or falhas) else "pronto"
        texto = relatorio(devolvidos, erros, avisos, linhas, gerados)
        try:
            gravar(record_id, token, status=status, avisos=texto[:95000])
        finally:
            shutil.rmtree(pasta, ignore_errors=True)
            print(f"status: {status} | {len(erros)} erro(s), {len(avisos)} aviso(s), {len(devolvidos)} arquivo(s) "
                  f"devolvido(s), {len(linhas)} linha(s) de anexo")
    sys.exit(1 if status == "falhou" else 0)


if __name__ == "__main__":
    main()
