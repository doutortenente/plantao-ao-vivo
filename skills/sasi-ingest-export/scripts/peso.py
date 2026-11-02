# -*- coding: utf-8 -*-
"""
peso.py — o que depende do peso e da altura do leito: peso predito e volume corrente, clearance de creatinina
(Cockcroft-Gault) e débito urinário em ml/kg/h com o estágio KDIGO pelo débito.

Zero alucinação: o peso só entra em conta com fonte e data (`"peso": {"kg": 66, "altura_cm": 153,
"fonte": "EcoTT", "data": "06/12/2025"}`). Sem isso, nada que depende dele é calculado (e o validar dá erro).

Fórmulas
  - Peso predito (ARDSNet): homem 50 + 0,91 x (altura - 152,4); mulher 45,5 + 0,91 x (altura - 152,4). É a
    `V.pbw` do app calculadoras-uti. VC alvo: 6 a 8 ml/kg de peso predito.
  - Cockcroft-Gault: (140 - idade) x peso / (72 x creatinina), x 0,85 na mulher. Com o peso informado (real).
  - KDIGO pelo débito (média da janela): < 0,5 ml/kg/h em 6 h = 1; em 12 h = 2; < 0,3 ml/kg/h em 24 h = 3.
    Diurese zero não é estadiada (anúria e diurese não quantificada em fralda dão o mesmo zero na folha).
"""
import datetime as dt
import re

IDADE_SEXO = re.compile(r"^\s*(\d{1,3})\s*([MF])\b", re.I)
CR = re.compile(r"^\s*CR\s*:\s*(.+?)\s*mg/dl", re.I)
DATA = re.compile(r"^\s*(\d{1,2})/(\d{1,2})/(\d{4})\s*$")


def _num(v):
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).strip().replace(",", "."))
    except ValueError:
        return None


def data(txt):
    """'06/12/2025' -> date; outro formato -> None."""
    m = DATA.match(str(txt or ""))
    if not m:
        return None
    try:
        return dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None


def ler(leito):
    """{'kg', 'altura_cm', 'fonte', 'data'} do leito, ou None quando falta peso, fonte ou data."""
    p = leito.get("peso")
    if not isinstance(p, dict):
        return None
    kg = _num(p.get("kg"))
    fonte = p.get("fonte")
    d = data(p.get("data"))
    if not kg or kg <= 0 or not (isinstance(fonte, str) and fonte.strip() not in ("", "?")) or not d:
        return None
    alt = _num(p.get("altura_cm"))
    return {"kg": kg, "altura_cm": alt if alt and alt > 0 else None, "fonte": fonte.strip(), "data": f"{d:%d/%m/%Y}"}


def dias(p, hoje):
    """Idade do peso em dias na data do plantão."""
    d = data(p.get("data"))
    return (hoje - d).days if d and hoje else None


def idade_sexo(txt):
    """'90F' -> (90, 'F'); fora do formato -> (None, None)."""
    m = IDADE_SEXO.match(str(txt or ""))
    return (int(m.group(1)), m.group(2).upper()) if m else (None, None)


def peso_predito(sexo, altura_cm):
    return (50 if sexo == "M" else 45.5) + 0.91 * (altura_cm - 152.4)


def vc(pp):
    """VC alvo de 6 a 8 ml/kg de peso predito, em ml inteiros."""
    return round(6 * pp), round(8 * pp)


def clcr(idade, sexo, kg, cr):
    return (140 - idade) * kg / (72 * cr) * (0.85 if sexo == "F" else 1)


def creatinina(laboratorio):
    """(atual, anterior) da linha "CR: 1,4 => 1,5 mg/dl" (aceita também "->", das evoluções antigas) (formato do BRIEFING); sem a linha ou com o atual
    ilegível -> (None, None)."""
    for linha in laboratorio or []:
        for parte in str(linha).split("|"):
            m = CR.match(parte)
            if m:
                vals = [_num(x) for x in re.split(r"[-=]>", m.group(1))]
                if vals[-1] is None:  # atual ilegível ("1,4 => ?"): a da véspera não vale como atual
                    return None, None
                return vals[-1], (vals[-2] if len(vals) > 1 else None)
    return None, None


def imc(kg, altura_cm):
    return kg / (altura_cm / 100) ** 2


def debito(diurese_ml, horas, kg):
    return diurese_ml / horas / kg


def kdigo_debito(ml_kg_h, horas):
    """Estágio KDIGO pelo débito urinário médio da janela; sem critério -> None."""
    if horas >= 24 and ml_kg_h < 0.3:
        return 3
    if horas >= 12 and ml_kg_h < 0.5:
        return 2
    if horas >= 6 and ml_kg_h < 0.5:
        return 1
    return None
