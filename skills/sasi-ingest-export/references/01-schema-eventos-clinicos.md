# 📊 Schema Supabase — `eventos_clinicos` + `evolucoes` + `pacientes`

Este é o **contrato de dados** que o payload de ingest deve respeitar. Espelhado de `src/lib/supabaseClient.ts`.

---

## Tabela `pacientes`

Cadastro do leito. Só cria/atualiza quando explicitamente pedido (novo paciente, alta, transferência).

```sql
create table pacientes (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid references auth.users(id),
  leito         text not null,
  uti           text not null check (uti in ('UTI2','UTI3','UTI4')),
  nome          text not null,
  idade         integer check (idade between 0 and 130),
  peso          numeric(5,2) check (peso between 1 and 400),
  altura        numeric(5,2) check (altura between 30 and 250),
  hd            text,                         -- hipótese diagnóstica
  data_adm      date not null default current_date,
  alergias      text,
  gravidade     text default 'estavel' check (gravidade in ('estavel','moderado','grave','critico','obito')),
  status_leito  text default 'ativo' check (status_leito in ('ativo','alta','obito','transferencia')),
  sofa_baseline integer,                      -- pra ΔSOFA de Sepsis-3
  created_at    timestamptz default now(),
  updated_at    timestamptz default now(),
  unique (uti, leito, status_leito)  -- 1 paciente ativo por leito
);
```

**Escopo de leitos SASI:**

- UTI2 = 12 leitos (1–12)
- UTI3 = 13 leitos (1–13)
- UTI4 = 8 leitos (1–8)
- Total = 33 leitos

---

## Tabela `evolucoes`

**UM registro por paciente por plantão**. Snapshot completo de sistemas.

```sql
create table evolucoes (
  id             uuid primary key default gen_random_uuid(),
  paciente_id    uuid not null references pacientes(id) on delete cascade,
  user_id        uuid references auth.users(id),
  data_evolucao  timestamptz not null default now(),
  plantao        text check (plantao in ('manha','tarde','noite','plantao_24h')),
  neuro          jsonb default '{}'::jsonb,
  resp           jsonb default '{}'::jsonb,
  hemo           jsonb default '{}'::jsonb,
  tgi            jsonb default '{}'::jsonb,
  renal          jsonb default '{}'::jsonb,
  hemato         jsonb default '{}'::jsonb,
  infecto        jsonb default '{}'::jsonb,
  dvas           jsonb default '[]'::jsonb,   -- array de Infusao
  sedativos      jsonb default '[]'::jsonb,   -- array de Infusao
  impressao      text[],
  conduta        text[],
  sofa_snapshot  jsonb,                       -- cache do cálculo
  sofa_total     integer,
  created_at     timestamptz default now(),
  updated_at     timestamptz default now()
);
```

### Estrutura de cada JSONB de sistema

**`resp`** (campos que o OCR preenche):

```json
{
  "suporte": "VNI | AA | CN | O2 | IOT + VM",
  "fr": "28",
  "spo2": "94",
  "fio2O2": "0.35",
  "vmFio2": "0.4",
  "pao2": "72",
  "ausculta": "MV+ bilateral, crepitantes em bases",
  "secrecao": "moderada, amarelada"
}
```

**`hemo`:**

```json
{
  "pa_sys_min": "88",
  "pa_sys_max": "135",
  "pa_dia_min": "52",
  "pa_dia_max": "82",
  "pam1": "62",    // ← MIN! Bug #11
  "pam2": "90",    // ← MAX
  "fc_min": "78",
  "fc_max": "112",
  "perfusao": "boa | fria | moteada",
  "pulso": "cheio | fino | filiforme"
}
```

**`renal`:**

```json
{
  "diurese": "1200",
  "diureseHoras": "24",
  "bh": "-450",
  "cr1": "1.8",     // pior (maior)
  "cr2": "1.2",     // melhor
  "ur": "82",
  "trrc": false,
  "na_ur": "45"
}
```

**`hemato`:**

```json
{
  "hb": "9.2",
  "ht": "28",
  "leuco": "14500",
  "plaq1": "180",    // pior (menor)
  "plaqUnit": "×10³/µL",
  "inr": "1.4"
}
```

**`dvas`** (array):

```json
[
  {
    "id": "uuid",
    "droga": "Noradrenalina",
    "diluicao_mg": 16,
    "diluicao_ml": 250,
    "vazao_ml_h": 8,
    "started_at": "2026-04-24T06:00:00-03:00"
  }
]
```

---

## Tabela `eventos_clinicos` — O CORAÇÃO do Meta-Vision

**Timeseries pura**. Cada valor numérico importante vira UMA linha aqui. É daqui que saem as tendências de 72h, o ΔSOFA,
o BH acumulado.

```sql
create table eventos_clinicos (
  id           uuid primary key default gen_random_uuid(),
  paciente_id  uuid not null references pacientes(id) on delete cascade,
  evolucao_id  uuid references evolucoes(id) on delete set null,
  user_id      uuid references auth.users(id),
  ts           timestamptz not null,           -- quando o valor foi medido (não quando digitado)
  tipo         text not null check (tipo in (
                  'sofa_total','sofa_resp','sofa_coag','sofa_liver',
                  'sofa_cardio','sofa_neuro','sofa_renal',
                  'pam','pam_min','pf_ratio','lactato','diurese_h',
                  'bh_h','temp','fc','fr','spo2','hb','plaq',
                  'cr','ur','leuco','na','k','bb','inr',
                  'nor_dose','adr_dose','vaso_dose','dobuta_dose',
                  'gcs','rass','cam_icu','custom'
                )),
  valor_num    numeric,
  valor_json   jsonb,                          -- pra eventos compostos (gaso completa, cultura)
  unidade      text,
  fonte        text not null check (fonte in (
                  'manual','gemini_ocr','claude_ocr','appsheet',
                  'auto_trigger','edge_function','api_import'
                )),
  confidence   numeric(3,2),                   -- 0.00 a 1.00
  source_text  text,                           -- trecho original do OCR
  requires_review boolean default false,
  created_at   timestamptz default now()
);

create index idx_eventos_pac_ts on eventos_clinicos (paciente_id, ts desc);
create index idx_eventos_tipo_ts on eventos_clinicos (tipo, ts desc);
```

---

## 📦 PAYLOAD de ingest (schema `sasi-ocr-ingest/v1`)

> Gravação operacional: MCP com comando **deploy** — não POST em Edge Function.

Isto é o **shape exato** que Claude deve produzir ao final da extração:

```json
{
  "$schema": "sasi-ocr-ingest/v1",
  "extracted_at": "2026-04-24T14:32:00-03:00",
  "source": {
    "type": "folha_enfermagem | lab_bioquimica | lab_hemograma | lab_gasometria | lab_coag | lab_cultura | laudo_imagem | prescricao | texto_livre",
    "fonte": "claude_ocr",
    "confidence_overall": 0.92,
    "warnings": [
      "plaquetas sem unidade explícita — assumido ×10³/µL",
      "timestamp inferido de now() — folha não tinha hora"
    ]
  },
  "target": {
    "uti": "UTI3",
    "leito": "7",
    "paciente_id": null    // null se criar paciente novo; UUID se já existir
  },
  "paciente_upsert": null,  // ou objeto Paciente parcial se novo/mudança
  "evolucao_snapshot": {
    "data_evolucao": "2026-04-24T06:00:00-03:00",
    "plantao": "manha",
    "neuro": { "...": "..." },
    "resp": { "...": "..." },
    "hemo": { "...": "..." },
    "renal": { "...": "..." },
    "hemato": { "...": "..." },
    "infecto": { "...": "..." },
    "dvas": [],
    "sedativos": []
  },
  "eventos_clinicos": [
    {
      "ts": "2026-04-24T06:00:00-03:00",
      "tipo": "pam_min",
      "valor_num": 62,
      "unidade": "mmHg",
      "confidence": 0.95,
      "source_text": "PAM 62",
      "requires_review": false
    },
    {
      "ts": "2026-04-24T06:00:00-03:00",
      "tipo": "lactato",
      "valor_num": 3.4,
      "unidade": "mmol/L",
      "confidence": 0.88,
      "source_text": "Lac 3,4",
      "requires_review": false
    }
  ],
  "pendencias": [
    { "tarefa": "TC abdome controle pós-op", "prioridade": 2 },
    { "tarefa": "SBT amanhã 10h", "prioridade": 1 }
  ]
}
```

### Regras de preenchimento do payload

1. **`target.paciente_id` é null** → MCP `sasi_deploy_ingest` procura por `(uti, leito, status_leito=ativo)`; se achar,
   usa; se não, exige `paciente_upsert` preenchido.
2. **`evolucao_snapshot` é null** quando a foto é só de lab/imagem (eventos isolados). Nesse caso, os valores vão SÓ em
   `eventos_clinicos` e linkam à evolução ativa do dia.
3. **`eventos_clinicos` é SEMPRE array** (pode ter 1, 10, 50 itens).
4. **Toda gasometria gera**: `ph`, `pco2`, `po2`, `hco3`, `be`, `lactato`, `pf_ratio` (se FiO2 disponível) — como
   `valor_json` num único evento OU eventos separados se o backend preferir (usar separados — mais fácil de plotar).
5. **Toda dose de DVA vira**: `nor_dose`, `adr_dose`, `vaso_dose`, `dobuta_dose` com `valor_num` em mcg/kg/min.
6. **`pendencias` é array opcional** de `{tarefa, prioridade}` (prioridade `1`|`2`|`3`, default `2`). Cada item vira uma
   linha na tabela `pendencias`, com `evolucao_id` linkado à evolução deste deploy (ou `null` se for só lab/imagem).
   **NÃO repetir a tarefa dentro de `conduta`/`impressao`** — o array é a fonte única.
