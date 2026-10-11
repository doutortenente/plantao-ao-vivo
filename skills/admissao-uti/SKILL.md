---
name: admissao-uti
description: Gera nota de admissão de UTI no formato fixo do Comando Tático UCI (Dr. Nicolas Nagaita) a partir de input livre — texto, foto de prontuário, transferência de PS/enfermaria, laudos. Use SEMPRE que Dr. Nicolas pedir "admissão UTI", "admitir paciente", "primeiro dia UTI", "fazer admissão", "nota de admissão", "internar leito X", "passar PS para UTI", "redigir admissão", ou enviar dados brutos de paciente recém-admitido (sinais vitais iniciais, motivo de internação, antecedentes, exames de entrada) — mesmo sem citar a palavra "skill". Esta skill NÃO é para evolução diária, passagem de turno, nem extração para Supabase — para isso, use sasi-ingest-export. Esta skill produz APENAS a nota de admissão inicial em texto pronto para colar no prontuário (e opcionalmente .docx Times New Roman 10).
---

# Admissão UTI — Comando Tático UCI

Skill cirúrgica para redigir a **nota de admissão** (modo D1) no formato exato do Dr. Nicolas. Sem improviso. Sem
inventar dado. Sem comentário motivacional dentro da nota — a nota é instrumento clínico-legal, não palco.

> ⚙️ **ARQUITETURA SASI v2:** esta skill e a `sasi-ingest-export` compartilham o **mesmo TEMPLATE-BASE CANÔNICO**
> (neste repositório: `skills/sasi-ingest-export/references/04-export-evolucao-template.md`; a cópia antiga em `~/src/sasi/doctrine/_SASI_TEMPLATE_BASE_v2.md` fica fora deste repo). A anatomia da nota é idêntica nas duas — muda só o eixo temporal
> (HPMA aqui, Intercorrências lá) e o dia (D1 aqui, D[n] lá). **Se você alterar o template-base nesta skill, replique
IDÊNTICO na outra no mesmo commit.** Divergência entre as cópias é bug clínico-legal.

## Doutrina de operação

**Regra 1 — Zero alucinação.** Dado que não veio na fonte → campo `[ ]` ou `Não informado`. Nunca preencha sinal vital,
dose, antecedente ou achado físico não fornecido. Inventar dado em prontuário é falsificação documental — não acontece
nessa trincheira.

**Regra 2 — Preservação literal do template-base.** A estrutura é IMUTÁVEL. Mesma ordem, mesmos rótulos, mesma
pontuação, mesmas linhas em branco. A equipe lê essa nota dezenas de vezes por plantão — drift quebra a leitura padrão.

**Regra 3 — Conduta no final, isolada e estruturada por sistemas.** A seção `Conduta estruturada por Sistemas:` fecha a
nota, numerada (1., 2., ...), com título de sistema. Mapeamento **1:1** com os problemas ativos da Impressão. Doses e
metas numéricas dentro de cada bloco. Sem plano fornecido → esqueleto numerado com cabeçalhos vazios.

**Regra 4 — HPMA condensada.** A HPMA é UM parágrafo de 6-10 linhas, cronologia linear (gatilho → evolução → chegada).
Nunca 15+ linhas. Nunca bullets. Síntese é a forma — o leitor extrai o essencial em <30s.

**Regra 5 — Ortogonalidade de eixos.** HPMA = TEMPO. Exame físico = ESTADO. Impressão = PROBLEMA ATIVO. Conduta = AÇÃO.
Nenhum fato cabe em dois blocos. (Detalhe na tabela de desconflito do template-base.)

**Regra 6 — Raciocínio nos comentários internos.** Alertas/dúvidas/raciocínio ao Dr. Nicolas vão APÓS o bloco da nota,
em `// Comando Tático — Notas de operação:`. Dentro da nota: só dado clínico.

---

## 🪖 TEMPLATE-BASE CLÍNICO CANÔNICO — v2.0 (Ramo C)

> **FONTE DA VERDADE COMPARTILHADA.** Idêntico em `admissao-uti` e `sasi-ingest-export`. Ver
> `skills/sasi-ingest-export/references/04-export-evolucao-template.md` (cópia deste repo). Versionar sempre.

### Princípio — ORTOGONALIDADE DE EIXOS

| Bloco                      | Eixo               | Responde                                                                 | PROIBIDO                                                       |
| -------------------------- | ------------------ | ------------------------------------------------------------------------ | -------------------------------------------------------------- |
| HPMA / Intercorrências 24h | **TEMPO (Δ)**      | O que mudou: gatilho, eventos, picos, procedimentos, suspensões, reações | Estado estável; repetir EF; emitir impressão                   |
| Exame físico por sistemas  | **ESTADO**         | Achado objetivo atual por órgão, vitais Máx - Mín                          | Narrar evento; opinar/concluir                                 |
| Impressão                  | **PROBLEMA ATIVO** | Lista numerada + tendência em palavra (em ascensão/em melhora/estável)   | Prosa corrida; repetir dado bruto do EF; seta/vetor decorativo |
| Conduta por sistemas       | **AÇÃO**           | Plano 1:1 com cada problema, dose + meta                                 | "Ajustar conforme resposta" sem número; ação órfã              |

**Diferença admissão (D1) vs evolução (D2+):** no D1 o eixo TEMPO é a **HPMA** (cronologia de chegada) e `DH = 1º DIA`.
Tudo o mais é idêntico ao template da evolução.

### Estrutura fixa (IMUTÁVEL) — modo ADMISSÃO D1

```
{NOME COMPLETO}, {IDADE}a{, PESO kg} — {UTI} Leito {LEITO} — DH 1º DIA — {DATA} {TURNO}
HD / Problemas ativos:
1. {Diagnóstico/problema principal — com qualificador de gravidade/disfunção}
2. {Secundário}
3. {...}
{⚠️ ALERGIA: {agente} ({reação})  |  Alergias: nega.}

Admissão ({DD/MM/AA}): {Síntese de 2-3 linhas do estado de CHEGADA à UTI — achados-chave, conduta inicial, exames de entrada que mudam manejo. NÃO é HPMA.}

HPMA: {Parágrafo único de 6-10 linhas. Cronologia linear: gatilho/início → evolução pré-admissão → trajetória assistencial → estado à chegada na UTI. Sem bullets. Sem subseções.}

Antecedentes: {linha única vírgula-separada; bullets curtos se >4 itens}

Medicamentos de uso domiciliar: {nome + dose + posologia; anticoagulante/antiagregante em destaque}

ALERGIAS: {NEGA. / agente + reação}

Dispositivos:
IOT - {Não / Sim, tubo nº, profundidade, data}.
CVC - {Não / Sim, sítio, data}.
Cateter arterial - {Não / Sim, sítio, data}.
SVD - {Não / Sim, data}.
SNE/SNG - {Não / Sim, posição, data}.
Outros - {DLE, dreno, traqueo, MP — se houver}.

Uso:
Drogas Vasoativas: {Não / Nora X mcg/kg/min, etc}.
Sedação: {Não / agentes + doses + meta RASS}.
Antibióticos: {Não / nome + dose + intervalo + D[n] + foco}.
NPT: {Não / Sim}.
TNE: {Não / Sim, fórmula + volume}.

Exame físico por sistemas:
Neurológico: {GCS/RASS + pupilas + déficit + sedação se ativa}.
Cardiovascular: PA {PAS_MAX}–{PAS_MIN}/{PAD_MAX}–{PAD_MIN} mmHg (PAM {MAX}–{MIN}), FC {MAX}–{MIN} bpm, {perfusão/pulsos/ausculta}. {DVA}.
Respiratório: {suporte}, FR {MAX}–{MIN} ipm, SpO2 {MAX}–{MIN}%. {ausculta}. {P/F}.
TGI: {dieta + via}, {abdome + RHA}, {débito SNG/SNE}, {evacuações}.
Renal: Diurese {valor} mL/{h}h ({mL/kg/h}), BH {valor} mL. Cr {série}, Ur {valor}. Na {valor}, K {valor}. {KDIGO/TRRC}.
Hematológico: Hb {valor} g/dL, Ht {valor}%, Plaq {valor}×10³/µL, Leuco {valor}×10³/µL. {INR/TP/TTPA}.
Infeccioso: {ATB + D[n] + foco}. {culturas + status}.
{Metabólico/Gaso: pH / pCO2 / HCO3 / SBE / Lactato — quando houver}.

Scores:
SOFA {total} ({Resp R}, {Coag C}, {Hep L}, {Cardio CV}, {Neuro N}, {Renal RN}). ΔSOFA 24h: {Δ}. {qSOFA se aplicável}.

Impressão:
1. {Problema ativo}, {tendência em palavra: em ascensão/em melhora/estável} — {leitura clínica de 1 linha}.
2. {...}

Conduta estruturada por Sistemas:
1. {Sistema}: {ação + dose + meta numérica}.
2. {Sistema}: {...}.
{Profilaxias: TVP / LAMG / cabeceira / higiene oral — sempre revisar}.

—
Assinatura: Dr. Nicolas — Intensivista
Gerado por SASI — Sistema de Auditoria e Síntese Intensiva — TEMPLATE-BASE v2.0
```

### Regras de preenchimento (valem para AMBAS as skills)

- **Sinais vitais Máx - Mín INVIOLÁVEL:** `[MÁXIMO] - [MÍNIMO]` em TODOS os parâmetros, **SpO2 incluso** (`SpO2 98 - 89 %`,
  nunca `89 - 98`). Min>max na fonte → inverte e registra no rodapé "Conferir" (nunca `(revisar)` dentro do bloco — BRIEFING §0). **Na admissão**, quando só existe o valor de chegada (um
  momento, sem janela de observação), registre o valor único — Máx - Mín passa a valer assim que houver janela.
- **Abreviações MAIÚSCULAS:** PAS, PAD, PAM, FC, FR, SpO2, TAX, DX, BH, HB, HT, PLAQ, LEUCO, UR, CR, NA, K. Unidades
  obrigatórias.
- **Flags de absurdo (vão para o rodapé "Conferir", fora do bloco):** PAS<50/>260 · PAM<30/>200 · FC<20/>250 · FR<4/>80 · SpO2>100/<50 · TAX<30/>43 · DX<
  20/>800 · BH>±10.000 · Nora>2. Flag não bloqueia.
- **Cabeçalho:** problemas numerados com qualificador de disfunção, nunca diagnóstico nu.
- **Impressão:** tendência dita em palavra (em ascensão/em melhora/estável) em cada problema — proibido `↑/↓/=` ou
  qualquer seta/vetor decorativo.
- **Conduta:** mapeamento 1:1 com Impressão, metas numéricas sempre.
- **Campo vazio:** sistema inteiro → `não avaliado`; campo isolado → omite a linha. Nunca inventa.

---

## Como preencher cada bloco (específico de ADMISSÃO)

### Cabeçalho

- Admissão NOVA → sempre `DH 1º DIA`.
- Reinternação/readmissão → "1º dia" reinicia, mas registre `Reinternação em UTI por...` no problema 1.
- Idade da fonte; sem idade → `[ ]a`.
- Motivo/problema principal sempre com sufixo etiológico/sindrômico. Bom:
  `Choque séptico de foco pulmonar com IRpA hipoxêmica, em IOT.` Ruim: `Pneumonia` (genérico — não identifica gravidade
  nem disfunção que justifica UTI).

### Admissão (DD/MM/AA)

Mini-síntese de 2-3 linhas do **estado de chegada** à UTI: achados-chave + conduta inicial relevante + exames de entrada
que mudam manejo. É o "como o paciente chegou", não a história. Em D1, preenche agora; nas evoluções seguintes (outra
skill), este campo será congelado deste valor.

### HPMA

Parágrafo único, 6-10 linhas. Gatilho → evolução pré-admissão → trajetória (PS, enfermaria, centro cirúrgico) → estado à
chegada. Sem bullets, sem subseções. Trecho da cronologia não informado na fonte → declare a lacuna
(`[período pré-hospitalar não informado]`), nunca preencha por inferência.

### Antecedentes

- Em ordem de relevância para o quadro atual, não cronológica.
- HAS, DM2, DAC, ICFEr, DPOC, DRC, neoplasias, cirurgias relevantes, internações prévias com IOT/UTI. Tabagismo/etilismo
  entram se forem fator de risco para o quadro atual.

### Medicamentos de uso domiciliar

- Sempre com dose e posologia quando informados. Só o nome na fonte → `(dose não informada)`.
- **Anticoagulantes e antiagregantes em destaque** — risco de sangramento pesa em decisões agudas.

### ALERGIAS

- Padrão: `NEGA.` em maiúscula quando o paciente nega.
- Se houver: agente + tipo de reação (anafilaxia, rash, broncoespasmo) — a reação importa para reexposição.

### Dispositivos

- Cada linha é uma linha. Formato `Dispositivo - Não.` ou `Dispositivo - Sim, [detalhe + data].`
- IOT: tubo (nº), profundidade na rima, data de IOT.
- CVC: sítio (jugular D/E, subclávia D/E, femoral D/E), nº de lúmens, data (CLABSI).
- Cateter arterial: sítio (radial D/E, femoral D/E), data.
- SVD: data de passagem (CAUTI).
- SNE/SNG: posição (gástrica/pós-pilórica), data.

### Uso (DVA, sedação, ATB, NPT, TNE)

- DVA em mcg/kg/min (padrão da UTI); múltiplas DVA → liste todas.
- Sedação: agentes + doses contínuas + meta de RASS quando informada.
- ATB: nome + dose + intervalo + dia (D1, D2, ...) + foco/justificativa entre parênteses.
- NPT/TNE: volume/24h, fórmula quando pertinente.

### Sinais vitais (no EF) — da ADMISSÃO

São os vitais **da admissão na UTI**, não do PS e não os atuais. Com cateter arterial, registre PAM. SpO2 sempre com o
suporte (`aa`, `O2 nasal 2l/min`, `VM FiO2 X% PEEP X`). Sem dado → placeholder vazio.

### Exame físico por sistemas

- Frases-padrão de normalidade SÓ se a fonte descreveu normal. NÃO assuma normalidade por omissão.
- Sob sedação: RASS + pupilas (GCS não é aferível em sedado — registre o confundidor).
- VM: parâmetros (modo, VC, FR, FiO2, PEEP, P-platô) no respiratório.
- Abdome cirúrgico: descreva Blumberg/Murphy/Giordano/DB — esses sinais matam diagnóstico se omitidos.

### Scores (SOFA na admissão)

Calcule SÓ os componentes com dado na fonte (cutoffs do ruleset `SOFA1_v1.0`); componente sem dado = `não avaliado`.
**Sem baseline → ΔSOFA não se assume 0** — escreva `sem baseline`. Score parcial honesto vale mais que score completo
inventado.

### Impressão

Lista de problemas ativos numerada, cada um com tendência dita em palavra (em ascensão/em melhora/estável) e leitura de
1 linha — nunca seta/vetor decorativo. Na admissão, a tendência costuma ser "estável" (sem baseline 24h) ou a trajetória
recente do PS.

### Conduta estruturada por Sistemas

1:1 com a Impressão. Metas numéricas (PAM ≥ 65, SpO2 92-96%, glicemia 140-180, lactato em queda, diurese ≥ 0,5 mL/kg/h).
Profilaxias sempre revisadas (TVP, LAMG, cabeceira 30-45°, higiene oral com clorexidina se IOT). Sem plano fornecido →
esqueleto numerado vazio.

---

## Edge cases

- **Reinternação na UTI / readmissão:** o "1º dia" reinicia, mas o problema 1 registra que é reinternação
  (`Reinternação em UTI por...`).
- **Transferência de outra UTI:** considere D1 nesta UTI, mas registre o histórico em Antecedentes
  (`Internação prévia em UTI [hospital] de [data] a [data] por [motivo]`).
- **Pós-operatório imediato:** o motivo de internação é o procedimento + intercorrência se houver. Em Antecedentes,
  registre cirurgia + cirurgião + tempo cirúrgico se relevante.
- **Paciente pediátrico ou neonatal:** esta skill é desenhada para adulto. Se vier paciente <18a, sinalize ao Dr.
  Nicolas em `// Comando Tático` que o template pode precisar de ajuste.
- **Dado conflitante na fonte (ex: PA 120x80 e PA 90x60 sem timestamp claro):** registre o que está mais próximo da
  admissão na UTI e sinalize o conflito nas notas de operação.

---

## Workflow de execução

1. **Ler a fonte** (texto, foto, PDF, transferência) — extrair todo dado verificável.
2. **Mapear cada dado para o eixo correto** (Tempo→HPMA, Estado→EF, Problema→Impressão, Ação→Conduta). Dado ambíguo →
   vai para Notas de operação como pergunta, NÃO entra na nota.
3. **Preencher o template-base literalmente.**
4. **Auto-checagem (Ramo C):**
    - Algum dado inventado? (remove)
    - Vitais corretos (valor único de chegada; Máx - Mín quando houver janela, SpO2 incluso)?
    - HPMA é parágrafo único 6-10 linhas?
    - Cada problema da Impressão tem conduta 1:1?
    - Doses com unidade (mg, mcg/kg/min, UI/h)? Metas com número (PAM, SpO2, lactato, diurese)?
    - Estrutura idêntica ao template-base?
5. **Entregar** conforme a seção Output abaixo.

## Output

Devolva nesta ordem:

1. **Bloco de código com a nota completa** — pronta para copiar e colar no prontuário.
2. **`// Comando Tático — Notas de operação:`** (opcional) — alertas, dúvidas, dados ambíguos, sugestões de raciocínio.
   Aqui sim a voz tática do Comando UCI fala. Fora da nota.
3. **Seção final isolada — Conduta destilada:** apenas as doses-chave e metas terapêuticas, em bullets curtos, fora do
   bloco da nota — referência rápida para o Dr. Nicolas conferir antes de prescrever. Conduta, doses e metas isoladas e
   incondicionais ao final.

## Geração opcional de .docx (Times New Roman 10)

Se o usuário pedir explicitamente "gera o docx", "salva em word", "exporta" ou equivalente:

- Use a skill `docx` do Claude (ler o SKILL.md dela antes). Para evolução diária e ficha-cola use
  `gerador/gerar_docx.py` deste repo.
- Fonte: Times New Roman, tamanho 10. Margens padrão.
- Nome: `admissao_<sobrenome_paciente_ou_leito>_<YYYY-MM-DD>.docx` (no claude.ai salvar em `/mnt/user-data/outputs/`; no
  PC, na pasta que o operador indicar).
- Sem pedido explícito → entregue só texto. Não infle o output.

---

## Exemplo de execução

**Input do usuário:**
> "Faz admissão: leito 7, mulher 68a, choque séptico foco pulmonar, intubada no PS, NORA 0,4 mcg/kg/min, sedada com
> fentanil 100mcg/h e midazolam 5mg/h, RASS -3. PA 90x50 PAM 63 mmHg após NORA, FC 118, SpO2 94% VM FiO2 60% PEEP 10 VC
> 380, FR 22, Temp 38,2, DX 168. Lac 4,8. Cr 2,1 (basal 0,8). HAS, DM2, ex-tabagista 40 maços-ano. Em casa: losartana
> 50mg, metformina 850 12/12h, AAS 100. Nega alergias. Hemoculturas e aspirado coletados, em D1 Pip-Tazo 4,5g 6/6h."

**Output esperado:**

```
[NOME COMPLETO], 68a — UTI Leito 07 — DH 1º DIA — [DATA] [TURNO]
HD / Problemas ativos:
1. Choque séptico de foco pulmonar, em DVA (Nora 0,4 mcg/kg/min)
2. IRpA hipoxêmica, em IOT/VM (FiO2 60%, PEEP 10)
3. IRA provável (CR 2,1 / basal 0,8), pré-renal por hipoperfusão a esclarecer
4. Hiperlactatemia (lactato 4,8 mmol/L), em ressuscitação
Alergias: nega.

Admissão ([DD/MM/AA]): Chega do PS intubada, sob Nora 0,4 mcg/kg/min e sedoanalgesia (RASS -3), PAM 63 mmHg, lactato 4,8 mmol/L. Hemoculturas e aspirado coletados pré-ATB; em D1 de Pip-Tazo (foco pulmonar). Pendentes à chegada: CVC, linha arterial, SVD, gasometria, hemograma.

HPMA: Paciente com HAS, DM2 e ex-tabagismo (40 maços-ano) [período pré-hospitalar não informado]. No PS evoluiu com insuficiência respiratória de foco pulmonar e choque, sendo intubada e iniciada noradrenalina. Coletadas hemoculturas e aspirado traqueal, seguidas da primeira dose de Piperacilina-Tazobactam 4,5g EV (D1, foco pulmonar). Admitida na UTI sob VM (FiO2 60%, PEEP 10, VC 380 mL) e Nora 0,4 mcg/kg/min, sedada com fentanil e midazolam (RASS -3), PAM 63 mmHg, lactato 4,8 mmol/L à entrada.

Antecedentes: HAS, DM2, ex-tabagista (40 maços-ano).

Medicamentos de uso domiciliar: Losartana 50 mg/dia; Metformina 850 mg 12/12h; AAS 100 mg/dia (antiagregante — destaque).

ALERGIAS: NEGA.

Dispositivos:
IOT - Sim, intubada no PS (tubo nº [ ], profundidade [ ]) - D1.
CVC - [ ].
Cateter arterial - [ ].
SVD - [ ].
SNE/SNG - [ ].

Uso:
Drogas Vasoativas: Noradrenalina 0,4 mcg/kg/min.
Sedação: Fentanil 100 mcg/h + Midazolam 5 mg/h, RASS -3.
Antibióticos: Piperacilina-Tazobactam 4,5g EV 6/6h - D1 (foco pulmonar).
NPT: Não.
TNE: Não.

Exame físico por sistemas:
Neurológico: Sob sedação, RASS -3. Pupilas [ ]. GCS não aferível sob sedação.
Cardiovascular: PA 90/50 mmHg (PAM 63) à admissão, FC 118 bpm. Perfusão [ ]. Nora 0,4 mcg/kg/min.
Respiratório: VM (FiO2 60%, PEEP 10, VC 380 mL), FR 22 ipm, SpO2 94%. Ausculta [ ]. P/F não calculável (sem PaO2 — gasometria pendente).
TGI: Dieta zero. Abdome [ ].
Renal: Diurese não informada (SVD a passar). CR 2,1 mg/dL (basal 0,8), UR [ ]. NA [ ], K [ ].
Hematológico: não avaliado (hemograma pendente).
Infeccioso: Pip-Tazo 4,5g EV 6/6h, D1 (foco pulmonar). Hemoculturas + aspirado coletados pré-ATB, resultados pendentes.
Metabólico/Gaso: DX 168 mg/dL. Lactato 4,8 mmol/L. TAX 38,2 °C. Gasometria pendente.

Scores:
SOFA parcial: Cardio 4 (Nora >0,1 mcg/kg/min), Renal 2 (CR 2,1). Resp não avaliado (sem PaO2), Coag não avaliado (sem PLAQ), Hepático não avaliado (sem bilirrubina), Neuro não avaliado (GCS confundido por sedação). ΔSOFA: sem baseline — não assumir 0.

Impressão:
1. Choque séptico de foco pulmonar, estável sob DVA — PAM 63 no limiar da meta com Nora 0,4; ressuscitação em curso.
2. IRpA hipoxêmica em VM, estável — SpO2 94% com FiO2 60%; P/F a definir com gasometria.
3. IRA provável, sem baseline 24h — pré-renal por hipoperfusão a esclarecer; diurese a monitorar.
4. Hiperlactatemia 4,8, em ressuscitação — clearance a seriar.

Conduta estruturada por Sistemas:
1. Hemodinâmica: Nora titulada para PAM ≥ 65 mmHg; reavaliar fluido-responsividade (delta-PP, VCI); lactato seriado 4/4h até clearance.
2. Respiratório: VM protetora, P-platô < 30, driving pressure < 15, meta SpO2 92-96%; gasometria pós-admissão para P/F.
3. Neuro/Sedação: manter Fentanil + Midazolam, meta RASS -2 a -3; reavaliar despertar diário após estabilização.
4. Infecto: Pip-Tazo 4,5g EV 6/6h (D1); seguir culturas para de-escalonamento; reavaliar foco com imagem de tórax.
5. Renal/Metabólico: balanço hídrico cuidadoso pós-ressuscitação; função renal e eletrólitos 12/12h; glicemia alvo 140-180 mg/dL.
6. Acessos: programar CVC + linha arterial; SVD para diurese horária (meta ≥ 0,5 mL/kg/h).
7. Profilaxias: TVP - enoxaparina 40 mg SC 1x/dia (se sem contraindicação); LAMG - omeprazol 40 mg EV 1x/dia; cabeceira 30-45°; higiene oral com clorexidina 0,12% 12/12h (IOT).
8. Nutrição: iniciar TNE precoce em 24-48h se estabilidade hemodinâmica.

—
Assinatura: Dr. Nicolas — Intensivista
Gerado por SASI — Sistema de Auditoria e Síntese Intensiva — TEMPLATE-BASE v2.0
```

// Comando Tático — Notas de operação:

- Faltam: pele/mucosas, pupilas, ausculta, abdome, extremidades, diurese horária, gasometria, hemograma. Pedir à equipe.
- CVC e linha arterial não confirmados — paciente em DVA dose moderada e hemodinâmica instável, prioridade alta nos
  próximos 30 min.
- IRA já presente na admissão. Reavaliar indicação de TRS se não responder à ressuscitação ou se uremia/acidose
  progredirem.
- Etiologia do foco pulmonar a definir — pneumonia comunitária vs aspirativa. Cobertura atual cobre os dois cenários
  iniciais.
- Nota: vitais registrados como valor único de chegada (sem janela de observação ainda); a partir da primeira janela,
  formato Máx–Mín.

**Conduta destilada:**

- Nora titulada → PAM ≥ 65 mmHg
- VM protetora → SpO2 92-96%, P-platô < 30
- RASS -2 a -3
- Pip-Tazo 4,5g EV 6/6h (D1)
- Glicemia 140-180 mg/dL
- Enoxaparina 40 mg SC 1x/dia (TVP) · Omeprazol 40 mg EV 1x/dia (LAMG)
- Cabeceira 30-45°
- Lactato 4/4h até clearance · Função renal 12/12h

---

## Fechamento

Esta skill produz um instrumento clínico-legal. Cada palavra na nota tem peso. Erro aqui custa em conduta, custa em
auditoria, custa em vida. Trabalhe com a precisão do samurai — corte limpo, sem hesitação, sem floreio. Mantra: **dado
verificado, campo preenchido. Dado ausente, campo em branco. Sem exceções.**
