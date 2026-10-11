---
name: controles-vitais-janela
description: >
  Transcreve scans/fotos/PDFs de FOLHAS DE CONTROLE DE ENFERMAGEM da UTI (modelo
  Beneficência Portuguesa "PLANEJAMENTO ASSISTENCIAL TERAPIA INTENSIVA ADULTO" +
  "Controle de dor / Ganhos-Perdas") e os reformata no MODELO COPIAR-E-COLAR por
  JANELA (24 h = folha inteira, 12 h = um turno), com flags de instabilidade
  [Nx > limiar]. USE SEMPRE que Dr. Nicolas enviar foto/scan/PDF de folha de
  controles, sinais vitais manuscritos, balanço hídrico de enfermagem, ou pedir
  "transcreve os parâmetros", "controles", "folha de sinais vitais", "resume o
  plantão", "sumário por janela", "formata por janela", "extrai os parâmetros",
  "passa o mapa de sinais vitais", "24h", "12h", "turno noturno/diurno" — mesmo
  sem citar a palavra "skill". Opera em ZERO ALUCINAÇÃO: campo sem fonte legível
  vira `?`, nunca é inventado. NÃO gera JSON Supabase nem nota de evolução de
  prontuário — para isso use sasi-ingest-export. Esta skill produz APENAS o
  sumário tático por janela em texto copiável + flags + conduta isolada.
---

# 🪖 controles-vitais-janela — Transcrição Tática de Folhas de Controle

> Fonte única consolidada em 24-jun-2026 a partir de 3 versões divergentes
> (SKILL.md completo + SINAIS_VITAIS enxuto + EXTRAÇÂO_EVOLUÇÂO V2). Base = a
> versão completa; modelo de saída alinhado ao `references/exemplo-resolvido.md`
> (contrato de saída padrão-ouro). Alterou aqui? É a única cópia — não fork.

## Amostras de folha (md)

Três PDFs reais convertidos para referência de layout (texto OCR fraco — scan manuscrito):

- `references/amostras/folha-uti2-2026-05-10.md`
- `references/amostras/sinais-uti2-2026-06-21.md`
- `references/amostras/prescricao-uti2-2026-06-21.md`

Transcrição operacional continua vindo da foto/PDF que o Dr. enviar no plantão.

## Missão

Pegar a folha bruta de enfermagem (manuscrita, fotografada, escaneada) e cuspir, por leito, um bloco **copiar-e-colar**
com os parâmetros agregados na janela (Máx - Mín) + a contagem de eventos que cruzaram limiar clínico. É um raio-X da
gestão do plantão: quem só lê a paisagem perde o predador escondido no mato.

**Escopo:** transcrição + sumário por janela. NADA além disso.

- Quer JSON pro Supabase ou nota de evolução? → `sasi-ingest-export`.
- Quer nota de admissão? → `admissao-uti`.

---

## ⛔ DOUTRINA ZERO ALUCINAÇÃO (não-negociável)

1. Campo ilegível / ausente → `?`. NUNCA estimar, nunca preencher por inferência.
2. Sinal vital sempre em **Máx - Mín** (ex.: FC 110 - 72), SEM EXCEÇÃO — inclusive SpO2.
3. Valor de fonte digitada > manuscrita em caso de conflito. Registrar discrepância.
4. Rótulo de bomba/droga (BIC) só é nomeado se legível; senão `BIC ilegível`. Se compatível mas incerto (ex.: "NORA" ≈
   noradrenalina) → nomear + `CONFIRMAR`.
5. PAM em parênteses é o valor mais confiável (calculado). Em conflito Sist/Diast vs PAM, ancorar na PAM e marcar o
   resto como incerto.

---

## 🎯 RECONHECIMENTO DE INPUT

Dispara quando o documento contém qualquer um:

- Cabeçalho "PLANEJAMENTO ASSISTENCIAL TERAPIA INTENSIVA ADULTO" (folha de SV).
- Cabeçalho "Controle de dor - Escala Utilizada" / grade "Ganhos / Perdas" (balanço).
- Tabela horária 7→6 (q2h) com colunas T, FR, FC, PA, Glicemia, Saturação.
- Foto de sinais vitais manuscritos / balanço hídrico.

Um PDF costuma trazer **vários leitos**, cada um com **2 páginas** (SV + balanço). Parear SV+balanço pelo nome/leito do
cabeçalho antes de montar o bloco.

---

## 🕐 LÓGICA DE JANELA (24 h vs 12 h)

A folha cobre 24 h em 2 turnos de 6 aferições q2h:

- **Turno diurno (6–18 h):** linhas 7, 9, 11, 13, 15, 17 (+ 8,10,12,14,16,18).
- **Turno noturno (19–6 h):** linhas 19, 21, 23, 1, 3, 5.
- Total: 12 aferições / 24 h.

Regra de decisão:

- Default = **24 h** (todas as aferições; contagem de eventos mais completa). Evolução diurna também usa 24 h
  (07 h do dia anterior até 05 h) — recortar só a noite foi o erro de 11/10/2026.
- Se o Tenente disser "12 h", "turno", "noturno", "diurno", "meu plantão" → recortar SÓ o turno pedido (6 aferições) e
  rotular a janela corretamente.
- Rotular SEMPRE no cabeçalho do bloco a janela usada ("Sinais Vitais 24 h" /
  "12 h noturno"). Nunca rotular 12 h em cima de dado de 24 h, nem vice-versa.

---

## 📊 MAPA DE EXTRAÇÃO

Layout completo da folha em `references/mapa-folha.md`. Resumo operacional:

### Folha de Sinais Vitais

- Ordem das colunas: Hora · T · FR · FC · PA (Sist/Diast (Méd)) :00h e :30h · Glicemia mg/dl · Saturação Arterial ·
  Dor · PVC · RASS · Suporte (Cateter O2, Nebulização, Modalidade, Peep, FiO2).
- **Armadilha FR×FC:** a caligrafia às vezes inverte. Desambiguar por fisiologia:
  o número 60–140 é FC; 8–35 é FR. Não copiar cego pela posição.
- PA: registrar Sist/Diast com PAM em parênteses → `118/60 (62)`.
- Suporte: "AA" = ar ambiente; "1L/2L" = cateter nasal; senão transcrever literal.

### Folha de Balanço (Ganhos / Perdas)

- Ganhos: Nutrição (VO/dieta/SNE) · Endovenoso (bomba) · Infus. Rápida · Dil.
- Perdas: Diurese · SNG/SNE · Evacuação · Resíduo Gástrico · Dreno.
- **Balanço = soma das CÉLULAS, nunca o total escrito à mão** (corrigido 11/10/2026; ver docs/BRIEFING.md §4).
  Os rodapés `Ganhos 6-18h`, `Ganhos 19-6h`, `D:` e `BH:` servem só de CONFERÊNCIA. Divergência vai para o
  rodapé da resposta, fora do bloco. A conta é do motor `skills/sasi-ingest-export/scripts/build_passagem.py`.
  Exemplo real (11/10/2026, UF de CVVHDF): rodapé diurno 960 ml; células 70 ml/h × 4 + 80 ml/h × 8 = 920 ml.
- **Ingesta** = soma das células de ganho dos dois turnos (rodapé só confere).
- **Evacuação:** contar + qualidade + quantidade (ex.: "4x líquida +++/4"). Sem registro legível →
  `s/ registro legível`.

---

## 🚩 DICIONÁRIO DE LIMIARES (as flags)

Contar eventos com desigualdade ESTRITA, dentro da janela escolhida. Mostrar o colchete SÓ quando a contagem ≥ 1 (linha
limpa quando 0 — sinal alto).

| Parâmetro     | Flag          |
| ------------- | ------------- |
| PAS           | `[Nx < 90]`   |
| PAD           | `[Nx < 50]`   |
| PAM           | `[Nx < 65]`   |
| FC            | `[Nx > 100]`  |
| FR            | `[Nx > 20]`   |
| SpO2          | `[Nx < 92]`   |
| TAX           | `[Nx < 35,5]` |
| Dx (glicemia) | `[Nx > 180]`  |

`Dx` lista os valores aferidos separados por ` / ` (maior → menor), ex.:
`Dx: 337 / 246 mg/dl [2x > 180]`.

---

## 📐 TEMPLATE DE SAÍDA (copiar-e-colar — MANTER LIMPO)

Um bloco por leito. No MODO EXTRAÇÃO PURA, devolver EXCLUSIVAMENTE o texto do modelo: sem introdução, sem saudação, sem
explicação dentro do output clínico.

### Regras de formatação (invioláveis)

- Título do bloco: `LEITO XX — NOME, IDADE+SEXO` (ex.: `LEITO 04 — LUIZ J. G., 80M`).
- Títulos de seção: só a primeira letra maiúscula ("Sinais vitais 24 h", "Laboratório").
- Abreviaturas SEMPRE maiúsculas: PAS, PAD, PAM, FC, FR, SpO2, TAX, DX, BH, HB, HT, PLAQ, LEUCO, UR, CR, MG, NA, CAI, K,
  P.
- Intervalos estritamente `[Máximo]–[Mínimo]` (ex.: `PAS: 120–80`).
- Dextros: `Dx: v1 / v2 / v3 mg/dl` (maior → menor).
- Observação original ao lado do item, entre parênteses (ex.: `(1x < 92)`, `Cateter nasal O2 2L`).
- Unidades obrigatórias (padrão UTI se faltar): mmHg, bpm, rpm, %, ºC, mg/dl, mEq/L, mmol/L, ml, /mm3.
- Decimais com vírgula BR original (`36,8` · `1,3`).
- Sequência de lab seriado com seta ` -> ` (ex.: `UR: 44 -> 50 -> 42 mg/dl`).
- AUSÊNCIA DE DADO → OMITE a linha/variável. Nunca traço, nunca valor inventado.
- `Sup O2`: ar ambiente/cateter → entre parênteses no fim da linha do SpO2 (`SpO2: 98 - 92 % (AA)`);
  ventilação mecânica → linha própria logo depois do Dx (`Sup O2: VM por TQT, PCV, PEEP 7, FiO2 40 %`).
  Nunca na linha da diurese. (Corrigido 11/10/2026 para bater com docs/BRIEFING.md.)

### Modelo exato (repetir o bloco por paciente)

```
LEITO XX — NOME, IDADE+SEXO

Sinais Vitais [JANELA]:
PAS: max - min mmHg [Nx < 90]
PAD: max - min mmHg [Nx < 50]
PAM: max - min mmHg [Nx < 65]
FC: max - min bpm [Nx > 100]
FR: max - min rpm [Nx > 20]
SpO2: max - min % [Nx < 92] (AA ou cateter)
TAX: max - min ºC [Nx < 35,5]
Dx: v1 / v2 / v3 mg/dl [Nx > 180]
Dieta: ... | Ingesta: ... ml
Evacuação: ...
Diurese: ... ml
BH: ± ... ml

Laboratório:
HB: ... g/dl | HT: ... % | PLAQ: ... /mm3
LEUCO: ... /mm3 ( segmentados/bastonetes )
UR: v1 -> v2 mg/dl
CR: v1 -> v2 mg/dl
MG: ... mg/dl | NA: ... mEq/L | CAI: ... mmol/L | K: ... mEq/L | P: ... mg/dl

Outros:
[Drenos, resíduo gástrico, parâmetros hemodinâmicos, peso, dispositivos, BIC/DVA, etc.]
```

- Linha sem violação → omitir o colchete.
- Seção (Laboratório / Outros) sem nenhum dado → omitir a seção inteira.
- BIC suspeita de droga vasoativa → linha em "Outros": `⚠ BIC c/ rótulo compatível com X (CONFIRMAR)`.

### Validação de sanidade (HITL) — registrar NO RODAPÉ (fora do bloco) quando:

1. **Inversão** `[Mínimo] > [Máximo]` em PAS/PAM/FC/FR/SpO2 → inverter a ordem na saída e registrar no rodapé.
2. **SpO2 > 100**.
3. **Caracteres misturados** (letra dentro de número, ex.: `12O`).
4. **Absurdo fisiológico:** PAS <50 ou >260 · PAM <30 ou >200 · FC <20 ou >250 · FR <4 ou >80 · SpO2 <50 · TAX <30 ou >
   43 · DX <20 ou >800 · Diurese <0 ou >5000 · BH <−5000 ou >+5000.

Flag não bloqueia: o valor sai limpo no bloco e a dúvida vai para o rodapé "Conferir". O médico decide (HITL).
Nada de `(revisar)` dentro do bloco colável (BRIEFING §0, lei 1).

---

## 🔴 HEURÍSTICA DE FLAG CRÍTICO (pós-blocos, FORA do texto colável)

Marcar como vermelho o leito que bater ≥ 1:

- PAM < 65 sustentada (≥ 3 aferições) ou PAM ≤ 55 em qualquer ponto.
- Oligúria (diurese < ~0,5 mL/kg/h estimada) + BH muito positivo (> +1000).
- FC > 100 sustentada + hipotensão na mesma janela.
- SpO2 < 92 recorrente apesar de suporte O2.
- Dx > 250 recorrente (descontrole glicêmico).
- BIC de vasopressor identificada/suspeita. Esses pedem reavaliação AGORA, não no próximo round.

---

## 🗣️ MODOS DE RESPOSTA

- **MODO EXTRAÇÃO PURA (default p/ pedido estruturado):** devolver SÓ os blocos do template — sem SITREP, sem comentário
  tático, sem CONDUTA FINAL. Nada além do modelo.
- **MODO BRIEFING (quando pedir "passagem", "leitura tática", "resume o plantão"):**
  abrir com SITREP curto (folha, janela, nº leitos) → blocos limpos → DEPOIS dos blocos, flags vermelhos + comentário
  tático (fora do texto colável) → `CONDUTA FINAL` isolada (prioridades por leito, metas numéricas, doses SÓ se houver
  fonte legível).
- Raciocínio quando pedido: Chain-of-draft, ≤ 5 palavras por passo, conclusão após `####`.

---

## 💊 MÓDULO B — TERAPIAS VIGENTES POR SISTEMA

Dispara com: "terapias por sistema", "prescrição por sistema", "agrupa a prescrição",
"conduta por sistema", "medicações por sistema" — ou como adendo do handoff. Pega a PRESCRIÇÃO vigente (eletrônica
digitada + manuscritos) e reorganiza as terapias ATIVAS por aparelho/sistema. Um bloco copiar-e-colar por leito.

### Zero alucinação (mesma doutrina)

- Fonte digitada > manuscrita. Marca como escrita + genérico entre parênteses só se o mapeamento for SEGURO; incerto →
  `(CONFIRMAR)`.
- Droga ilegível → `?`. Nunca inventar dose/via/frequência.
- ATB SEMPRE com início (`I: dd/mm` ou `D0`). DVA/BIC SEMPRE sinalizada.
- Diluição/dose: conferir e marcar `(revisar)` se fora do racional (ex.: Nora > 2 mcg/kg/min).

### Ordem canônica (omitir sistema vazio)

NEURO (sedação/analgesia/antipsicótico/anticonvulsivante) → CV (DVA, antiarrítmico, anti-HTN, BB, antiagregante) → RESP
(broncodilatador, inalatório, suporte O2/VNI) → ATB/INFECC (com início) → RENAL/HE (diurético, reposição) →
ENDÓCRINO/METAB (insulina, hipoglicemiante, controle Dx) → HEMATO (anticoag/profilaxia TEV, hemocomponentes) →
TGI/NUTRIÇÃO (IBP, dieta, NPT, TNE, procinético) → PROFILAXIA/PELE/OUTROS → DISPOSITIVOS.

### Template (copiar-e-colar, limpo)

```
LEITO XX — NOME — Terapias vigentes por sistema:
NEURO: ...
CV: ...
RESP: ...
ATB: ... (I: dd/mm)
RENAL/HE: ...
ENDÓCRINO: ...
HEMATO: ...
TGI/NUTRIÇÃO: ...
DISPOSITIVOS: ...
```

### Filtro HANDOFF (modo enxuto — default no briefing de plantão)

Quando o output for passagem de turno, OMITIR do bloco:

- Protocolo de correção glicêmica: "insulina conforme dextro" e "G50% se DX<70".
- Toda medicação SN (se necessário) e ACM (a critério médico). Manter SOMENTE: terapia fixa/programada, infusões
  contínuas/BIC, ATB (com início), insulina basal/fixa (ex.: Lantus, Humalog horário fixo), dieta/NPT/TNE, dispositivos.
  Item SN/ACM clinicamente crítico (ex.: anticoagulante com plaquetopenia, transfusão)
  sai do bloco mas vai para os flags táticos — nunca some do radar.

### Flags críticos de terapia (fora do bloco)

- DVA / vasodilatador em BIC ativo → marcar.
- ATB > 7 dias ou sem data → revisar duração / descalonamento.
- Anticoagulante prescrito + PLQ < 50k ou sangramento ativo → CONFLITO, confirmar.
- Hemocomponente em curso → registrar + recoletar controle pós.

---

## 📋 MÓDULO C — BLOCO UNIFICADO DE HANDOFF / EVOLUÇÃO (default da passagem)

Quando o pedido for o briefing de plantão / evolução completa, entregar UM bloco copiar-e-colar por leito.

### SEQUÊNCIA CANÔNICA (corrigida 11/10/2026 — fonte única: docs/BRIEFING.md)

A versão de 21/06/26 deste módulo não tinha Laboratório e usava títulos diferentes do BRIEFING.
Valem a ordem e os títulos do BRIEFING:

1. Sinais vitais + balanço [janela, default 24 h]
2. Laboratório (séries com ` -> `; gasometria aqui)
3. Terapias vigentes (por sistema; Filtro HANDOFF do Módulo B)
4. Exame físico (copiado da evolução anterior — o médico altera ao "canetar"; sem labs)
5. Evolução / Eventos 24 h (só o delta)
6. Impressão / Problemas ativos (sem setas)
7. Plano terapêutico e Condutas (ação 1:1 com cada problema + meta numérica + profilaxias)

Na evolução do dia vai SÓ isso. Identificação, HPMA, antecedentes, dispositivos e exames antigos já estão no
prontuário e não são repetidos.

Regras:

- Cabeçalho `LEITO XX — NOME COMPLETO — DIA DE UTI — DATA TURNO` em linha isolada.
- Janela e flags dos vitais seguem o Módulo A.
- Dieta (tipo) na linha de balanço; detalhe de NPT/TNE/produto/vazão em TGI/NUTRIÇÃO.
- ORTOGONALIDADE DE EIXOS: Eventos = só o delta; Exame físico = só estado; Impressão = problema + tendência em
  palavra (em ascensão/em melhora/estável), sem seta; Plano = ação 1:1 com cada problema + meta numérica.
- Linha/sistema/bloco sem dado → omitir. Observação/divergência → rodapé "Conferir", fora do bloco.
- Template completo e checklist: `docs/BRIEFING.md`. Conta: motor `build_passagem.py`.
  Entrega em Word: `gerador/gerar_docx.py` (ver `docs/formato-entrega.md`).

---

## ✅ CHECKLIST DE EXECUÇÃO

1. Identificar todos os leitos e parear SV + balanço.
2. Definir janela (default 24 h; recortar turno se pedido) e rotular.
3. Transcrever q2h sob zero alucinação (`?` no ilegível; FR×FC por fisiologia).
4. Passar as séries cruas ao motor (`skills/sasi-ingest-export/scripts/build_passagem.py`): ele faz Máx - Mín,
   flags e balanço somando CÉLULAS. O LLM não faz conta.
5. Extrair Sup O2 / Dieta / células de ganho e perda / Evacuação; rodapé da folha só para conferência.
6. Detectar BIC/DVA e dispositivos; marcar `CONFIRMAR` se incerto.
7. Montar blocos limpos → comentário tático + flags vermelhos → CONDUTA FINAL isolada.

Worked example completo em `references/exemplo-resolvido.md`. Entrega em Word (evolução + ficha-cola):
`gerador/gerar_docx.py`, formato em `docs/formato-entrega.md`.
