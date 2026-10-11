---
tags: [sasi, template, evolucao, reference]
---

# 🖋️ Exportar Evolução — Template de Nota de Prontuário (modo D2+)

Produz texto **copiável e colável** direto na evolução oficial. Estilo SOAP adaptado à realidade UTI-BR, ancorado no
TEMPLATE-BASE CANÔNICO SASI v2 (Ramo C).

> ⚙️ **ARQUITETURA SASI v2:** este template é a **mesma anatomia** da skill `admissao-uti`. A nota de evolução é o
> template-base no **modo D2+**: o eixo TEMPO é `Intercorrências 24h` (não HPMA), o `DH` é o dia real, o campo
> `Admissão (DD/MM/AA):` é **congelado** da admissão original, e os sinais vitais são a faixa Máx - Mín das 24h.
> **O bloco TEMPLATE-BASE abaixo é IDÊNTICO ao da `admissao-uti`. Alterou aqui → replica lá no mesmo commit.
Divergência = bug clínico-legal.**

**Entrada esperada:** snapshot da evolução (JSONB) + cadastrais do paciente + histórico 72h (se disponível). **Saída:**
Markdown estruturado, pronto para o prontuário eletrônico.

> 📖 **Leitura obrigatória antes de redigir:** `00-estilo-texto-clinico.md` — acentuação, CAPS, setas, zero didática,
> conduta com fonte.

---

## Estrutura fixa (IMUTÁVEL) — modo EVOLUÇÃO D2+

```
{NOME COMPLETO}, {IDADE}a{, PESO kg} — {UTI} Leito {LEITO} — DH {N}º DIA — {DATA} {TURNO}
HD / Problemas ativos:
1. {Diagnóstico/problema principal — com qualificador de gravidade/disfunção}
2. {Secundário}
3. {...}
{⚠️ ALERGIA: {agente} ({reação})  |  Alergias: nega.}

Admissão ({DD/MM/AA}): {CONGELADO da admissão original — estado de chegada, não atualiza}

Intercorrências 24h: {SÓ o que mudou no período. Eventos, picos pressóricos/febris, procedimentos, suspensões/introduções de droga, reações, deltas de débito. Verbos de ação. NUNCA descrever estado estável nem repetir o EF.}

Antecedentes: {linha única vírgula-separada; bullets se >4}

Medicamentos de uso domiciliar: {se relevante; anticoagulante em destaque}

ALERGIAS: {NEGA. / agente + reação}

Dispositivos:
IOT - {...}. CVC - {...}. Cateter arterial - {...}. SVD - {...}. SNE/SNG - {...}. Outros - {...}.

Uso:
Drogas Vasoativas: {Não / Nora X mcg/kg/min (em desmame / em escalada)}.
Sedação: {Não / agentes + doses + meta RASS}.
Antibióticos: {Não / nome + dose + intervalo + D[n] + foco}.
NPT: {...}. TNE: {...}.

Exame físico por sistemas:
Neurológico: {GCS/RASS + pupilas + déficit + sedação}.
Cardiovascular: PA {PAS_MAX}–{PAS_MIN}/{PAD_MAX}–{PAD_MIN} mmHg (PAM {MAX}–{MIN}), FC {MAX}–{MIN} bpm, {perfusão/pulsos/ausculta}. {DVA}.
Respiratório: {suporte}, FR {MAX}–{MIN} ipm, SpO2 {MAX}–{MIN}%. {ausculta}. {P/F}.
TGI: {dieta + via}, {abdome + RHA}, {débito SNG/SNE}, {evacuações}.
Renal: Diurese {valor} mL/{h}h ({mL/kg/h}), BH {valor} mL. Cr {série}, Ur {valor}. Na {valor}, K {valor}. {KDIGO/TRRC}.
Hematológico: Hb {valor} g/dL, Ht {valor}%, Plaq {valor}×10³/µL, Leuco {valor}×10³/µL. {INR/TP/TTPA}.
Infeccioso: {ATB + D[n] + foco}. {culturas + status}.
{Metabólico/Gaso: pH / pCO2 / HCO3 / SBE / Lactato — quando houver}.

Exames de imagem relevantes:
- {modalidade + data: laudo resumido — só o que muda conduta}

Scores:
SOFA {total} ({Resp}, {Coag}, {Hep}, {Cardio}, {Neuro}, {Renal}). ΔSOFA 24h: {Δ}. {qSOFA se aplicável}.

Impressão:
1. {Problema ativo} — {leitura clínica de 1 linha}.
2. {...}

Conduta estruturada por Sistemas:
1. {Sistema}: {ação + dose + meta numérica}.
2. {Sistema}: {...}.
{Profilaxias: TVP / LAMG / cabeceira / higiene oral — sempre revisar}.
{Seguimento de especialidades + pendências/contingência — as tarefas acionáveis saem do array `pendencias[]` (fonte única, ver SKILL.md regra nº 7), não redigidas soltas aqui}.

—
Assinatura: Dr. Nicolas — Intensivista
Gerado por SASI — Sistema de Auditoria e Síntese Intensiva — TEMPLATE-BASE v2.0
```

### Regras de preenchimento (valem para AMBAS as skills)

- **Sinais vitais Máx - Mín INVIOLÁVEL:** `[MÁXIMO] - [MÍNIMO]` em TODOS os parâmetros, **SpO2 incluso** (`SpO2 98 - 89 %`,
  nunca `89 - 98`). Min>max na fonte → inverte e registra no rodapé "Conferir" (nunca `(revisar)` dentro do bloco — BRIEFING §0).
- **Abreviações MAIÚSCULAS:** PAS, PAD, PAM, FC, FR, SpO2, TAX, DX, BH, HB, HT, PLAQ, LEUCO, UR, CR, NA, K. Unidades
  obrigatórias.
- **Flags de absurdo (vão para o rodapé "Conferir", fora do bloco):** PAS<50/>260 · PAM<30/>200 · FC<20/>250 · FR<4/>80 · SpO2>100/<50 · TAX<30/>43 · DX<
  20/>800 · BH>±10.000 · Nora>2. Flag não bloqueia.
- **Cabeçalho:** problemas numerados com qualificador de disfunção, nunca diagnóstico nu.
- **Impressão:** tendência dita em palavras (`em ascensão`, `em melhora`, `estável`), **sem** vetor `↑/↓/=` decorativo
  por problema — proibido desde a reforma de estilo (ver `00-estilo-texto-clinico.md` §3).
- **Conduta:** mapeamento 1:1 com Impressão, metas numéricas sempre.
- **Campo vazio:** sistema inteiro → `não avaliado`; campo isolado → omite a linha. Nunca inventa.
