# 🎯 Estimativa do Diâmetro da VSVE — A Única Estimativa Autorizada

A regra-mãe das skills clínicas é **zero alucinação**. O diâmetro da VSVE é a **única** exceção, porque a comunidade
médica validou fórmulas de estimativa para exatamente este parâmetro, justamente porque ele é mensurável em apenas ~73%
dos pacientes críticos enquanto o VTI sai em >90%.

Toda estimativa é **sempre marcada** no output (`lvot_estimado: true` + warning). Nunca passa despercebida.

---

## Por que o diâmetro é o calcanhar de Aquiles do débito

O diâmetro entra **ao quadrado** na área:

```
Área VSVE = 0.785 × D²
```

Logo, o erro do diâmetro é amplificado:

- erro de **5%** no diâmetro → ~**10%** de erro no VS
- erro de **10%** no diâmetro → ~**21%** de erro no VS

Por isso a doutrina: **débito com diâmetro estimado → confie na TENDÊNCIA do VTI, não no valor absoluto de DC.** O VTI
medido seriadamente no mesmo paciente é muito mais confiável que o DC absoluto calculado com diâmetro chutado.

---

## Fórmula primária — Leye et al. 2009

```
D_VSVE (mm) = 5.7 × SC(m²) + 12.1
```

- Derivada em 382 pacientes sem doença valvar aórtica nem de aorta ascendente
- Independente do sexo após indexação à SC
- Validada em 173 pacientes com estenose aórtica (AVA calculada vs medida: r = 0,89)
- Os autores a descrevem como **salvaguarda** para "quando a medida é difícil ou impossível por TTE"

**Fonte:** Leye M et al. Size-adjusted LVOT diameter reference values. J Am Soc Echocardiogr 2009;22 (5):445-451.

---

## Recalibração para UTI — Cox/Wiersema 2022

Em 1177 pacientes críticos, a fórmula de Leye **superestimou** o diâmetro em média **+2,4 mm** (± 1,7; LoA −1,0 a +5,8
mm). O ajuste do intercepto para a população de UTI eliminou o viés.

```
D_VSVE_UTI (mm) = (5.7 × SC + 12.1) − 2.4        ← usado como PRIMÁRIO em UTI pelo motor
```

Diâmetro médio real na UTI: **21 ± 2 mm** (homens 22 ± 2; mulheres 20 ± 2). Determinantes: altura, peso, sexo.

**Fonte:** Cox EGM, Koeze J, van der Horst ICC, Wiersema R, et al. Calculated LVOT diameter for critically ill patients.
J Intensive Care 2022;10:31.

---

## Referência cruzada — mBSA capping (Murthi / protocolo FREE)

Usa a SC como diâmetro em cm, com teto:

```
SC ≤ 1.8       → D = 1.8 cm
1.8 < SC < 2.2 → D = SC (em cm)
SC ≥ 2.2       → D = 2.2 cm
```

O motor reporta este valor como **referência cruzada** (`mbsa_referencia_mm`), não como primário. Serve de sanity check
rápido.

---

## O que NÃO usar

- **SC crua como diâmetro** (sem capping nem regressão): erro percentual **91%** vs referência — proibido. Os autores
  são explícitos: *"BSA não deve ser usada como substituto do diâmetro da VSVE."*
- O modelo computacional SVR (ε-SVR, Aligholizadeh 2020) tem erro 33% — melhor que mBSA (58%) e SC crua (91%), mas ainda
  acima do limiar de 30% aceito para comparação com termodiluição. Não implementado aqui por exigir features extras;
  Leye-Cox é o padrão prático.

**Fonte:** Aligholizadeh E, Teeter W, Murthi S, et al. Cardiovasc Ultrasound 2020;18:37.

---

## Comportamento do motor (resumo)

1. Se `lvot_diam_cm` (MEDIDO) é fornecido → usa, marca `fonte: MEDIDO`. Fim.
2. Se ausente e há SC → estima por **Leye-Cox UTI**, marca `fonte: ESTIMADO`, `lvot_estimado: true`, e emite warning com
   os três valores (Leye bruto, ajustado-UTI usado, mBSA referência).
3. Se ausente e sem SC → **não estima**, retorna `null` + warning (VS/DC/IC bloqueados). Zero alucinação preservada.

---

## Limitação geométrica fundamental

A VSVE é **ovoide**, não circular (demonstrado por TC). Todo método de diâmetro 2D subestima a área verdadeira. Isso
vale tanto pra medida quanto pra estimativa — é mais um motivo para a **tendência do VTI** ser o parâmetro de confiança
em UTI, e para qualquer DC absoluto ser lido como ordem de grandeza, não número exato.
