# 🚨 Sanity Checks Clínicos — Zero-Hallucination Validation

Toda extração passa por esta malha. Campo fora da malha → `requires_review: true` + warning.

**Princípio não-negociável:** a malha NÃO corrige o valor. Apenas sinaliza. O médico decide. O sistema não é responsável
por "melhorar" o que o OCR leu — é responsável por **gritar** quando o valor é clinicamente implausível.

---

## 🫁 Respiratório

| Parâmetro | Range fisiológico | Flag se                    | Ação                                            |
| --------- | ----------------- | -------------------------- | ----------------------------------------------- |
| SpO2      | 0–100%            | `> 100`                    | `physiological_error` — impossível              |
| SpO2      | 0–100%            | `< 40 e paciente vivo`     | `review` — provável erro de leitura             |
| FR        | 4–80 ipm          | `> 60`                     | `review` — compatível mas extremo               |
| PaO2      | 20–600 mmHg       | `> 600` sem VM + alta FiO2 | `review`                                        |
| FiO2      | 21–100%           | `< 21 ou > 100`            | `physiological_error`                           |
| P/F ratio | 50–500+           | `> 500`                    | `review`                                        |
| pH        | 6,80–7,80         | fora desse intervalo       | `physiological_error` — incompatível com a vida |
| pCO2      | 10–150 mmHg       | `> 150`                    | `review`                                        |
| HCO3      | 4–50 mEq/L        | fora                       | `review`                                        |
| Lactato   | 0,5–25 mmol/L     | `> 20`                     | `review` — mortalidade >90%                     |

**Coerência gaso**: se `pH` normal mas `pCO2 > 60` e `HCO3 < 20` → provavelmente OCR trocou dígitos, flagar.

---

## 🫀 Hemodinâmico

| Parâmetro     | Range       | Flag se            | Ação                                                                 |
| ------------- | ----------- | ------------------ | -------------------------------------------------------------------- |
| PA sistólica  | 40–280 mmHg | fora               | `physiological_error`                                                |
| PA diastólica | 20–160 mmHg | fora               | `physiological_error`                                                |
| PAM           | 30–180 mmHg | fora               | `physiological_error`                                                |
| FC            | 20–250 bpm  | fora               | `physiological_error`                                                |
| FC            | 30–220      | sinusal sustentado | ok                                                                   |
| Temperatura   | 32–42°C     | `< 32 ou > 42`     | `physiological_error` ou hipotermia terapêutica (verificar contexto) |

**Coerência PA**: `pa_dia > pa_sys` → inverter? NÃO. Marcar `flag: data_inversion_suspected` e retornar ambos como
estão. **Coerência PAM**: `PAM ≈ (PAS + 2·PAD) / 3`. Se o valor extraído diverge do calculado em > 15 mmHg, marcar
`review`.

---

## 💧 Renal / BH

| Parâmetro   | Range              | Flag se      | Ação                                 |           |                   |
| ----------- | ------------------ | ------------ | ------------------------------------ | --------- | ----------------- |
| Diurese 24h | 0–10 000 mL        | `> 8000`     | `review` — provável poliúria ou erro |           |                   |
| Diurese 24h | 0–10 000           | `= 0`        | ok, oligúria severa / anúria         |           |                   |
| mL/kg/h     | 0–15               | `< 0,3`      | KDIGO 1 (flag automático, não erro)  |           |                   |
| BH 24h      | −8000 a +12 000 mL | `            | bh                                   | > 10 000` | `logical_anomaly` |
| Creatinina  | 0,1–20 mg/dL       | `> 15`       | `review` — checar unidade (µmol/L?)  |           |                   |
| Ureia       | 5–400 mg/dL        | `> 300`      | `review`                             |           |                   |
| Na          | 110–180 mEq/L      | fora         | `review`                             |           |                   |
| K           | 1,5–9,5 mEq/L      | `> 8 ou < 2` | `review` — risco arritmia imediata   |           |                   |

---

## 🩸 Hematologia

| Parâmetro         | Range           | Flag se                        | Ação                                          |
| ----------------- | --------------- | ------------------------------ | --------------------------------------------- |
| Hb                | 2–22 g/dL       | `< 3 ou > 20`                  | `review`                                      |
| Leucócitos        | 0,1–100 ×10³/µL | `> 80`                         | `review` — leucemóide vs erro                 |
| Plaquetas         | 1–2000 ×10³/µL  | `< 10`                         | ok (trombocitopenia severa), mas flag `alert` |
| Plaquetas unidade | —               | valor 1 000–10 000 sem unidade | `plaq_unit_ambiguous`                         |
| INR               | 0,8–10          | `> 8`                          | `review`                                      |

---

## 💊 DVAs e dose máxima razoável

Não são limites absolutos — são **red flags** que sugerem erro de OCR/diluição.

| Droga         | Dose razoável       | Flag se | Racional                                                       |
| ------------- | ------------------- | ------- | -------------------------------------------------------------- |
| Noradrenalina | 0,01–2,0 mcg/kg/min | `> 2,0` | doses acima sugerem diluição errada; marcar `dose_absurd_high` |
| Adrenalina    | 0,01–2,0 mcg/kg/min | `> 2,0` | idem                                                           |
| Dobutamina    | 2–20 mcg/kg/min     | `> 30`  | idem                                                           |
| Vasopressina  | 0,01–0,06 UI/min    | `> 0,1` | idem (dose fixa, não titulada)                                 |
| Dopamina      | 1–20 mcg/kg/min     | `> 30`  | idem                                                           |

Dose **absurda baixa** (Nor `< 0,001`): provável erro de vírgula; flagar `dose_absurd_low`.

Use `calcDoseInfusao` de `src/lib/calculations/infusao.ts` para o cálculo real a partir de vazão + diluição + peso.

---

## 🔗 Incompatibilidades clínicas que disparam alerta

### Droga VO com SNE

Se prescrição tem `via: Oral` E paciente tem `SNE` documentada → flag `clinical_incompatibility`.

**Exceções** (podem ser trituradas e dadas por SNE):

- Paracetamol, dipirona, omeprazol (cápsulas NÃO, comprimidos sim), metformina, captopril.

**Nunca pode SNE** (sublingual/liberação prolongada):

- Nifedipina retard, morfina MST, diazepam SL, nitroglicerina SL, qualquer `XR/SR/LP`.

### Glicemia em jejum absurda

- Jejum declarado + glicemia > 200 mg/dL → flag `review` (DM não-controlado ou hiperglicemia de estresse)
- Jejum declarado + glicemia < 40 → flag `critical_alert` (hipoglicemia severa)

### pH + HCO3 incongruente

- pH > 7,5 + HCO3 < 20 → matematicamente impossível sem pCO2 muito baixo → flag coerência gaso

### SOFA cardio sem peso

Dose de Nor em mcg/kg/min exige peso. Se `peso = null` → SOFA cardio retorna `null` com `missing: ['peso']`. NÃO assuma
70kg.

### SOFA sem baseline

ΔSOFA não calculável → marcar `delta_unavailable`, **NÃO** assumir baseline 0.

### Gasometria venosa rotulada como arterial

Gaso venosa rotulada arterial → P/F não aplicável, flag.

### Cultura positiva sem antibiograma

Cultura positiva sem antibiograma → flag `antibiograma_missing` (laudo provavelmente incompleto/preliminar).

### PAM calculada vs medida divergente

PAM calculada vs medida divergente > 15 mmHg → `review`.

---

## 📅 Sanity de datas/timestamps

- Data da folha no futuro → flag `date_future`
- Data da folha > 7 dias antes de hoje → flag `date_stale`
- Horário com AM/PM em formato BR → BR usa 24h, se aparecer AM/PM suspeitar erro de OCR.

---

## 🧠 Conduta com flags

Fluxo:

1. Extrair o valor.
2. Rodar a malha de ranges.
3. Se flag: adicionar ao warning array + setar `requires_review: true` do evento.
4. **NÃO** bloquear o payload — ele segue pro Supabase.
5. O frontend renderiza com cor amarela (review) ou vermelha (physiological_error) pra chamar atenção.

A inteligência fica no frontend e no intensivista. O OCR é dumb-and-honest: leu assim, reporta assim, com flag se está
estranho.

---

## Modo Nerd — Por que não corrigir automaticamente

Corrigir "silenciosamente" um SpO2 de 145% pra 95% é iatrogenia computacional. Cria confiança falsa no pipeline. O
princípio **zero-hallucination** do docx CAME-VKG está correto nisto: dado errado deve propagar errado com flag, não
virar dado "melhorado" por suposição.

O custo de sinalizar um valor estranho é 1 segundo de review do médico. O custo de mascarar um erro é um paciente
morrendo por decisão baseada em dado inventado. A assimetria é gritante.
