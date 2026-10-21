# -*- coding: utf-8 -*-
"""
checagens.py — cruzamentos de segurança da prescrição (rodam dentro do motor, build_passagem.py).

Não mudam nada no texto: cada achado vira aviso "ALERTA: …", que sai no topo do "Conferir" e no chat.
  1. Alergia × prescrição (pela classe da droga; penicilina × cefalosporina/carbapenêmico como reação cruzada).
  2. Sem profilaxia de TEV nem anticoagulação, e o plano não justifica (contraindicação, plaquetopenia,
     sangramento, deambulando…). A linha "Profilaxias: TEV …" do plano sozinha não dispensa o alerta.
  3. Duplicidade: dois IBP, dois anticoagulantes, ou a mesma droga em dois itens da ficha.
  4. Droga que o plano anterior mandou suspender e continua prescrita (precisa de `plano_anterior`). Lê por oração:
     "suspendo X e mantenho Y" só suspende X; "não suspender X", "se sangrar, suspender X" e "avaliar suspensão"
     não contam.
Item suspenso (bloco SUSPENSOS, ou "suspenso/a" na mesma oração) não conta como prescrito.

O dicionário abaixo é a única fonte: marca e genérico → classe. Droga fora dele não é checada.
Para acrescentar: uma linha em DROGAS. Alergia escrita como classe ("AINE", "sulfa", "beta-lactâmico",
"fluoroquinolona", "anti-inflamatório") também vale (ALERGIA_CLASSE).
"""
import re
import unicodedata

# genérico: (classe, marcas e grafias que também identificam a droga)
DROGAS = {
    "dipirona": ("dipirona", ["novalgina", "metamizol", "anador", "lisador", "buscopan composto"]),
    "paracetamol": ("paracetamol", ["tylenol", "acetaminofeno"]),
    # penicilinas
    "penicilina": ("penicilina", ["benzetacil", "penicilina cristalina", "benzilpenicilina", "penicilina g", "pnc"]),
    "amoxicilina": ("penicilina", ["clavulin", "amoxil", "amox/clav", "amoxi/clav", "amoxicilina-clavulanato"]),
    "ampicilina": ("penicilina", ["unasyn", "ampi-sulbactam", "ampi/sulbactam", "ampicilina-sulbactam"]),
    "oxacilina": ("penicilina", []),
    "piperacilina": ("penicilina", ["tazocin", "piperacilina-tazobactam", "pip-tazo", "pip/tazo", "piptazo",
                                    "pipetazo"]),
    # cefalosporinas
    "cefalotina": ("cefalosporina", ["keflin"]),
    "cefazolina": ("cefalosporina", ["kefazol"]),
    "cefalexina": ("cefalosporina", ["keflex"]),
    "cefuroxima": ("cefalosporina", ["zinacef"]),
    "ceftriaxona": ("cefalosporina", ["rocefin", "triaxin", "ceftriaxone"]),
    "cefotaxima": ("cefalosporina", ["claforan"]),
    "ceftazidima": ("cefalosporina", ["fortaz"]),
    "cefepima": ("cefalosporina", ["maxcef", "cefepime"]),
    "ceftarolina": ("cefalosporina", ["zinforo"]),
    "ceftazidima-avibactam": ("cefalosporina", ["torgena"]),
    # carbapenêmicos
    "meropenem": ("carbapenemico", ["meronem", "mero"]),
    "imipenem": ("carbapenemico", ["tienam"]),
    "ertapenem": ("carbapenemico", ["invanz"]),
    # outros ATB
    "sulfametoxazol": ("sulfonamida", ["bactrim", "trimetoprima", "smx-tmp", "smx/tmp", "smx+tmp", "smz-tmp", "smt-tmp"]),
    "ciprofloxacino": ("quinolona", ["cipro"]),
    "levofloxacino": ("quinolona", ["levaquin", "tavanic"]),
    "moxifloxacino": ("quinolona", ["avalox"]),
    "azitromicina": ("macrolideo", ["zitromax"]),
    "claritromicina": ("macrolideo", ["klaricid"]),
    "vancomicina": ("glicopeptideo", ["vancocina"]),
    "metronidazol": ("nitroimidazol", ["flagyl"]),
    "clindamicina": ("lincosamida", ["dalacin"]),
    "teicoplanina": ("glicopeptideo", ["targocid"]),
    "gentamicina": ("aminoglicosideo", []),
    "amicacina": ("aminoglicosideo", []),
    "polimixina": ("polimixina", ["polimixina b"]),
    "linezolida": ("oxazolidinona", ["zyvox"]),
    # AINEs
    "cetoprofeno": ("aine", ["profenid"]),
    "ibuprofeno": ("aine", ["alivium"]),
    "diclofenaco": ("aine", ["voltaren", "cataflam"]),
    "tenoxicam": ("aine", ["tilatil"]),
    "cetorolaco": ("aine", ["toragesic", "ketorolaco"]),
    "parecoxibe": ("aine", ["bextra"]),
    "nimesulida": ("aine", []),
    "acido acetilsalicilico": ("aine", ["aas", "aspirina"]),
    # opioides
    "morfina": ("opioide", ["dimorf"]),
    "fentanil": ("opioide", ["fentanila", "fentanest"]),
    "tramadol": ("opioide", ["tramal"]),
    "metadona": ("opioide", ["mytedom"]),
    "oxicodona": ("opioide", ["oxycontin"]),
    "codeina": ("opioide", []),
    "meperidina": ("opioide", ["dolantina"]),
    "nalbufina": ("opioide", ["nubain"]),
    "remifentanil": ("opioide", ["ultiva"]),
    "sufentanil": ("opioide", ["sufenta"]),
    # IBP e anticoagulantes (duplicidade e TEV)
    "pantoprazol": ("ibp", ["pantozol"]),
    "omeprazol": ("ibp", ["losec"]),
    "esomeprazol": ("ibp", ["nexium"]),
    "lansoprazol": ("ibp", []),
    "enoxaparina": ("anticoagulante", ["clexane", "enoxa", "hbpm"]),
    "heparina": ("anticoagulante", ["hnf", "liquemine"]),
    "fondaparinux": ("anticoagulante", ["arixtra"]),
    "dalteparina": ("anticoagulante", ["fragmin"]),
    "rivaroxabana": ("anticoagulante", ["xarelto"]),
    "apixabana": ("anticoagulante", ["eliquis"]),
    "dabigatrana": ("anticoagulante", ["pradaxa"]),
    "varfarina": ("anticoagulante", ["marevan"]),
}

# como a alergia pode vir escrita (sem acento, minúsculo, "β" = "beta") → classes que ela cobre
ALERGIA_CLASSE = (
    (r"dipirona|novalgina|metamizol", {"dipirona"}),
    (r"penicilin", {"penicilina"}),
    (r"beta[\s-]*lactam", {"penicilina", "cefalosporina", "carbapenemico"}),
    (r"cefalospor", {"cefalosporina"}),
    (r"carbapen", {"carbapenemico"}),
    (r"\bsulfas?\b|sulfonamid", {"sulfonamida"}),  # "sulfato" (ferroso, de magnésio) não é sulfa
    (r"\baines?\b|\bainhs?\b|anti[\s-]*inflamat", {"aine"}),
    (r"quinolon", {"quinolona"}),  # fluoroquinolona incluída
    (r"opioide|opiaceo", {"opioide"}),
    (r"macrolid", {"macrolideo"}),
    (r"aminoglicos", {"aminoglicosideo"}),
)
CRUZADA = {"penicilina": {"cefalosporina", "carbapenemico"}}
MECANICA_TEV = re.compile(r"compressao pneumatica|\bcpi\b|meias? (elasticas?|de compressao)")
# o plano só dispensa o alerta de TEV quando diz por que não há profilaxia, na mesma oração em que fala de TEV
SEM_TEV_JUSTIFICADO = re.compile(r"(?<!sem )contra-?indica|plaquetopeni|sangramento ativo|sangrando|"
                                 r"anticoagula\w* plena|nao indicad|deambulando|baixo risco|risco baixo|suspens")
# ordem de suspender (não a forma farmacêutica "suspensão oral", "Bactrim suspensão 20 ml")
SUSPENSAO = re.compile(r"\bsuspens[oa]s?\b|\bsuspend\w*|\bsuspensao\s+d[oae]s?\b")
# negação/intenção colada ao verbo ("não suspender", "avaliar suspensão"): não é suspensão
NAO_SUSPENDE = re.compile(r"\b(nao|avaliar|avalio|considerar|considero|programar|programo|discutir|possivel)\s+"
                          r"(?:\w+\s+)?(?:a\s+|de\s+)?$")
# condicional no começo da frase ("Se sangrar, suspender") ou depois do verbo ("suspender se plaquetas < 50",
# "suspender 12 h antes da traqueostomia")
CONDICIONAL_ANTES = re.compile(r"^[\W\d]*(se|caso)\b")
CONDICIONAL_DEPOIS = re.compile(r"\b(se|caso)\b|\bantes d[aoe]s?\b")  # "… 12 h antes da TQT": programado
# oração de alergia que nega ("Nega outras", "Não há alergias", "Sem alergias conhecidas"); "Não tolera X" é alergia
ALERGIA_NEGADA = re.compile(r"^\s*(nega\b|nenhum|nkda|desconhec|nao\s+(ha|tem|possui|refere|sabe|conhec|informad)|"
                            r"sem\s+(alergi|historico|antecedente|registro|relato|outras?)\b|sem\s*$)")
# o que pode sobrar numa oração que só continua a lista de drogas ("suspendo X, Y e Z"): dose, via, D, horário
SO_LISTA = re.compile(r"\([^)]*\)|\d+[.,]?\d*|\b(mg|g|mcg|ui|ml|ev|vo|sc|im|sne|sng|h|dia|de|do|da|a|o|os|as|"
                      r"tambem|ambos|ambas)\b|[\W_]")
HEPARINA_SELO = re.compile(r"selo|lock|cateter|heparinizad|flush|permeabil")


def _sem_acento(txt):
    return "".join(c for c in unicodedata.normalize("NFD", str(txt).lower()) if unicodedata.category(c) != "Mn")


_TERMOS = sorted(((_sem_acento(t), g) for g, (_, marcas) in DROGAS.items() for t in [g] + marcas),
                 key=lambda x: -len(x[0]))


def _termos_em(s):
    for termo, generico in _TERMOS:
        for m in re.finditer(r"(?<![a-z])" + re.escape(termo) + r"(?![a-z])", s):
            yield m, generico


def drogas_em(texto):
    """Genéricos citados num texto (marca ou genérico, palavra inteira)."""
    achados = []
    for _, generico in _termos_em(_sem_acento(texto)):
        if generico not in achados:
            achados.append(generico)
    return achados


def droga_antes(texto, pos, alcance=60):
    """Genérico citado mais perto antes da posição `pos` (até `alcance` caracteres) na MESMA oração, ou None.
    A oração começa depois do último ";", "+" ou ", " fora de parênteses: "Ceftriaxona (D5) + Metronidazol (D3)"
    não atribui o D3 à ceftriaxona."""
    s = _sem_acento(texto)
    inicio, prof = 0, 0
    for i in range(pos - 1, -1, -1):
        c = s[i]
        if c == ")":
            prof += 1
        elif c == "(":
            prof = max(prof - 1, 0)
        elif prof == 0 and (c in ";+·" or (c == "," and s[i + 1:i + 2] == " ")):
            inicio = i + 1
            break
    perto = [(m.end() + inicio, g) for m, g in _termos_em(s[inicio:pos]) if pos - (m.end() + inicio) <= alcance]
    return max(perto)[1] if perto else None


def lista(valor):
    """Campo de texto do leito como lista de linhas (aceita string com quebras de linha)."""
    if isinstance(valor, str):
        return valor.split("\n")
    return [v for v in valor or [] if isinstance(v, str)] if isinstance(valor, list) else []


def linhas_da_ficha(ficha, bloco):
    """[(rótulo, [itens])] de `infusoes`/`sistemas`, ignorando linha fora do formato (o validar acusa)."""
    out = []
    for linha in (ficha or {}).get(bloco) or []:
        if isinstance(linha, (list, tuple)) and len(linha) == 2 and isinstance(linha[0], str):
            out.append((linha[0], lista(linha[1]) if not isinstance(linha[1], str) else [linha[1]]))
    return out


def _oracoes(s):
    return [o for o in re.split(r"[;,.·]|\s+e\s+|\s+mas\s+", s) if o.strip()]  # " · " separa itens na ficha


def suspenso(texto):
    """O texto manda suspender (e não é a forma farmacêutica "suspensão oral")?"""
    return bool(SUSPENSAO.search(_sem_acento(texto)))


def prescritas_em(texto):
    """Drogas do texto, tirando as das orações que dizem que estão suspensas ("suspensa se…" continua valendo)."""
    s = _sem_acento(texto)
    if re.match(r"^\W*suspens[oa]", s):
        return []
    fora = set()
    for o in _oracoes(s):
        m = SUSPENSAO.search(o)
        if m and not CONDICIONAL_DEPOIS.search(o[m.end():]):
            fora.update(drogas_em(o))
    return [g for g in drogas_em(s) if g not in fora]


def suspensos_no_plano(linhas):
    """Drogas que o plano mandou suspender, lidas por oração (ver docstring do módulo)."""
    suspensos = set()
    for linha in linhas:
        s = _sem_acento(linha)
        if re.match(r"^[\W\d]*suspens\w*\s*:", s):  # "- Suspensos: azitromicina, claritromicina"
            suspensos.update(drogas_em(s))
            continue
        for frase in re.split(r"[;.]", s):
            if CONDICIONAL_ANTES.search(frase):
                continue
            oracoes = _oracoes(frase)
            for i, o in enumerate(oracoes):
                m = SUSPENSAO.search(o)
                if not m or NAO_SUSPENDE.search(o[:m.start()]) or CONDICIONAL_DEPOIS.search(o[m.end():]):
                    continue
                suspensos.update(drogas_em(o))
                # a lista continua nas orações seguintes ("suspendo X, Y e Z"); com o plural, também nas de antes
                # ("X e Y suspensos"); para na primeira oração que tem outra coisa ("e mantenho Tazocin")
                vizinhas = [oracoes[i + 1:]] + ([oracoes[:i][::-1]] if re.match(r"suspens[oa]s\b", o[m.start():])
                                                else [])
                for lado in vizinhas:
                    for v in lado:
                        if not drogas_em(v) or _tem_outra_coisa(v):
                            break
                        suspensos.update(drogas_em(v))
    return suspensos


def _tem_outra_coisa(oracao):
    """A oração tem algo além de drogas, dose e via (um verbo, outra ordem)?"""
    resto = oracao
    for m, _ in sorted(_termos_em(oracao), key=lambda x: -len(x[0].group(0))):
        resto = resto.replace(m.group(0), " ")
    return bool(SO_LISTA.sub(" ", resto).strip())


def _itens_prescritos(leito):
    """(rótulo, texto) de cada item da prescrição da ficha; SUSPENSOS (e variantes) fica de fora."""
    f = leito.get("ficha") or {}
    return [(rot.strip().upper(), it) for rot, itens in linhas_da_ficha(f, "infusoes") + linhas_da_ficha(f, "sistemas")
            if not rot.strip().upper().startswith("SUSPENS") for it in itens]


def _alergia(leito):
    a = leito.get("alergia") or (leito.get("ficha") or {}).get("alergia") or ""
    return a if isinstance(a, str) else ""


def checar(leito):
    """Lista de avisos 'ALERTA: …' do leito."""
    alertas = []
    itens = _itens_prescritos(leito)
    textos = [t for _, t in itens] + lista(leito.get("terapias"))
    prescritas = []
    for t in textos:
        for g in prescritas_em(t):
            if g not in prescritas:
                prescritas.append(g)

    # 1. alergia ("Nega outras; dipirona": a oração negativa sai, o resto é checado)
    escrita = _alergia(leito)
    alergia = " ; ".join(o for o in re.split(r"[;,/.()]|\s[-–—]\s|\s+e\s+",
                                             _sem_acento(escrita).replace("β", "beta"))
                         if o.strip() and not ALERGIA_NEGADA.search(o))
    if alergia.strip():
        classes = set()
        for rx, cls in ALERGIA_CLASSE:
            if re.search(rx, alergia):
                classes |= cls
        for g in drogas_em(alergia):
            classes.add(DROGAS[g][0])
        for g in prescritas:
            cls = DROGAS[g][0]
            if cls in classes:
                alertas.append(f"ALERTA: alergia a {escrita} e {g} prescrito ({cls})")
            elif any(cls in CRUZADA.get(c, ()) for c in classes):
                alertas.append(f"ALERTA: alergia a {escrita} e {g} prescrito: reação cruzada possível, "
                               "conferir a reação prévia")

    # 2. TEV
    # selo de cateter com heparina não é profilaxia
    tem_anticoag = any(DROGAS[g][0] == "anticoagulante" for t in textos for g in prescritas_em(t)
                       if not (g == "heparina" and HEPARINA_SELO.search(_sem_acento(t))))
    tem_mecanica = any(MECANICA_TEV.search(_sem_acento(t)) for t in textos)
    # justificativa só vale se a mesma oração não prescreve a profilaxia ("TEV: Enoxaparina 40 mg até deambular")
    justificado = any(re.search(r"\btev\b", o) and SEM_TEV_JUSTIFICADO.search(o)
                      and not any(DROGAS[g][0] == "anticoagulante" for g in drogas_em(o))
                      for c in lista(leito.get("conduta")) for o in re.split(r"[;.]", _sem_acento(c)))
    if not (tem_anticoag or tem_mecanica or justificado):
        alertas.append("ALERTA: sem profilaxia de TEV nem anticoagulação prescrita, e o plano não diz por quê")

    # 3. duplicidade (só na prescrição da ficha, onde cada droga aparece uma vez)
    por_item = [(rot, prescritas_em(t)) for rot, t in itens]
    contagem = {}
    for _, gs in por_item:
        for g in gs:
            contagem[g] = contagem.get(g, 0) + 1
    for g, n in contagem.items():
        if n > 1:
            alertas.append(f"ALERTA: {g} aparece em {n} itens da prescrição")
    for cls, nome in (("ibp", "IBP"), ("anticoagulante", "anticoagulante")):
        gs = [g for g in contagem if DROGAS[g][0] == cls]
        if len(gs) > 1:
            alertas.append(f"ALERTA: dois {nome} prescritos ({', '.join(gs)})")

    # 4. suspenso no plano anterior e ainda prescrito
    suspensos = suspensos_no_plano(lista(leito.get("plano_anterior")))
    for g in prescritas:
        if g in suspensos and any(g in gs for _, gs in por_item):
            alertas.append(f"ALERTA: o plano anterior mandou suspender {g} e ele continua na prescrição")
    return alertas
