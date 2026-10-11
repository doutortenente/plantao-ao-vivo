# 08 — Banco P0 (10-ago-2026): tabelas novas e como gravar

Sete migrations aplicadas no banco vivo em 10-ago (carimbos `20260810083301` a `20260810084920`), mais a
reclassificação dos 14 eventos `custom`. Este arquivo é o contrato de gravação pós-P0. Regra de sempre vale
dobrado: campo sem fonte é `null`, `ts` é o horário da COLETA (nunca `now()` silencioso).

## Regras que mudaram

1. `pacientes.gravidade` agora é `estavel | watcher | instavel | critico` (obito saiu — desfecho é
   `status_leito`). `evolucoes.illness_severity` usa o MESMO enum, e é a gravidade DAQUELA nota.
2. `evolucoes`: mandar `data_plantao` (data do plantão que está no TÍTULO/folha, não a do relógio) e `turno`
   (`diurna`|`noturna`). Se não mandar, trigger deriva — noturna iniciada antes das 07h cai no dia anterior.
   `tipo_nota`: `admissao`|`seriada`|`alta`|`andar`. `autor_crm`/`autor_nome` quando a fonte mostrar.
3. `internacao_id`: NÃO preencher em tabela nenhuma — trigger carimba com a internação aberta do paciente.
   Reinternação também é automática (reativar o leito reabre episódio).
4. **`pacientes.dispositivos` é DERIVADO. Escrever nele é proibido** — qualquer escrita manual é sobrescrita
   no próximo evento. A fonte da verdade é `dispositivo_episodios`.
5. `pam_min`/`pas_min` = legado. Janela de vitais vai em `janelas_24h`.

## `dispositivo_episodios`

Quando a fonte mostrar dispositivo com data:

| Na fonte | Gravar |
|---|---|
| "CVC sim (08/05/26)" | INSERT `{tipo:'cvc', sitio, data_inicio:'2026-05-08'}` — se já não houver episódio aberto igual |
| "SVD não (15/03 a 24/03)" | episódio FECHADO `{data_inicio:'…-03-15', data_fim:'…-03-24'}` |
| "PICC retirado por infecção 14/01" | UPDATE do episódio aberto: `data_fim` + `motivo_fim:'infeccao'` |

`tipo`: iot · traqueo · cvc · picc · arterial · svd · sne · sng · dreno · gtt · trr · marca_passo · outro
`motivo_fim`: eletivo · infeccao · troca · disfuncao · alta · obito · outro
As chavinhas do painel acendem/apagam sozinhas a partir daqui. Dias de uso: `vw_dispositivos_ativos` (derivado).

## `atbs`

1 linha por CURSO: `{droga, dose, via, frequencia, data_inicio, data_fim (null = ativo),
duracao_planejada_dias (o "7" de D7/7), foco, intencao ('empirica'|'dirigida'|'profilatica')}`.
D-day NUNCA se grava — é `hoje − data_inicio` (view `vw_dias_atb_ativo`).
"Escalonado X → Y": fechar o curso X (`data_fim` + `motivo_suspensao`) e abrir o curso Y.
Histórico de ATB de nota antiga também entra (cursos fechados) — é o que sustenta o empírico da próxima sepse.

## `culturas` + `antibiograma`

`lab_cultura` → `culturas {material, coleta_ts, laudo_ts (null = sem laudo final), crescimento, agente,
ufc_por_ml, observacoes}`. Parcial: `laudo_ts` null + `observacoes: "parcial 72h negativa"`.
Antibiograma: 1 linha por antibiótico em `antibiograma {cultura_id, antibiotico, resultado 'S'|'I'|'R', cim}`.

## `janelas_24h`

1 linha por vital por janela: `{tipo, janela_inicio, janela_fim, valor_max, valor_min, n_total (nº de
aferições NA FOLHA — não chutar 12), n_fora_baixo + limiar_baixo, n_fora_alto + limiar_alto,
fonte:'claude_ocr', confidence, source_text}`.
Os números saem do `build_passagem.py` — o LLM não conta. Limiares default = os do BRIEFING
(PAS<90 · PAD<50 · PAM<65 · FC>100 · FR>20 · SpO2<92 · TAX<35,5 · Dx>180); hipertensão (PAM>110) quando a
folha justificar. Chave única `(paciente, tipo, janela_fim)`: reprocessar a mesma folha não duplica.
Render pronto no formato da nota: `vw_janelas_24h_render` → "PAM 90-56 (4/12 <65)".

## Vocabulário (79 códigos — `custom` morreu)

Labs novos: troponina · probnp · d_dimero · tp · ttpa · tgo · tgp · ggt · fa · bd · bi · amilase · lipase ·
dhl · vhs · tsh · t4l  (`bb` segue sendo a bilirrubina TOTAL — insumo do SOFA hepático)
Folha: pvc · diurese_24h · diurese_parcial · uf_dialise · debito_dreno
Valor sem tipo no dicionário: declarar no warning e NÃO gravar como `custom`.
