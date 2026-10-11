# 🖋️ Template — Nota Interpretativa de Ecocardiograma

Texto **copiável** pra colar na evolução do prontuário. Estrutura por câmara/função, red flags na frente. Campo `null` →
omita a linha ou escreva "não avaliado"; NUNCA escreva o achado inventado.

---

## Estrutura padrão

```markdown
# EcoTT — {DATA} — Leito {LEITO} {UTI} — {MODO: POCUS à beira-leito | Laudo formal}

{🚨 RED FLAGS — só aparece se houver: tamponamento / TEP-cor pulmonale agudo / SAM-obstrução VSVE / FEVE gravemente reduzida / derrame significativo. Abre a nota.}

## Função sistólica do VE
FEVE {valor}% ({Simpson | eyeball | EPSS} — {fonte}). {classe}. {alterações segmentares se houver}.
VTI VSVE {valor} cm. {nota de tendência se seriado}.

## Função diastólica
{MODO B: grau {I/II/III} (Nagueh 2016), pressão de enchimento {normal/elevada}, E/e' {valor}, e' sept {x}/lat {y}, VAEi {z}, VRT {w}}
{MODO A: E/e' {valor} ({base}) → {interpretação}}

## Ventrículo direito
TAPSE {valor} mm ({normal/disfunção}). {S' {x} cm/s}. Relação VD/VE {valor}. PSAP {valor} mmHg ({PAD {fonte}}).

## Volume / VCI
VCI {máx} cm, {colapsabilidade/distensibilidade} {valor}% → PAD estimada {valor} mmHg. {responsividade}.

## Valvas
{só o relevante: EA/IAo/IM/IT com grau. ⚠️ se EA/IAo significativa → débito por VTI invalidado}

## Hemodinâmica calculada
{vinda da skill hemodinamica-calculada}
DC {valor} L/min | IC {valor} L/min/m² ({classe}) | RVS {valor} dynes·s·cm⁻⁵ ({classe}).
{⚠️ se diâmetro VSVE estimado: aviso de erro quadrático — priorizar tendência do VTI}
{⚠️ se PVC estimada da VCI: RVS semiquantitativa}
Fluido-responsividade: {responsivo/não responsivo} ({teste + valor}).
Perfil provável: {perfil}.

## Impressão
{bullets 3-5 linhas integrando os achados — a foto hemodinâmica do paciente}

---
**CONDUTA**
{numerada, com doses e metas}

---
*POCUS/análise por Dr. Nicolas — Intensivista*
```

---

## Regras de preenchimento

### Fonte sempre marcada

- "FEVE 30% (Simpson, laudo)" — quantitativo, alta confiança
- "FEVE ~30% (eyeball, POCUS)" — semiquantitativo, triagem
- Nunca apague a distinção.

### Campos vazios

Não escreva `null` nem `N/A`. Omita a linha, ou "não avaliado neste exame". Ex.: sem strain no laudo → não cite strain.

### Diâmetro VSVE estimado

Sempre que a hemodinâmica usou estimativa, a nota carrega:
> ⚠️ Diâmetro da VSVE estimado (Leye-Cox) — erro quadrático no débito. Valor absoluto de DC com cautela; priorizar
> tendência do VTI seriado.

### Red flags

Abrem a nota em bloco próprio, antes de tudo. Ex.:
> 🚨 **SAM com gradiente VSVE 60 mmHg** — obstrução dinâmica. Conduta CONTRAINTUITIVA: volume + suspender inotrópico. NÃO
> escalar dobutamina.

### Impressão (bullets concisos)

```
- VE hiperdinâmico (FEVE >70%, eyeball) com VTI baixo (14 cm) e VCI colapsável → padrão hipovolêmico/distributivo.
- VD preservado (TAPSE 22). Sem sinais de cor pulmonale agudo.
- RVS baixa (estimada) compatível com componente distributivo.
- Responsivo a volume (PLR ΔVTI +14%).
```

### Conduta (imperativo, numerada, com doses e metas)

```
1. Expandir 500 mL cristaloide balanceado, reavaliar VTI em 15 min.
2. Se PAM mantém <65 após volume → noradrenalina 0,05 mcg/kg/min, titular PAM ≥65.
3. Reavaliar responsividade antes de cada novo bolus — parar se ΔVTI <10%.
4. POCUS de controle em 2h (VTI + VCI + função VE).
```

---

## Saída Supabase (opcional)

Quando pedir "salvar"/"manda pro banco": gere os eventos de eco conforme `04-schema-supabase.md` da skill
`hemodinamica-calculada` (tipo `custom` + `valor_json` com subtipo). Nunca faz UPSERT daqui — só o payload.

---

## Lembrete final

A nota é instrumento clínico-legal. **Sem motivacional dentro dela** — Goggins fica fora do prontuário. Dentro: só
achado, interpretação e conduta. A persona e o raciocínio tático vão na conversa com o Dr. Nicolas, fora do bloco da
nota.
