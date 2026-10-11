# 🔍 Dicionário de Extração — o que extrair de cada tipo de documento

Uma seção por tipo. Cada seção lista **campos obrigatórios**, **campos opcionais**, **armadilhas**.

---

## 📋 `folha_enfermagem`

Folha impressa ou manuscrita, geralmente em grade horária de 24h ou por turno.

**Obrigatórios** (se ausente → perguntar ou retornar null com warning):

- `leito`, `uti` (se não na foto, perguntar ANTES de extrair)
- `data_evolucao` (data da folha)
- `plantao` (manhã/tarde/noite conforme horário do round)

**Snapshot de sistemas a preencher (JSONB):**

- **resp**: `fr` (menor/maior), `spo2` (menor/maior, extrair o PIOR como principal), `fio2O2` ou `vmFio2`, `suporte`
  (inferir: se tem PEEP → `IOT + VM`; se tem VNI escrito → `VNI`; cateter O2 + fluxo → `CN` ou `O2`)
- **hemo**: `pa_sys_min`, `pa_sys_max`, `pa_dia_min`, `pa_dia_max`, `pam1` (MIN), `pam2` (MAX), `fc_min`, `fc_max`
- **renal**: `diurese` (total das 24h ou do turno), `diureseHoras` (duração coberta), `bh` (balanço hídrico do período)
- **neuro**: escalas (GCS, RASS, CAM-ICU, Richmond) — **gerar evento próprio `gcs`** (componente SOFA neuro), além de
  registrar no snapshot. Se sedado (RASS −4/−5): registrar `gcs` + `gcs_confounded_by_sedation: true`.
- **dvas**: qualquer droga em BIC com `vazao_ml_h`, `diluicao`, `droga`

**Armadilhas específicas:**

- Vírgula decimal: folhas BR usam `37,5 / 98,6 / 1,2`. EXTRAIR COM VÍRGULA ou ponto, NÃO faça aritmética.
- FC/FR às vezes aparecem como "80-110" → extrair como range: `fc_min=80, fc_max=110`.
- Temperatura: se estiver `37.5°C` vs `99.5°F` → forçar Celsius (não tem °F em UTI brasileira; se aparecer,
  provavelmente é erro de OCR).
- Diurese: se a folha tem volume por hora (marcado h1, h2...), SOMAR mentalmente SÓ SE confiança alta; senão marcar
  `diurese_sum_inferred: true` em warnings.
- BH negativo é REAL (paciente desidratado/diurético). NÃO inverter sinal.
- Infusões: campo "gotas/min" precisa ser convertido pra mL/h (1 gt ≈ 0,0667 mL em equipo padrão 20gt/mL, ou 0,0333 em
  microgotas). Se incerto → devolver valor bruto + unidade original no `source_text`.

**Output de eventos clínicos** (gerar UM evento por cada):

- `pam_min`, `pam` (média), `fc` (MAX — pior), `fr` (MAX), `spo2` (MIN — pior), `diurese_h` (calc: diurese/horas),
  `bh_h`, `temp` (MAX — pior se febril)
- **`gcs`** (SOFA neuro) + `valor_json:{pre_sedacao, confounded_by_sedation}`; e evento **`rass`** se houver sedação
- **vasopressores por droga** (SOFA cardio): `nor_dose`/`adr_dose`/`dopa_dose`/`dobuta_dose` em mcg/kg/min +
  `valor_json:{duracao_min}` (precisa peso; sem peso → `null` + `missing:["peso"]`). NÃO somar drogas
- **`diurese_h`** em mL/h (se a folha só traz total 24h, dividir por 24 + `valor_json:{from_24h_total:true}`)
- Se VM/gaso no período: `pf_ratio` + `valor_json:{suporte_vent: VMI|VNI|HFNC|none}`

---

## 🩸 `lab_bioquimica`

Painel padrão: Ureia, Cr, Na, K, Mg, Ca, glicemia, TGO, TGP, FA, GGT, BB (total/direto/indireto), PCR, procalcitonina.

**Extrair:**

- Nome do teste (normalizado: "Ureia", "Creatinina", "Sódio", "Potássio", "Glicemia", "TGO", "TGP", "Bilirrubina Total",
  "PCR", "Procalcitonina")
- Valor numérico + unidade (manter unidade original do laudo)
- Data/hora da COLETA (não da emissão do laudo!)
- Valores de referência (se listados) — pra flag de out-of-range

**Mapeamento para `eventos_clinicos.tipo`:**

- Ureia → `ur` (mg/dL)
- Creatinina → `cr` (mg/dL)
- Sódio → `na` (mEq/L)
- Potássio → `k` (mEq/L)
- Bilirrubina Total → `bb` (mg/dL) — **componente SOFA hepático: sempre gerar evento quando o painel traz BB; se
  ausente, declarar faltante, não inventar**
- (outros → `custom` com `valor_json`)

**Armadilhas:**

- Creatinina em µmol/L vs mg/dL: se valor > 50 → suspeitar µmol/L (dividir por 88,4 pra mg/dL) e marcar warning.
- Glicemia em mg/dL (BR) vs mmol/L (EU): > 50 em BR é mg/dL sem discussão.
- PCR em mg/L (BR) vs mg/dL (US): BR usa mg/L, valores típicos 0-200.

---

## 🩸 `lab_hemograma`

**Extrair:** Hb, Ht, VCM, HCM, CHCM, RDW, leucócitos (total + diferencial: segmentados, bastões, linfócitos, monócitos,
eosinófilos), plaquetas.

**Armadilhas críticas:**

- **Plaquetas — unidade ambígua**: BR laboratórios variam entre `×10³/µL` (ex: `180`) e `/µL` (ex: `180000`). REGRA: se
  valor < 1000 → `×10³/µL`; se valor > 10000 → `/µL` (divide por 1000 pra normalizar); se entre 1000-10000 →
  **AMBÍGUO**, marcar `plaq_unit_ambiguous: true`, retornar valor original + warning.
- Leucócitos: mesmo problema (`14.500` vs `14500` vs `14,5`). Se valor < 100 → `×10³/µL`; se > 1000 → `/µL`.
- **Desvio à esquerda**: se bastões > 10% → flag (infecção ativa/grave).
- Reticulócitos: se presente, extrair mas não compor evento clínico principal.

**Eventos gerados:** `hb`, `plaq`, `leuco` (sempre em `×10³/µL` após normalização).

---

## 💨 `lab_gasometria`

**Extrair:** pH, pCO2, pO2, HCO3 (real e padrão), BE (base excess), Lactato, SatO2, FiO2 (se registrada na gaso),
hemoglobina (cooximetria).

**Sempre calcular P/F ratio** quando tem pO2 + FiO2: `PF = pO2 / (FiO2/100)`. Se FiO2 estava em fração (0,4), converter:
`PF = pO2 / 0.4`.

**Classificação do distúrbio** (adicionar em warnings como info):

- pH < 7,35 → acidose; pH > 7,45 → alcalose
- pCO2 alto com pH baixo → acidose respiratória
- HCO3 baixo com pH baixo → acidose metabólica
- Anion gap = Na − (Cl + HCO3). Se > 12 → HAGMA (provável lactato/CAD/IRA)

**Armadilhas:**

- Tipo de gaso: **arterial** (padrão) vs **venosa** (`pH` ~7,33 mesmo normal, `pCO2` 40-50 mesmo normal). Se o laudo diz
  "venosa", marcar e NÃO aplicar critérios arteriais.
- Lactato: unidade `mmol/L` (padrão) vs `mg/dL` (× 0,111 pra mmol/L). BR usa mmol/L predominante.
- SatO2 da gaso vs da oximetria → pode divergir. Usar SatO2 da oximetria pro `spo2`, da gaso pro `custom`.

**Eventos gerados:** `po2`, `pf_ratio` (SOFA resp; gravar `valor_json:{suporte_vent: VMI|VNI|HFNC|none}` — motor só
pontua resp 3–4 com suporte; se FiO₂ ausente → `pf_ratio=null` + `missing:["fio2"]`), `lactato`, + `custom` com
`valor_json` do painel completo.

---

## 🧪 `lab_coag`

**Extrair:** TP (s + %), INR, TTPA (s + RNI), fibrinogênio, dímero-D.

**Evento gerado:** `inr` (numérico), `custom` pra fibrinogênio/D-dímero.

---

## 🦠 `lab_cultura`

**Estrutura obrigatória:**

```json
{
  "material": "hemocultura | urocultura | tqt | lavado_bal | lcr | secreção_ferida | ...",
  "coleta_ts": "2026-04-24T06:00:00-03:00",
  "crescimento": true,
  "agente": "Escherichia coli",
  "ufc_por_ml": 100000,
  "antibiograma": [
    { "antibiotico": "Ceftriaxona", "resultado": "R" },
    { "antibiotico": "Meropenem",   "resultado": "S" },
    { "antibiotico": "Polimixina B","resultado": "S" }
  ]
}
```

Valores de antibiograma: `S` (sensível), `I` (intermediário), `R` (resistente). Se laudo escreve
"sensível"/"resistente", normalizar pra S/I/R.

Vai pra `eventos_clinicos` como `tipo='custom'`, `valor_json` com a estrutura acima.

**CRÍTICO — não inventar antibiograma**: se o laudo lista 5 antibióticos, liste os 5. Se lista 20, liste os 20. Nunca
omita por brevidade. O intensivista PRECISA do painel completo pra decidir descalonamento.

---

## 🧠 `laudo_imagem`

TC/RM/RX/USG/ECO.

**Extrair:**

- Tipo de exame (`TC crânio`, `RX tórax`, `USG abdome`, `ECO transtorácico`, etc.)
- Data/hora
- **Achados** (bullets curtos, extraindo as frases-chave do laudo)
- **Conclusão** (cópia literal da seção "Conclusão:" ou "Impressão:")

**NÃO reinterpretar**: copiar texto do laudo, não tentar "melhorar" ou concluir algo que o radiologista não concluiu.

Vai pra `eventos_clinicos` como `tipo='custom'`, `valor_json` com `{tipo_exame, achados, conclusao}`.

---

## 💊 `prescricao`

**Extrair por linha**: droga, dose, via, frequência, horário.

**Armadilhas:**

- Abreviações BR: `VO`=oral, `EV`=IV, `IM`=intramuscular, `SC`=subcutânea, `IN`=intranasal, `SNE`=sonda nasoentérica.
- Frequência: `8/8h` = a cada 8h = 3x/dia; `12/12h` = 2x/dia; `SN` = se necessário.
- Dose: manter unidade literal (`500mg`, `1g`, `10UI`).

**Vai pra `evolucao_snapshot` como array** — não gera `evento_clinico` (exceto se for DVA, aí entra em `dvas` do
snapshot).

**Ordenar por sistema (modo D):** ao exportar prescrição, classificar cada droga em 1 dos 7 blocos canônicos
(Cardiovascular · SNC · GI/Endócrino · Infeccioso/Respiratório · Hematológico/Profilaxias · Nutrição/Eletrólitos ·
Sintomáticos/SN) e rodar o safety check conservador — ver `references/07-export-prescricao-ordenada.md`.

---

## 📝 `texto_livre`

Evolução digitada/dictada. Parse heurístico:

- Procurar padrões `PAM X mmHg`, `SpO2 X%`, `FC X bpm`, `diurese X mL`.
- Procurar drogas em BIC: `Nor 0,3 mcg/kg/min`, `Fentanil 100 mcg/h`.
- Extrair `impressao` (linhas com "Paciente evoluindo...", "em quadro de...") e `conduta` (linhas com "manter",
  "iniciar", "suspender", "aumentar").

Quando em dúvida, preencher `warnings` com o trecho ambíguo e retornar `null` no campo.

---

## 📌 Pendências / Tarefas → array `pendencias[]`

**O que é pendência:** uma **tarefa acionável do próximo turno** — algo que alguém precisa *fazer* ou *conseguir*, não
um estado clínico. Sai do resumo e vai pro array `pendencias: [{tarefa, prioridade}]`. É a fonte única: a mesma tarefa
**não** se repete na Conduta nem na Impressão.

**Gatilhos de detecção** (verbo de ação / espera por resultado):

- Verbos imperativos: "solicitar", "programar", "agendar", "passar (sonda/acesso)", "reavaliar", "discutir com (CCIH /
  cirurgia / neuro)", "colher", "trocar", "puncionar".
- Espera por exame/parecer/procedimento: "Aguarda TC", "Aguarda CATE", "Aguarda EDA", "Aguarda Holter", "Aguarda
  ecocardiograma", "Aguarda parecer X", "Aguarda cultura".
- Ações com hora marcada: "SBT amanhã 10h", "extubação programada", "diálise às 14h".
- Providências de risco: "HEMOTRANSFUSÃO urgente", "reservar hemoderivados", "reserva de vaga".

**NÃO é pendência** (fica no eixo próprio, não vira tarefa): diagnóstico/impressão ("sepse pulmonar"), meta terapêutica
contínua já em curso ("manter PAM > 65", "controle glicêmico"), dose/prescrição (vai em `prescricao`/`dvas`).

**Prioridade:**
| Valor | Quando | Exemplos | |---|---|---| | `1` | Tempo-sensível / segurança do paciente | HEMOTRANSFUSÃO urgente,
corrigir distúrbio grave, procedimento com hora marcada | | `2` | Rotina do dia (default) | TC de controle, parecer de
especialidade, colher cultura | | `3` | Pode esperar / eletivo | conciliação medicamentosa, agendamento eletivo |

**Zero alucinação:** só vira pendência o que está escrito/dito. Não inferir tarefa "que faria sentido". Se a frase é
ambígua entre conduta e tarefa, manter no resumo e sinalizar em `warnings`.
