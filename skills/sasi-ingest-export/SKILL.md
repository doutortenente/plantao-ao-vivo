---
name: sasi-ingest-export
description: Extrai dados clínicos estruturados a partir de fotos de folhas de enfermagem, PDFs/imagens de laboratório, laudos de imagem e texto livre para o sistema SASI (Comando UTI Alpha — 33 leitos UTI 2/3/4) e os converte em payload JSON validado para a tabela Supabase `eventos_clinicos` / `evolucoes`. Também gera o texto formatado para "Exportar Evolução" (nota de prontuário) e "Exportar Turno" (passagem de plantão em 1 página). USE ESTA SKILL SEMPRE que Dr. Nicolas enviar foto de folha de enfermagem, sinais vitais manuscritos, hemograma/bioquímica, gasometria, TC/RM/RX, prescrição, balanço hídrico, ou pedir "ingerir leito X", "processar evolução", "gerar evolução médica", "passar turno", "exportar evolução", "exportar turno", "salvar no Supabase" — mesmo que não cite a palavra "skill". Opera sob regra de ZERO ALUCINAÇÃO: campo sem fonte legível retorna `null` e gera warning, nunca é inventado.
---

# 🪖 SASI — Ingest & Export Clínico

Operação: transformar caos (fotos borradas, PDFs, texto solto) em dados estruturados auditados, e devolver síntese
clínica pronta pra prontuário / passagem.

---

## 🎯 Quando disparar

Você é o **scanner + auditor + redator** do Dr. Nicolas. Dispara quando:

- Foto de folha de enfermagem (sinais vitais, balanço, débitos, infusões)
- PDF ou foto de exame laboratorial (hemograma, bioquímica, gasometria, coagulograma, cultura)
- PDF/foto de laudo (TC, RM, RX, ECO, USG)
- Foto de prescrição médica
- Texto livre com dados clínicos colados
- Comandos explícitos: "ingerir leito N", "processar evolução", "exportar evolução", "exportar turno", "gerar passagem"

---

## 🧭 Fluxo operacional — 4 fases

### FASE 1 — Classificação do insumo (10s)

Identifique **o tipo de documento** antes de qualquer extração:

| Tipo               | Pistas visuais                                                      |
| ------------------ | ------------------------------------------------------------------- |
| `folha_enfermagem` | Grade horária, PA/FC/FR/Tax em colunas, colunas de 24h ou por turno |
| `lab_bioquimica`   | Ureia, Cr, Na, K, glicemia, TGO, TGP, BB                            |
| `lab_hemograma`    | Hb, Ht, leucócitos, plaquetas, VCM, HCM                             |
| `lab_gasometria`   | pH, pCO2, pO2, HCO3, BE, Lac, SatO2                                 |
| `lab_coag`         | INR, TTPA, TP                                                       |
| `lab_cultura`      | Material, crescimento, antibiograma (S/I/R)                         |
| `laudo_imagem`     | Cabeçalho "TC de...", "RX de...", "Conclusão:"                      |
| `prescricao`       | Posologia, via, frequência, data                                    |
| `texto_livre`      | Evolução digitada/dictada                                           |

Se houver ambiguidade, estado o tipo provável e pergunte **uma** confirmação curta — TDAH não tolera interrogatório, vá
direto ao ponto.

### FASE 2 — Extração com confidence scores

Leia `references/02-extraction-dictionary.md` para o dicionário completo de campos por tipo de documento.

**Regras de ouro da extração:**

1. **Zero alucinação**: campo ilegível/ausente → `null` com `confidence: 0` e adicione ao array `warnings`. NUNCA chute
   valores "razoáveis".
2. **Vírgula decimal BR**: número no documento com vírgula (`37,5`) → extrair como string `"37.5"` ou manter vírgula — o
   backend aplica `parseFloatBR`. JAMAIS converter pra float no meio do pipeline.
3. **Unidades explícitas**: sempre retornar `valor` + `unidade` como campos separados. Plaquetas em especial: se vier
   `150` sem unidade, marcar `plaq_unit_ambiguous: true`.
4. **Timestamp de origem**: se a folha tem horário (ex: `06:00`), extrair e converter pra ISO
   `YYYY-MM-DDTHH:mm:00-03:00` (America/Sao_Paulo). Se não tem → usa `now()` e marca `ts_inferred: true`.
5. **Leito e UTI obrigatórios**: se a foto não mostra, PERGUNTE. Sem leito não há ingest.

### FASE 3 — Auditoria clínica (zero-hallucination sanity check)

Leia `references/03-clinical-sanity-checks.md` para ranges físicos e regras de incompatibilidade. Para cada valor
extraído, aplique:

- **Range fisiológico** (ex: SpO2 > 100 → flag `physiological_error`)
- **Consistência interna** (ex: pH 7,6 com pCO2 80 → incongruente → flag)
- **Balanço hídrico absurdo** (>±10 000 ml/24h → flag)
- **Dose fora do racional** (Nor > 2 mcg/kg/min → flag, provável erro de diluição)

Qualquer flag **não é bloqueador** — o JSON segue, mas campo `requires_human_review: true`.

### FASE 4 — Geração de saída (uma das três, conforme o que o usuário pediu)

> 📖 **Leitura OBRIGATÓRIA antes de redigir qualquer texto** (`impressao[]`, `conduta[]`, `pendencias[]`, resumos,
> exports A/B/C/D): `references/00-estilo-texto-clinico.md`. Regras: acentuação sempre, CAPS só siglas/rótulos de seção,
> `->` só entre valores numéricos seriados (nunca como conectivo de frase), **proibido `↑/↓/=` ou qualquer seta/símbolo
decorativo em qualquer lugar** (Impressão, Conduta, passagem, pendência, notação de droga/escore — tendência sempre em
> palavra: "em desmame"/"em escalada", "em melhora"/"em piora"/"estável", delta de SOFA como `(+2)`/`(-1)`), zero
> explicação didática/mecanismo de ação, conduta só com fonte rastreável (sem genérico de preenchimento, sem sigla não
> confirmada).

**A. Payload de ingest** (padrão quando ele subiu foto/PDF sem comando extra):
Leia `references/01-schema-eventos-clinicos.md` para o schema exato. **Banco mudou em 10-ago-2026** (tabelas novas de ATB, culturas, dispositivos e janelas de vitais): leia também `references/08-p0-banco-10ago.md` antes de gravar. Devolve JSON validado (`sasi-ocr-ingest/v1`). O Dr.
Nicolas revisa; gravação no Supabase só com **“deploy”** / **“salvar no Supabase”** via MCP.

**Pendências/tarefas vão no array próprio `pendencias: [{tarefa, prioridade}]`** (prioridade `1`=alta/tempo-sensível,
`2`=rotina do dia [default], `3`=pode esperar) — **NUNCA** embutidas na Conduta, na Impressão ou no texto da passagem. O
`sasi_deploy_ingest` grava cada item como linha na tabela `pendencias`, que alimenta a coluna "Pendências/Riscos" da
Passagem de Turno e a ficha do paciente. Regra de detecção em `references/02-extraction-dictionary.md`.

**B. Exportar Evolução** (quando pedir "exportar evolução" ou "gerar nota de prontuário"):
Leia `references/04-export-evolucao-template.md` (modo D2+ / TEMPLATE-BASE v2). Saída é **texto puro em Markdown**,
copiar-e-colar direto na evolução oficial. Template v1 SOAP legado: `04-export-evolucao-template_v1_LEGADO.md`.

**C. Exportar Turno** (quando pedir "passagem", "exportar turno", "passagem de plantão"):
Leia `references/05-export-passagem-turno.md`. Saída é **1 página A4**, condensada, por paciente ou bloco de leitos. **O
cálculo é do script, não do LLM.** Balanço hídrico, Máx–Mín dos vitais e flags saem do motor determinístico
`scripts/build_passagem.py` — o LLM extrai os números **crus** por leito, o motor calcula e monta o `.md`. Ver «🧮 Motor
de cálculo» abaixo. Motivo: LLM erra aritmética/classificação (contava diurese como ingesta, somava balanço errado).

**D. Exportar Prescrição Ordenada** (quando subir foto de prescrição ou pedir "ordenar/exportar prescrição"):
Leia `references/07-export-prescricao-ordenada.md`. Saída = prescrição agrupada em **7 blocos por sistema** + safety
check conservador (zero alucinação). Texto puro pro prontuário. **NÃO grava no banco** — fluxo faseado: texto revisável
agora, SQL é fase 2 (quando o frontend consumir).

---

## 🧮 Motor de cálculo determinístico — `scripts/build_passagem.py`

**Regra de ouro: o LLM NÃO faz aritmética** (mesma doutrina de `hemodinamica-calculada`). O LLM lê a folha e extrai os
números **crus**; o script calcula. Isso mata o bug de balanço (diurese contada como ingesta, soma errada) de forma
estrutural.

**O que o motor calcula:** Máx–Mín de cada vital + contagem de flags `[Nx > limiar]` · `balanço = Σganhos − Σperdas` com
dicionário canônico (CANON) que **reclassifica** item lançado no lado errado (diurese→perda, com warning) · monta o
bloco `.md` no formato da passagem.

**Uso:**

```bash
python3 scripts/build_passagem.py --file leito.json   # 1 leito OU {"meta":..,"leitos":[..]}
python3 scripts/build_passagem.py --demo              # validação (com o bug embutido → corrigido)
```

**JSON de entrada (o que o LLM extrai, por leito):**

```json
{
  "leito": "01", "iniciais": "VLC", "dia_internacao": "5º",
  "sup_o2": "AA", "dieta": "...",
  "vitais": { "PAS": [139,128], "PAD": {"max":84,"min":59}, "FC": [...], "TAX": [...], "Dx": [...] },
  "ganhos": [ {"nome":"dieta","ml":600}, {"nome":"soro EV","ml":430} ],
  "perdas": [ {"nome":"diurese","ml":1100} ],
  "evacuacao": "ausente no período",
  "terapias": "…", "exame_fisico": "…", "evolucao": "…",
  "impressao": ["…"], "conduta": ["…"]
}
```

- `vitais.<nome>`: **lista horária** (flags exatas `[Nx]`) ou `{"max","min"}` (flag `[≥1x]`). Vitais reconhecidos:
  `PAS PAD PAM FC FR SpO2 TAX Dx`.
- `ganhos`/`perdas`: `{nome, ml}` OU `{nome, serie:[célula por hora]}` — **prefira a série**: o script soma as células
  cruas. **NUNCA confie no total que a enfermagem escreveu à mão** — ela também erra a conta; some as células. Célula
  ilegível → passar como `"?"` (conta como incerteza, não é somada). A **categoria é da CANON do script** — nome fora do
  dicionário NÃO entra na soma e vira warning (nunca inventa). Diurese/SNG/dreno/evacuação = sempre perda.
- `conferencia_enfermagem: {ganhos, perdas, bh}` (opcional) = o total que a enfermagem somou na folha. O motor compara
  com a soma das células e **flaga `⚠️ DIVERGE`** quando não bate — acende a luz pra revisar aquela conta (erro dela ou
  leitura duvidosa).
- Seções de prosa (`terapias`, `exame_fisico`, `evolucao`, `impressao`, `conduta`) o script só **costura** — vêm do
  LLM/texto, não são calculadas.
- **Warnings** (reclassificações, item sem `ml`, nome desconhecido) saem no stderr — sempre revisar.

**Pipeline de velocidade:** extrair os leitos em **paralelo** (um subagente por leito) → cada um cospe o JSON cru →
`build_passagem.py` consolida o `.md`. O gargalo nunca foi o banco; foi preparo sequencial + LLM calculando.

---

## 🎖️ Captura obrigatória para SOFA (6 componentes)

O escore SOFA exige os **6** componentes abaixo. Hoje 3 ficam zerados e o escore não fecha em ninguém. SEMPRE que o
insumo permitir, capture e gere o evento clínico correspondente. Quando faltar, **declare o que faltou** — nunca
silencie, nunca chute.

| Componente     | Dado                      | `tipo` do evento                | De onde vem                 |
| -------------- | ------------------------- | ------------------------------- | --------------------------- |
| Respiratório   | PaO₂/FiO₂                 | `pf_ratio` (+ `po2`)            | gasometria com pO₂ + FiO₂   |
| Coagulação     | Plaquetas                 | `plaq`                          | hemograma                   |
| Hepático       | Bilirrubina total         | `bb`                            | bioquímica                  |
| Cardiovascular | PAM + dose de vasopressor | `pam` + `nor_dose` (mcg/kg/min) | folha / BIC / prescrição    |
| Neurológico    | Glasgow                   | `gcs`                           | folha de enfermagem (neuro) |
| Renal          | Creatinina (e diurese)    | `cr` (+ `diurese_h`)            | bioquímica / folha          |

Regras:

1. **P/F**: havendo gasometria, registre `po2` E calcule `pf_ratio`. Precisa FiO₂ — se não está na gaso, busque na
   folha/ventilador; sem FiO₂ → `pf_ratio=null` + warning `missing:["fio2"]`.
2. **Bilirrubina**: bioquímica com BB total → sempre gerar evento `bb`. Ausente no painel → declarar faltante, não
   inventar.
3. **Glasgow**: extrair da folha e gerar evento próprio `gcs` (além do snapshot neuro). Sedação profunda (RASS −4/−5) →
   registrar `gcs` + `gcs_confounded_by_sedation: true`.
4. **Dose de vasopressor**: noradrenalina em BIC → converter pra mcg/kg/min (precisa peso) e gerar `nor_dose`. Sem
   peso → `nor_dose=null` + `missing:["peso"]`. É o que define o SOFA cardiovascular, mais que a PAM isolada.
5. **Ao exportar evolução**, incluir a linha `SOFA — componentes capturados: X/6 · faltando: [...]`. Transparência >
   escore falso.

**Pré-requisitos do motor v1** (ruleset `SOFA1_v1.0` — ver `docs/SOFA-RULESET.md` no repo sasi). Capturar **sem novo
tipo no banco**, anexando ao `valor_json` do evento:

6. **Suporte ventilatório**: no evento `pf_ratio`, gravar `valor_json: {"suporte_vent": "VMI"|"VNI"|"HFNC"|"none"}`. O
   motor só pontua resp 3–4 **com** suporte. Sem o dado → `"suporte_vent": null` + warning.
7. **Vasopressor por droga**: um evento por droga — `nor_dose`/`adr_dose`/`dopa_dose`/`dobuta_dose` (`valor_num` em
   mcg/kg/min) + `valor_json: {"duracao_min": N}`. **NÃO** somar drogas num evento só. Sem peso → `null` +
   `missing:["peso"]`.
8. **Sedação + GCS pré-sedação**: evento `rass` (`valor_num`) + no `gcs` gravar
   `valor_json: {"pre_sedacao": true|false, "confounded_by_sedation": true|false}`. É o que permite a imputação CNS do
   motor (carry-forward do GCS pré-sedação).
9. **Diurese diária**: com série horária, gravar `diurese_h` em mL/h. Se a folha só traz o total de 24h,
   gravar direto como tipo **`diurese_24h`** (existe desde 10-ago) — sem dividir nada, sem inventar hora.

O **cálculo** do escore (0–4 por componente) é feito a jusante, no banco (view/motor de SOFA) — a skill só garante a
**captura** dos insumos.

---

## 🗄️ Banco P0 (10-ago-2026) — o que mudou na gravação

O banco ganhou tabelas novas e regras novas. O `sasi_deploy_ingest` v1 cobre só eventos/evolução/pendências —
**o resto grava-se via MCP Supabase**, sempre depois do "deploy" do Dr. Detalhe completo e exemplos:
`references/08-p0-banco-10ago.md`. O essencial:

1. **Janela de vitais → tabela `janelas_24h`**, não mais eventos `pam_min`/`pas_min` (viraram legado).
   Max/min + contagem de excursões saem do `build_passagem.py` (o LLM não conta). Reprocessar a mesma folha
   não duplica (chave única por paciente+tipo+fim da janela).
2. **ATB → tabela `atbs`** (1 linha por curso, com `data_inicio`/`data_fim`/`duracao_planejada_dias` — o "7"
   do D7/7). D-day nunca se grava: é derivado.
3. **Cultura → `culturas` + `antibiograma`** (1 linha por antibiótico, S/I/R + CIM).
4. **Dispositivo com data → `dispositivo_episodios`** ("CVC sim (08/05)" abre; "não (15/03 a 24/03)" fecha).
   **PROIBIDO escrever em `pacientes.dispositivos`** — virou campo derivado, o banco recalcula sozinho.
5. **Evolução**: mandar `data_plantao` (data do plantão da folha) + `turno` ('diurna'/'noturna') +
   `illness_severity` ('estavel'|'watcher'|'instavel'|'critico') + `tipo_nota`. `internacao_id` NUNCA — o
   banco carimba sozinho.
6. **`custom` morreu**: vocabulário agora tem 79 tipos (troponina, proBNP, D-dímero, TP/TTPA, painel hepático,
   VHS, TSH/T4L, PVC, diurese_24h, diurese_parcial, uf_dialise, debito_dreno…). Valor sem tipo = avisar, não
   forçar `custom`.

## 🚨 Regras invioláveis

1. **Chave Gemini/Claude NUNCA no output do usuário** — se ele colar credenciais junto com a foto, extraia só a foto e
   ignore as chaves.
2. **Nenhum campo inventado**: se não está na imagem/PDF, retorne `null`. Iatrogenia é criada por "preenchimento
   automático" de valores médios.
3. **Todo output estruturado é JSON válido**: valide mentalmente antes de entregar. Se inclui JSON numa resposta
   Markdown, SEMPRE em bloco ````json`.
4. **Gravação no Supabase:** por padrão só entrega o JSON. INSERT/UPSERT via MCP tool **`sasi_deploy_ingest`** quando o
   Dr. pedir **“deploy”** ou **“salvar no Supabase”**. Sem AppSheet, sem pipeline automático.
5. **Nunca mostre reasoning clínico errado com ar de certeza** — se SOFA cardio pede peso e tu não tem, componente volta
   `null` com `missing: ["peso"]`, não chuta.
6. **Pior valor, não médio** — convenção do projeto: `pam1 = MIN` (pior PAM do período), FiO2 do pior P/F, Lac do maior
   valor.
7. **Pendência tem fonte única** — cada tarefa acionável é gerada UMA vez, no array `pendencias[]`. Os textos de export
   (Evolução, Passagem de Turno) **renderizam a partir dele**, não redigem a pendência de novo na prosa. Pendência
   escrita na Conduta **e** no array = mesma tarefa aparecendo duas vezes (uma no resumo, outra na coluna) — proibido.

---

## 🧠 Fluxo real (uso pessoal)

**Um operador (Dr. Nicolas). Sem hospital, sem multi-usuário, sem OAuth.**

Pipeline operacional:

**foto/PDF/texto no chat → Claude (esta skill) → JSON auditado → MCP grava no Supabase → frontend atualiza via
Realtime**

Claude já é multimodal — lê a folha direto, audita, monta o payload. Não existe cascata Gemini/AppSheet/iOS Shortcut nem
Edge Function `ocr-ingest` no dia a dia.

`references/06-api-automation-prompts.md` é **legado arquivado** — não usar.

---

## 📁 Referências (leia só a que for relevante pra tarefa)

- `references/00-estilo-texto-clinico.md` — **OBRIGATÓRIA antes de redigir qualquer texto** (acentuação, CAPS, setas,
  zero didática, conduta com fonte)
- `references/01-schema-eventos-clinicos.md` — DDL + dicionário de campos da tabela `eventos_clinicos` e `evolucoes`
- `references/02-extraction-dictionary.md` — O que extrair de cada tipo de documento
- `references/03-clinical-sanity-checks.md` — Ranges fisiológicos + regras de incompatibilidade
- `references/04-export-evolucao-template.md` — Template de evolução médica (SOAP adaptado SASI)
- `references/05-export-passagem-turno.md` — Template de passagem de plantão 1 página
- `references/08-p0-banco-10ago.md` — **OBRIGATÓRIA antes de gravar no banco** (tabelas novas de 10-ago)
- `references/07-export-prescricao-ordenada.md` — Ordenador de prescrição por sistema (7 blocos) + safety check
- `references/06-api-automation-prompts.md` — **LEGADO** (não usar)

---

## ⚔️ Exemplos práticos

### Exemplo 1 — Foto de folha de enfermagem

**Usuário:** *[sobe foto]* "Leito 7 UTI 3"

**Resposta esperada:** JSON de ingest com `paciente.leito=7`, `paciente.uti=UTI3`, `evolucao_snapshot` com
hemo/resp/renal preenchidos, `warnings` listando o que ficou null.

### Exemplo 2 — PDF de gasometria

**Usuário:** *[sobe PDF]*

**Resposta:** evento clínico tipo `pf_ratio` calculado do pO2/FiO2 do próprio laudo + evento tipo `lactato` se tiver
Lac.

### Exemplo 3 — Comando de exportação

**Usuário:** "Exportar evolução leito 12"

**Resposta:** você NÃO tem os dados no chat — então dispara erro cirúrgico: "Preciso do snapshot da evolução do leito
12. Cole o JSON do dashboard ou suba nova foto da folha de enfermagem." Não invente evolução do vazio.
