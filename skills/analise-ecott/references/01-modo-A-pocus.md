# 🔬 MODO A — POCUS / Ultrassom Point-of-Care à Beira-Leito

Medidas que o **próprio intensivista** pega. Natureza qualitativa/semiquantitativa — velocidade sobre precisão. Sempre
marque "(POCUS)" no número e, em dúvida diagnóstica, recomende eco formal.

---

## 1. Função sistólica do VE — estimativa rápida

### Olhômetro (eyeball)

Estimativa visual da FEVE por operador treinado concorda bem com Simpson (diferença média <2%). Categorize:

- **Hiperdinâmico** (>70%): cavidade quase oblitera na sístole ("kissing walls") → pensar hipovolemia/vasoplegia
- **Normal** (52–72%)
- **Reduzido** (~35–50%)
- **Gravemente reduzido** (<35%) → RED FLAG

### EPSS (separação septo–ponto E) — M-mode em PLAX

Distância entre o ponto E da mitral (abertura máxima) e o septo interventricular.

- **EPSS >7 mm → FEVE reduzida (<50%)**
- **EPSS ≥13 mm → FEVE gravemente reduzida (<35%)**
- **Invalidado por:** estenose mitral, insuficiência aórtica (jato empurra o folheto), HVE grave.

**Fonte:** McKaigney CJ et al. Am J Emerg Med 2014;32:493-497.

### MAPSE (excursão do plano anular mitral) — adjunto

- Normal >10 mm; <8 mm sugere disfunção sistólica longitudinal.

---

## 2. Débito — VTI da VSVE (à beira-leito)

Mesma fórmula da skill `hemodinamica-calculada`. À beira-leito o intensivista pega o **VTI** (apical 5C, Doppler
pulsado) e, em geral, **estima o diâmetro** (a skill faz isso por Leye-Cox).

- VTI normal: **18–22 cm**
- **VTI <18 cm** → débito tende baixo (volume/contratilidade)
- **VTI >22 cm** → débito tende alto (vasoplegia/hiperdinâmico)
- A **tendência do VTI** seriado é o ouro do POCUS — mais confiável que DC absoluto.

→ Para o cálculo, invoque `hemodinamica-calculada`.

---

## 3. Volume — Veia Cava Inferior (VCI)

Medir 1–2 cm distal à junção com o AD (ou logo caudal às veias hepáticas), longitudinal subcostal, M-mode ou B.

```
Colapsabilidade (espontâneo)  = (máx − mín)/máx × 100
Distensibilidade (ventilado)  = (máx − mín)/mín × 100
```

- VCI <2,1 cm + colapso >50% → PAD baixa (~3 mmHg), tende a responsivo
- VCI >2,1 cm + colapso <50% → PAD alta (~15 mmHg)
- **Cutoffs de fluido-resp:** dVCI >18% (ventilado, Barbier) · cVCI >40–50% (espontâneo)

**Armadilhas:** PEEP alto, pressão intra-abdominal alta, VD insuficiente, volume corrente baixo, respiração espontânea
ativa degradam a acurácia. **VCI pletórica fixa do tamponamento/cor pulmonale NÃO é hipervolemia** — é red flag.

---

## 4. Função do VD — POCUS

- **TAPSE** (M-mode no anel tricúspide lateral, apical 4C focada no VD): normal **>17 mm**; **<17 mm = disfunção de
  VD**.
- **S' tricúspide** (Doppler tecidual): normal **>9,5 cm/s**.
- **Relação VD/VE** (apical 4C, diástole): normal ~0,67; **>0,9–1,0 = dilatação patológica** → pensar sobrecarga aguda
  (TEP) ou crônica.

---

## 5. Pressão pulmonar — POCUS

```
PSAP = 4 × (VRT)² + PAD
```

- VRT = pico do jato de regurgitação tricúspide (Doppler contínuo, m/s)
- PAD estimada pela VCI
- PSAP >35 mmHg → hipertensão pulmonar provável

→ Cálculo na `hemodinamica-calculada`.

---

## 6. Diástole simplificada — E/e' (POCUS)

- E (Doppler pulsado, ponta dos folhetos mitrais) / e' (Doppler tecidual anular septal e/ou lateral)
- **E/e' médio >14 → pressão de enchimento do VE elevada** (congestão)
- e' septal <7 cm/s ou lateral <10 cm/s → disfunção diastólica

---

## 7. Fluido-responsividade rápida

- **Elevação passiva das pernas (PLR)** + remedir VTI: **ΔVTI ≥10% = responsivo**. Válido em FA e respiração
  espontânea — o teste mais robusto à beira-leito.
- **ΔVpeak aórtico >12%** (VM passiva, sinusal).
- **Distensibilidade da VCI >18%** (ventilado).

---

## Síntese MODO A — o que o POCUS responde em 2 minutos

1. **A bomba funciona?** (eyeball/EPSS da FEVE)
2. **O tanque está cheio ou vazio?** (VCI + responsividade)
3. **O VD aguenta?** (TAPSE, VD/VE)
4. **Tem ameaça imediata?** (red flags — ver `03-red-flags.md`)

Tudo semiquantitativo. A força do POCUS é a **tendência** e a **triagem**, não o valor de bula. Precisão fina → eco
formal (MODO B).
