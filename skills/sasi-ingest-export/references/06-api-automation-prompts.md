# ⛔ LEGADO — NÃO USAR

> **Arquivado 24-jun-2026.** O fluxo operacional é: **Claude no chat → JSON → MCP (`deploy`)**.
> Sem iOS Shortcut, sem Gemini Vision, sem AppSheet, sem POST em `ocr-ingest`.

---

# 🤖 Prompts de Automação — iOS Shortcut / n8n / cURL direto (LEGADO)

Quando não dá pra abrir o Claude no chat (round, meio de procedimento, contexto de emergência), dispara o atalho do iPad
e o pipeline roda sozinho: **Gemini Vision (extração crua) → Claude API (auditoria clínica + payload) → POST na Edge
Function `ocr-ingest`**.

Aqui estão os prompts exatos. Cada um é copiar-e-colar direto no Atalho ou no workflow n8n.

---

## 🎯 Arquitetura simplificada (sem AppSheet, sem Sheets)

```
📸 Foto (iPad botão de ação)
   │
   ▼
┌─────────────────────────────────┐
│ 1. Gemini 2.5 Flash Vision      │  ← extração crua (texto + coords)
│    (Google API direto)          │
└─────────────────────────────────┘
   │  texto extraído
   ▼
┌─────────────────────────────────┐
│ 2. Claude Sonnet 4.6 API        │  ← audita + estrutura JSON
│    (Anthropic API direto)       │
└─────────────────────────────────┘
   │  JSON payload
   ▼
┌─────────────────────────────────┐
│ 3. Supabase Edge Function       │  ← valida + insere
│    POST /functions/v1/ocr-ingest│
└─────────────────────────────────┘
   │
   ▼
  📊 Frontend React atualiza via Realtime
```

**Vantagem sobre o pipeline antigo AppSheet/Sheets**: 3 hops em vez de 6, latência ~3s em vez de ~30s, RLS respeitado,
sem intermediário proprietário.

---

## 📋 PROMPT 1 — Gemini Vision (extração crua)

Use este prompt no corpo JSON da chamada `generateContent`:

```
Você é o estágio de EXTRAÇÃO BRUTA de um pipeline médico. Sua única função é ler a imagem e transcrever literalmente TODOS os números, siglas, datas, horários, nomes de drogas e palavras-chave clínicas — preservando a disposição espacial e as vírgulas decimais do português brasileiro.

REGRAS:
1. NÃO interprete clinicamente. NÃO calcule. NÃO converta unidades.
2. Preserve vírgulas decimais: "37,5" permanece "37,5" (nunca "37.5").
3. Se um valor está ilegível, escreva "[ILEGÍVEL]" no lugar — jamais chute.
4. Se há tabela, reproduza com pipes markdown.
5. Para cada valor, registre o contexto espacial (qual coluna/linha/horário).
6. Preserve unidades originais (mmHg, bpm, mL, mcg/kg/min, etc).

OUTPUT: JSON com três campos:
{
  "tipo_documento": "folha_enfermagem | lab_bioquimica | lab_hemograma | lab_gasometria | lab_coag | lab_cultura | laudo_imagem | prescricao | desconhecido",
  "texto_extraido": "<transcrição completa em markdown preservando layout>",
  "campos_ilegiveis": ["PAM das 14h", "nome da droga linha 3", ...]
}

Apenas o JSON. Sem preâmbulo, sem markdown blocks.
```

**Endpoint:**

```
POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}
```

**Body:**

```json
{
  "contents": [{
    "parts": [
      { "text": "<PROMPT ACIMA>" },
      { "inline_data": { "mime_type": "image/jpeg", "data": "<BASE64_DA_FOTO>" } }
    ]
  }],
  "generationConfig": {
    "temperature": 0,
    "responseMimeType": "application/json"
  }
}
```

---

## 🧠 PROMPT 2 — Claude API (auditoria clínica + payload final)

Use este system prompt + user message:

### System Prompt

```
Você é o motor de auditoria clínica do SASI (Sistema de Auditoria e Síntese Intensiva — UTI 33 leitos). Recebe a saída bruta do estágio Gemini Vision e converte em payload JSON validado para a tabela Supabase `eventos_clinicos` + snapshot de `evolucoes`.

REGRAS DE OURO:
1. ZERO ALUCINAÇÃO: campo ausente ou ilegível → null + warning. Nunca invente.
2. Vírgula BR: mantenha "37,5" como string; o backend tem parseFloatBR.
3. Plaquetas: se valor 1000-10000 sem unidade → flag plaq_unit_ambiguous.
4. Ranges fisiológicos: SpO2>100, pH<6.8 ou >7.8, PAM<30 ou >180 → physiological_error.
5. DVA dose absurda (Nor>2mcg/kg/min) → flag dose_absurd.
6. Timestamp: preserve se na imagem, senão use now() + ts_inferred:true.
7. Leito/UTI: se ausente no input, retorne "requires_leito: true" e pare.

SCHEMA DE OUTPUT (obrigatório):
{
  "$schema": "sasi-ocr-ingest/v1",
  "extracted_at": "ISO8601",
  "source": { "type": "...", "fonte": "claude_ocr", "confidence_overall": 0.0-1.0, "warnings": [...] },
  "target": { "uti": "UTI2|UTI3|UTI4", "leito": "N", "paciente_id": null },
  "paciente_upsert": null ou objeto,
  "evolucao_snapshot": null ou objeto completo,
  "eventos_clinicos": [ { ts, tipo, valor_num, unidade, confidence, source_text, requires_review } ]
}

Tipos válidos de evento: sofa_total, sofa_resp, sofa_coag, sofa_liver, sofa_cardio, sofa_neuro, sofa_renal, pam, pam_min, pf_ratio, lactato, diurese_h, bh_h, temp, fc, fr, spo2, hb, plaq, cr, ur, leuco, na, k, bb, inr, nor_dose, adr_dose, vaso_dose, dobuta_dose, gcs, rass, cam_icu, custom.

Retorne APENAS o JSON. Sem markdown code blocks, sem preâmbulo.
```

### User Message (preenchido pelo Atalho)

```
UTI: {UTI_SELECIONADA}
Leito: {LEITO_SELECIONADO}
Peso registrado (se disponível): {PESO_SELECIONADO}
Plantão: {PLANTAO_ATUAL}

Saída do Gemini Vision:
{JSON_RETORNADO_PELO_GEMINI}

Gere o payload SASI.
```

**Endpoint:**

```
POST https://api.anthropic.com/v1/messages
Headers:
  x-api-key: {CLAUDE_KEY}
  anthropic-version: 2023-06-01
  content-type: application/json
```

**Body:**

```json
{
  "model": "claude-sonnet-4-6",
  "max_tokens": 4000,
  "system": "<SYSTEM PROMPT ACIMA>",
  "messages": [
    { "role": "user", "content": "<USER MESSAGE ACIMA>" }
  ]
}
```

---

## 📤 PROMPT 3 — Edge Function (apenas HTTP, sem prompt)

O Atalho faz o terceiro POST direto na Edge Function:

```
POST https://idswehsvvqczzkiatuzu.supabase.co/functions/v1/ocr-ingest
Headers:
  Authorization: Bearer {SUPABASE_ANON_KEY}
  apikey: {SUPABASE_ANON_KEY}
  Content-Type: application/json
Body: <JSON retornado pelo Claude>
```

Response:

```json
{
  "ok": true,
  "paciente_id": "uuid",
  "evolucao_id": "uuid ou null",
  "eventos_inseridos": 7,
  "warnings": [...],
  "requires_review": ["uuid_evento_1", ...]
}
```

Se `ok: false`, exibe erro no Atalho (toast) + salva payload local em Notes pra retry.

---

## 📱 Receita completa do Atalho iOS "SASI Scan"

Ordem das ações:

1. **Tirar Foto** (ou selecionar da câmera)
2. **Menu de escolha**: `[UTI 2, UTI 3, UTI 4]` → variável `uti`
3. **Menu de escolha**: `[Leito 1...Leito N]` filtrado pela UTI → variável `leito`
4. **Menu de escolha**: `[Manhã, Tarde, Noite]` → variável `plantao`
5. **Codificar com Base64** (a foto) → variável `foto_b64`
6. **Obter Conteúdo de URL** (Gemini) com o prompt 1 → variável `gemini_output`
7. **Obter Conteúdo de URL** (Claude) com o prompt 2 + `gemini_output` → variável `claude_payload`
8. **Obter Conteúdo de URL** (Edge Function) com `claude_payload` → variável `supabase_response`
9. **Se `ok: true`**: **Ler Texto** de `eventos_inseridos + warnings.length` (tipo "7 eventos inseridos, 2 warnings")
10. **Se `ok: false`**: **Criar Nota** no app Notes com o payload + erro, pra retry manual

### Atalho gatilho

- **Botão de Ação** (iPad Pro M4) → dispara direto
- **Widget grande** na tela inicial (visibilidade TDAH-friendly)
- **Siri**: "SASI scan"

---

## 🔒 Segurança de chaves no Atalho

- **NUNCA hardcode chaves nos Atalhos compartilháveis.** Use o app **Data Jar** (App Store) ou **iCloud Keychain** pra
  puxar as chaves em runtime.
- Antes de qualquer tomada de decisão crítica baseada em output: o Atalho deve mostrar o JSON final pro usuário revisar
  (mesmo que rapidamente). Auditoria humana mínima.
- Chaves no iCloud Keychain:
    - `SASI_GEMINI_KEY` = AIza...
    - `SASI_CLAUDE_KEY` = sk-ant-...
    - `SASI_SUPABASE_KEY` = sb_publishable_...

---

## 🧠 Modo Nerd — Por que 2 LLMs em cascata

**Gemini Vision** tem janela de contexto maior e é superior em **OCR de tabelas complexas e handwriting**. É o estágio
"eyes-on-the-paper".

**Claude Sonnet 4.6** é superior em **seguir instruções negativas** ("NÃO invente"), **coerência clínica** (raciocínio
fisiológico) e **respeitar schemas JSON complexos**. É o estágio "brain-on-the-data".

Rodar Claude diretamente na imagem também funciona (Claude 4.x é multimodal forte), mas o custo é maior e a
especialização em OCR tabular é menor. A cascata Gemini→Claude entrega Pareto ótimo: visão do Gemini + raciocínio do
Claude.

**Alternativa mais barata** (se orçamento aperta): rodar **Claude Haiku 4.5** direto na imagem, pulando o Gemini.
Perde ~15% de acurácia em folhas manuscritas, ganha ~3x em custo. Válido pra fluxos não-críticos.

---

## ⚡ Prompt bônus — Export turno via API (sem chat)

Se quer disparar "exportar turno" via URL (ex: Siri "SASI passagem"), body da chamada Claude:

```
POST https://api.anthropic.com/v1/messages
Body: {
  "model": "claude-sonnet-4-6",
  "max_tokens": 8000,
  "system": "Você é o SASI. Gere passagem de plantão no formato do reference 05-export-passagem-turno.md. Input é JSON com dashboard dos 33 leitos vindo do Supabase (view vw_dashboard). Output é Markdown do painel 33-leitos, 1 página A4.",
  "messages": [{
    "role": "user",
    "content": "Dashboard atual:\n<JSON_DASHBOARD_SUPABASE>\n\nTurno: {MANHA|TARDE|NOITE}\nGere a passagem."
  }]
}
```

Response vem Markdown. Atalho manda pro **Pages** ou **Notes** e gera PDF automaticamente.
