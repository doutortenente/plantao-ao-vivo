# ✅ Exemplo Resolvido — CONTRATO DE SAÍDA (padrão-ouro)

> Input = scan de folha (s). Output = ISTO. Nada mais, nada menos.
> Blocos LIMPOS (colam no prontuário/passagem). Comentário tático e flags
> vermelhos FORA do bloco. Fecha com CONDUTA FINAL isolada.

---

## Formato exato do bloco (1 por leito)

```
LEITO 04 — LUIZ J. G., 80M 

Sinais Vitais 24 h:
PAS: 135 - 112 mmHg
PAD: 70 - 52 mmHg
PAM: 81 - 67 mmHg
FC: 87 - 60 bpm
FR: 26 - 17 rpm [5x > 20]
SpO2: 98 - 91 % (AA -> cateter O2 2 L/min) [1x < 92]
TAX: 36,8 - 36,0 ºC
Dx: 222 / 193 / 173 / 126 mg/dl [2x > 180]
Dieta: VO + SNE | Ingesta hídrica: 1.725 ml
Evacuação: 1x (++, pastosa) 
Diurese: 2.200 ml
BH: - 475 ml

```

Regras visíveis no contrato:

- Máx - Mín em TODOS (inclusive SpO2). Colchete só quando contagem ≥ 1.
- `Dx` = valores `/`-separados, maior→menor.
- Balanço = soma das células (motor). Rodapé da folha só confere; divergência vai para o rodapé da resposta.
- Dispositivo/BIC relevante → linha própria no balanço (ex.: `Noradrenalina: 7 -> 5 -> 2,5 ml/h`); dúvida de rótulo → rodapé.
- Sup O2: AA/cateter entre parênteses no SpO2; VM em linha própria após o Dx.

---

## Estrutura completa da resposta

1. **SITREP** (1–2 linhas): qual folha, qual janela, quantos leitos. Ex.:
   `🦅 SITREP — NOVO PLANTÃO / UTI ADULTO 2 — 10/06/2026 — 3 LEITOS`
2. **Blocos** copiar-e-colar (limpos), um por leito.
3. **Flags vermelhos** (fora do bloco): leitos que exigem reavaliação AGORA. Ex.:
   `⚠ FC fixa em 60 bpm em 9/12 aferições — marcapasso/betabloqueio. Glic 126→222.`
4. **CONDUTA FINAL** isolada e incondicional.

---

## CONDUTA FINAL (sempre, isolada)

```
CONDUTA FINAL:
- Leito XX: <prioridade imediata>.
Metas: PAM ≥ 65 · SpO2 ≥ 94% · Glicemia 140–180 · Diurese ≥ 0,5 mL/kg/h.
Doses: só se houver fonte legível na folha/prescrição; senão campo nulo.
```

Sem prescrição na mão = SEM dose inventada. Folha de enfermagem não traz infusão nominal legível → não cravar mcg/kg/min
nem UI de insulina.
