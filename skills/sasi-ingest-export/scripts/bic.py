# -*- coding: utf-8 -*-
"""
bic.py — drogas em bomba de infusão contínua: concentração, dose por kg e teto.

Fonte única da tabela: app calculadoras-uti do Dr. Nicolas (github.com/doutortenente/calculadoras-uti,
docs/index.html, `const DROGAS`, commit 8ec731c de 09/10/2026), que por sua vez vem da planilha "Calculadoras
para UTI". Apresentação (massa e volume por ampola), unidade de dose, teto e a fonte de cada teto são os do app.
As contas (`concentracao`, `dose`, casas decimais) são as funções `conc`, `doseDe` e `casas` do app, em Python.
Mudou no app, muda aqui (e os testes em tests/test_bic.py usam o autoteste do app como gabarito).

O que é deste repositório (não do app): os apelidos (marcas vistas nas prescrições da Beneficência), o grupo da
ficha-cola (DVA, SEDAÇÃO, BNM) e a regra de que a dose sai da diluição PRESCRITA (ampolas + diluente), nunca de uma
diluição padrão suposta.

Entrada (um item de `infusoes_continuas` do leito, gerador/schema-plantao.md):
  {"droga": "Hyponor", "ampolas": 4, "diluente_ml": 234, "ml_h": {"07": 3, "16": 2}}
  - `diluente_ml`: o volume de diluente da prescrição; o volume final soma o das ampolas (4 x 4 ml + 234 = 250 ml).
  - `volume_final_ml` no lugar de `diluente_ml`: como no app (0 = puro).
  - `ml_h`: número ou série por hora da folha. Sem `ml_h`, a vazão sai da série do balanço com o nome da droga.
  - `mg_por_ampola` e `ml_por_ampola`: só se a apresentação for outra (noradrenalina em mg de BASE).
"""
import re
import unicodedata
from decimal import ROUND_HALF_UP, Decimal

# id: nome, massa por ampola (mg; vasopressina em UI), ml por ampola, unidade da concentração, modo da dose,
# unidade da dose, teto, fonte do teto (texto do app), grupo na ficha, apelidos
TABELA = {
    "noradrenalina": ("Noradrenalina", 4, 4, "mcg/ml", "mcgkgmin", "mcg/kg/min", 1, "definido por você", "DVA",
                      ["norepinefrina", "hyponor", "nora"]),
    "vasopressina": ("Vasopressina", 20, 1, "UI/ml", "uimin", "UI/min", 0.07, "bula", "DVA", ["encrise"]),
    "adrenalina": ("Adrenalina", 1, 1, "mcg/ml", "mcgkgmin", "mcg/kg/min", 2, "planilha e bula", "DVA",
                   ["epinefrina"]),
    "dobutamina": ("Dobutamina", 250, 20, "mcg/ml", "mcgkgmin", "mcg/kg/min", 20, "planilha", "DVA",
                   ["dobutrex", "dobuta"]),
    "milrinone": ("Milrinone", 10, 10, "mcg/ml", "mcgkgmin", "mcg/kg/min", 0.785, "planilha, 1,13 mg/kg/dia", "DVA",
                  ["milrinona", "primacor"]),
    "nitroprussiato": ("Nitroprussiato", 50, 2, "mcg/ml", "mcgkgmin", "mcg/kg/min", 10, "planilha e bula", "DVA",
                       ["nipride"]),
    "nitroglicerina": ("Nitroglicerina", 50, 10, "mcg/ml", "mcgmin", "mcg/min", 200, "planilha", "DVA", ["tridil"]),
    "dopamina": ("Dopamina", 50, 10, "mcg/ml", "mcgkgmin", "mcg/kg/min", 20, "planilha", "DVA", ["revivan"]),
    "fentanil": ("Fentanil", 0.5, 10, "mcg/ml", "mcgh", "mcg/h", 200, "planilha", "SEDAÇÃO",
                 ["fentanila", "fentanest", "fenta"]),
    "midazolam": ("Midazolam", 50, 10, "mg/ml", "mgkgh", "mg/kg/h", None, "", "SEDAÇÃO", ["dormonid", "mida"]),
    "propofol": ("Propofol", 200, 20, "mcg/ml", "mcgkgmin", "mcg/kg/min", 67, "limite clínico de UTI (4 mg/kg/h)",
                 "SEDAÇÃO", ["diprivan", "propovan"]),
    "cetamina": ("Cetamina", 100, 2, "mg/ml", "mgkgh", "mg/kg/h", 1, "planilha", "SEDAÇÃO", ["ketamina", "ketalar"]),
    "dexmedetomidina": ("Dexmedetomidina", 0.2, 2, "mcg/ml", "mcgkgh", "mcg/kg/h", 1.4, "planilha", "SEDAÇÃO",
                        ["precedex"]),
    "morfina": ("Morfina", 10, 1, "mg/ml", "mgh", "mg/h", None, "", "SEDAÇÃO", ["dimorf"]),
    "rocuronio": ("Rocurônio", 50, 5, "mcg/ml", "mcgkgmin", "mcg/kg/min", 12, "planilha (bula vai até 16)", "BNM",
                  ["esmeron"]),
}
GRUPOS = ("DVA", "SEDAÇÃO", "BNM")  # ordem das linhas na ficha-cola
# apelidos que são marca: na ficha a droga sai com a marca da prescrição; sinônimo e abreviação ("norepinefrina",
# "nora", "dobuta") saem pelo genérico
MARCAS = {"hyponor", "encrise", "dobutrex", "primacor", "nipride", "tridil", "revivan", "fentanest", "dormonid",
          "diprivan", "propovan", "ketalar", "precedex", "dimorf", "esmeron"}
SEM_PESO = {"mcgh", "mgh", "mcgmin", "uimin"}
# alertas do app além do teto: (droga, limite, é ALERTA?, texto)
ALEM_DO_TETO = (("nitroprussiato", 2, True, "acima de 2 mcg/kg/min o cianeto passa da depuração"),
                ("vasopressina", 0.04, False, "acima de 0,04 UI/min é terapia de resgate"))
HORA = re.compile(r"^(\d{1,2})(?:\s*h(?:\s*\d{2})?|:\d{2})?$")  # o mesmo da folha no motor


def _norm(txt):
    s = unicodedata.normalize("NFD", str(txt or "").strip().lower())
    return re.sub(r"\s+", " ", "".join(c for c in s if unicodedata.category(c) != "Mn"))


def achar(nome):
    """Droga da tabela pelo genérico, pelo nome do app ou por um apelido (o texto inteiro, não um pedaço)."""
    alvo = _norm(nome)
    for i, (n, mg, ml, cu, modo, du, teto, fonte, grupo, apelidos) in TABELA.items():
        if alvo and alvo in {i, _norm(n)} | {_norm(a) for a in apelidos}:
            return {"id": i, "nome": n, "mg": mg, "ml": ml, "cu": cu, "modo": modo, "du": du, "teto": teto,
                    "fonte_teto": fonte, "grupo": grupo, "apelidos": apelidos}
    return None


def mencionadas(texto):
    """Ids das drogas da tabela citadas num texto (genérico, nome ou apelido, palavra inteira), na ordem da tabela."""
    palavras = set(re.findall(r"[a-z0-9]+", _norm(texto)))
    return [i for i, d in TABELA.items() if palavras & ({i, _norm(d[0])} | {_norm(a) for a in d[-1]})]


def volume_final(d, ampolas, diluente_ml=None, volume_final_ml=None, ml_por_ampola=None):
    """Volume da bolsa em ml. Com `volume_final_ml`, como no app (0 = puro); com `diluente_ml`, ampolas + diluente."""
    ml = ml_por_ampola or d["ml"]
    if volume_final_ml is not None:
        return volume_final_ml if volume_final_ml > 0 else ampolas * ml
    if diluente_ml is not None:
        return ampolas * ml + diluente_ml
    return None


def concentracao(d, ampolas, diluente_ml=None, volume_final_ml=None, mg_por_ampola=None, ml_por_ampola=None):
    """Concentração na unidade da tabela (`cu`): a função `conc` do app."""
    vf = volume_final(d, ampolas, diluente_ml, volume_final_ml, ml_por_ampola)
    if not vf or vf <= 0:
        return None
    base = ampolas * (mg_por_ampola or d["mg"]) / vf
    return base * 1000 if d["cu"] == "mcg/ml" else base


def dose(d, c, ml_h, kg=None):
    """Dose na unidade da tabela (`du`): a função `doseDe` do app. Droga por kg sem peso -> None."""
    modo = d["modo"]
    if modo not in SEM_PESO and not kg:
        return None
    if modo == "mcgkgmin":
        return c * ml_h / kg / 60
    if modo in ("mcgkgh", "mgkgh"):
        return c * ml_h / kg
    if modo in ("mcgh", "mgh"):
        return c * ml_h
    return c * ml_h / 60  # mcgmin, uimin


def casas(d):
    """Casas decimais da dose: as do app."""
    return 3 if d["modo"] == "uimin" else (2 if d["modo"] in ("mgkgh", "mcgkgh", "mcgkgmin") else 1)


def arred(x, n):
    """Arredonda como o toFixed do app (meio para cima sobre o valor binário exato)."""
    return float(Decimal(x).quantize(Decimal(1).scaleb(-n), rounding=ROUND_HALF_UP))


def fmt(x, n=2):
    """Número no padrão BR com até `n` casas, sem zeros à direita: 4000 -> "4.000", 0,0323 -> "0,03"."""
    q = Decimal(x).quantize(Decimal(1).scaleb(-n), rounding=ROUND_HALF_UP)
    inteiro, _, dec = f"{q:f}".partition(".")
    inteiro = f"{int(inteiro):,}".replace(",", ".")
    dec = dec.rstrip("0")
    return inteiro + ("," + dec if dec else "")


def _num(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).strip().replace(",", "."))
    except ValueError:
        return None


def _ordem_folha(k):
    m = HORA.match(str(k).strip())
    return (int(m.group(1)) % 24 - 7) % 24 if m and int(m.group(1)) <= 24 else None


def vazoes(ml_h):
    """Vazões (ml/h) na ordem da folha (07 h -> 06 h), só onde mudam. Devolve (lista, avisos)."""
    avisos = []
    if isinstance(ml_h, dict):
        ordenadas = sorted(((_ordem_folha(k), v) for k, v in ml_h.items()), key=lambda x: (x[0] is None, x[0] or 0))
        celulas = []
        for _, v in ordenadas:
            celulas += v if isinstance(v, list) else [v]
    elif isinstance(ml_h, list):
        celulas = ml_h
    else:
        celulas = [ml_h]
    seq, ileg = [], 0
    for v in celulas:
        n = _num(v)
        if n is None:
            ileg += 1
            continue
        if not seq or seq[-1] != n:
            seq.append(n)
    if ileg:
        avisos.append(f"{ileg} célula(s) de vazão ilegível(is), fora da sequência")
    return seq, avisos


def _serie_do_balanco(d, ganhos):
    """Série do balanço cujo nome traz a droga (genérico ou apelido, palavra inteira): célula = ml/h da bomba."""
    nomes = {d["id"], _norm(d["nome"])} | {_norm(a) for a in d["apelidos"]}
    for g in ganhos or []:
        if not isinstance(g, dict) or g.get("serie") is None:
            continue
        if set(re.findall(r"[a-z0-9]+", _norm(g.get("nome", "")))) & nomes:
            return g["serie"]
    return None


def nome_na_ficha(item, d):
    """"Hyponor" quando a prescrição traz a marca; senão o genérico ("Noradrenalina")."""
    escrito = str(item.get("droga") or "").strip()
    return f"{escrito[:1].upper()}{escrito[1:]}" if _norm(escrito) in MARCAS else d["nome"]


def linha(item, kg=None, ganhos=None):
    """Texto da evolução e da ficha de um item de `infusoes_continuas`. Droga fora da tabela -> None.

    Evolução: "Noradrenalina: 16 mg/250 ml (64 mcg/ml), 3 -> 2 ml/h (0,05 -> 0,03 mcg/kg/min)" (rótulo = droga,
    como as outras linhas do bloco). Ficha, em 1 linha, o que corre agora: "Hyponor 16 mg/250 ml · 2 ml/h · 0,03
    mcg/kg/min" (a folha tem de caber; a sequência fica na evolução).
    Devolve {"id", "grupo", "evolucao", "ficha", "doses", "avisos"} (avisos com "ALERTA:" quando passa do teto)."""
    d = achar(item.get("droga"))
    if d is None:
        return None
    amp = _num(item.get("ampolas"))
    mg_amp, ml_amp = _num(item.get("mg_por_ampola")), _num(item.get("ml_por_ampola"))
    dil, vfin = _num(item.get("diluente_ml")), _num(item.get("volume_final_ml"))
    c = concentracao(d, amp, dil, vfin, mg_amp, ml_amp) if amp else None
    if c is None:
        return {"id": d["id"], "grupo": d["grupo"], "evolucao": None, "ficha": None, "doses": [],
                "avisos": [f"{d['nome']}: diluição incompleta (ampolas e diluente_ml ou volume_final_ml): "
                           "dose não calculada"]}
    unidade_massa = "UI" if d["cu"].startswith("UI") else "mg"
    bolsa = f"{fmt(amp * (mg_amp or d['mg']))} {unidade_massa}/{fmt(volume_final(d, amp, dil, vfin, ml_amp), 1)} ml"
    evo, fic = f"{d['nome']}: {bolsa} ({fmt(c)} {d['cu']})", f"{nome_na_ficha(item, d)} {bolsa}"
    avisos = []
    folha = _serie_do_balanco(d, ganhos)
    fonte = item.get("ml_h") if item.get("ml_h") is not None else folha
    seq, av = vazoes(fonte) if fonte is not None else ([], [])
    avisos += [f"{d['nome']}: {a}" for a in av]
    if item.get("ml_h") is not None and folha is not None:
        seq_folha = vazoes(folha)[0]
        if seq_folha and seq_folha != seq:
            avisos.append(f"{d['nome']}: `ml_h` ({' -> '.join(fmt(v, 1) for v in seq)} ml/h) diferente da série do "
                          f"balanço ({' -> '.join(fmt(v, 1) for v in seq_folha)} ml/h): a dose saiu do `ml_h`, conferir")
    if not seq:
        avisos.append(f"{d['nome']}: sem vazão na folha (nem `ml_h` nem série no balanço): dose não calculada")
        return {"id": d["id"], "grupo": d["grupo"], "evolucao": f"{evo}, sem vazão na folha",
                "ficha": f"{fic} · sem vazão na folha", "doses": [], "avisos": avisos}
    vaz = " -> ".join(fmt(v, 1) for v in seq) + " ml/h"
    doses = [dose(d, c, v, kg) for v in seq]
    if None in doses:
        avisos.append(f"{d['nome']}: sem peso, dose por kg não calculada")
        return {"id": d["id"], "grupo": d["grupo"], "evolucao": f"{evo}, {vaz}",
                "ficha": f"{fic} · {fmt(seq[-1], 1)} ml/h", "doses": [], "avisos": avisos}
    n = casas(d)
    doses = [arred(x, n) for x in doses]
    txt_dose = " -> ".join(fmt(x, n) for x in doses) + f" {d['du']}"
    maior = max(doses)
    if d["teto"] is not None and maior > d["teto"]:
        avisos.append(f"ALERTA: {d['nome']} {fmt(maior, n)} {d['du']} acima do teto de {fmt(d['teto'], 3)} "
                      f"({d['fonte_teto']}): conferir diluição e vazão")
    for i, limite, alerta, texto in ALEM_DO_TETO:
        if d["id"] == i and maior > limite and not (d["teto"] is not None and maior > d["teto"]):
            avisos.append(("ALERTA: " if alerta else "") + f"{d['nome']} {fmt(maior, n)} {d['du']}: {texto}")
    return {"id": d["id"], "grupo": d["grupo"], "evolucao": f"{evo}, {vaz} ({txt_dose})",
            "ficha": f"{fic} · {fmt(seq[-1], 1)} ml/h · {fmt(doses[-1], n)} {d['du']}", "doses": doses, "avisos": avisos}
