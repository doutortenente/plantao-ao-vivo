# ⚔️ Perfis de Choque e Conduta Tática

Como integrar débito + RVS + VCI/fluido-responsividade + função para classificar o choque e decidir: **volume,
vasopressor ou inotrópico**. O `perfil_provavel` do motor é apoio — a palavra final integra os achados qualitativos do
eco (contratilidade, VD, derrame) que a `analise-ecott` extrai.

---

## Os 4 perfis (matriz de decisão)

| Perfil                   | Contratilidade/FEVE                          | VCI             | IC / VTI         | RVS       | Conduta-âncora                                        |
| ------------------------ | -------------------------------------------- | --------------- | ---------------- | --------- | ----------------------------------------------------- |
| **Hipovolêmico**         | hiperdinâmico, VE pequeno ("kissing walls")  | colapsada, fina | baixo            | alta      | **Volume** se responsivo; reavaliar                   |
| **Distributivo/Séptico** | normal/hiperdinâmico (ou deprimido na sepse) | variável        | alto (ou normal) | **baixa** | **Vasopressor** (noradrenalina 1ª linha)              |
| **Cardiogênico**         | deprimido, VE dilatado                       | pletórica, fixa | baixo            | alta      | **Inotrópico** ± reduzir afterload; cuidado c/ volume |
| **Obstrutivo**           | VD dilatado (TEP) ou tamponamento            | pletórica       | baixo            | alta      | Tratar a causa (trombólise/dreno); volume ponte       |

---

## Algoritmo de decisão à beira-leito

```
1. IC baixo (<2,2)?
   ├── SIM → RVS alta? 
   │        ├── SIM → VCI pletórica + FEVE baixa? → CARDIOGÊNICO → inotrópico (dobutamina)
   │        │                                      → se VD dilatado/PSAP alta → OBSTRUTIVO → investigar TEP/tamponamento
   │        └── VCI colapsável + responsivo? → HIPOVOLÊMICO → volume
   └── NÃO (IC normal/alto) → RVS baixa? → DISTRIBUTIVO → vasopressor

2. Responde a volume? (ΔVpeak>12% / dVCI>18% / PLR ΔVTI≥10%)
   ├── SIM → expandir 250–500 mL cristaloide, reavaliar VTI
   └── NÃO → PARAR fluido (fútil/danoso) → escalar vaso/inotrópico
```

---

## Metas terapêuticas (Surviving Sepsis Campaign 2021 — Evans et al.)

- **PAM-alvo inicial em choque séptico: ≥ 65 mmHg** (sobre alvos mais altos) — recomendação com evidência moderada.
- **Noradrenalina = vasopressor de 1ª linha** (recomendação forte). Adicionar vasopressina se Nor ≳0,25–0,5 mcg/kg/min
  para poupar catecolamina.
- **Cristaloide balanceado** como fluido de escolha; reavaliar responsividade a cada bolus em vez de infundir cego.
- Adjuntos de perfusão: **clareamento de lactato** e **tempo de enchimento capilar** (CRT) guiam ressuscitação tanto
  quanto a PA.

**Fonte:** Evans L, Rhodes A, Alhazzani W, et al. Surviving Sepsis Campaign 2021. Crit Care Med 2021;49 (11):
e1063-e1143.

---

## Gatilhos que MUDAM a conduta (limiares de virada)

- **Perda de responsividade a volume** (ΔVTI <10% pós-PLR) → **parar fluidos**, mesmo que PAM ainda baixa.
- **Surgimento de B-lines pulmonares / VCI pletórica** → **parar fluidos** (congestão).
- **Queda do VTI sob vasopressor** → pensar **inotrópico** ou **obstrução dinâmica da VSVE (SAM)** — esta última é
  contraintuitiva: trata com **volume + reduzir inotrópico/vasodilatador**, nunca escalar inotrópico.
- **IC mantém baixo apesar de volume e PAM corrigida** → **inotrópico** (dobutamina), reavaliar FEVE.

---

## Doses de partida (referência — sempre confirmar diluição institucional)

> Estas são doses de PARTIDA usuais. A conduta final do Dr. Nicolas prevalece. Diluições conforme protocolo da
> Beneficência.

- **Noradrenalina:** iniciar 0,05–0,1 mcg/kg/min, titular para PAM ≥65.
- **Vasopressina:** 0,03 UI/min fixa (adjuvante, não titular como 1ª linha).
- **Dobutamina:** 2,5–5 mcg/kg/min, titular por IC/perfusão; vigiar taquiarritmia e hipotensão.
- **Adrenalina:** 0,05–0,1 mcg/kg/min (2ª/3ª linha ou choque com componente cardiogênico).

A `hemodinamica-calculada` **não prescreve sozinha** — ela calcula, classifica e propõe. Doses e metas vão no bloco
**CONDUTA FINAL** isolado, para decisão binária do Dr. Nicolas.
