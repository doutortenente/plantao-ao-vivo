#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
calc_hemo.py — Calculadora hemodinâmica determinística por ecocardiografia (UTI adulto)
========================================================================================
Comando Tático UCI — Dr. Nicolas. Zero erro aritmético: o LLM NÃO faz conta, este script faz.

REGRA DE OURO (zero alucinação):
  - Input ausente => derivado correspondente = None + entrada em `warnings`. NUNCA chuta.
  - ÚNICA estimativa autorizada: DIÂMETRO DA VSVE (LVOT), via fórmula validada (Leye 2009
    + recalibração para UTI de Cox/Wiersema 2022). Sempre marcado com flag `estimado: true`.

USO:
  echo '{"sexo":"M","peso":80,"altura":175,"lvot_vti_cm":18,"fc_bpm":92}' | python3 calc_hemo.py
  python3 calc_hemo.py --json '{"...": ...}'
  python3 calc_hemo.py --demo        # roda caso de validação interno

ENTRADA (JSON, todos os campos OPCIONAIS — decimal com ponto):
  Antropometria:
    sexo            "M" | "F"
    peso            kg
    altura          cm
    idade           anos
    sc_informada    m²  (se quiser sobrepor o cálculo de DuBois)
  VSVE / débito:
    lvot_diam_cm    cm  (diâmetro MEDIDO da VSVE; se ausente e antropometria presente => ESTIMA)
    lvot_vti_cm     cm  (VTI da via de saída do VE)
    fc_bpm          bpm
  Resistência:
    pam_mmhg        mmHg (pressão arterial média)
    pvc_mmhg        mmHg (PVC medida; se ausente, usa pad_estimada da VCI quando disponível)
  VD / pressão pulmonar:
    vrt_ms          m/s  (pico de velocidade do jato de regurgitação tricúspide)
    pad_mmhg        mmHg (PAD medida; se ausente, estima pela VCI)
  Veia cava inferior:
    vci_max_cm      cm
    vci_min_cm      cm
    ventilado       true|false  (true=VM passiva => distensibilidade; false=espontânea => colapsabilidade)
  Fluido-responsividade (Doppler aórtico, VM passiva, ritmo sinusal):
    vpeak_max_cms   cm/s
    vpeak_min_cms   cm/s
  Elevação passiva das pernas (PLR) — válida em FA/espontânea:
    vti_pre_cm      cm  (VTI VSVE basal)
    vti_post_cm     cm  (VTI VSVE após PLR / ou pós-expansão)
  Função diastólica:
    onda_e_cms      cm/s (E mitral, Doppler pulsado)
    e_linha_sept_cms cm/s (e' septal, Doppler tecidual)
    e_linha_lat_cms  cm/s (e' lateral, Doppler tecidual)
  Contexto (afeta apenas avisos, não cálculo):
    ritmo           "sinusal" | "fa" | "outro"

SAÍDA: JSON com debito{}, resistencia{}, pressao_pulmonar{}, vci{}, fluido_resp{},
       diastole{}, perfil_provavel, flags[], warnings[], fontes{}.

FONTES (ver references/01-formulas-cutoffs.md para detalhamento e citação):
  Quiñones 2002 (ASE Doppler) · Lang/Mitchell 2015 (ASE Chamber Quant) ·
  Leye 2009 (LVOT size-adjusted) · Cox/Wiersema 2022 (LVOT UTI) ·
  Feissel 2001 (ΔVpeak) · Barbier 2004 (dVCI) · Monnet 2005 (PLR) ·
  Nagueh 2016 (diastólica ASE/EACVI) · Rudski 2010 (VD/PAD) · Evans 2021 (SSC metas).
"""

import argparse
import json
import math
import sys

VERSION = "hemodinamica-calculada/calc_hemo/v1.0"


# ----------------------------------------------------------------------------- helpers
def _num(v):
    """Converte para float aceitando vírgula decimal BR; retorna None se vazio/inválido."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip().replace(",", ".")
        if s == "" or s.lower() in ("null", "none", "na", "n/a"):
            return None
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _r(v, n=2):
    """Arredonda mantendo None."""
    return None if v is None else round(v, n)


# ----------------------------------------------------------------------------- BSA
def bsa_dubois(peso_kg, altura_cm):
    """Superfície corporal (DuBois & DuBois, 1916), m²."""
    if peso_kg is None or altura_cm is None:
        return None
    return 0.007184 * (peso_kg**0.425) * (altura_cm**0.725)


# ----------------------------------------------------------------------------- LVOT estimate
def estimar_lvot_diam_cm(sc_m2, sexo):
    """
    Estimativa do diâmetro da VSVE (ÚNICA estimativa autorizada).
    Leye et al. 2009:  D_mm = 5.7 * BSA + 12.1   (validada p/ AVA, salvaguarda quando TTE difícil)
    Cox/Wiersema 2022: em UTI, Leye superestima +2.4 mm => intercepto ajustado p/ críticos.
    Retorna dict com leye_mm, icu_ajustado_mm (primário em UTI), mbsa_mm (referência cruzada), cm primário.
    """
    if sc_m2 is None:
        return None
    leye_mm = 5.7 * sc_m2 + 12.1
    icu_mm = leye_mm - 2.4  # recalibração UTI (Cox/Wiersema 2022, viés médio -2.4 mm)
    # mBSA capping (protocolo FREE / Murthi): SC<=1.8 ->1.8cm; 1.8-2.2 -> SC cm; >=2.2 ->2.2cm
    mbsa_cm = max(1.8, min(2.2, sc_m2))
    return {
        "leye_mm": round(leye_mm, 1),
        "icu_ajustado_mm": round(icu_mm, 1),
        "mbsa_referencia_mm": round(mbsa_cm * 10, 1),
        "diam_primario_cm": round(icu_mm / 10.0, 2),  # UTI usa o ajustado de Cox
        "sexo_nota": ("homem ~22mm / mulher ~20mm (Cox 2022)" if sexo else None),
    }


# ----------------------------------------------------------------------------- core calc
def calcular(inp):
    W = []  # warnings
    F = []  # flags clínicas
    out = {
        "$schema": VERSION,
        "antropometria": {},
        "debito": {},
        "resistencia": {},
        "pressao_pulmonar": {},
        "vci": {},
        "fluido_resp": {},
        "diastole": {},
        "perfil_provavel": None,
        "flags": F,
        "warnings": W,
    }

    # --- parse inputs
    sexo = (inp.get("sexo") or "").strip().upper() or None
    if sexo and sexo not in ("M", "F"):
        sexo = None
    peso = _num(inp.get("peso"))
    altura = _num(inp.get("altura"))
    idade = _num(inp.get("idade"))
    sc_inf = _num(inp.get("sc_informada"))
    lvot_d = _num(inp.get("lvot_diam_cm"))
    lvot_vti = _num(inp.get("lvot_vti_cm"))
    fc = _num(inp.get("fc_bpm"))
    pam = _num(inp.get("pam_mmhg"))
    pvc = _num(inp.get("pvc_mmhg"))
    vrt = _num(inp.get("vrt_ms"))
    pad = _num(inp.get("pad_mmhg"))
    vci_max = _num(inp.get("vci_max_cm"))
    vci_min = _num(inp.get("vci_min_cm"))
    ventilado = inp.get("ventilado")
    vpk_max = _num(inp.get("vpeak_max_cms"))
    vpk_min = _num(inp.get("vpeak_min_cms"))
    vti_pre = _num(inp.get("vti_pre_cm"))
    vti_post = _num(inp.get("vti_post_cm"))
    onda_e = _num(inp.get("onda_e_cms"))
    e_sept = _num(inp.get("e_linha_sept_cms"))
    e_lat = _num(inp.get("e_linha_lat_cms"))
    ritmo = (inp.get("ritmo") or "").strip().lower() or None

    # === BSA ===
    if sc_inf is not None:
        sc = sc_inf
        out["antropometria"]["sc_m2"] = _r(sc)
        out["antropometria"]["sc_fonte"] = "informada"
    else:
        sc = bsa_dubois(peso, altura)
        out["antropometria"]["sc_m2"] = _r(sc)
        out["antropometria"]["sc_fonte"] = "DuBois (peso+altura)" if sc else None
        if sc is None:
            W.append(
                "SC não calculada: faltam peso e/ou altura. IC/IS e estimativa de VSVE ficam bloqueados."
            )
    out["antropometria"]["peso_kg"] = peso
    out["antropometria"]["altura_cm"] = altura
    out["antropometria"]["sexo"] = sexo
    out["antropometria"]["idade"] = idade

    # === DIÂMETRO VSVE (medido > estimado) ===
    lvot_estimado = False
    if lvot_d is not None:
        diam = lvot_d
        out["debito"]["lvot_diam_cm"] = _r(diam)
        out["debito"]["lvot_diam_fonte"] = "MEDIDO"
        if not (1.5 <= diam <= 3.0):
            F.append(
                f"Diâmetro VSVE medido {diam} cm fora do esperado (1.5–3.0 cm) — revisar janela/medida."
            )
    else:
        est = estimar_lvot_diam_cm(sc, sexo)
        if est is not None:
            diam = est["diam_primario_cm"]
            lvot_estimado = True
            out["debito"]["lvot_diam_cm"] = diam
            out["debito"][
                "lvot_diam_fonte"
            ] = "ESTIMADO (Leye 2009 + ajuste UTI Cox/Wiersema 2022)"
            out["debito"]["lvot_diam_estimativa_detalhe"] = est
            W.append(
                "DIÂMETRO DA VSVE ESTIMADO (não medido). Erro do diâmetro é QUADRÁTICO no VS — "
                "tratar débito absoluto com cautela e priorizar TENDÊNCIA do VTI. "
                f"Leye bruto {est['leye_mm']}mm; ajustado-UTI {est['icu_ajustado_mm']}mm (usado); "
                f"mBSA(ref) {est['mbsa_referencia_mm']}mm."
            )
        else:
            diam = None
            out["debito"]["lvot_diam_cm"] = None
            out["debito"]["lvot_diam_fonte"] = None
            W.append(
                "Diâmetro VSVE ausente e não estimável (sem SC). VS/DC/IC bloqueados."
            )

    out["debito"]["lvot_estimado"] = lvot_estimado

    # === ÁREA VSVE ===  (π/4 · D² = 0.785 · D²)
    area = None
    if diam is not None:
        area = 0.785398 * diam**2
        out["debito"]["area_vsve_cm2"] = _r(area, 3)

    # === VOLUME SISTÓLICO / DÉBITO / ÍNDICES ===
    vs = dc = ic = isv = None
    out["debito"]["lvot_vti_cm"] = _r(lvot_vti)
    if area is not None and lvot_vti is not None:
        vs = area * lvot_vti  # mL
        out["debito"]["volume_sistolico_ml"] = _r(vs, 1)
        if not (20 <= vs <= 180):
            F.append(
                f"Volume sistólico {vs:.0f} mL fora do usual (20–180 mL) — revisar VTI/diâmetro."
            )
    else:
        if lvot_vti is None:
            W.append("VTI da VSVE ausente: VS/DC/IC não calculados.")
    if vs is not None and fc is not None:
        dc = vs * fc / 1000.0  # L/min
        out["debito"]["debito_cardiaco_lmin"] = _r(dc, 2)
    elif vs is not None and fc is None:
        W.append("FC ausente: DC/IC não calculados (VS disponível).")
    if sc:
        if vs is not None:
            isv = vs / sc  # mL/m²
            out["debito"]["indice_sistolico_ml_m2"] = _r(isv, 1)
        if dc is not None:
            ic = dc / sc  # L/min/m²
            out["debito"]["indice_cardiaco_lmin_m2"] = _r(ic, 2)

    # classificação do débito
    if ic is not None:
        if ic < 2.0:
            out["debito"]["classe_ic"] = "BAIXO (<2.0) — débito crítico"
            F.append("Índice cardíaco BAIXO (<2.0 L/min/m²).")
        elif ic < 2.5:
            out["debito"]["classe_ic"] = "limítrofe (2.0–2.5)"
        elif ic <= 4.0:
            out["debito"]["classe_ic"] = "normal (2.5–4.0)"
        else:
            out["debito"]["classe_ic"] = "ALTO (>4.0) — hiperdinâmico"
            F.append(
                "Índice cardíaco ALTO (>4.0) — padrão hiperdinâmico (pensar distributivo)."
            )
    # coerência VTI×FC (Blanco) quando não há diâmetro
    if lvot_vti is not None:
        if lvot_vti < 18:
            out["debito"][
                "nota_vti"
            ] = "VTI <18 cm: débito tende a baixo (checar volume/contratilidade)."
        elif lvot_vti > 22:
            out["debito"][
                "nota_vti"
            ] = "VTI >22 cm: débito tende a alto (pensar vasoplegia/hiperdinâmico)."
        else:
            out["debito"]["nota_vti"] = "VTI 18–22 cm: faixa normal."

    # === RESISTÊNCIA VASCULAR SISTÊMICA ===
    # estima PVC pela VCI se PVC não medida (usa pad estimada adiante)
    rvs = irvs = None
    pvc_uso = pvc
    pvc_fonte = "medida" if pvc is not None else None

    # === VCI / PAD ===
    pad_est = None
    if vci_max is not None and vci_min is not None:
        colaps = (
            (vci_max - vci_min) / vci_max * 100 if vci_max > 0 else None
        )  # colapsabilidade
        disten = (
            (vci_max - vci_min) / vci_min * 100 if vci_min > 0 else None
        )  # distensibilidade
        out["vci"]["vci_max_cm"] = _r(vci_max)
        out["vci"]["vci_min_cm"] = _r(vci_min)
        out["vci"]["colapsabilidade_pct"] = _r(colaps, 1)
        out["vci"]["distensibilidade_pct"] = _r(disten, 1)
        # PAD estimada (Rudski 2010): regra dicotômica diâmetro+colapso
        if vci_max <= 2.1 and (colaps is not None and colaps > 50):
            pad_est = 3
            out["vci"]["pad_estimada_mmhg"] = 3
            out["vci"]["pad_faixa"] = "0–5"
        elif vci_max > 2.1 and (colaps is not None and colaps < 50):
            pad_est = 15
            out["vci"]["pad_estimada_mmhg"] = 15
            out["vci"]["pad_faixa"] = "10–20"
        else:
            pad_est = 8
            out["vci"]["pad_estimada_mmhg"] = 8
            out["vci"]["pad_faixa"] = "5–10 (intermediário)"
        out["vci"]["pad_fonte"] = "estimada VCI (Rudski 2010)"
    elif vci_max is not None or vci_min is not None:
        W.append(
            "VCI incompleta (precisa máx E mín): índices de VCI e PAD estimada não calculados."
        )

    # PVC para RVS: usa medida; senão PAD medida; senão PAD estimada da VCI
    if pvc_uso is None:
        if pad is not None:
            pvc_uso = pad
            pvc_fonte = "PAD medida (substituta de PVC)"
        elif pad_est is not None:
            pvc_uso = pad_est
            pvc_fonte = "PAD estimada VCI (substituta de PVC)"

    if pam is not None and dc is not None and pvc_uso is not None:
        rvs = (pam - pvc_uso) / dc * 80.0
        out["resistencia"]["rvs_dynes_s_cm5"] = _r(rvs, 0)
        out["resistencia"]["formula"] = "(PAM - PVC)/DC × 80"
        out["resistencia"]["pvc_usada_mmhg"] = pvc_uso
        out["resistencia"]["pvc_fonte"] = pvc_fonte
        if ic is not None and ic > 0:
            irvs = (pam - pvc_uso) / ic * 80.0
            out["resistencia"]["irvs_dynes_s_cm5_m2"] = _r(irvs, 0)
        if rvs < 800:
            out["resistencia"]["classe"] = "BAIXA (<800) — vasoplegia/distributivo"
            F.append(
                "RVS BAIXA (<800) — perfil vasodilatado (pensar séptico/distributivo)."
            )
        elif rvs <= 1200:
            out["resistencia"]["classe"] = "normal (800–1200)"
        else:
            out["resistencia"]["classe"] = "ALTA (>1200) — vasoconstrição"
            F.append(
                "RVS ALTA (>1200) — vasoconstrição (hipovolemia/cardiogênico/frio)."
            )
        if pvc_fonte and "estimada" in pvc_fonte:
            W.append(
                "RVS calculada com PVC ESTIMADA pela VCI — valor semiquantitativo, use a tendência."
            )
    else:
        faltam = [
            n for n, v in (("PAM", pam), ("DC", dc), ("PVC/PAD", pvc_uso)) if v is None
        ]
        if faltam:
            W.append(f"RVS não calculada: faltam {', '.join(faltam)}.")

    # === PRESSÃO PULMONAR (PSAP) ===
    pad_para_psap = pad if pad is not None else pad_est
    if vrt is not None:
        if pad_para_psap is not None:
            psap = 4 * vrt**2 + pad_para_psap
            out["pressao_pulmonar"]["psap_mmhg"] = _r(psap, 0)
            out["pressao_pulmonar"][
                "formula"
            ] = "4×(VRT)² + PAD (Bernoulli simplificada)"
            out["pressao_pulmonar"]["vrt_ms"] = _r(vrt)
            out["pressao_pulmonar"]["pad_usada_mmhg"] = pad_para_psap
            out["pressao_pulmonar"]["pad_fonte"] = (
                "medida" if pad is not None else "estimada VCI"
            )
            if psap > 35:
                out["pressao_pulmonar"]["classe"] = "elevada (>35 mmHg)"
                F.append(
                    f"PSAP estimada {psap:.0f} mmHg — hipertensão pulmonar provável."
                )
            else:
                out["pressao_pulmonar"]["classe"] = "normal (≤35 mmHg)"
        else:
            W.append(
                "VRT presente mas sem PAD (medida ou via VCI): PSAP não calculada."
            )
    # gradiente VD-AD isolado (sem PAD) ainda é informativo
    if vrt is not None:
        out["pressao_pulmonar"]["gradiente_vd_ad_mmhg"] = _r(4 * vrt**2, 0)

    # === FLUIDO-RESPONSIVIDADE ===
    fr = out["fluido_resp"]
    respondedor_flags = []
    # ΔVpeak aórtico (Feissel >12%)
    if vpk_max is not None and vpk_min is not None and (vpk_max + vpk_min) > 0:
        dvpeak = 100 * (vpk_max - vpk_min) / ((vpk_max + vpk_min) / 2)
        fr["delta_vpeak_pct"] = _r(dvpeak, 1)
        fr["delta_vpeak_cutoff"] = ">12% sugere resposta a volume (Feissel 2001)"
        fr["delta_vpeak_responsivo"] = dvpeak > 12
        respondedor_flags.append(("ΔVpeak", dvpeak > 12))
    # dVCI / cVCI
    if "distensibilidade_pct" in out["vci"] or "colapsabilidade_pct" in out["vci"]:
        if ventilado is True and out["vci"].get("distensibilidade_pct") is not None:
            d = out["vci"]["distensibilidade_pct"]
            fr["vci_distensibilidade_pct"] = d
            fr["vci_cutoff"] = ">18% sugere resposta (Barbier 2004, VM passiva)"
            fr["vci_responsivo"] = d > 18
            respondedor_flags.append(("dVCI", d > 18))
        elif ventilado is False and out["vci"].get("colapsabilidade_pct") is not None:
            c = out["vci"]["colapsabilidade_pct"]
            fr["vci_colapsabilidade_pct"] = c
            fr["vci_cutoff"] = ">40–50% sugere resposta (respiração espontânea)"
            fr["vci_responsivo"] = c > 42
            respondedor_flags.append(("cVCI", c > 42))
        elif ventilado is None:
            W.append(
                "Campo 'ventilado' ausente: não dá pra escolher distensibilidade (VM) vs colapsabilidade (espontâneo) da VCI."
            )
    # PLR / pós-expansão (Monnet ≥10%)
    if vti_pre is not None and vti_post is not None and vti_pre > 0:
        dvti = 100 * (vti_post - vti_pre) / vti_pre
        fr["delta_vti_plr_pct"] = _r(dvti, 1)
        fr["delta_vti_plr_cutoff"] = (
            "≥10% = responsivo (Monnet 2005; válido em FA/espontânea)"
        )
        fr["delta_vti_plr_responsivo"] = dvti >= 10
        respondedor_flags.append(("PLR-ΔVTI", dvti >= 10))

    if respondedor_flags:
        pos = [n for n, r in respondedor_flags if r]
        neg = [n for n, r in respondedor_flags if not r]
        if pos and not neg:
            fr["sintese"] = f"RESPONSIVO a volume ({', '.join(pos)} positivos)."
        elif neg and not pos:
            fr["sintese"] = (
                f"NÃO responsivo a volume ({', '.join(neg)} negativos) — fluido provavelmente fútil/danoso."
            )
        else:
            fr["sintese"] = (
                f"DISCORDANTE: positivos [{', '.join(pos)}] vs negativos [{', '.join(neg)}] — priorizar PLR/teste dinâmico."
            )

    # === DIÁSTOLE / E/e' ===
    if onda_e is not None and (e_sept is not None or e_lat is not None):
        es = [x for x in (e_sept, e_lat) if x is not None]
        e_media = sum(es) / len(es)
        ee = onda_e / e_media
        out["diastole"]["e_sobre_elinha"] = _r(ee, 1)
        out["diastole"]["e_linha_base"] = (
            "média sept+lat"
            if len(es) == 2
            else ("septal" if e_sept is not None else "lateral")
        )
        out["diastole"][
            "cutoff"
        ] = "E/e' médio >14 sugere pressão de enchimento VE elevada (Nagueh 2016)"
        if ee > 14:
            out["diastole"][
                "interpretacao"
            ] = "pressão de enchimento do VE ELEVADA (>14)"
            F.append("E/e' >14 — pressão de enchimento do VE elevada (congestão).")
        elif ee < 8:
            out["diastole"]["interpretacao"] = "pressão de enchimento normal (<8)"
        else:
            out["diastole"][
                "interpretacao"
            ] = "zona cinzenta (8–14) — integrar VAEi, VRT, e'"
    elif onda_e is not None:
        W.append("Onda E presente sem e' (septal/lateral): E/e' não calculado.")

    # === PERFIL HEMODINÂMICO INTEGRADO (heurística de apoio, não substitui exame) ===
    perfil = _classificar_perfil(out, ventilado)
    out["perfil_provavel"] = perfil

    # fontes (para citação na nota)
    out["fontes"] = {
        "debito_vti": "Quiñones 2002 (ASE Doppler); Lang/Mitchell 2015 (ASE Chamber Quant)",
        "estimativa_lvot": "Leye 2009 (JASE 22:445); Cox/Wiersema 2022 (J Intensive Care 10:31)",
        "fluido_resp": "Feissel 2001 (Chest 119:867); Barbier 2004 (ICM 30:1740); Monnet 2005 (ICM 31:1195)",
        "diastole": "Nagueh 2016 (JASE 29:277)",
        "vd_pad_psap": "Rudski 2010 (JASE 23:685)",
        "metas": "Evans 2021 (Surviving Sepsis Campaign, CCM 49:e1063)",
    }
    return out


def _classificar_perfil(out, ventilado):
    """Heurística de perfil de choque combinando IC, RVS, VCI, fluido-resp.
    Retorna string descritiva + grau de confiança. NÃO é diagnóstico — é apoio."""
    ic = out["debito"].get("indice_cardiaco_lmin_m2")
    classe_ic = out["debito"].get("classe_ic", "")
    rvs = out["resistencia"].get("rvs_dynes_s_cm5")
    classe_rvs = out["resistencia"].get("classe", "")
    fr = out["fluido_resp"].get("sintese", "")
    vci_pad = out["vci"].get("pad_estimada_mmhg")

    sinais = []
    # Distributivo: IC alto/normal + RVS baixa
    if (ic is not None and ic > 3.5) and (rvs is not None and rvs < 800):
        sinais.append(
            "DISTRIBUTIVO/vasoplégico (IC alto + RVS baixa) — vasopressor 1ª linha (noradrenalina)"
        )
    # Cardiogênico: IC baixo + RVS alta + VCI pletórica
    if (ic is not None and ic < 2.2) and (rvs is not None and rvs > 1200):
        sinais.append(
            "CARDIOGÊNICO (IC baixo + RVS alta) — inotrópico ± reduzir afterload; cuidado com volume"
        )
    # Hipovolêmico: VCI colapsável + responsivo + RVS alta
    if ("RESPONSIVO" in fr and "NÃO" not in fr) and (
        vci_pad == 3 or (rvs is not None and rvs > 1200)
    ):
        sinais.append(
            "HIPOVOLÊMICO provável (responsivo a volume + VCI colapsável/RVS alta) — expandir e reavaliar"
        )
    # Obstrutivo: VCI pletórica fixa sem IC alto (PSAP alta / VD) — sinal indireto
    psap = out["pressao_pulmonar"].get("psap_mmhg")
    if vci_pad == 15 and psap is not None and psap > 40 and (ic is None or ic < 2.5):
        sinais.append(
            "Considerar OBSTRUTIVO (VCI pletórica + PSAP alta) — investigar TEP/cor pulmonale/tamponamento no eco"
        )

    if not sinais:
        return "Indeterminado pelos dados numéricos — integrar com achados qualitativos do eco (contratilidade, VD, derrame)."
    return " | ".join(sinais)


# ----------------------------------------------------------------------------- demo
def _demo():
    """Caso de validação: homem 80kg/175cm, VTI 18, FC 92, diâmetro estimado, VCI 2.4/1.9 ventilado,
    PAM 65, VRT 2.9, E 90, e'sept 6, e'lat 8."""
    caso = {
        "sexo": "M",
        "peso": 80,
        "altura": 175,
        "idade": 60,
        "lvot_vti_cm": 18,
        "fc_bpm": 92,
        "pam_mmhg": 65,
        "vrt_ms": 2.9,
        "vci_max_cm": 2.4,
        "vci_min_cm": 1.9,
        "ventilado": True,
        "onda_e_cms": 90,
        "e_linha_sept_cms": 6,
        "e_linha_lat_cms": 8,
        "ritmo": "sinusal",
    }
    return calcular(caso)


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(
        description="Calculadora hemodinâmica por ecocardiografia (UTI)."
    )
    ap.add_argument("--json", help="String JSON de entrada.")
    ap.add_argument(
        "--demo", action="store_true", help="Roda caso de validação interno."
    )
    args = ap.parse_args()

    if args.demo:
        print(json.dumps(_demo(), ensure_ascii=False, indent=2))
        return

    raw = args.json
    if not raw:
        raw = sys.stdin.read()
    raw = (raw or "").strip()
    if not raw:
        print(
            json.dumps(
                {"erro": "entrada vazia: forneça JSON via stdin ou --json"},
                ensure_ascii=False,
            )
        )
        sys.exit(1)
    try:
        inp = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"erro": f"JSON inválido: {e}"}, ensure_ascii=False))
        sys.exit(1)

    result = calcular(inp)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
