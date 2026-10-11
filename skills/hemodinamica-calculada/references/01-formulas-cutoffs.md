# 📐 Fórmulas, Cutoffs e Dicionário de Inputs

Tudo que o motor `calc_hemo.py` calcula, com equação exata, valor normal, cutoff de decisão e fonte primária. **Zero
alucinação**: o que não está aqui, o script não inventa.

---

## Dicionário de inputs (JSON de entrada)

Todos OPCIONAIS. Decimal com ponto ou vírgula. Campo ausente = não calcula o derivado correspondente.

| Campo                                  | Unidade                | Alimenta                                                      |
| -------------------------------------- | ---------------------- | ------------------------------------------------------------- |
| `sexo`                                 | "M"/"F"                | nota da estimativa de VSVE                                    |
| `peso`                                 | kg                     | SC (DuBois) → IC, IS, estimativa VSVE                         |
| `altura`                               | cm                     | SC (DuBois)                                                   |
| `idade`                                | anos                   | contexto                                                      |
| `sc_informada`                         | m²                     | sobrepõe DuBois                                               |
| `lvot_diam_cm`                         | cm                     | área VSVE → VS (MEDIDO tem prioridade)                        |
| `lvot_vti_cm`                          | cm                     | VS (com área)                                                 |
| `fc_bpm`                               | bpm                    | DC                                                            |
| `pam_mmhg`                             | mmHg                   | RVS, PSAP indireto                                            |
| `pvc_mmhg`                             | mmHg                   | RVS (se ausente, usa PAD)                                     |
| `vrt_ms`                               | m/s                    | PSAP, gradiente VD-AD                                         |
| `pad_mmhg`                             | mmHg                   | PSAP, RVS (se PVC ausente)                                    |
| `vci_max_cm` / `vci_min_cm`            | cm                     | colapsabilidade, distensibilidade, PAD estimada               |
| `ventilado`                            | true/false             | escolhe distensibilidade (VM) vs colapsabilidade (espontâneo) |
| `vpeak_max_cms` / `vpeak_min_cms`      | cm/s                   | ΔVpeak (fluido-resp)                                          |
| `vti_pre_cm` / `vti_post_cm`           | cm                     | ΔVTI por PLR (fluido-resp)                                    |
| `onda_e_cms`                           | cm/s                   | E/e'                                                          |
| `e_linha_sept_cms` / `e_linha_lat_cms` | cm/s                   | E/e'                                                          |
| `ritmo`                                | "sinusal"/"fa"/"outro" | avisos                                                        |

---

## 1. Superfície Corporal (SC / BSA)

**Fórmula (DuBois & DuBois 1916):**

```
SC (m²) = 0.007184 × peso(kg)^0.425 × altura(cm)^0.725
```

---

## 2. Débito Cardíaco pela VSVE (método VTI)

```
Área VSVE (cm²) = π × (D/2)²  =  0.785 × D²        [D = diâmetro VSVE em cm]
Volume Sistólico VS (mL)      = Área VSVE × VTI VSVE(cm)
Débito Cardíaco DC (L/min)    = VS × FC / 1000
Índice Cardíaco IC (L/min/m²) = DC / SC
Índice Sistólico IS (mL/m²)   = VS / SC
```

**Valores de referência:**

- VTI VSVE: **18–22 cm** (média ~20 ± 3) com FC 55–95 bpm
- VS: **60–100 mL**
- DC: **4–8 L/min**
- IC: **2,5–4,0 L/min/m²** (BAIXO <2,0 crítico; ALTO >4,0 hiperdinâmico)
- IS: **35–65 mL/m²**

**Como obter (resumo — detalhe na analise-ecott):** diâmetro em PLAX zoom, meio-sístole, inner-edge to inner-edge, 0,5–1
cm proximal ao ânulo aórtico. VTI em apical 5C, Doppler pulsado, amostra no MESMO nível do diâmetro, ângulo <20°. FA →
média de 3–5 ciclos.

**Fonte:** Quiñones MA et al. ASE Doppler Quantification. J Am Soc Echocardiogr 2002;15:167-184. Lang/Mitchell et al.
ASE Chamber Quantification 2015;28:1-39.

---

## 3. Resistência Vascular Sistêmica (RVS)

```
RVS  (dynes·s·cm⁻⁵)     = (PAM − PVC) / DC × 80
IRVS (dynes·s·cm⁻⁵·m²)  = (PAM − PVC) / IC × 80
```

- Normal RVS: **800–1200** (BAIXA <800 = vasoplegia/distributivo; ALTA >1200 = vasoconstrição)
- Conversão: 1 unidade Wood = 80 dynes·s·cm⁻⁵
- PVC: se medida, usa; senão usa PAD medida; senão PAD estimada da VCI → **RVS semiquantitativa** (tendência, não bula)

**Fonte:** convenção fisiológica padrão; estimativa de PVC pela VCI per Rudski 2010.

---

## 4. Pressão Sistólica da Artéria Pulmonar (PSAP)

```
Gradiente VD-AD (mmHg) = 4 × (VRT)²              [VRT = pico do jato de regurg. tricúspide, m/s]
PSAP (mmHg)            = 4 × (VRT)² + PAD         [Bernoulli simplificada]
```

- Normal PSAP: **≤35 mmHg** (elevada >35)
- PAD: medida, ou estimada pela VCI (ver item 5)

**Fonte:** Rudski LG et al. ASE Right Heart. J Am Soc Echocardiogr 2010;23:685-713.

---

## 5. PAD estimada pela VCI (Rudski 2010)

| VCI máx       | Colapsabilidade | PAD estimada | Faixa |
| ------------- | --------------- | ------------ | ----- |
| ≤2,1 cm       | >50%            | **3 mmHg**   | 0–5   |
| >2,1 cm       | <50%            | **15 mmHg**  | 10–20 |
| intermediário | —               | **8 mmHg**   | 5–10  |

```
Colapsabilidade cVCI (%)  = (VCImáx − VCImín) / VCImáx × 100
Distensibilidade dVCI (%) = (VCImáx − VCImín) / VCImín × 100
```

---

## 6. Fluido-responsividade

### 6a. Variação respiratória da velocidade aórtica (ΔVpeak) — VM passiva, ritmo sinusal

```
ΔVpeak (%) = 100 × (Vpeak_máx − Vpeak_mín) / [(Vpeak_máx + Vpeak_mín)/2]
```

- **Cutoff >12% = responsivo** (Feissel 2001: S 100% / E 89% em choque séptico ventilado)
- Alternativa >13% (Monnet 2005, AUROC 0,82)

### 6b. VCI

- **Ventilado (passivo):** distensibilidade **dVCI >18% = responsivo** (Barbier 2004: S 90% / E 90%)
- **Espontâneo:** colapsabilidade **cVCI >40–50% = responsivo**

### 6c. Elevação passiva das pernas (PLR) / pós-expansão — válido em FA e espontânea

```
ΔVTI (%) = 100 × (VTI_pós − VTI_pré) / VTI_pré
```

- **Cutoff ≥10% = responsivo** (Monnet 2005). Equivale a autotransfusão reversível ~300 mL.

**Limitações (o motor avisa, a nota reforça):** ΔVpeak e dVCI exigem VM controlada + sinusal + volume corrente ≥8 mL/kg;
PEEP alto, pressão intra-abdominal alta e VD insuficiente degradam a VCI. Em dúvida → PLR.

**Fontes:** Feissel M et al. Chest 2001;119:867-873. Barbier C et al. Intensive Care Med 2004;30:1740-1746. Monnet X et
al. Intensive Care Med 2005;31:1195-1201.

---

## 7. Função diastólica — E/e'

```
E/e' = E (Doppler pulsado mitral) / e' (Doppler tecidual anular)
e' base = média septal+lateral (ou o disponível)
```

- **E/e' médio >14 → pressão de enchimento do VE ELEVADA**
- <8 → normal; 8–14 → zona cinzenta (integrar VAEi >34 mL/m², VRT >2,8 m/s, e' sept <7 / lat <10 cm/s)

**Fonte:** Nagueh SF et al. ASE/EACVI Diastolic Function. J Am Soc Echocardiogr 2016;29:277-314.

---

## Resumo dos cutoffs de decisão (cola rápida)

| Parâmetro  | Normal           | Decisão                               |
| ---------- | ---------------- | ------------------------------------- |
| IC         | 2,5–4,0 L/min/m² | <2,0 baixo débito; >4,0 hiperdinâmico |
| RVS        | 800–1200         | <800 vasoplegia; >1200 vasoconstrição |
| PSAP       | ≤35 mmHg         | >35 HP provável                       |
| ΔVpeak     | —                | >12% responsivo (VM/sinusal)          |
| dVCI       | —                | >18% responsivo (VM)                  |
| cVCI       | —                | >40–50% responsivo (espontâneo)       |
| ΔVTI PLR   | —                | ≥10% responsivo (universal)           |
| E/e' médio | <8               | >14 enchimento elevado                |
| PAD (VCI)  | 3 / 8 / 15       | conforme diâmetro+colapso             |
