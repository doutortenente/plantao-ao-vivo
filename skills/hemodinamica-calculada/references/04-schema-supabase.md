# 📊 Mapeamento Supabase — Eventos de Ecocardiograma

Os eventos de eco entram na tabela `eventos_clinicos` do SASI. Como a constraint `tipo` **não** tem valores específicos
de eco, usamos `tipo: "custom"` + `valor_json` carregando o subtipo. Mesmo contrato das outras skills clínicas. **Nunca
faz UPSERT daqui** — só produz o payload; o Edge Function grava (mantém RLS honesta).

Schema completo de `eventos_clinicos` / `evolucoes` / `pacientes`: ver a referência `01-schema-eventos-clinicos.md` da
skill `sasi-ingest-export` (fonte canônica). Aqui só o que é específico de eco.

---

## Padrão do evento de eco

```json
{
  "ts": "2026-06-29T08:00:00-03:00",
  "tipo": "custom",
  "valor_num": 2.88,
  "valor_json": {
    "dominio": "ecocardiograma",
    "subtipo": "indice_cardiaco",
    "unidade": "L/min/m2",
    "fonte_medida": "vti_vsve",
    "lvot_estimado": true
  },
  "unidade": "L/min/m2",
  "fonte": "claude_ocr",
  "confidence": 0.9,
  "source_text": "VTI 18, FC 92, diâmetro estimado",
  "requires_review": false
}
```

- `valor_num`: o número principal do evento (ex: o IC, o DC, a PSAP).
- `valor_json.subtipo`: identifica a medida (lista abaixo).
- `valor_json.lvot_estimado`: **obrigatório** em eventos derivados de débito quando o diâmetro foi estimado → marca
  `requires_review: true`.
- `fonte`: `claude_ocr` quando extraído de imagem/laudo; `manual` quando digitado pelo Dr. Nicolas.

---

## Subtipos de eco (valor_json.subtipo)

**Débito:**

- `volume_sistolico` (mL) · `debito_cardiaco` (L/min) · `indice_cardiaco` (L/min/m2) · `indice_sistolico` (mL/m2) ·
  `lvot_vti` (cm) · `lvot_diametro` (cm)

**Resistência / pressão:**

- `rvs` (dynes·s·cm-5) · `irvs` (dynes·s·cm-5·m2) · `psap` (mmHg) · `pad_estimada` (mmHg)

**VCI / fluido-resp:**

- `vci_max` (cm) · `vci_min` (cm) · `vci_colapsabilidade` (%) · `vci_distensibilidade` (%) · `delta_vpeak` (%) ·
  `delta_vti_plr` (%)

**Diástole / função:**

- `e_sobre_elinha` · `feve` (%) · `tapse` (mm) · `fac` (%)

---

## Regras de geração do payload

1. **Um evento por número relevante.** Não empacote tudo num só — facilita plotar tendência de 72h (ex: IC seriado).
2. **Eventos com diâmetro estimado** carregam `lvot_estimado: true` e `requires_review: true`.
3. **Flags clínicas do motor** (RVS baixa, PSAP alta, IC baixo) viram `requires_review: true` no evento correspondente,
   para a auditoria humana enxergar.
4. **`confidence`** reflete a qualidade do input: medida direta limpa ~0,95; estimativa/janela ruim ~0,7; valor
   inferido <0,6.
5. **Timestamp `ts`** = quando o eco foi feito (não quando digitado). Sem hora → `now()` America/Sao_Paulo + nota.
6. **Leito/UTI** vêm do contexto da conversa; sem eles, não monta o `target` — pergunta uma vez.

---

## Shape do payload (envelope, espelha sasi-ocr-ingest/v1)

```json
{
  "$schema": "sasi-ocr-ingest/v1",
  "extracted_at": "2026-06-29T08:05:00-03:00",
  "source": {
    "type": "laudo_imagem",
    "fonte": "claude_ocr",
    "confidence_overall": 0.9,
    "warnings": ["diâmetro VSVE estimado (Leye-Cox) — débito absoluto com cautela"]
  },
  "target": { "uti": "UTI2", "leito": "4", "paciente_id": null },
  "paciente_upsert": null,
  "evolucao_snapshot": null,
  "eventos_clinicos": [
    { "ts": "...", "tipo": "custom", "valor_num": 5.63,
      "valor_json": {"dominio":"ecocardiograma","subtipo":"debito_cardiaco","unidade":"L/min","lvot_estimado":true},
      "unidade": "L/min", "fonte": "claude_ocr", "confidence": 0.8,
      "source_text": "VTI 18 / FC 92", "requires_review": true },
    { "ts": "...", "tipo": "custom", "valor_num": 711,
      "valor_json": {"dominio":"ecocardiograma","subtipo":"rvs","unidade":"dynes.s.cm-5","pvc_estimada":true},
      "unidade": "dynes.s.cm-5", "fonte": "claude_ocr", "confidence": 0.7,
      "source_text": "PAM 65, PAD VCI 15", "requires_review": true }
  ]
}
```

`evolucao_snapshot` é `null` quando o eco é evento isolado (vai só em `eventos_clinicos`, linka à evolução ativa do
dia). Se o Dr. Nicolas quiser o eco dentro da evolução do plantão, a `analise-ecott` escreve a síntese no campo `hemo`
do snapshot — mas isso é decisão dele, não automático.
