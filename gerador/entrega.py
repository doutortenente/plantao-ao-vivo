# -*- coding: utf-8 -*-
"""
entrega.py — o fim do plantão no chat, montado pelo programa (chamado pelo gerar_docx.py).

  guardar_anterior()  antes de sobrescrever: a versão anterior vai para <saida>/historico/<data-hora>/
                      (o Word não tem histórico; corrigir uma entrega não pode apagar a anterior)
  diff_por_leito()    o que mudou no texto da evolução desde a versão anterior, leito a leito
  mensagem()          rascunho de <saida>/mensagem.md, no formato das instruções do projeto:
                      1ª linha = o que saiu e quantos itens para conferir; alertas uma vez só (os já dados numa
                      entrega anterior não voltam); "Conferir" por leito; conduta com as linhas de meta numérica.
"""
import datetime as dt
import difflib
import re
import shutil
from pathlib import Path

META_NUMERICA = re.compile(r"(?i)\bmeta\b|\balvo\b|[<>]=?\s*\d|[≥≤]\s*\d")


def guardar_anterior(pasta, nomes):
    """Move os arquivos que vão ser sobrescritos para historico/<data-hora>/. Devolve a pasta ou None."""
    existentes = [Path(pasta) / n for n in nomes if (Path(pasta) / n).exists()]
    if not existentes:
        return None
    destino = Path(pasta) / "historico" / dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    destino.mkdir(parents=True, exist_ok=True)
    for arq in existentes:
        shutil.move(str(arq), destino / arq.name)
    return destino


def _por_leito(texto):
    blocos, atual = {}, None
    for linha in texto.splitlines():
        m = re.match(r"^LEITO (\S+) —", linha)
        if m:
            atual = m.group(1)
            blocos[atual] = []
        if atual:
            blocos[atual].append(linha)
    return blocos


def diff_por_leito(antes, depois):
    """{leito: [linhas '+'/'-']} só dos leitos que mudaram."""
    a, d = _por_leito(antes), _por_leito(depois)
    mudou = {}
    for leito in list(d) + [x for x in a if x not in d]:
        linhas = [l for l in difflib.unified_diff(a.get(leito, []), d.get(leito, []), lineterm="", n=0)
                  if l[:1] in "+-" and not l.startswith(("+++", "---"))]
        if linhas:
            mudou[leito] = linhas
    return mudou


def _alertas_ja_dados(historico):
    if not historico or not (Path(historico) / "mensagem.md").exists():
        return set()
    txt = (Path(historico) / "mensagem.md").read_text(encoding="utf-8")
    bloco = txt.split("**Alertas**", 1)[1].split("\n\n**", 1)[0] if "**Alertas**" in txt else ""
    return {l[2:].strip() for l in bloco.splitlines() if l.startswith("- ")}


def mensagem(plantao, avisos, arquivos, erros_conferencia=(), historico=None):
    """Texto do rascunho do chat (markdown)."""
    n = len(plantao["leitos"])
    alertas, conferir = [], {}
    for a in avisos:
        leito, _, txt = a.partition(": ")
        if txt.startswith("ALERTA: "):
            alertas.append(f"L{leito.lstrip('L')}: {txt[len('ALERTA: '):]}")
        else:
            conferir.setdefault(leito, []).append(txt)
    for l in plantao["leitos"]:
        alertas += [f"L{l['leito']}: {a}" for a in l.get("alertas", [])]
    vistos, novos = _alertas_ja_dados(historico), []
    for a in alertas:
        if a not in vistos and a not in novos:
            novos.append(a)
    repetidos = len(dict.fromkeys(alertas)) - len(novos)
    n_conferir = sum(len(v) for v in conferir.values()) + len(erros_conferencia)

    nomes = ", ".join(Path(a).name for a in arquivos)
    linhas = [f"Saíram a evolução e a ficha-cola de {n} leito{'s' if n > 1 else ''} ({nomes}); "
              f"{n_conferir} {'itens' if n_conferir != 1 else 'item'} para conferir.", ""]
    if erros_conferencia:
        linhas += ["**Não entregar ainda: a conferência achou erro**"] + [f"- {e}" for e in erros_conferencia] + [""]
    if novos or repetidos:
        linhas.append("**Alertas**")
        linhas += [f"- {a}" for a in novos]
        if repetidos:
            linhas.append(f"- ({repetidos} alerta(s) já dado(s) na entrega anterior, não repetidos)")
        linhas.append("")
    if conferir:
        linhas.append("**Conferir**")
        for leito, itens in conferir.items():
            linhas.append(f"- {leito}: " + "; ".join(itens))
        linhas.append("")
    conduta = []
    for l in plantao["leitos"]:
        tema = ""
        for c in l.get("conduta", []):
            m = re.match(r"^\s*\d+\.\s*([^:]+):\s*(.*)$", c)
            if m:
                tema, resto = m.group(1), m.group(2)
            else:
                resto = c.strip().lstrip("- ").rstrip(";")
            if resto and META_NUMERICA.search(resto):
                conduta.append(f"- L{l['leito']} {tema}: {resto}".replace(" :", ":"))
    if conduta:
        linhas += ["**Conduta (metas)**"] + conduta
    return "\n".join(linhas).rstrip() + "\n"
