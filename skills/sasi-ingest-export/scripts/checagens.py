# -*- coding: utf-8 -*-
"""
checagens.py — cruzamentos de segurança da prescrição (rodam dentro do motor, build_passagem.py).

Não mudam nada no texto: cada achado vira aviso "ALERTA: …", que sai no topo do "Conferir" e no chat.
  1. Alergia × prescrição (pela classe da droga; penicilina × cefalosporina/carbapenêmico como reação cruzada).
  2. Sem profilaxia de TEV nem anticoagulação, e o plano não fala de TEV.
  3. Duplicidade: dois IBP, dois anticoagulantes, ou a mesma droga em dois itens da ficha.
  4. Droga que o plano anterior mandou suspender e continua prescrita (precisa de `plano_anterior`).

O dicionário abaixo é a única fonte: marca e genérico → classe. Droga fora dele não é checada.
Para acrescentar: uma linha em DROGAS. Alergia escrita como classe ("AINE", "sulfa", "betalactâmico") também vale.
"""
import re
import unicodedata

# genérico: (classe, marcas e grafias que também identificam a droga)
DROGAS = {
    "dipirona": ("dipirona", ["novalgina", "metamizol", "anador", "lisador"]),
    "paracetamol": ("paracetamol", ["tylenol", "acetaminofeno"]),
    # penicilinas
    "penicilina": ("penicilina", ["benzetacil", "penicilina cristalina"]),
    "amoxicilina": ("penicilina", ["clavulin", "amoxil"]),
    "ampicilina": ("penicilina", ["unasyn"]),
    "oxacilina": ("penicilina", []),
    "piperacilina": ("penicilina", ["tazocin", "piperacilina-tazobactam", "pip-tazo"]),
    # cefalosporinas
    "cefalotina": ("cefalosporina", ["keflin"]),
    "cefazolina": ("cefalosporina", ["kefazol"]),
    "cefalexina": ("cefalosporina", ["keflex"]),
    "cefuroxima": ("cefalosporina", ["zinacef"]),
    "ceftriaxona": ("cefalosporina", ["rocefin", "triaxin"]),
    "cefotaxima": ("cefalosporina", ["claforan"]),
    "ceftazidima": ("cefalosporina", ["fortaz"]),
    "cefepima": ("cefalosporina", ["maxcef"]),
    "ceftarolina": ("cefalosporina", ["zinforo"]),
    "ceftazidima-avibactam": ("cefalosporina", ["torgena"]),
    # carbapenêmicos
    "meropenem": ("carbapenemico", ["meronem"]),
    "imipenem": ("carbapenemico", ["tienam"]),
    "ertapenem": ("carbapenemico", ["invanz"]),
    # outros ATB
    "sulfametoxazol": ("sulfonamida", ["bactrim", "trimetoprima"]),
    "ciprofloxacino": ("quinolona", ["cipro"]),
    "levofloxacino": ("quinolona", ["levaquin", "tavanic"]),
    "moxifloxacino": ("quinolona", ["avalox"]),
    "azitromicina": ("macrolideo", ["zitromax"]),
    "claritromicina": ("macrolideo", ["klaricid"]),
    "vancomicina": ("glicopeptideo", ["vancocina"]),
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
    "cetorolaco": ("aine", ["toragesic"]),
    "parecoxibe": ("aine", ["bextra"]),
    "nimesulida": ("aine", []),
    "acido acetilsalicilico": ("aine", ["aas", "aspirina"]),
    # opioides
    "morfina": ("opioide", ["dimorf"]),
    "fentanil": ("opioide", ["fentanila"]),
    "tramadol": ("opioide", ["tramal"]),
    "metadona": ("opioide", ["mytedom"]),
    "oxicodona": ("opioide", ["oxycontin"]),
    "codeina": ("opioide", []),
    "meperidina": ("opioide", ["dolantina"]),
    "nalbufina": ("opioide", ["nubain"]),
    # IBP e anticoagulantes (duplicidade e TEV)
    "pantoprazol": ("ibp", ["pantozol"]),
    "omeprazol": ("ibp", ["losec"]),
    "esomeprazol": ("ibp", ["nexium"]),
    "lansoprazol": ("ibp", []),
    "enoxaparina": ("anticoagulante", ["clexane"]),
    "heparina": ("anticoagulante", ["hnf", "liquemine"]),
    "fondaparinux": ("anticoagulante", ["arixtra"]),
    "dalteparina": ("anticoagulante", ["fragmin"]),
    "rivaroxabana": ("anticoagulante", ["xarelto"]),
    "apixabana": ("anticoagulante", ["eliquis"]),
    "dabigatrana": ("anticoagulante", ["pradaxa"]),
    "varfarina": ("anticoagulante", ["marevan"]),
}

# como a alergia pode vir escrita → classes que ela cobre
ALERGIA_CLASSE = {
    "dipirona": {"dipirona"}, "novalgina": {"dipirona"}, "metamizol": {"dipirona"},
    "penicilina": {"penicilina"}, "betalactamico": {"penicilina", "cefalosporina", "carbapenemico"},
    "cefalosporina": {"cefalosporina"}, "carbapenemico": {"carbapenemico"},
    "sulfa": {"sulfonamida"}, "sulfonamida": {"sulfonamida"},
    "aine": {"aine"}, "aines": {"aine"}, "anti-inflamatorio": {"aine"}, "antiinflamatorio": {"aine"},
    "quinolona": {"quinolona"}, "opioide": {"opioide"}, "opiaceo": {"opioide"},
    "macrolideo": {"macrolideo"}, "aminoglicosideo": {"aminoglicosideo"},
}
CRUZADA = {"penicilina": {"cefalosporina", "carbapenemico"}}
MECANICA_TEV = re.compile(r"compressao pneumatica|\bcpi\b|meia (elastica|de compressao)")


def _sem_acento(txt):
    return "".join(c for c in unicodedata.normalize("NFD", str(txt).lower()) if unicodedata.category(c) != "Mn")


_TERMOS = sorted(((_sem_acento(t), g) for g, (_, marcas) in DROGAS.items() for t in [g] + marcas),
                 key=lambda x: -len(x[0]))


def drogas_em(texto):
    """Genéricos citados num texto (marca ou genérico, palavra inteira)."""
    s = _sem_acento(texto)
    achados = []
    for termo, generico in _TERMOS:
        if re.search(r"(?<![a-z])" + re.escape(termo) + r"(?![a-z])", s) and generico not in achados:
            achados.append(generico)
    return achados


def _itens_prescritos(leito):
    """(rótulo, texto) de cada item da prescrição da ficha; SUSPENSOS fica de fora."""
    f = leito.get("ficha") or {}
    return [(rot.strip().upper(), it) for rot, itens in f.get("infusoes", []) + f.get("sistemas", [])
            if rot.strip().upper() not in ("SUSPENSOS", "SUSPENSO") for it in itens]


def checar(leito):
    """Lista de avisos 'ALERTA: …' do leito."""
    alertas = []
    itens = _itens_prescritos(leito)
    textos = [t for _, t in itens] + [t for t in leito.get("terapias", []) if not re.match(r"\s*suspens", t, re.I)]
    prescritas = []
    for t in textos:
        for g in drogas_em(t):
            if g not in prescritas:
                prescritas.append(g)

    # 1. alergia
    alergia = _sem_acento(leito.get("alergia") or (leito.get("ficha") or {}).get("alergia") or "")
    if alergia and not re.match(r"^\s*(nega|nao|sem|\?)", alergia):
        classes = set()
        for termo, cls in ALERGIA_CLASSE.items():
            if re.search(r"(?<![a-z])" + re.escape(termo), alergia):
                classes |= cls
        for g in drogas_em(alergia):
            classes.add(DROGAS[g][0])
        for g in prescritas:
            cls = DROGAS[g][0]
            if cls in classes:
                alertas.append(f"ALERTA: alergia a {leito.get('alergia')} e {g} prescrito ({cls})")
            elif any(cls in CRUZADA.get(c, ()) for c in classes):
                alertas.append(f"ALERTA: alergia a {leito.get('alergia')} e {g} prescrito: reação cruzada possível, "
                               "conferir a reação prévia")

    # 2. TEV
    tem_anticoag = any(DROGAS[g][0] == "anticoagulante" for g in prescritas)
    tem_mecanica = any(MECANICA_TEV.search(_sem_acento(t)) for t in textos)
    plano_fala_tev = any(re.search(r"\btev\b", _sem_acento(c)) for c in leito.get("conduta", []))
    if not (tem_anticoag or tem_mecanica or plano_fala_tev):
        alertas.append("ALERTA: sem profilaxia de TEV nem anticoagulação prescrita, e o plano não fala de TEV")

    # 3. duplicidade (só na prescrição da ficha, onde cada droga aparece uma vez)
    por_item = [(rot, drogas_em(t)) for rot, t in itens]
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
    suspensos = set()
    for linha in leito.get("plano_anterior", []):
        s = _sem_acento(linha)
        for trecho in re.findall(r"suspen\w*\s+(?:de\s+|o\s+|a\s+)?([^;,.]+)|([^;,.:]+?)\s+suspens[oa]s?\b", s):
            suspensos.update(drogas_em(" ".join(trecho)))
    for g in prescritas:
        if g in suspensos and any(g in gs for _, gs in por_item):
            alertas.append(f"ALERTA: o plano anterior mandou suspender {g} e ele continua na prescrição")
    return alertas
