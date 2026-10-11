# 🎖️ Exportar Turno — Passagem de Plantão 1 Página

Formato condensado, **uma folha A4 por paciente** ou **painel 33-leitos** (estilo "status ops board"). O objetivo é
sobreviver à passagem de plantão de 33 leitos em < 30 min.

> 📖 **Leitura obrigatória antes de redigir:** `00-estilo-texto-clinico.md` — acentuação, CAPS, setas, zero didática,
> conduta com fonte.

---

## 📐 Formato A — Passagem individual (1 paciente)

Use quando o comando é `"passar turno leito 7"` ou similar.

```markdown
╔═══════════════════════════════════════════════════════════════╗
║  PASSAGEM — Leito {LEITO} {UTI} — {DATA_TURNO}                ║
╚═══════════════════════════════════════════════════════════════╝

🏷️  {NOME}, {IDADE}a, {PESO}kg · DH {DIAS}º · HD: {HD}
⚠️  Alergias: {ALERGIAS_OR_NEGA}

📊 SOFA {SOFA} (Δ24h {DELTA_SOFA}) · qSOFA {QSOFA} · gravidade: {GRAVIDADE}

─── STATUS POR SISTEMA (pior valor 24h) ────────────────────────
🧠 NEURO    {GCS_OR_RASS}  ·  {SEDACAO_SE_ATIVA}
🫁 RESP     {SUPORTE}  ·  FiO2 {FIO2}%  ·  SpO2 {SPO2}%  ·  P/F {PF}
🫀 HEMO     PAM {PAM_MIN} · FC {FC_MAX}  ·  {DVAS_LINHA}
💧 RENAL    DU {DU_ML_KG_H} mL/kg/h  ·  BH {BH}  ·  Cr {CR} ({KDIGO})
🩸 HEMATO   Hb {HB} · Plaq {PLAQ} · INR {INR}
🦠 INFEC    {ATBs_D_X} · {CULTURAS_ATIVAS}

─── PONTOS DE ATENÇÃO ───────────────────────────────────────────
🚨 {ALERTA_1}
🚨 {ALERTA_2}

─── TAREFAS PENDENTES PRÓXIMO TURNO ────────────────────────────
☐ {TAREFA_1}
☐ {TAREFA_2}
☐ {TAREFA_3}

─── SE PIORAR ──────────────────────────────────────────────────
{PLANO_RESCUE}
═════════════════════════════════════════════════════════════════
```

### Regras de preenchimento

- **Pior valor 24h**: sempre o mais grave (PAM min, FC max, SpO2 min, Cr max).
- **DVAs linha única, sem seta decorativa**: `Nor 0,20 em desmame · Vaso 0,04` (ou `em escalada`) — tendência dita em
  palavra, não com `↑/↓` (ver `00-estilo-texto-clinico.md` §3).
- **ATBs com D-X**: `Merop D-3 · Linez D-5` (X = dias de terapia).
- **Alertas**: apenas o que REALMENTE muda decisão no próximo turno. Máximo 3.
- **Tarefas pendentes**: checkbox, imperativa, com horário se crítico (`☐ SBT 10h`). **Fonte única = array
  `pendencias[]`** do payload (uma linha por item, ordenar por `prioridade`). Este bloco RENDERIZA o array — não redija
  a tarefa aqui de novo se ela já está no array (ver regra inviolável nº 7 do SKILL.md). Uma tarefa que ainda não está
  no array deve ser adicionada AO array, não escrita solta aqui.
- **Plano rescue**: o que fazer se deteriorar. Curto, decisivo
  (`PAM < 60 → retoma Nor 0.25 + bolus SF 500; SpO2 < 90 → sedação profunda + aumentar PEEP 10`).

---

## 📐 Formato B — Painel 33-leitos (visão da UTI inteira)

Use quando o comando é `"passar turno UTI"` ou `"passagem geral"`. Output é tabela densa.

```markdown
# 🪖 Painel SASI — Passagem {DATA_TURNO}

## UTI 2 — 12 leitos

| L   | Paciente  | Idade | HD (resumido)             | SOFA | ΔSOFA | Sup | DVA               | Alerta principal    |
| --- | --------- | ----- | ------------------------- | ---- | ----- | --- | ----------------- | ------------------- |
| 01  | Silva, M. | 72a   | Choque cardiogênico       | 12   | +2    | VM  | Nor 0.6 · Dobu 10 | Lactato 5.2 subindo |
| 02  | Souza, A. | 45a   | TCE grave + VM prolongada | 8    | 0     | VM  | —                 | PIC 18 estável      |
| ... |           |       |                           |      |       |     |                   |                     |

## UTI 3 — 13 leitos
...

## UTI 4 — 8 leitos
...

## 🔴 TOP 5 — Pacientes críticos do turno
1. **L1 UTI2** — Silva, M. — SOFA 12 (+2), Nor 0,6 escalando, lactato não clareia. Avaliar ECMO VA.
2. **L7 UTI3** — João Silva — ΔSOFA -1 (melhora), mas IRA KDIGO 2. SBT hoje 10h.
3. ...

## ⏰ AGENDA DO TURNO
- 07h — Round conjunto com CCIH (L3 UTI4 — candiduria)
- 09h — TC abdome L7 UTI3 (controle pós-op)
- 10h — SBT L7 UTI3
- 14h — Família L1 UTI2 (conversa fim de vida)
```

---

## 🔧 Regras de compressão (caber em 1 página)

Regras de corte brutais:

1. **Sem verbos supérfluos**: `Paciente apresenta PAM de 62` → `PAM 62`. Corta artigos, pronomes, conjunções.
2. **Abreviaturas padrão UTI**: `VM` = vent mecânica, `CN` = cateter nasal, `BH` = balanço, `DU` = diurese, `HD` =
   hipótese diagnóstica, `DH` = dia de hospitalização.
3. **Unidades implícitas**: `PAM 62` (mmHg), `Cr 1.8` (mg/dL), `Plaq 180` (×10³/µL). Só escreve unidade se fora do
   padrão.
4. **Doses de DVA sem unidade** (convenção do plantão): `Nor 0.20` = 0.20 mcg/kg/min.
5. **Corta cronologia**: não escreve "às 06h a PAM estava em 62 e às 10h subiu pra 70". Escreve: `PAM 62→70`.
6. **Corta hedging**: não escreve "provavelmente por causa de...". Escreve: `provável sepse → aumentar PEEP`.

---

## 🧠 Modo Nerd — Information density como arma

Estudos de handoff (Arora 2005, JAMA) mostram que **falhas de passagem de plantão = 80% dos erros evitáveis em UTI**. A
solução dos meta-análises: **standardized handoff (I-PASS, SBAR)** reduz falhas em 30–50%.

Este formato é **SBAR-UTI-compactado**: Situation (cabeçalho) → Background (HD + DH) → Assessment (status por sistema +
SOFA) → Recommendation (tarefas + rescue). Comprimido para densidade informacional ≥ 2 bits por cm² de papel.

O truque do painel 33-leitos é o mesmo que Erwin Smith usa na reunião de comandantes: **cada leito é um ponto no mapa**,
cada número é uma métrica de ameaça. O plantonista não lê — *scanea*. E num round onde tu tem 30s por leito, a
informação precisa estar pre-indexada pelo teu córtex visual, não pelo teu hipocampo.

**Por que TOP 5 separado**: Pareto. 5 pacientes puxam 80% da carga cognitiva do plantão. Isolar eles força a atenção do
entrante onde importa.
