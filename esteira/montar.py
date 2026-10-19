# -*- coding: utf-8 -*-
"""
montar.py — das leituras do leitura.py ao JSON do plantão de UM leito (gerador/schema-plantao.md).

Só arruma o que foi lido, sem conta e sem texto novo:
  - vitais por hora (2 leituras na mesma hora = lista); célula que não é número vira "?" e aviso;
  - balanço pela COLUNA impressa da folha → nome que o motor conhece (CANON), com o rótulo manuscrito ao lado
    ("EV NORA", "dreno penrose"); rótulo que mudaria o lado da conta fica de fora do nome (aviso). Coluna
    "outra" com rótulo desconhecido passa como veio: o validar barra a ficha (sumir com o item deixaria o BH errado
    calado);
  - rodapé da folha só em conferencia_enfermagem (o motor confere);
  - prescrição em INFUSÕES / POR SISTEMAS na ordem da ficha; ATB com "(I: dd/mm)" para o motor escrever o D, ou
    "(D?)" sem data impressa; colírio, pele e afins saem da ficha (aviso);
  - PENDÊNCIAS = só as ordens escritas na prescrição; o resto o Dr. fecha no chat;
  - laboratório: laudo digital pelo labs.py; escaneado pelos valores lidos, com o anterior da evolução anterior;
  - cabeçalho sem fonte = "?" e aviso; identificação diferente entre os documentos = ERRO (ficha não sai);
  - marcas de dúvida ("(revisar)", "(confirmar)", "⚠") saem do texto e viram aviso; "**" sai (negrito é do
    gerador); "–"/"—" viram "-" e "→" vira "->".
Toda dúvida vai para leito.avisos (o "Conferir").
"""
import datetime as dt
import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "gerador"))
sys.path.insert(0, str(RAIZ / "skills" / "sasi-ingest-export" / "scripts"))
import build_passagem as motor  # noqa: E402
import evolucao_anterior  # noqa: E402
import labs  # noqa: E402
import validar  # noqa: E402

INFUSOES = ("DVA", "SEDAÇÃO", "ATB", "VM", "O2", "DIETA", "NPT", "TRS")
SISTEMAS = ("NEURO", "CV", "RESP", "TGI", "RENAL", "ENDÓCRINO", "ANALGESIA", "PROFILAXIA", "SN")
COLUNA = {  # coluna impressa do Mod. 0120-01 → (nome no CANON do motor, lado)
    "VO": ("ingesta VO", "ganhos"), "Dieta": ("dieta", "ganhos"), "SNE": ("dieta SNE", "ganhos"),
    "Água": ("água", "ganhos"), "Med": ("medicação", "ganhos"), "Endovenoso": ("EV", "ganhos"),
    "Infus. Rápida": ("infusão rápida", "ganhos"), "Dil.": ("diluição", "ganhos"),
    "Diurese": ("diurese", "perdas"), "SNG/SNE": ("débito SNG/SNE", "perdas"), "Evacuação": ("evacuação", "perdas"),
    "Resíduo Gástrico": ("resíduo gástrico", "perdas"), "Dreno/SVD": ("dreno", "perdas"),
    "outra (ganho)": (None, "ganhos"), "outra (perda)": (None, "perdas"),
}
VITAIS = {"t": "TAX", "fr": "FR", "fc": "FC", "dx": "Dx", "spo2": "SpO2"}
SIGLA_LABS = {"PH": "pH", "PCO2": "pCO2", "PO2": "pO2", "SATO2": "SatO2", "LACTATO": "Lactato",
              "TROPONINA": "Troponina"}
LAB_CURTO = ((("HB", "Hb"), ("LEUCO", "Leuco"), ("PLAQ", "Plaq")), (("UR", "Ur"), ("CR", "Cr")),
             (("NA", "Na"), ("K", "K"), ("MG", "Mg"), ("CAI", "CaI"), ("P", "P")),
             (("pH", "pH"), ("pCO2", "pCO2"), ("HCO3", "HCO3"), ("BE", "BE"), ("Lactato", "Lactato")),
             (("PCR", "PCR"), ("INR", "INR"), ("Troponina", "Trop")))
UNIDADES = re.compile(r"\s*(g/dl|%|/mm3|mg/dl|mg/l|meq/l|mmol/l|mmhg|ng/ml|ng/l)\s*$", re.I)
DUVIDA = re.compile(r"\s*\((?:revisar(?: ocr)?|confirmar)\)|\s*⚠\s*(?:BIC)?", re.I)
MAX_PENDENCIAS = 7


def _sem_acento(txt):
    return "".join(c for c in unicodedata.normalize("NFD", str(txt)) if unicodedata.category(c) != "Mn")


def limpar(txt, avisos=None, onde=""):
    """Texto lido → texto da ficha (ver docstring). None fica None."""
    if txt is None:
        return None
    s = str(txt)
    if DUVIDA.search(s) and avisos is not None:
        avisos.append(f"{onde}: dúvida de leitura tirada do texto: {s[:70]}")
    s = DUVIDA.sub("", s).replace("**", "").replace("–", "-").replace("—", "-").replace("→", "->")
    return re.sub(r"\s+", " ", s).strip() or None


def valor(v):
    """Célula de sinal vital → número, "?" ou "< 20"; None se vazia; False se não é número."""
    if v is None or not str(v).strip():
        return None
    s = str(v).strip().replace(" ", "")
    if s == "?":
        return "?"
    m = re.fullmatch(r"([<>])(\d+(?:[.,]\d+)?)", s)
    if m:
        return f"{m.group(1)} {m.group(2).replace('.', ',')}"
    if re.fullmatch(r"\d+", s):
        return int(s)
    if re.fullmatch(r"\d+[.,]\d+", s):
        return float(s.replace(",", "."))
    return False


def volume(v):
    """Volume em ml ("1.840", "+ 540", "-300", "150") → número; "?" → "?"; vazio → None; outra coisa → False."""
    if v is None or not str(v).strip():
        return None
    s = str(v).strip().replace(" ", "").replace("ml", "").replace("mL", "")
    if s == "?":
        return "?"
    if not re.fullmatch(r"[+-]?(\d{1,3}(\.\d{3})+|\d+)(,\d+)?", s):
        return False
    n = float(s.replace(".", "").replace(",", "."))
    return int(n) if n == int(n) else n


def _leito(ident):
    d = re.sub(r"\D", "", str((ident or {}).get("leito") or ""))
    return d.zfill(2) if d else None


def _tokens(nome):
    return {t for t in re.findall(r"[A-Z]+", _sem_acento(nome or "").upper()) if len(t) >= 3}


def identidade(leituras):
    """Erros se leito ou nome diferem entre os documentos (ficha de um paciente com dado de outro)."""
    erros = []
    docs = [(k, d["identificacao"]) for k, d in leituras.items() if isinstance(d, dict) and d.get("identificacao")]
    leitos = {k: _leito(i) for k, i in docs if _leito(i)}
    if len(set(leitos.values())) > 1:
        erros.append("leito diferente entre os documentos: " + ", ".join(f"{k} L{v}" for k, v in leitos.items()))
    nomes = [(k, _tokens(i.get("nome"))) for k, i in docs if _tokens(i.get("nome"))]
    for i, (ka, a) in enumerate(nomes):
        for kb, b in nomes[i + 1:]:
            if not a & b:
                erros.append(f"nome do paciente diferente entre {ka} e {kb}")
    return erros


def _data(txt, hoje):
    return motor._data(txt, hoje) if txt else None


def data_do_plantao(informada, leituras, hoje, avisos):
    """Data do plantão: a informada no disparo > a da prescrição > a da folha + 1 dia (a folha começa às 07 h da
    véspera). Devolve date ou None."""
    d_inf = _data(informada, hoje)
    d_rx = _data(((leituras.get("prescricao") or {}).get("identificacao") or {}).get("data"), hoje)
    d_folha = _data(((leituras.get("controles") or {}).get("identificacao") or {}).get("data"), hoje)
    data = d_inf or d_rx or (d_folha + dt.timedelta(days=1) if d_folha else None)
    if d_inf and d_rx and d_inf != d_rx:
        avisos.append(f"data informada {d_inf:%d/%m} diferente da prescrição ({d_rx:%d/%m}): valeu a informada")
    if not (d_inf or d_rx) and d_folha:
        avisos.append(f"data do plantão deduzida da folha de controle ({d_folha:%d/%m} + 1 dia): conferir")
    if data and d_folha and (data - d_folha).days != 1:
        avisos.append(f"folha de controle de {d_folha:%d/%m} para o plantão de {data:%d/%m}: conferir a janela")
    return data


# ── controles ───────────────────────────────────────────────────────────────────────────────────────────────
def vitais(afericoes, avisos):
    """{"PAS": {"07": 132, "09": [126, 120]}, …} e o suporte de O2 da última aferição."""
    out, suportes = {}, []

    def por(nome, hora, v, cru):
        if v is None:
            return
        if v is False:
            avisos.append(f"controles: {nome} das {hora} h \"{cru}\" não é número: ficou \"?\"")
            v = "?"
        atual = out.setdefault(nome, {}).get(hora)
        out[nome][hora] = v if atual is None else (atual if isinstance(atual, list) else [atual]) + [v]

    ordem = {h: i for i, h in enumerate(motor.SLOTS)}
    for a in sorted(afericoes or [], key=lambda a: ordem.get(motor._hora(a.get("hora")), 99)):
        hora = motor._hora(a.get("hora"))
        if not hora:
            avisos.append(f"controles: hora \"{a.get('hora')}\" não reconhecida: linha fora da conta")
            continue
        for leitura in a.get("pa") or []:
            for k in ("pas", "pad", "pam"):
                por(k.upper(), hora, valor(leitura.get(k)), leitura.get(k))
        for k, nome in VITAIS.items():
            por(nome, hora, valor(a.get(k)), a.get(k))
        if limpar(a.get("suporte")):
            suportes.append(limpar(a.get("suporte"), avisos, "controles"))
    if len(set(suportes)) > 1:
        avisos.append("controles: suporte de O2 mudou no período: " + " -> ".join(dict.fromkeys(suportes)))
    return out, (suportes[-1] if suportes else None)


def balanco(colunas, avisos):
    """(ganhos, perdas) no formato do schema, pela coluna impressa."""
    lados = {"ganhos": [], "perdas": []}
    for c in colunas or []:
        canon, lado = COLUNA[c["coluna"]]
        rot = limpar(c.get("rotulo"), avisos, "controles")
        if canon is None:
            nome = rot or "?"
        elif c["coluna"] == "Dreno/SVD" and rot and re.search(r"svd", rot, re.I):
            nome = "diurese (SVD)"
        else:
            nome = f"{canon} {rot}" if rot else canon  # sem parênteses: o rótulo quebra limpo na grade da ficha
        if canon and motor.classify(nome) != lado[:-1]:
            avisos.append(f"controles: rótulo \"{rot}\" da coluna {c['coluna']} mudaria o lado da conta: "
                          f"ficou \"{canon}\"")
            nome = canon
        serie = {}
        for cel in c.get("celulas") or []:
            hora, v = motor._hora(cel.get("hora")), volume(cel.get("ml"))
            if v is None:
                continue
            if not hora:
                avisos.append(f"controles: célula de {nome} com hora \"{cel.get('hora')}\" não reconhecida: "
                              "fora da conta")
                continue
            if v is False:
                avisos.append(f"controles: {nome} das {hora} h \"{cel.get('ml')}\" não é volume: ficou \"?\"")
                v = "?"
            atual = serie.get(hora)
            serie[hora] = v if atual is None else (atual if isinstance(atual, list) else [atual]) + [v]
        if serie:
            lados[lado].append({"nome": nome, "serie": serie})
    return lados["ganhos"], lados["perdas"]


def rodape(r, avisos):
    conf = {}
    for chave, campo in (("ganhos", "ganhos_24h"), ("perdas", "perdas_24h"), ("diurese", "diurese_24h"),
                         ("bh", "bh_24h")):
        v = volume((r or {}).get(campo))
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            conf[chave] = v
        elif v is not None:
            avisos.append(f"controles: rodapé {campo} \"{(r or {}).get(campo)}\" ilegível: não conferido")
    return conf


# ── prescrição ──────────────────────────────────────────────────────────────────────────────────────────────
def item(it, avisos):
    """Linha da ficha: 'Nome dose via freq (I: dd/mm) => horários'."""
    partes = [limpar(it.get(k), avisos, "prescrição") for k in ("nome", "dose", "via", "frequencia")]
    txt = " ".join(p for p in partes if p)
    if it.get("grupo") == "ATB":
        ini = limpar(it.get("inicio"))
        txt += f" (I: {ini})" if ini and re.fullmatch(r"\d{1,2}/\d{1,2}(/\d{2,4})?", ini) else " (D?)"
    hor = limpar(it.get("horarios"), avisos, "prescrição")
    return txt + (f" => {hor}" if hor else "")


def prescricao(rx, avisos):
    """(infusoes, sistemas, linha ATB das terapias, pendências)."""
    grupos, fora = {}, []
    for it in rx.get("itens") or []:
        txt = item(it, avisos)
        if it.get("grupo") == "OUTRO" or validar.ITENS_FORA_DA_FICHA.search(txt):
            fora.append(txt)
            continue
        grupos.setdefault(it.get("grupo"), []).append(txt)
    if fora:
        avisos.append("prescrição: fora da ficha-cola: " + "; ".join(fora))
    infusoes = [[g, grupos[g]] for g in INFUSOES if g in grupos]
    suspensos = [s for s in (limpar(x, avisos, "prescrição") for x in rx.get("suspensos") or []) if s]
    sistemas = [[g, grupos[g]] for g in SISTEMAS if g in grupos] + ([["SUSPENSOS", suspensos]] if suspensos else [])
    atb = [t.split(" => ")[0] for t in grupos.get("ATB", [])]
    ordens = [o for o in (limpar(x, avisos, "prescrição") for x in rx.get("ordens") or []) if o]
    if len(ordens) > MAX_PENDENCIAS:
        avisos.append(f"prescrição: {len(ordens)} ordens; só as {MAX_PENDENCIAS} primeiras foram para PENDÊNCIAS: "
                      + "; ".join(ordens[MAX_PENDENCIAS:]))
    return infusoes, sistemas, (["ATB: " + "; ".join(atb) + "."] if atb else []), ordens[:MAX_PENDENCIAS]


# ── laboratório ─────────────────────────────────────────────────────────────────────────────────────────────
def _leitos_citados(texto):
    return {m.zfill(2) for m in re.findall(r"(?i)\bleito\s*:?\s*(\d{1,3})", texto or "")}


def laboratorio(texto, lido, n_leito, anterior, avisos):
    """Linhas de Laboratório (BRIEFING §1). Laudo de outro leito, ou de vários, não é usado."""
    if texto:
        citados = _leitos_citados(texto)
        if citados and (len(citados) > 1 or n_leito not in citados):
            avisos.append(f"labs: laudo cita o(s) leito(s) {', '.join(sorted(citados))}: não usado, ler no chat")
            return []
        linhas, av = labs.ler_laudo(texto, anterior)
        avisos += [f"labs: {a}" for a in av]
        return linhas
    if lido:
        valores = {}
        for e in lido.get("exames") or []:
            v = limpar(e.get("valor"), avisos, "labs")
            if v:
                valores[SIGLA_LABS.get(e["sigla"], e["sigla"])] = v
        return labs.montar(valores, labs.anteriores(anterior))
    return []


def lab_curto(linhas):
    """Laboratório da ficha a partir das linhas do BRIEFING ('HB: 11,2 -> 10,8 g/dl | …' → 'Hb 11,2 -> 10,8 | …')."""
    valores = {}
    for linha in linhas:
        corpo = re.sub(r"^\s*(Gaso\s*\w?|Outros)\s*:\s*", "", re.sub(r"\([^)]*\)", "", linha))
        for parte in re.split(r"\s\|\s|\s/\s", corpo):
            m = re.match(r"^\s*([A-Za-zÀ-ú0-9-]+)\s*:?\s+(.+?)\s*$", parte)
            if m:
                valores[m.group(1)] = UNIDADES.sub("", m.group(2)).strip()
    out = []
    for grupo in LAB_CURTO:
        partes = [f"{curto} {valores[k]}" for k, curto in grupo if k in valores]
        if partes:
            out.append(" | ".join(partes))
    return out


# ── leito ───────────────────────────────────────────────────────────────────────────────────────────────────
def montar(leituras, contexto):
    """leituras: {"controles", "prescricao", "labs": dict | None, "labs_texto": str | None}.
    contexto: {"data": "dd/mm/aaaa" | None, "turno", "evolucao_anterior": texto | None, "hoje": date}.
    Devolve (plantao, erros). Erro = a ficha não pode sair (o JSON rascunho sai assim mesmo)."""
    hoje = contexto.get("hoje") or dt.date.today()
    docs = {k: v for k, v in leituras.items() if k in ("controles", "prescricao", "labs") and v}
    avisos, erros = [], identidade(docs)
    for k, d in docs.items():
        avisos += [f"{k}: {p}" for p in d.get("pendencias") or []]
    ctl, rx = docs.get("controles") or {}, docs.get("prescricao") or {}
    idents = [d.get("identificacao") or {} for d in (rx, ctl, docs.get("labs") or {})]

    def primeiro(campo):
        return next((limpar(i.get(campo)) for i in idents if limpar(i.get(campo))), None)

    n_leito = next((_leito(i) for i in idents if _leito(i)), None)
    if not n_leito:
        erros.append("leito não identificado em nenhum documento")
    data = data_do_plantao(contexto.get("data"), docs, hoje, avisos)
    if not data:
        erros.append("data do plantão não encontrada (informe no disparo ou na prescrição)")
    m = re.search(r"UTI\D*(\d+)", _sem_acento(primeiro("unidade") or "").upper())
    if not m:
        avisos.append("unidade (UTI N) não encontrada no cabeçalho")
    idade = re.sub(r"\D", "", primeiro("idade") or "")
    sexo = (primeiro("sexo") or "")[:1].upper()
    cabecalho = {}
    for campo, chave in (("diagnostico", "diagnostico"), ("alergias", "alergia"), ("dispositivos", "dispositivos")):
        v = limpar(rx.get(campo), avisos, "prescrição")
        if not v:
            avisos.append(f"{chave}: não consta na prescrição: ficou \"?\"")
        cabecalho[chave] = v or "?"

    sv, sup = vitais(ctl.get("afericoes"), avisos)
    ganhos, perdas = balanco(ctl.get("balanco"), avisos)
    infusoes, sistemas, terapias, vigiar = prescricao(rx, avisos)

    anterior = {}
    if contexto.get("evolucao_anterior"):
        lidos, av = evolucao_anterior.ler(contexto["evolucao_anterior"].splitlines())
        if n_leito in lidos:
            anterior = lidos[n_leito]
            avisos += [a for a in av if a.startswith(f"L{n_leito}:")]
        else:
            avisos.append(f"evolução anterior sem o leito {n_leito}: exame físico e plano anterior não copiados")
    laboratorio_ = laboratorio(leituras.get("labs_texto"), docs.get("labs"), n_leito,
                               anterior.get("laboratorio_anterior"), avisos)
    avisos.append("dia de UTI: sem a data de admissão na UTI (preencher admissao_uti)")

    leito = {
        "leito": n_leito or "?", "nome": primeiro("nome") or "?",
        "idade_sexo": f"{idade}{sexo}" or "?", "dia_uti": "D? UTI", **cabecalho,
        "dieta": limpar(rx.get("dieta")) or limpar(ctl.get("dieta")),
        "vitais": sv, "sup_o2": sup, "ganhos": ganhos, "perdas": perdas,
        "conferencia_enfermagem": rodape(ctl.get("rodape"), avisos),
        "evacuacao": limpar(ctl.get("evacuacao"), avisos, "controles"),
        "laboratorio": laboratorio_, "terapias": terapias,
        "exame_fisico": anterior.get("exame_fisico") or [], "plano_anterior": anterior.get("plano_anterior") or [],
        "avisos": avisos,
        "ficha": {"infusoes": infusoes, "sistemas": sistemas, "vigiar": vigiar, "lab": lab_curto(laboratorio_),
                  "lab_titulo": f"LABORATÓRIO {data:%d/%m}" if data else "LABORATÓRIO"},
    }
    leito = {k: v for k, v in leito.items() if v not in (None, {}, [])} | {"avisos": avisos, "ficha": leito["ficha"]}
    d_rx = _data((rx.get("identificacao") or {}).get("data"), hoje) or data
    meta = {"unidade": f"UTI {m.group(1)}" if m else "UTI ?", "data": f"{data:%d/%m/%Y}" if data else "",
            "turno": contexto.get("turno") or "diurno", "janela": "24 h",
            "data_prescricao": f"{d_rx:%d/%m}" if d_rx else ""}
    return {"meta": meta, "leitos": [leito]}, erros
