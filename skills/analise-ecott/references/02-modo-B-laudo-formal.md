# 📋 MODO B — Laudo de Ecocardiograma Transtorácico Formal

Dados quantitativos do ecocardiografista. Precisão alta. Extraia **somente o que está no laudo** — campo ausente = "não
consta no laudo", nunca inventado.

---

## 1. Função sistólica do VE

### FEVE — Simpson biplano (método dos discos)

Padrão-ouro de superfície. Endocárdio traçado em diástole e sístole nas apical 4C e 2C, excluindo músculos papilares.

**Valores normais (ASE/EACVI 2015):**

- FEVE normal: **53–73%** (homens 52–72%; mulheres 54–74%)
- **FEVE <52% (H) / <54% (M) = disfunção sistólica**
- Reduzida 41–51% leve · 30–40% moderada · **<30% grave → RED FLAG**

**Volumes indexados:**

- VDF indexado normal até 74 mL/m² (H) / 61 mL/m² (M)
- VSF indexado normal até 31 mL/m² (H) / 24 mL/m² (M)

**Teichholz:** NÃO usar quando há alterações segmentares (assume geometria simétrica — limitação maior). Se o laudo só
traz Teichholz em paciente com IAM/segmentar, sinalize a limitação.

**Strain longitudinal global (GLS):** detecta disfunção subclínica com FEVE ainda normal. Normal mais negativo que −18%
a −20%; menos negativo = pior.

**Fonte:** Lang RM, Badano LP, Mor-Avi V, et al. ASE/EACVI Chamber Quantification. J Am Soc Echocardiogr 2015;28:1-39.

---

## 2. Função diastólica — Algoritmo ASE/EACVI 2016 (Nagueh)

### Passo 1 (FEVE normal) — 4 variáveis

1. e' septal **<7 cm/s** OU e' lateral **<10 cm/s**
2. E/e' médio **>14**
3. Velocidade de RT **>2,8 m/s**
4. Volume do AE indexado (VAEi) **>34 mL/m²**

→ **<50% positivos** = diástole normal · **=50%** = indeterminado · **>50%** = disfunção diastólica

### Passo 2 — graduação / pressão de enchimento

- **Grau I** (relaxamento prejudicado): E/A <0,8 + E ≤50 cm/s → pressão de enchimento **normal**
- **Grau II** (pseudonormal): E/A 0,8–2,0 com ≥2 critérios positivos → pressão **elevada**
- **Grau III** (restritivo): E/A >2,0 → pressão **elevada**

**Limitação:** correlação modesta com PCP invasiva (r ~0,17–0,46); ~30% indeterminados em alguns estudos. Útil, não
substitui cateter em casos complexos.

**Fonte:** Nagueh SF et al. ASE/EACVI Diastolic Function. J Am Soc Echocardiogr 2016;29:277-314.

---

## 3. Ventrículo direito e acoplamento VD–AP

- **TAPSE** <17 mm → disfunção
- **S' tricúspide** <9,5 cm/s → disfunção
- **FAC** (variação fracional de área) <35% → disfunção
- **RIMP/Tei** >0,40 (pulsado) ou >0,55 (tecidual) → disfunção global do VD
- **TAPSE/PSAP <0,36 mm/mmHg** = desacoplamento VD–AP (pior prognóstico em IC/HP)
- **Sinal 60/60** (TAcel pulmonar <60 ms + gradiente RT <60 mmHg) → cor pulmonale agudo/TEP

**Fonte:** Rudski LG et al. ASE Right Heart. J Am Soc Echocardiogr 2010;23:685-713.

---

## 4. Pressão pulmonar

```
PSAP = 4 × (VRT)² + PAD
```

- PSAP normal ≤35 mmHg
- PAD pela VCI (tabela 3/8/15 mmHg — ver `01-modo-A-pocus.md` ou skill hemodinamica-calculada)
- Pressão média de AP e pressão diastólica de AP podem constar no laudo formal

---

## 5. Valvas (impacto no cálculo de débito)

⚠️ **Estenose aórtica (EA) e insuficiência aórtica (IAo) significativas invalidam o método VTI de débito pela VSVE.** Se
o laudo descreve EA/IAo relevante, NÃO reporte DC por VSVE com falsa precisão — sinalize a limitação.

- **EA:** gradiente médio, AVA, velocidade máxima — graus leve/moderado/grave
- **IM/IT:** grau (leve/moderada/grave), por área de jato/PISA/vena contracta
- **SAM:** se presente → ver red flag de obstrução dinâmica (`03-red-flags.md`)

---

## 6. RVS e perfil (laudo + invasivo)

```
RVS = (PAM − PVC)/DC × 80   [800–1200 normal]
```

Quando o laudo formal traz DC por VTI confiável, a `hemodinamica-calculada` fecha RVS e perfil. PVC: invasiva se houver
cateter, senão estimada pela VCI (semiquantitativa).

---

## Síntese MODO B — o que o laudo formal entrega

1. **Quantificação precisa** da FEVE (Simpson) e volumes indexados
2. **Diástole graduada** (algoritmo Nagueh 2016) com pressão de enchimento
3. **VD completo** (TAPSE, S', FAC, RIMP, acoplamento)
4. **Valvopatias graduadas** — incluindo as que quebram o método VTI
5. **PSAP medida** pelo jato tricúspide

Confiança quantitativa, mas com latência. Combine com o POCUS do plantão para a foto hemodinâmica completa.
