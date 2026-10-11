# 🪖 BRIEFING OBRIGATÓRIO — Extração e Compilação Clínica (UTI / SASI)

> Leia ISTO antes de tocar em QUALQUER folha/lab/prescrição do Dr. Nicolas.
> Revisado em 11/10/2026: janela padrão 24 h, evolução só com os blocos que mudam, entrega em Word
> (`docs/formato-entrega.md`), motor em `skills/sasi-ingest-export/scripts/build_passagem.py`.
> Output = instrumento clínico-legal que ele cola no prontuário. Sem explicação,
> sem preâmbulo, sem elogio. Só dado clínico limpo.

## 0. As 3 leis mais quebradas

1. **MODO EXTRAÇÃO PURA — zero explicação dentro do bloco clínico.** Nada de
   "(recalculado…)", "(soma das células…)", "(revisar)", "(em queda)" no meio. Toda observação/conferência/divergência
   vai FORA, num rodapé ("Flags táticos"). O bloco que ele cola no prontuário é limpo.
2. **Diurese e BH: some as células, NUNCA o total escrito à mão.** A última célula não é a diurese total. Motor:
   `skills/sasi-ingest-export/scripts/build_passagem.py`.
3. **Laboratório é SEÇÃO PRÓPRIA, com séries (`->`).** Nunca embutir lab no exame físico.

## 1. Estrutura por leito (ordem fixa)

```
LEITO XX — Nome Completo — Dn UTI — DD/MM/AAAA TURNO

## Sinais vitais + balanço [24 h]:
PAS: max - min mmHg [flag]
PAD: max - min mmHg [flag]
PAM: max - min mmHg [flag]
FC: max - min bpm [flag]
FR: max - min rpm [flag]
SpO2: max - min % (suporte se AA/cateter)
TAX: max - min ºC [flag]
Dx: v1 / v2 / v3 mg/dl [flag]
Sup O2: ...            ← SÓ linha própria se VM. Nunca se AA/cateter.
Dieta: ... | Ingesta hídrica: ... ml
Evacuação: ...
Diurese: ... ml
BH: ± ... ml

## Laboratório:
HB: ... g/dl | HT: ... % | PLAQ: ... /mm3 | LEUCO: ... /mm3 (seg/bast)
UR: v1 -> v2 mg/dl
CR: v1 -> v2 mg/dl
NA: ... | K: ... | MG: ... | CAI: ... | P: ...
Gaso: pH / HCO3 / SBE / Lactato (se houver)
Outros: PCR / troponina / D-dímero / INR (se houver)

## Terapias vigentes:
CV: ...
ATB: ... (D[n], I: dd/mm)
RENAL/HE: ...
ENDÓCRINO: ...
HEMATO: ...
TGI/NUTRIÇÃO: ...
NEURO / RESP / OUTROS / DISPOSITIVOS: ...

## Exame físico:
Neurológico: ...
Cardiovascular: ...
Respiratório: ...
TGI: ...
Renal: ...
(SEM labs aqui — labs já foram na seção Laboratório)

## Evolução / Eventos 24 h:
{só o Δ do período — eventos, picos, procedimentos, suspensões/introduções. Verbo de ação.}

## Impressão / Problemas ativos:
1. {Problema}: {leitura de 1 linha}.

## Plano terapêutico e Condutas:
1. {Sistema/Tema}:
- {ação concreta};
- {ação concreta};
2. {Sistema}: {ação + meta}.
```

### O que NÃO entra na evolução do dia

Identificação, HPMA/admissão, antecedentes, medicações de uso domiciliar, dispositivos e exames complementares
antigos. Já estão no prontuário. Entram só as 7 seções acima.

## 2. Formatação inegociável

- Máx – Mín com `" - "` (espaço-hífen-espaço). NUNCA `–` nem `—`. SpO2 incluso (max primeiro).
- Sup O2: AA/cateter → entre parênteses no fim do SpO2. VM → linha própria após Dx. NUNCA na diurese.
- Labs seriais com `" -> "`. Só com valores REAIS da fonte — não inventar coleta anterior.
- Balanço em linhas separadas: Dieta|Ingesta / Evacuação / Diurese / BH.
- Abreviações MAIÚSCULAS. Decimal com vírgula BR.
- Flags `[Nx > limiar]` só quando ≥1. Limiares: PAS<90 PAD<50 PAM<65 FC>100 FR>20 SpO2<92 TAX<35,5 DX>180.
  Acrescentados em 11/10/2026: DX<70 e TAX>37,8 (hipoglicemia e febre não passam calados).
- **Impressão SEM setinhas ↑/↓/=** (o Dr. detesta). Texto limpo.
- Campo sem fonte → OMITE a linha. Nunca inventa.

## 3. Plano terapêutico é a ALMA — não seja raso

Padrão-ouro (mão do próprio Dr.):

```
## Plano terapêutico e Condutas:
1. Neurológico:
- Aguarda laudo RM e angio RM;
- Aguarda USG doppler de carótidas;
- Aguarda avaliação Neuro-clínica.
2. Cardio: Solicito Avaliação Cardiologia e EcoTT (investigação etiologia cardioembólica).
3. Manejo AVCi:
- Mantida Dapt (AAS + Clopidogrel) + Rosuvastatina;
- Normoglicemia, Normotermia e Normotensão;
- Se RNC / novo déficit focal: TC de crânio na urgência.
4. Metabólico: Correção hipoMg (1,4).
5. Seguimento especialidades: Neuro-clínica e Cardiologia.
```

Verbo de comando (Solicito/Mantida/Correção/Aguarda), contingência (Se X → Y), meta numérica quando cabível, profilaxias
sempre (TEV/LAMG/cabeceira). Cada problema da Impressão tem sua conduta. Raso = reprovado.

## 4. Diurese/BH

- Some TODAS as células de diurese (não a última). BH = Σganhos − Σperdas.
- Nunca confie no total manuscrito. Conferir com `skills/sasi-ingest-export/scripts/build_passagem.py`.
- Caso 11/10/2026 L10: UF de CVVHDF 70 ml/h × 4 + 80 ml/h × 8 = 920 ml no diurno; o rodapé dizia 960.
- Resíduo gástrico e débito de SNG são perdas e entram na soma, mesmo quando o rodapé da folha não os soma.
- Caso 04/07 L04: última célula 600, mas diurese total 780 (100+30+10+40+600) → BH +1369 (folha escreveu +1449 com
  perdas 700). No bloco vai só 780/+1369; divergência no rodapé.

## 5. Checklist final (todos ou refaz)

- [ ] `" - "` nos vitais (SpO2 incluso). [ ] Sup O2 no lugar certo, nunca na diurese.
- [ ] Laboratório seção própria, séries `->` onde há. [ ] Diurese somada célula-a-célula.
- [ ] Zero explicação no bloco (obs no rodapé). [ ] Impressão sem setinhas.
- [ ] Plano rico e acionável. [ ] Campo sem fonte omitido. [ ] 7 seções na ordem (cabeçalho + 7).
- [ ] Janela 24 h (07 h a 05 h) salvo pedido explícito. [ ] Ficha-cola: 1 folha por leito, com todos os vitais e o balanço.
