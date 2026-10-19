#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_passagem.py — motor determinístico do plantão (UTI adulto)
================================================================
O LLM lê a letra da enfermagem; este script faz TODA a conta.
Formato de saída: docs/BRIEFING.md (fonte única do formato).

O que o motor garante
  - Máx - Mín de cada sinal vital, com " - " (nunca "–"), máximo primeiro.
  - Contagem de flags com desigualdade estrita, colchete só quando >= 1.
  - Balanço = soma das CÉLULAS (ganhos - perdas). O total escrito à mão
    só serve de conferência; divergência vai para o rodapé, nunca para o bloco.
  - Item de balanço fora do dicionário não entra na conta e vira aviso.
  - Valor ilegível ("?") não entra no Máx - Mín e vira aviso.
  - Nada de explicação dentro do bloco clínico: observação vai para os avisos.
  - Cruzamentos de segurança (checagens.py): alergia × prescrição, TEV, duplicidade, droga
    suspensa no plano anterior. Saem como "ALERTA: …" no topo dos avisos.
  - Dias (preparar): ATB escrito "(I: 30/12)" ou "(D?, I: 30/12)" vira "(D2, I: 30/12)" — dia de
    início = D0; dia de UTI sai de `admissao_uti` — dia da admissão = D1 (decisão de 19/10/2026).
    D escrito à mão que diverge da conta é corrigido e vira aviso.

Uso
  python3 build_passagem.py --demo
  python3 build_passagem.py --file plantao.json      # {"meta":{..},"leitos":[..]} ou 1 leito
  python3 build_passagem.py --json '{...}'
  cat plantao.json | python3 build_passagem.py

Entrada (por leito) — ver gerador/schema-plantao.md para o contrato completo
  {
    "leito": "01", "nome": "Fulano de Tal", "iniciais": "FT",
    "dia_internacao": "4º", "turno": "diurno",
    "vitais": {"PAS": [146, 126, "?", 122], "PAD": {"max": 94, "min": 71, "flag": 0}, ...},
    "sup_o2": "AA" | "VM por TQT, PCV, PEEP 7, FiO2 40 %",
    "dieta": "geral VO",
    "ganhos": [{"nome": "dieta VO", "serie": [200, 200]}, {"nome": "soro EV", "ml": 430}],
    "perdas": [{"nome": "diurese", "serie": [200, 300]}, {"nome": "UF", "ml": 1880}],
    "conferencia_enfermagem": {"ganhos": 1840, "perdas": 1300, "bh": 540},
    "evacuacao": "ausente (última 08/10)",
    "outros_balanco": ["Noradrenalina: 7 -> 5 -> 2,5 ml/h"],
    "laboratorio": ["HB: 13,4 -> 13,2 g/dl | HT: 39,9 -> 40,4 %", ...],
    "terapias": [...], "exame_fisico": [...], "evolucao": [...],
    "impressao": [...], "conduta": [...],
    "avisos": ["texto que vai para o rodapé, nunca para o bloco"]
  }
"""

import argparse
import copy
import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import checagens  # noqa: E402

# ── Dicionário canônico de balanço hídrico ──────────────────────────────────
# Radical curto (<= 3 letras) só casa com PALAVRA INTEIRA ("ev", "sf", "ch", "uf"),
# para "ev" não engolir "evacuação". Vence o radical mais longo que casar.
CANON = {
    # GANHOS
    "dieta": "ganho", "nutren": "ganho", "diamax": "ganho", "proline": "ganho",
    "nutri": "ganho", "tne": "ganho", "npt": "ganho", "enteral": "ganho",
    "parenteral": "ganho", "agua": "ganho", "água": "ganho", "hidrat": "ganho",
    "soro": "ganho", "sf": "ganho", "sg": "ganho", "ringer": "ganho",
    "ev": "ganho", "endovenoso": "ganho", "bomba": "ganho", "bic": "ganho",
    "dil": "ganho", "diluic": "ganho", "diluiç": "ganho", "medicac": "ganho",
    "medicaç": "ganho", "hemocomp": "ganho", "ch": "ganho", "plasma": "ganho",
    "albumina": "ganho", "ingesta": "ganho", "vo": "ganho", "reposic": "ganho",
    "reposiç": "ganho", "infus": "ganho", "sedac": "ganho", "sedaç": "ganho",
    "noradren": "ganho", "nora": "ganho", "propofol": "ganho", "fentanil": "ganho",
    "fenta": "ganho", "precedex": "ganho", "midazol": "ganho",
    "hemac": "ganho", "hemác": "ganho", "plaquet": "ganho", "crioprec": "ganho", "adrenal": "ganho",
    "vasopress": "ganho", "dobuta": "ganho", "dexmedet": "ganho", "bicarb": "ganho", "glicose": "ganho",
    "atb": "ganho", "antibiot": "ganho",
    # PERDAS
    "diurese": "perda", "diur": "perda", "urin": "perda", "svd": "perda", "sog": "perda",
    "sng": "perda", "gastric": "perda", "residuo": "perda", "resíduo": "perda",
    "dreno": "perda", "penrose": "perda", "torax": "perda", "tórax": "perda",
    "evacuac": "perda", "evacuaç": "perda", "fezes": "perda", "fistula": "perda",
    "fístula": "perda", "vomito": "perda", "vômito": "perda", "emese": "perda",
    "aspirado": "perda", "sangramento": "perda", "uf": "perda", "drenag": "perda", "hemovac": "perda",
    "colostom": "perda", "ileostom": "perda", "cvvhdf": "perda", "hemodiafil": "perda",
    "ultrafiltr": "perda", "hemodial": "perda", "dialise": "perda", "diálise": "perda",
}

# Limiares (BRIEFING §2). Dx < 70 e TAX > 37,8 foram acrescentados em 11/10/2026
# para hipoglicemia e febre não passarem calados — ver docs/DECISOES.md.
LIMIARES = {
    "PAS": [("lt", 90, "< 90")],
    "PAD": [("lt", 50, "< 50")],
    "PAM": [("lt", 65, "< 65")],
    "FC": [("gt", 100, "> 100")],
    "FR": [("gt", 20, "> 20")],
    "SpO2": [("lt", 92, "< 92")],
    "TAX": [("lt", 35.5, "< 35,5"), ("gt", 37.8, "> 37,8")],
    "Dx": [("gt", 180, "> 180"), ("lt", 70, "< 70")],
}
UNID = {"PAS": "mmHg", "PAD": "mmHg", "PAM": "mmHg", "FC": "bpm", "FR": "rpm",
        "SpO2": "%", "TAX": "ºC", "Dx": "mg/dl"}
ORDEM_VITAIS = ["PAS", "PAD", "PAM", "FC", "FR", "SpO2", "TAX", "Dx"]

TITULOS = {
    "vitais": "Sinais vitais + balanço",
    "laboratorio": "Laboratório:",
    "terapias": "Terapias vigentes:",
    "exame_fisico": "Exame físico:",
    "evolucao": "Evolução / Eventos 24 h:",
    "impressao": "Impressão / Problemas ativos:",
    "conduta": "Plano terapêutico e Condutas:",
}


# ── utilidades ───────────────────────────────────────────────────────────────
def _fmt(n, casas=None):
    """Inteiro sem casa; decimal com vírgula BR; milhar com ponto."""
    if n is None:
        return "?"
    n = float(n)
    if casas is not None:
        return f"{n:.{casas}f}".replace(".", ",")
    if n.is_integer():
        return f"{int(n):,}".replace(",", ".")
    inteiro, dec = f"{n:.1f}".split(".")
    return f"{int(inteiro):,}".replace(",", ".") + "," + dec


# ── horários da folha (Mod. 0120-01): aferição q2h, 07 h a 05 h ─────────────
SLOTS = ("07", "09", "11", "13", "15", "17", "19", "21", "23", "01", "03", "05")
DIURNO, NOTURNO = set(SLOTS[:6]), set(SLOTS[6:])
HORA = re.compile(r"^(\d{1,2})(?:\s*h|:\d{2})?$")


def _hora(k):
    m = HORA.match(str(k).strip())
    return f"{int(m.group(1)):02d}" if m and int(m.group(1)) < 24 else None


def por_hora(dados):
    """{'07': 146, '09': [120, 118], …} -> (horas, valores em ordem). Outra coisa -> None."""
    if not isinstance(dados, dict) or not dados or not all(_hora(k) for k in dados):
        return None
    horas, valores = [], []
    for k, v in dados.items():
        horas.append(_hora(k))
        valores += v if isinstance(v, list) else [v]
    return horas, valores


def _num(v):
    """Converte célula em (valor_numérico, texto_exibido). '?' -> (None, '?')."""
    if v is None:
        return None, None
    if isinstance(v, (int, float)):
        return float(v), None
    s = str(v).strip().replace(",", ".")
    m = re.fullmatch(r"([<>])\s*(\d+(?:\.\d+)?)", s)
    if m:  # "< 20" -> conta como 19,9 para flag; exibe "< 20"
        base = float(m.group(2))
        return (base - 0.1 if m.group(1) == "<" else base + 0.1), f"{m.group(1)} {_fmt(base)}"
    try:
        return float(s), None
    except ValueError:
        return None, "?"


def classify(nome):
    """Categoria canônica de um item de balanço, ou None se desconhecido."""
    s = str(nome).strip().lower()
    palavras = re.findall(r"[a-zà-ú0-9]+", s)
    melhor = None
    for radical, cat in CANON.items():
        if len(radical) <= 3:
            casa = radical in palavras
        else:
            casa = any(p.startswith(radical) for p in palavras) or radical in s
        if casa and (melhor is None or len(radical) > len(melhor[0])):
            melhor = (radical, cat)
    return melhor[1] if melhor else None


# ── balanço ──────────────────────────────────────────────────────────────────
def calc_balanco(ganhos, perdas):
    avisos, it_g, it_p = [], [], []
    g_total = p_total = 0.0

    def consumir(itens, lado):
        nonlocal g_total, p_total
        for it in itens or []:
            nome = it.get("nome", "?")
            if it.get("serie") is not None:
                serie = it["serie"]
                ph = por_hora(serie)
                vals = [_num(v) for v in (ph[1] if ph else serie)]
                ileg = sum(1 for v, t in vals if v is None and t == "?")
                ml = sum(v for v, _ in vals if v is not None)
                if ileg:
                    avisos.append(f"'{nome}': {ileg} célula(s) ilegível(is) — soma pode estar subestimada")
            else:
                ml = it.get("ml")
                if ml is None:
                    avisos.append(f"'{nome}' sem volume — fora da conta")
                    continue
                ml = float(ml)
            cat = classify(nome)
            if cat is None:
                avisos.append(f"'{nome}' fora do dicionário — NÃO somado")
                continue
            if cat != lado:
                avisos.append(f"RECLASSIFICADO: '{nome}' veio como {lado}, é {cat} — corrigido")
            if cat == "ganho":
                g_total += ml; it_g.append((nome, ml))
            else:
                p_total += ml; it_p.append((nome, ml))

    consumir(ganhos, "ganho")
    consumir(perdas, "perda")
    return {"ganho_total": g_total, "perda_total": p_total, "balanco": g_total - p_total,
            "itens_ganho": it_g, "itens_perda": it_p, "avisos": avisos}


# ── sinais vitais ────────────────────────────────────────────────────────────
def resumo_vital(nome, dados):
    """
    dados: lista horária (números, '?', '< 20')  OU
           {"max":..,"min":.., "flag": N | {"< 50": N}}  quando só se tem o agregado.
    Retorna (texto_max, texto_min, flags[], avisos[], lista_dx_ordenada|None)
    """
    avisos, flags = [], []
    lim = LIMIARES.get(nome, [])
    ph = por_hora(dados)
    horas_ileg = ""
    if ph:
        horas_ileg = ", ".join(f"{_hora(k)} h" for k, v in dados.items()
                               if any(_num(x) == (None, "?") for x in (v if isinstance(v, list) else [v])))
        dados = ph[1]
    if isinstance(dados, dict):
        vmax, tmax = _num(dados.get("max"))
        vmin, tmin = _num(dados.get("min"))
        fl = dados.get("flag")
        if isinstance(fl, int) and fl and lim:
            flags.append(f"[{fl}x {lim[0][2]}]")
        elif isinstance(fl, dict):
            flags += [f"[{n}x {k}]" for k, n in fl.items() if n]
        return tmax or _fmt_v(nome, vmax), tmin or _fmt_v(nome, vmin), flags, avisos, None
    pares = [_num(v) for v in dados]
    ileg = sum(1 for v, t in pares if v is None and t == "?")
    if ileg:
        avisos.append(f"{nome}: {ileg} aferição(ões) ilegível(is) fora do Máx - Mín"
                      + (f" ({horas_ileg})" if horas_ileg else ""))
    validos = [(v, t) for v, t in pares if v is not None]
    if not validos:
        return "?", "?", [], avisos, None
    for comp, ref, label in lim:
        hits = sum(1 for v, _ in validos if (v < ref if comp == "lt" else v > ref))
        if hits:
            flags.append(f"[{hits}x {label}]")
    vmax = max(validos, key=lambda x: x[0])
    vmin = min(validos, key=lambda x: x[0])
    dx = None
    if nome == "Dx":
        dx = [t or _fmt_v(nome, v) for v, t in sorted(validos, key=lambda x: -x[0])]
    return vmax[1] or _fmt_v(nome, vmax[0]), vmin[1] or _fmt_v(nome, vmin[0]), flags, avisos, dx


def _fmt_v(nome, v):
    if v is None:
        return "?"
    return _fmt(v, 1) if nome == "TAX" else _fmt(round(v) if nome != "TAX" else v)


def _eh_vm(sup):
    return bool(sup) and bool(re.search(r"\bVM\b|ventila|TQT.*(PCV|VCV|PSV)|IOT", sup, re.I))


# ── montagem por leito (estrutura usada pelo texto E pelo gerador .docx) ────
def compute_leito(leito, meta=None):
    meta = meta or {}
    avisos = list(leito.get("avisos", []))
    nome = leito.get("nome") or leito.get("iniciais", "?")
    ini = leito.get("iniciais")
    cab = f"LEITO {leito.get('leito', '?')} — {nome}" + (f" ({ini})" if ini and ini != nome else "")
    if leito.get("dia_internacao") or leito.get("dia_uti"):
        cab += f" — {leito.get('dia_uti') or 'DH ' + leito['dia_internacao']}"
    data, turno = meta.get("data", ""), leito.get("turno") or meta.get("turno", "")
    if data or turno:
        cab += f" — {data} {turno}".rstrip()

    vitais = leito.get("vitais", {})
    jan, av_jan = janela_efetiva(leito, meta)
    avisos += av_jan
    linhas = []
    sup = leito.get("sup_o2")
    vm = _eh_vm(sup)
    for nm in ORDEM_VITAIS:
        if nm not in vitais:
            continue
        tmax, tmin, flags, av, dx = resumo_vital(nm, vitais[nm])
        avisos += av
        if nm == "Dx":
            val = " / ".join(dx) if dx else f"{tmax} / {tmin}"
        else:
            val = f"{tmax} - {tmin}"
        linha = f"{nm}: {val} {UNID[nm]}"
        if nm == "SpO2" and sup and not vm:
            linha += f" ({sup})"
        if flags:
            linha += " " + " ".join(flags)
        linhas.append(linha)
        if nm == "Dx" and sup and vm:
            linhas.append(f"Sup O2: {sup}")
    if sup and vm and "Dx" not in vitais:
        linhas.append(f"Sup O2: {sup}")

    bal = calc_balanco(leito.get("ganhos"), leito.get("perdas"))
    avisos += bal["avisos"]
    conf = leito.get("conferencia_enfermagem") or {}
    diur = sum(ml for n, ml in bal["itens_perda"] if re.search(r"diur|urin|svd", n, re.I))
    for rot, calc, inf in (("Ganhos", bal["ganho_total"], conf.get("ganhos")),
                           ("Perdas", bal["perda_total"], conf.get("perdas")),
                           ("Diurese", diur, conf.get("diurese")),
                           ("BH", bal["balanco"], conf.get("bh"))):
        if inf is not None and abs(calc - float(inf)) > 0.5:
            avisos.append(f"CONFERÊNCIA — {rot}: folha diz {_fmt(inf)}, células somam {_fmt(calc)}")
    tem_bal = bool(leito.get("ganhos") or leito.get("perdas"))
    dieta = leito.get("dieta")
    if dieta or tem_bal:
        partes = []
        if dieta: partes.append(f"Dieta: {dieta}")
        if tem_bal: partes.append(f"Ingesta hídrica: {_fmt(bal['ganho_total'])} ml")
        linhas.append(" | ".join(partes))
    evac_ml = sum(ml for n, ml in bal["itens_perda"] if re.search(r"evacua|fezes", n, re.I))
    if leito.get("evacuacao") or evac_ml:
        txt = leito.get("evacuacao") or ""
        if evac_ml:
            txt = (txt + ", " if txt else "") + f"{_fmt(evac_ml)} ml"
        linhas.append(f"Evacuação: {txt}")
    outras = [(n[:1].upper() + n[1:], ml) for n, ml in bal["itens_perda"]
              if not re.search(r"diur|urin|svd|evacua|fezes", n, re.I)]
    if any(re.search(r"diur|urin|svd", n, re.I) for n, _ in bal["itens_perda"]):
        linhas.append(f"Diurese: {_fmt(diur)} ml")
    for n, ml in outras:
        linhas.append(f"{n}: {_fmt(ml)} ml")
    linhas += leito.get("outros_balanco", [])
    if tem_bal:
        b = bal["balanco"]
        linhas.append(f"BH: {'+' if b >= 0 else '-'} {_fmt(abs(b))} ml")

    secoes = [(f"{TITULOS['vitais']} {jan}:", linhas)]
    for chave in ("laboratorio", "terapias", "exame_fisico", "evolucao", "impressao", "conduta"):
        cont = leito.get(chave)
        if not cont:
            continue
        if isinstance(cont, str):
            cont = cont.split("\n")
        if chave == "impressao":
            cont = [c if re.match(r"^\d+\.", c) else f"{i}. {c}" for i, c in enumerate(cont, 1)]
        secoes.append((TITULOS[chave], list(cont)))
    avisos = checagens.checar(leito) + avisos  # alergia × prescrição, TEV, duplicidade, suspenso: no topo
    return {"cabecalho": cab, "secoes": secoes, "avisos": avisos, "balanco": bal, "janela": jan}


def render_leito(leito, meta=None):
    r = compute_leito(leito, meta)
    L = [r["cabecalho"]]
    for titulo, linhas in r["secoes"]:
        L += ["", titulo] + linhas
    return "\n".join(L), r["avisos"]


# ── janela: confere pelas horas das séries ────────────────────────────────────
def janela_efetiva(leito, meta):
    """Janela do título. Padrão 24 h (07 h a 05 h). Com séries por hora, o motor confere: só noite vira
    '19 - 05 h' (e ALERTA), só dia vira '07 - 17 h'. Recorte de turno só com meta.recorte ou leito.janela."""
    avisos = []
    declarada = leito.get("janela") or meta.get("janela") or "24 h"
    recorte = leito.get("recorte") or meta.get("recorte")
    vitais = leito.get("vitais", {})
    horas = set()
    sem_hora = []
    for nm, dados in vitais.items():
        ph = por_hora(dados)
        if ph:
            horas.update(ph[0])
        elif isinstance(dados, list):
            sem_hora.append(nm)
    if declarada != "24 h" or recorte:
        return declarada, avisos
    if not horas:
        if sem_hora:
            avisos.append("séries sem hora: o motor não conferiu se a janela de 24 h está completa")
        return declarada, avisos
    dia, noite = horas & DIURNO, horas & NOTURNO
    principais = set()
    for nm in ("PAS", "PAM", "FC"):
        ph = por_hora(vitais.get(nm))
        if ph:
            principais.update(ph[0])
    faltam = [h for h in SLOTS if h not in (principais or horas)]
    if dia and noite:
        if faltam:
            avisos.append("janela 24 h com aferição faltando às " + ", ".join(f"{h} h" for h in faltam))
        return "24 h", avisos
    if noite:
        avisos.append("ALERTA: janela pedida é 24 h, mas só há aferições de 19 a 05 h (faltou o diurno): "
                      "o título saiu 19 - 05 h")
        return "19 - 05 h", avisos
    avisos.append("ALERTA: janela pedida é 24 h, mas só há aferições de 07 a 17 h (faltou o noturno): "
                  "o título saiu 07 - 17 h")
    return "07 - 17 h", avisos


# ── dias de ATB e de UTI ─────────────────────────────────────────────────────
ATB_DIA = re.compile(r"\((?:D(\?|\d+),\s*)?I:\s*(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\)")
D_SOLTO = re.compile(r"\(D(\?|\d+)\)")  # "(D3)" sem a data de início: o motor não recalcula, só confere
# campos de texto do leito por onde o D do ATB passa (todos, para a evolução e a ficha não se contradizerem)
TEXTOS_LEITO = ("terapias", "conduta", "evolucao", "impressao")
TEXTOS_FICHA = ("vigiar", "exames")


def _data(txt, ref=None):
    """'01/01/2026' ou '30/12' (ano tirado de ref: a data mais recente que não passa de ref)."""
    m = re.match(r"^\s*(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?", str(txt or ""))
    if not m:
        return None
    d, mes, ano = int(m.group(1)), int(m.group(2)), m.group(3)
    if ano:
        ano = int(ano) + (2000 if len(ano) == 2 else 0)
    elif ref:
        ano = ref.year if (mes, d) <= (ref.month, ref.day) else ref.year - 1
    else:
        return None
    try:
        return dt.date(ano, mes, d)
    except ValueError:
        return None


def dias_atb(texto, data, calculados=None):
    """Escreve o D de cada ATB '(D?, I: dd/mm)' pela data do plantão. Devolve (texto, avisos).

    Trecho (entre ";") que diz "suspenso" não é recontado: o D final de um ATB suspenso fica como está.
    Início sem ano que daria mais de 60 dias (ex.: 20/10 num plantão de 19/10 = D364) não é escrito: fica o texto
    e vai para o Conferir. `calculados` (dict) recebe genérico → D, para conferir os "(Dn)" soltos depois."""
    avisos = []
    if not data:
        return texto, avisos

    def troca(m, trecho):
        escrito, d, mes, ano = m.group(1), m.group(2), m.group(3), m.group(4)
        inicio = _data(f"{d}/{mes}" + (f"/{ano}" if ano else ""), data)
        if not inicio or inicio > data:
            avisos.append(f"ATB com início inválido ou depois do plantão: {m.group(0)}")
            return m.group(0)
        n = (data - inicio).days
        if n > 60 and not ano:
            avisos.append(f"ATB com início {d}/{mes} daria D{n} ({m.group(0)}): conferir a data de início")
            return m.group(0)
        if n > 60:
            avisos.append(f"ATB há {n} dias ({m.group(0)}): conferir a data de início")
        if escrito not in (None, "?") and int(escrito) != n:
            avisos.append(f"ATB: estava D{escrito}, a conta dá D{n} (início {d}/{mes} = D0) — corrigido")
        g = checagens.droga_antes(trecho, m.start())
        if calculados is not None and g:
            calculados[g] = n
        return f"(D{n}, I: {d}/{mes}" + (f"/{ano}" if ano else "") + ")"

    partes = re.split(r"(;)", texto)
    for i, trecho in enumerate(partes):
        if trecho != ";" and not re.search(r"suspens", trecho, re.I):
            partes[i] = ATB_DIA.sub(lambda m, t=trecho: troca(m, t), trecho)
    return "".join(partes), avisos


def _dia_uti(leito, data, L):
    """dia_uti pela admissao_uti (admissão = D1). Devolve avisos."""
    adm_txt = leito.get("admissao_uti")
    if not adm_txt:
        return []
    if not data:
        return []  # o aviso de meta.data já saiu
    adm = _data(adm_txt, data)
    if not adm:
        return [f"{L}: admissao_uti ilegível ({adm_txt}): dia de UTI não calculado"]
    n = (data - adm).days + 1
    sem_ano = not re.match(r"^\s*\d{1,2}/\d{1,2}/\d{2,4}", str(adm_txt))
    if adm > data or n > 365 or (sem_ano and n > 180):
        return [f"{L}: admissao_uti {adm_txt} implausível para o plantão (daria D{n}): dia de UTI não mexido, conferir"]
    atual = leito.get("dia_uti") or ""
    if not isinstance(atual, str):
        return []  # o validar acusa o tipo
    m = re.search(r"\bD\s*(\d+)\s*UTI\b", atual, re.I) or re.fullmatch(r"\s*D\s*(\d+)\s*", atual)
    if not atual.strip():
        leito["dia_uti"] = f"D{n} UTI"
        return []
    if not m:
        return [f"{L}: dia_uti fora do formato \"Dn UTI\" (\"{atual}\"): a conta dá D{n} UTI — conferir"]
    avisos = []
    if int(m.group(1)) != n:
        avisos.append(f"{L}: dia de UTI estava D{m.group(1)}, a conta dá D{n} (admissão = D1) — corrigido")
    novo = f"D{n} UTI" if re.search(r"UTI", m.group(0), re.I) else f"D{n}"
    leito["dia_uti"] = atual[:m.start()] + novo + atual[m.end():]
    return avisos


def preparar(payload):
    """Cópia do plantão com os dias calculados (ATB e UTI). Devolve (plantao, avisos por leito 'Lxx: …').

    Campos de texto em string (com quebras de linha) viram lista. Linha de ficha fora do formato
    [rótulo, [itens]] fica como está (o validar acusa)."""
    dados = copy.deepcopy(payload)
    meta = dados.get("meta", {})
    data = _data(meta.get("data"))
    leitos = dados.get("leitos", [dados] if "leito" in dados else [])
    avisos = []
    if meta.get("data") and not (data and re.fullmatch(r"\s*\d{1,2}/\d{1,2}/\d{4}\s*", str(meta["data"]))):
        avisos.append(f"meta.data \"{meta.get('data')}\" fora do formato dd/mm/aaaa: dias de ATB e de UTI não "
                      "calculados")
        data = None
    for leito in leitos:
        L = f"L{leito.get('leito', '?')}"
        avisos += _dia_uti(leito, data, L)
        calculados, textos = {}, []  # textos: (onde, lista, índice) para conferir "(Dn)" e "D?" depois

        def passar(onde, valores, sufixo=""):
            novos = []
            for t in valores:
                t, av = dias_atb(t, data, calculados)
                novos.append(t); avisos.extend(f"{L}: {a}{sufixo}" for a in av)
            textos.extend((onde, t) for t in novos)
            return novos

        for chave in TEXTOS_LEITO + ("plano_anterior", "laboratorio", "exame_fisico", "outros_balanco"):
            if isinstance(leito.get(chave), str):
                leito[chave] = leito[chave].split("\n")
        for chave in TEXTOS_LEITO:
            if isinstance(leito.get(chave), list):
                leito[chave] = passar(chave, [t for t in leito[chave] if isinstance(t, str)])
        f = leito.get("ficha") if isinstance(leito.get("ficha"), dict) else {}
        for bloco in ("infusoes", "sistemas"):
            for linha in f.get(bloco) or []:
                if not (isinstance(linha, list) and len(linha) == 2 and isinstance(linha[1], list)):
                    continue
                if str(linha[0]).strip().upper().startswith("SUSPENS"):
                    continue  # ATB suspenso: o D final fica como foi escrito
                linha[1] = passar(f"ficha.{bloco}", [it for it in linha[1] if isinstance(it, str)], " (ficha)")
        for bloco in TEXTOS_FICHA:
            if isinstance(f.get(bloco), list):
                f[bloco] = passar(f"ficha.{bloco}", [t for t in f[bloco] if isinstance(t, str)], " (ficha)")
        for onde, t in textos:
            for m in D_SOLTO.finditer(t):
                g = checagens.droga_antes(t, m.start())
                if m.group(1) == "?":
                    avisos.append(f"{L}: \"D?\" sem data de início em `{onde}`: {t[:70]}")
                elif g in calculados and int(m.group(1)) != calculados[g]:
                    trecho = t[max(0, m.start() - 30):m.end()].lstrip(" -;,")
                    avisos.append(f"{L}: `{onde}` tem \"…{trecho}\", mas a conta dá D{calculados[g]} para {g}: "
                                  "conferir")
            if re.search(r"\(D\?,", t) and not re.search(r"suspens", t, re.I):
                avisos.append(f"{L}: \"D?\" não calculado em `{onde}`: {t[:70]}")
    return dados, list(dict.fromkeys(avisos))


def build(payload):
    payload, avisos_dias = preparar(payload)
    if "leitos" in payload:
        meta, leitos = payload.get("meta", {}), payload["leitos"]
    else:
        meta, leitos = {}, [payload]
    out, avisos = [], []
    for leito in leitos:
        txt, av = render_leito(leito, meta)
        out += [txt, ""]
        avisos += [f"L{leito.get('leito', '?')}: {a}" for a in av]
    avisos += avisos_dias
    avisos.sort(key=lambda a: "ALERTA:" not in a)  # alertas de segurança primeiro, ordem mantida
    return "\n".join(out).rstrip() + "\n", avisos


DEMO = {
    "meta": {"unidade": "UTI 4", "data": "27/06/2026", "turno": "diurno", "janela": "24 h"},
    "leitos": [{
        "leito": "01", "nome": "Paciente Demonstração", "iniciais": "PD", "dia_internacao": "5º",
        "sup_o2": "AA", "dieta": "geral hipossódica",
        "vitais": {
            "PAS": [139, 131, 120, 110, 101, 97, 105], "PAD": [84, 80, 72, 66, 61, 49, 63],
            "PAM": {"max": 96, "min": 70}, "FC": [102, 98, 88, 80, 74, 72, 79],
            "FR": [19, 17, 15, 14, 13, 12, 14], "SpO2": [97, 96, 96, "?", 95, 96, 97],
            "TAX": [36.9, 36.4, 36.0, 36.2, 36.1, 36.3, 36.5], "Dx": [116, 165, "< 20"],
        },
        # bug clássico: diurese lançada como ganho; "evacuação" não pode cair em "ev"
        "ganhos": [{"nome": "dieta VO", "serie": [200, 200, 230]}, {"nome": "soro EV", "ml": 400},
                   {"nome": "diurese", "serie": [300, 800]}],
        "perdas": [{"nome": "evacuação", "ml": 100}],
        "conferencia_enfermagem": {"bh": -200},
        "evacuacao": "1x pastosa",
        "laboratorio": ["HB: 9,8 -> 9,5 g/dl | HT: 29 -> 28 %", "CR: 6,4 -> 3,5 mg/dl"],
        "terapias": ["CV: Carvedilol 25 mg VO manhã; AAS 100 mg VO almoço."],
        "exame_fisico": ["Neurológico: ECG 15."],
        "evolucao": ["Sem instabilidade no período."],
        "impressao": ["IC aguda, estável - sem DVA."],
        "conduta": ["1. Cardiovascular:", "- Mantido carvedilol; meta PAM >= 65 mmHg;",
                    "2. Profilaxias: TEV / LAMG / cabeceira 30º."],
    }],
}


def main():
    ap = argparse.ArgumentParser(description="Motor determinístico do plantão UTI.")
    ap.add_argument("--json"); ap.add_argument("--file")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        payload = DEMO
    elif a.json:
        payload = json.loads(a.json)
    elif a.file:
        with open(a.file, encoding="utf-8") as f:
            payload = json.load(f)
    else:
        payload = json.load(sys.stdin)
    txt, avisos = build(payload)
    print(txt)
    if avisos:
        print("---\nRodapé (conferir — fora do bloco):", file=sys.stderr)
        for w in avisos:
            print(f"- {w}", file=sys.stderr)


if __name__ == "__main__":
    main()
