# -*- coding: utf-8 -*-
"""labs_72h.py — laboratório seriado de 72 h para a ficha-cola (pedido do Dr. em 22/11/2026).

Lê os laudos (PDF com texto ou .txt) de um ou mais leitos, agrupa por leito (prefixo "LL-" do nome do arquivo) e por
data da coleta ("Data da Coleta: dd/mm/aaaa", ou o dd-mm-aa do nome), e monta o bloco `ficha.lab` com as séries
"a => b => c" dos últimos 3 dias que têm coleta. Dia sem o exame = "—". Na ficha os eletrólitos também vão em série
(na evolução continuam sem série: labs.py). Dois exames afins dividem a linha quando cabem na coluna (Hb | Plaq,
Ur | Cr, Na | K, Mg | P, CaI | Lac, pH | pCO2, HCO3 | Lac), medidos em Times/Liberation Serif 10 pt.

Vários laudos no mesmo dia: vale a última coleta do dia (o laudo com hora mais tarde), mas o do laboratório central
vence a gasometria de beira-leito (arquivo com "gaso" no nome) em Hb, Na e K. Para ver todas as coletas
(cálcio 8/8 h, por exemplo), `--por-coleta`: um ponto por coleta e uma linha "Coletas …" com as horas.

Leitura (labs.py) é BETA: conferir contra o PDF; divergência vale o PDF.

Uso:
  python3 gerador/labs_72h.py <pasta ou laudos...> [--leito 03] [--por-coleta] [--json]
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "skills" / "sasi-ingest-export" / "scripts"))
import labs  # noqa: E402

# (sigla do labs.py, rótulo na ficha)
ORDEM = [("HB", "Hb"), ("PLAQ", "Plaq"), ("LEUCO", "Leuco"), ("UR", "Ur"), ("CR", "Cr"), ("NA", "Na"), ("K", "K"),
         ("MG", "Mg"), ("P", "P"), ("CA", "Ca"), ("CAI", "CaI"), ("ALB", "Alb"), ("pH", "pH"), ("pCO2", "pCO2"),
         ("HCO3", "HCO3"),
         ("Lactato", "Lac"), ("PCR", "PCR"), ("Troponina", "Trop"), ("INR", "INR")]
PARES = {("Hb", "Plaq"), ("Ur", "Cr"), ("Na", "K"), ("Mg", "P"), ("Mg", "CaI"), ("Ca", "CaI"), ("CaI", "Alb"),
         ("CaI", "Lac"), ("pH", "pCO2"), ("HCO3", "Lac"), ("PCR", "Trop"), ("Trop", "INR")}
LARGURA_CM = 7.9   # coluna CONTROLES (8,3 cm) menos as margens da célula
COLETA = re.compile(r"Data da Coleta:\s*(\d{2}/\d{2}/\d{4})(?:\s+(\d{2}):(\d{2}))?")
DATA_NOME = re.compile(r"(\d{2})-(\d{2})-(\d{2})(?!\d)")
LEITO_NOME = re.compile(r"^(\d{1,2})\s*-")

def _fonte():
    """Times New Roman ou a Liberation Serif (mesma métrica), achadas pelo fontconfig; sem elas, None."""
    try:
        import subprocess
        from PIL import ImageFont
        for nome in ("Times New Roman", "Liberation Serif"):
            r = subprocess.run(["fc-match", "-f", "%{file}", nome], capture_output=True, text=True, timeout=10)
            arq = r.stdout.strip()
            if arq and Path(arq).exists() and re.search(r"(?i)times|liberationserif|liberation_serif", arq):
                return ImageFont.truetype(arq, 1000)
    except Exception:  # noqa: BLE001 — sem PIL, sem fontconfig ou sem a fonte: estimativa por caractere
        pass
    return None


_F = _fonte()


def largura_cm(txt, pt=10):
    if _F is not None:
        return _F.getlength(txt) / 1000 * pt * 2.54 / 72
    return len(txt) * pt * 0.0148  # média da Times (0,42 em por caractere)


def _limpo(v, minimo=0):
    """Zeros à direita do decimal saem, deixando `minimo` casas: '15,20' -> '15,2' (mínimo 1); '138,0' -> '138'."""
    if "," not in v:
        return v
    inteiro, dec = v.split(",", 1)
    dec = dec.rstrip("0")
    dec = dec + "0" * (minimo - len(dec)) if len(dec) < minimo else dec
    return f"{inteiro},{dec}" if dec else inteiro


def _valor(sigla, v):
    v = v.strip()
    if sigla in ("HB", "HT", "UR"):
        v = _limpo(v, 1)
    elif sigla in ("NA", "pCO2", "HCO3"):
        v = _limpo(v)
    elif sigla == "pH" and re.fullmatch(r"\d,\d{3,}", v):
        v = f"{round(float(v.replace(',', '.')), 2):.2f}".replace(".", ",")  # 7,297 -> 7,30
    if sigla == "PLAQ":
        n = re.sub(r"\D", "", v.split(",")[0])
        return str(round(int(n) / 1000)) if len(n) > 3 else v
    return v


def coleta(texto, nome):
    """(datetime da coleta, origem) pelo laudo; sem "Data da Coleta", pelo dd-mm-aa do nome do arquivo."""
    datas = []
    for m in COLETA.finditer(texto):
        h = f"{m.group(2) or '00'}:{m.group(3) or '00'}"
        datas.append(datetime.strptime(f"{m.group(1)} {h}", "%d/%m/%Y %H:%M"))
    if datas:
        return max(datas)
    m = DATA_NOME.search(nome)
    if m:
        return datetime.strptime("/".join(m.groups()), "%d/%m/%y")
    return None


def ler(caminhos):
    """{leito: [(datetime, {sigla: valor}, arquivo)]} — avisos vão para stderr."""
    por_leito, avisos = {}, []
    for c in caminhos:
        c = Path(c)
        m = LEITO_NOME.match(c.name)
        if not m:
            avisos.append(f"{c.name}: sem o leito no começo do nome (LL-...): ignorado")
            continue
        texto = labs.texto_do_pdf(c) if c.suffix.lower() == ".pdf" else c.read_text(encoding="utf-8", errors="ignore")
        quando = coleta(texto, c.name)
        if quando is None:
            avisos.append(f"{c.name}: sem data da coleta: ignorado")
            continue
        valores, av = labs.extrair(texto)
        avisos += [f"{c.name}: {a}" for a in av]
        if valores:
            por_leito.setdefault(m.group(1).zfill(2), []).append((quando, valores, c.name))
    return por_leito, avisos


def pontos(coletas, por_coleta=False, dias=3, ate=None):
    """Lista ordenada de (ponto, {sigla: valor}) das coletas dos `dias` dias até `ate` (72 h: ate - 2 dias … ate)."""
    coletas = sorted(coletas, key=lambda x: x[0])
    ate = ate or max(q.date() for q, _, _ in coletas)
    datas = sorted({q.date() for q, _, _ in coletas if 0 <= (ate - q.date()).days < dias})
    if por_coleta:
        return [(q, v) for q, v, _ in coletas if q.date() in datas]
    out = []
    for d in datas:
        juntos = {}
        do_dia = [(q, v, n) for q, v, n in coletas if q.date() == d]
        # gasometria de beira-leito primeiro: o laudo do laboratório central vence; entre iguais, a última coleta
        for q, v, n in sorted(do_dia, key=lambda x: ("gaso" not in x[2].lower(), x[0])):
            juntos.update(v)
        out.append((datetime.combine(d, datetime.min.time()), juntos))
    return out


def serie(pts, sigla):
    vals = [_valor(sigla, v[sigla]) if sigla in v else "—" for _, v in pts]  # o "—" mantém a série alinhada às datas
    if not vals or all(x == "—" for x in vals):
        return None
    return " => ".join(vals)


def parear(itens, larg=LARGURA_CM, pt=10):
    out, i = [], 0
    while i < len(itens):
        a = itens[i]
        if i + 1 < len(itens):
            b = itens[i + 1]
            junto = f"{a} | {b}"
            if (a.split()[0], b.split()[0]) in PARES and largura_cm(junto.replace(" | ", "   |   "), pt) <= larg:
                out.append(junto); i += 2; continue
        out.append(a); i += 1
    return out


def bloco(coletas, por_coleta=False, ate=None):
    """{'lab_titulo': ..., 'lab': [...]} para o bloco `ficha` do leito."""
    pts = pontos(coletas, por_coleta, ate=ate)
    if not pts:
        return None
    itens = []
    for sigla, rot in ORDEM:
        s = serie(pts, sigla)
        if s:
            itens.append(f"{rot} {s}{' mil' if sigla == 'PLAQ' else ''}")
    lab = parear(itens)
    if por_coleta:
        horas = " · ".join(q.strftime("%d/%m %H h") for q, _ in pts)
        lab.insert(0, f"Coletas {horas}")
        titulo = f"LABORATÓRIO {pts[0][0]:%d/%m %H h} => {pts[-1][0]:%d/%m %H h}"
    else:
        titulo = "LABORATÓRIO " + " => ".join(f"{q:%d/%m}" for q, _ in pts)
    if ate and pts[-1][0].date() < ate:
        titulo += f" ({ate:%d/%m} sem coleta)"
    return {"lab_titulo": titulo, "lab": lab}


def main():
    ap = argparse.ArgumentParser(description="Laboratório seriado de 72 h para a ficha-cola (BETA)")
    ap.add_argument("entrada", nargs="+", help="pasta(s) ou laudos (PDF com texto / .txt), nome LL-...")
    ap.add_argument("--leito", action="append", help="só estes leitos (pode repetir)")
    ap.add_argument("--por-coleta", action="store_true", help="um ponto por coleta (com hora), não por dia")
    ap.add_argument("--json", action="store_true", help="saída JSON {leito: {lab_titulo, lab}}")
    ap.add_argument("--ate", help="último dia da janela (dd/mm/aaaa); padrão: a coleta mais recente de todos os leitos")
    a = ap.parse_args()
    arqs = []
    for e in a.entrada:
        p = Path(e)
        arqs += sorted(x for x in p.rglob("*") if x.suffix.lower() in (".pdf", ".txt")) if p.is_dir() else [p]
    por_leito, avisos = ler(arqs)
    for av in avisos:
        print("aviso:", av, file=sys.stderr)
    alvo = {x.zfill(2) for x in a.leito} if a.leito else None
    if a.ate:
        ate = datetime.strptime(a.ate, "%d/%m/%Y").date()
    else:
        ate = max((q.date() for c in por_leito.values() for q, _, _ in c), default=None)
    saida = {L: bloco(c, a.por_coleta, ate) for L, c in sorted(por_leito.items()) if not alvo or L in alvo}
    if a.json:
        print(json.dumps(saida, ensure_ascii=False, indent=1))
        return
    for L, b in saida.items():
        if b:
            print(f"== {L}  {b['lab_titulo']}")
            for linha in b["lab"]:
                print("  " + linha)


if __name__ == "__main__":
    main()
