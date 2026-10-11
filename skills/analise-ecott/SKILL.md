---
name: analise-ecott
description: Interpreta ecocardiograma para paciente de UTI adulto a partir de DOIS tipos de fonte — (A) POCUS/ultrassom point-of-care à beira-leito feito pelo próprio intensivista (VTI da VSVE, VCI, TAPSE, EPSS, E/e' simplificado, jato tricúspide) ou (B) laudo formal de ecocardiograma transtorácico do ecocardiografista (Simpson biplano, strain, PSAP, função diastólica completa). Detecta automaticamente a fonte, normaliza os achados, classifica função sistólica do VE e do VD, função diastólica e valvopatias, e dispara RED FLAGS de emergência (tamponamento, TEP/cor pulmonale agudo, SAM/obstrução dinâmica da VSVE, derrame pericárdico, FEVE gravemente reduzida). USE SEMPRE que Dr. Nicolas enviar foto/print/PDF de laudo de eco, descrever achados de eco à beira-leito, colar medidas ecocardiográficas, ou pedir "analisa o eco", "interpreta o ecocardiograma", "lê esse laudo", "avalia a função", "POCUS do leito X", "eco focado", "FEVE", "função do VD", "tem tamponamento?", "avalia derrame" — mesmo sem citar a palavra "skill". Regra ZERO ALUCINAÇÃO: achado não presente na fonte retorna null/não avaliado, NUNCA inventa. Quando há dados numéricos calculáveis (débito, RVS, PSAP, fluido-responsividade), INVOCA a skill hemodinamica-calculada. Esta skill produz a NOTA INTERPRETATIVA em texto pronto pra prontuário + opcionalmente payload Supabase. Para só calcular números, use hemodinamica-calculada direto.
---

# 🫀 Análise EcoTT — Interpretação de Ecocardiograma na UTI

Skill de leitura tática do ecocardiograma. Transforma medidas brutas (POCUS do plantonista) ou laudo formal
(ecocardiografista) em interpretação clínica acionável, com red flags na frente. **Não inventa achado** — eco é decisão
de vida, não preenchimento.

---

## 🎯 Quando disparar

Você é o **leitor + intérprete** do eco do Dr. Nicolas. Dispara quando:

- Foto/print/PDF de laudo de ecocardiograma transtorácico
- Descrição de achados de POCUS à beira-leito (texto solto)
- Medidas ecocardiográficas coladas (FEVE, TAPSE, VTI, E/e', PSAP…)
- Comandos: "analisa o eco", "interpreta esse laudo", "POCUS leito X", "avalia a função", "tem tamponamento?", "como tá
  o VD?"

**NÃO é esta skill** para: só rodar números hemodinâmicos sem interpretação → `hemodinamica-calculada` direto. Evolução
diária completa por sistemas → `sasi-ingest-export`. Admissão → `admissao-uti`.

---

## 🧭 Fluxo operacional — 4 fases

### FASE 1 — Detectar a fonte (MODO A vs MODO B)

Antes de interpretar, classifique a origem — muda os cutoffs e a confiança:

|            | MODO A — POCUS                                                                    | MODO B — Laudo formal                                                                                       |
| ---------- | --------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Quem fez   | o próprio intensivista, à beira-leito                                             | ecocardiografista                                                                                           |
| Pistas     | medidas pontuais (VTI, VCI, TAPSE, EPSS, "olhômetro" da FEVE), descrição informal | cabeçalho de laudo, Simpson biplano, strain/GLS, volumes indexados, PSAP medida, função diastólica graduada |
| Confiança  | qualitativa/semiquantitativa                                                      | quantitativa                                                                                                |
| Referência | `references/01-modo-A-pocus.md`                                                   | `references/02-modo-B-laudo-formal.md`                                                                      |

Pode haver **mistura** (POCUS com algumas medidas formais) — trate cada achado pela sua origem. Se ambíguo, assuma o
modo mais provável e siga; não interrogue.

### FASE 2 — RED FLAGS primeiro (varredura de emergência)

**ANTES** de qualquer cálculo bonito, varra `references/03-red-flags.md` para:

- **Tamponamento** (colapso diastólico de câmaras direitas, swinging heart, variação respiratória exagerada de fluxos,
  VCI pletórica)
- **TEP/cor pulmonale agudo** (McConnell, D-shape do septo, VD/VE >0,9–1,0, sinal 60/60)
- **SAM / obstrução dinâmica da VSVE** (gradiente VSVE alto + VE hiperdinâmico/hipovolêmico — conduta CONTRAINTUITIVA)
- **FEVE gravemente reduzida** / VE dilatado
- **Derrame pericárdico** (quantificar)

Red flag presente → ela abre a nota, não fica enterrada no meio.

### FASE 3 — Classificar função (por sistema do coração)

Normalize e classifique, sempre marcando a fonte de cada número:

- **VE sistólico**: FEVE (Simpson/eyeball/EPSS), VTI, classe
- **VE diastólico**: algoritmo ASE/EACVI 2016 (MODO B) ou E/e' simplificado (MODO A)
- **VD**: TAPSE, S', FAC, relação VD/VE, PSAP
- **Valvas**: estenose/insuficiência relevantes (atenção: valvopatia invalida o método VTI de débito)
- **Volume/VCI**: diâmetro, colapsabilidade/distensibilidade

### FASE 4 — Hemodinâmica + Nota + Conduta

Se há dados calculáveis (VTI, diâmetro, VCI, VRT, PAM, E/e'), **INVOQUE a skill `hemodinamica-calculada`**: monte o
JSON, rode `scripts/calc_hemo.py`, e traga débito/IC/RVS/PSAP/fluido-resp pra dentro da nota.

Saídas (uma ou mais, conforme pedido):

- **A. Nota interpretativa** (padrão): texto copiável pra prontuário. Template em `references/05-nota-template.md`.
- **B. Payload Supabase**: eventos de eco em `eventos_clinicos` (ver `04-schema-supabase.md` da skill
  hemodinamica-calculada).
- **C. Ambos.**

**CONDUTA FINAL, doses e metas** fecham a resposta, isoladas, padrão Comando Tático.

---

## 🚨 Regras invioláveis

1. **Zero alucinação.** Achado ausente na fonte → "não avaliado" ou `null`. NUNCA escreva FEVE, TAPSE, derrame ou
   qualquer achado que não veio na imagem/descrição. Inventar achado de eco em prontuário é falsificação.
2. **Red flag tem prioridade absoluta.** Tamponamento, TEP, SAM e FEVE gravemente reduzida abrem a nota. Velocidade
   salva — se há sinal de emergência, a interpretação para de ser bonita e vira ação.
3. **Marque a fonte de cada número.** "FEVE 30% (Simpson, laudo)" ≠ "FEVE ~30% (eyeball, POCUS)". A confiança muda a
   conduta.
4. **Cálculo é delegado.** Números hemodinâmicos vêm da `hemodinamica-calculada` (script determinístico), não da sua
   cabeça.
5. **Diâmetro VSVE estimado = aviso obrigatório.** Se a hemodinâmica usou diâmetro estimado, a nota carrega o alerta de
   erro quadrático e a ordem de priorizar tendência do VTI.
6. **Valvopatia quebra o VTI.** EA/IAo significativas invalidam o método de débito por VSVE — sinalize e não reporte DC
   com falsa precisão.
7. **POCUS é triagem, não laudo.** O olhômetro da FEVE e o EPSS são semiquantitativos. Em dúvida diagnóstica, recomende
   eco formal — não force precisão que a janela não dá.
8. **SAM é a armadilha mortal.** Obstrução dinâmica da VSVE em paciente hipovolêmico/hiperdinâmico se trata com VOLUME e
   RETIRADA de inotrópico — o oposto do reflexo. Se detectar, grite isso.

---

## 🧠 Modo Nerd — por que dois modos e red flags na frente

O eco na UTI tem duas naturezas que não se misturam: o **POCUS** é a Meta-Vision do Isagi — o intensivista identifica o
gol (a causa do choque) com o mínimo de passes, à beira-leito, em segundos, aceitando incerteza em troca de velocidade.
O **laudo formal** é o jogo posicional completo — precisão quantitativa, mas com latência (esperar o ecocardiografista).
A skill respeita as duas: cobra precisão do laudo e aceita a estimativa qualitativa do POCUS, sem fingir que olhômetro é
Simpson.

**Red flags na frente** é doutrina de trauma: a primeira passada do eco em hipotensão indiferenciada não é pra calcular
RVS com três casas decimais — é pra descartar as três coisas que matam em minutos (tamponamento, TEP maciço, VE parado)
e a armadilha que se trata ao contrário (SAM). O cálculo fino vem depois que o paciente não vai morrer no próximo
minuto. Erwin Smith não otimiza a formação enquanto o Titã Colossal está derrubando a muralha — ele neutraliza a ameaça
imediata primeiro.

---

## 📁 Referências (leia a relevante)

- `references/01-modo-A-pocus.md` — Cutoffs e técnica do POCUS à beira-leito (VTI, VCI, TAPSE, EPSS, E/e' simplificado)
- `references/02-modo-B-laudo-formal.md` — Laudo formal: FEVE Simpson, strain, diastólica ASE 2016, valvas, VD completo
- `references/03-red-flags.md` — Emergências: tamponamento, TEP/cor pulmonale, SAM, derrame, parada
- `references/04-protocolos-focados.md` — RUSH, FATE, padrões ecocardiográficos de cada choque
- `references/05-nota-template.md` — Template da nota interpretativa pra prontuário

A skill **hemodinamica-calculada** é invocada para todo número hemodinâmico (ela tem o script determinístico e o
mapeamento Supabase dos eventos de eco).

---

## ⚔️ Exemplos

### Exemplo 1 — POCUS à beira-leito

**Dr. Nicolas:** "POCUS leito 9: VE batendo bem no olhômetro, VTI da via 14, VCI 1,2 colabando total, TAPSE 22.
Ventilando espontâneo. PAM 58."

**Resposta:** detecta MODO A. Sem red flag. VE hiperdinâmico + VCI colapsável + VTI baixo → **padrão
hipovolêmico/distributivo**. Invoca `hemodinamica-calculada` (VTI 14, VCI colapsabilidade, diâmetro estimado) → débito
tende baixo, responsivo a volume. Nota + CONDUTA FINAL: volume e reavaliar; se não corrigir RVS, vasopressor.

### Exemplo 2 — Laudo formal (foto)

**Dr. Nicolas:** *[sobe foto de laudo]* "lê pra mim"

**Resposta:** detecta MODO B. Extrai FEVE Simpson, volumes, diástole graduada, PSAP, valvas — só o que está no laudo.
Classifica. Se FEVE baixa → red flag de disfunção sistólica abre a nota. Eventos pro Supabase se pedido.

### Exemplo 3 — Red flag SAM

**Dr. Nicolas:** "eco mostra VE hipercontrátil, gradiente na via de saída 60, SAM presente, paciente em choque pós-op"

**Resposta:** RED FLAG na frente — **obstrução dinâmica da VSVE**. Para tudo: conduta CONTRAINTUITIVA → volume +
suspender inotrópico/dobutamina + considerar betabloqueio + revisar vasodilatador. Grita o erro mortal de escalar
inotrópico aqui.
