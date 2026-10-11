# ✍️ Estilo de Texto Clínico — regras obrigatórias

Leitura **obrigatória antes de gerar qualquer texto** (`impressao[]`, `conduta[]`,
`pendencias[]`, resumos, exports de evolução/passagem/prescrição). Vale para todo texto que sai desta skill, gravado no
banco ou copiado pro prontuário.

**Fonte do padrão:** os `.txt`/`.docx` de evolução do próprio Dr. Nicolas (plantão UTI2, 04/05-jul-2026 — noturno e
diurno), extraídos e auditados nesta sessão. Auditoria achou 2 problemas na base de produção: (1) 0/66 itens de
`impressao`/
`conduta` gravados no Supabase tinham acento — vício de gravação, não do estilo do operador; (2) os próprios compilados
de plantão têm alguns trechos com ênfase em CAPS e preenchimento genérico que **não são o estilo do operador** e não
devem ser repetidos. As regras abaixo separam o que é **estilo do operador (preservar)** do que é **vício (banir)**.

---

## 1. Acentuação — português completo, sem exceção

Todo texto gerado (`impressao`, `conduta`, `pendencias`, resumos, docx exportado)
leva **todos os acentos** do português. Sem exceção, mesmo em campo curto ou telegráfico.

- ✅ `IRA em ascensão rápida: Cr 1,7 -> 4,2, ureia 76`
- ❌ `IRA em ascensao rapida: Cr 1,7 -> 4,2, ureia 76`

Isto corrige o vício encontrado no banco (0/66 itens sem acento) — não é uma regra nova de estilo, é a correção de um
bug de gravação.

---

## 2. CAPS — o que é permitido e o que é proibido

**CAPS permitido** (é o estilo real do operador, preservar):

- **Rótulos de seção** no formato `SISTEMA:` — `NEURO:`, `CV:`, `RESP:`, `ATB:`,
  `RENAL/HE:`, `HEMATO:`, `TGI/NUTRIÇÃO:`, `ENDÓCRINO:`, `OUTROS:` (ver §7 e
  `Terapias vigentes:` do compilado-fonte).
- **Siglas médicas consagradas**: `IRA`, `TRS`, `AVCi`, `DPOC`, `PAM`, `KDIGO`,
  `RASS`, `GCS`, `IOT`, `VM`, `CVVHDF`, `TEV`, `LAMG`, `PAV`, `ATB`, `DVA`, `TC`,
  `RM`, `EcoTT`, `ISC`, `HMA`, `AP`.

**CAPS proibido**: ênfase em palavra/expressão comum no meio da frase. Isso é vício, não estilo — se precisar de ênfase,
é negrito ou item destacado (ex.:
"⚠️ ALERGIA:"), nunca caixa alta solta na prosa.

- ❌ `DEFINIR TETO TERAPÊUTICO com a família` *(exemplo real, compilado 05-jul L10)*
- ✅ `Definir teto terapêutico com a família`
- ❌ `Respiratório: VIGILÂNCIA — SpO2 mínima 80%...` *(exemplo real, mesmo leito)*
- ✅ `Respiratório: vigilância — SpO2 mínima 80%...`
- ❌ `TRS contínua (CVVHD) URGENTE` *(exemplo real, evolução UTI3 05-jul)*
- ✅ `TRS contínua (CVVHD), urgente`

---

## 3. Setas/vetores — PROIBIDOS em qualquer texto gerado, só `->` de série sobrevive

**Regra absoluta: `↑`, `↓`, `=` (e qualquer variação — `[↑]`, `(↑2)`, seta como símbolo isolado) são PROIBIDOS em TODO
texto gerado por esta skill** — Impressão, Conduta, passagem de turno, pendência, notação de droga vasoativa/sedação e
delta de SOFA/score. Não existe exceção "decorativa": tendência sempre em **palavra**.

- Problema na Impressão: tendência em palavra — `em ascensão`, `em piora`,
  `em melhora`, `estável` — nunca `[↑]`/`[↓]`/`[=]` ao lado do problema.
    - ❌ `1. IRA em ascensão rápida [↑] — Cr 1,1 -> 3,5`
    - ✅ `1. IRA em ascensão rápida — Cr 1,1 -> 3,5`
- Droga vasoativa/sedação em desmame ou escalada: `em desmame` / `em escalada` por extenso — nunca seta.
    - ❌ `Nor 0.20↓`
    - ✅ `Nor 0,20 em desmame`
- Delta de SOFA/score: `(+2)` / `(-1)` numérico — nunca seta.
    - ❌ `SOFA 12 ↑2`
    - ✅ `SOFA 12 (+2)`

A **única sobrevivente** é `->` (ou `→`) entre **valores numéricos da mesma variável em série ao longo do tempo** — isso
é notação do próprio operador, não seta decorativa:

- ✅ `CR: 1,7 -> 2,0 -> 3,5 -> 4,2 mg/dl` *(exemplo real, compilado 05-jul L01)*
- ✅ `Hb 6,7 -> 8,7 g/dl`

**Proibido usar seta como conectivo de frase** (ligando causa/efeito ou duas ideias em prosa) — isso não é notação de
série, é atalho que quebra a leitura:

- ❌ `Febre persistente → associada Micafungina (05/07)` *(exemplo real, evolução UTI3 05-jul)*
- ✅ `Febre persistente; associada Micafungina (05/07)`
- ❌ `Aumentar ventilação-minuto (↑FR) p/ clarear CO2`
- ✅ `Aumentar ventilação-minuto (FR mais alta) para corrigir CO2` *(ver também §4 — aqui cabe cortar a explicação de
  mecanismo)*

---

## 4. Zero explicação didática / mecanismo de ação

Evolução é registro de intensivista pra intensivista — não é aula. Escreve a conduta (droga, dose, via, meta), nunca o
"porquê fisiológico" do porquê a droga funciona.

- ❌ `Gluconato de Ca 10% 20 mL EV lento — estabiliza membrana + trata iCa; meta iCa > 1,1.` *(exemplo real, evolução
  UTI3 05-jul)*
- ✅ `Gluconato de Ca 10% 20 mL EV lento; meta iCa > 1,1.`
- ❌ `Aumentar ventilação-minuto (↑FR) p/ clarear CO2 e corrigir pH` *(exemplo real, mesma evolução)*
- ✅ `Aumentar ventilação-minuto (FR); meta pH e SpO2 ≥ 94%`

---

## 5. Conduta = zero alucinação (fonte obrigatória)

Toda linha de conduta só existe se tiver fonte rastreável — texto do operador ou documento extraído (prescrição, folha,
laudo). Regras:

- **Droga com dose/via/frequência** quando prescrita — nunca solta.
- **Proibido genérico de preenchimento**: `"analgesia otimizada"`, `"conforme
  protocolo"`, `"se disponível"` e equivalentes. Se não há droga/dose/meta pra escrever, a linha não existe — não vira
  frase vaga pra "parecer completa".
    - ❌ `Hemodinâmico: investigo taquicardia sustentada; analgesia otimizada.` *(exemplo real, compilado 05-jul L12 —
      sem droga/dose na fonte)*
    - ✅ `Hemodinâmico: investigo taquicardia sustentada (dor, febre, volemia, hipercalcemia).`
- **Proibido sigla não confirmada na fonte.** Se a sigla/nome não aparece literalmente na
  prescrição/evolução/interconsulta de origem, não escreve.
    - ❌ `Cirúrgico: acompanhamento de Cirurgia Geral e GNEP` *(exemplo real, compilado 05-jul L12 — "GNEP" sem fonte
      confirmada no material do plantão)*
    - ✅ `Cirúrgico: acompanhamento de Cirurgia Geral.` *(ou, se a sigla existir na fonte, mantém — mas conferida, nunca
      suposta)*
- **Dose sem lastro é alucinação**, mesmo que farmacologicamente plausível — ex.:
  `Azul de metileno 1,5-2 mg/kg se refratário` só entra se essa dose estiver na prescrição/evolução de origem, nunca
  porque "é a dose de livro".
- **Sem fonte → a linha não existe.** Não vira `null` visível no texto nem reticências — some da lista, e some da
  Impressão também se o achado que a motivou não tiver fonte.

---

## 6. Compilado único por plantão

Um arquivo **final** por turno. Rascunho ganha sufixo `-rascunho` no nome
(`2026-07-05_clinico_evolucoes-uti2-diurno-COMPILADO-rascunho.docx`) e é **apagado**
assim que o final fechar. Nunca duas versões do mesmo plantão convivendo (achado real desta auditoria: dois compilados
divergentes do mesmo turno, `-v3` e
`-final`, com condutas diferentes para o mesmo leito — isso é o erro que esta regra existe pra impedir).

---

## 7. Esqueleto de referência (ordem fixa)

Estrutura tirada do compilado real do operador (`2026-07-05_clinico_evolucoes-
uti2-diurno-COMPILADO`, leitos L01/L02/L04/L07/L10/L11/L12) — é o esqueleto que
`04-export-evolucao-template.md` e os demais exports devem seguir:

1. Cabeçalho: `LEITO {N} — {Nome} ({iniciais}) — DH {N}º — {data} {turno}`
2. Diagnósticos/quadro atual, **numerados** (`1. 2. 3. ...`)
3. AP (antecedentes pessoais)
4. Medicações de uso domiciliar
5. Alergias
6. HMA (história da moléstia atual)
7. Dispositivos (IOT/CVC/PowerPICC/cateter arterial/SVD/SNE-SNG/outros)
8. Uso (DVA / Sedação / Antibióticos [+ prévios] / NPT / TNE)
9. Exames complementares (relevantes + prévios, com data)
10. Sinais vitais + balanço 24h (Máx–Mín, com flags `[Nx > limiar]`)
11. Laboratório (com série `->` quando houver múltiplas coletas)
12. Terapias vigentes — **por sistema**, rótulo em CAPS (`NEURO:`, `CV:`, `RESP:`,
    `ATB:`, `RENAL/HE:`, `ENDÓCRINO:`, `HEMATO:`, `TGI/NUTRIÇÃO:`, `OUTROS:`)
13. Exame físico — por sistema (Neurológico/Cardiovascular/Respiratório/TGI/ Renal/Extremidades)
14. Evolução / Eventos 24h (prosa curta, só o que mudou)
15. Impressão / Problemas ativos — **numerada**, sem vetor decorativo (§3)
16. Plano terapêutico e Condutas — **numerado por sistema**, metas numéricas
17. Profilaxias (TEV / LAMG / cabeceira) — sempre a última linha do plano
