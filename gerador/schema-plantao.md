# Contrato do JSON do plantão

Um arquivo por plantão. Lido pelo motor (`skills/sasi-ingest-export/scripts/build_passagem.py`) e pelo gerador
(`gerador/gerar_docx.py`). Exemplo completo: `gerador/exemplo/plantao-exemplo.json`.

Regra geral: o JSON leva números CRUS (células, séries). Quem soma, conta flag e formata é o motor.
Campo sem fonte → omitido. Ilegível → `"?"` dentro da série.

```jsonc
{
  "meta": {
    "unidade": "UTI 2",          // nome do arquivo: uti2
    "data": "11/10/2026",        // nome do arquivo: 11-10-26
    "turno": "diurno",           // nome do arquivo: ...-evolucoes-diurno
    "janela": "24 h",            // padrão; um leito pode sobrescrever
    "data_prescricao": "11/10"
  },
  "leitos": [{
    "leito": "01",
    "nome": "NOME COMPLETO",
    "iniciais": "NC",                       // opcional
    "idade_sexo": "36F",
    "dia_uti": "D4 UTI",
    "diagnostico": "linha curta",           // hoje não impresso: a ficha usa ficha.dx
    "alergia": "Nega",                      // hoje não impresso: a ficha usa ficha.alergia
    "dieta": "geral VO",                    // vai na linha de balanço
    "janela": "desde a admissão (19 h - 05 h)",  // opcional

    "vitais": {                             // série horária OU agregado
      "PAS": [146, 126, "?", 122],
      "PAD": {"max": 94, "min": 71, "flag": 0},          // agregado: flag = nº de vezes no 1º limiar
      "TAX": {"max": 36.8, "min": 35.0, "flag": {"< 35,5": 3}},
      "Dx": [255, 141, "< 20", 176]
    },
    "sup_o2": "AA" ,                        // AA/cateter → (AA) no SpO2; VM → linha própria
    "ganhos": [{"nome": "dieta SNE", "serie": [100, 100]}, {"nome": "soro EV", "ml": 500}],
    "perdas": [{"nome": "diurese (SVD)", "serie": [150, 100]}, {"nome": "UF", "serie": [70, 80]},
               {"nome": "resíduo gástrico", "serie": [40, 25]}],
    "conferencia_enfermagem": {"ganhos": 1840, "perdas": 1300, "bh": 540},  // rodapé da folha, só confere
    "evacuacao": "ausente (última 08/10)",
    "outros_balanco": ["Noradrenalina: 7 -> 5 -> 2,5 ml/h"],
    "avisos": ["vai para o rodapé Conferir, nunca para o bloco"],

    "laboratorio": ["HB: 13,4 -> 13,2 g/dl | HT: 39,9 -> 40,4 %", "UR: 26,4 -> 26,1 mg/dl"],
    "terapias": ["RESP: ...", "ATB: Rocefin 1 g EV 12/12h (D4, I: 08/10)."],
    "exame_fisico": ["- SNC: ...", "- ACV: ..."],
    "evolucao": ["frase com verbo de ação", "..."],
    "impressao": ["Problema, tendência - leitura de 1 linha"],
    "conduta": ["1. Respiratório:", "- ação;", "2. Profilaxias: TEV ...; LAMG ...; cabeceira 30º."],

    "dispositivos": "TQT (06/10) · PICC MSD (15/09) · SVD (22/09)",  // hoje não impresso: a ficha usa ficha.disp
    "alertas": ["até 3 frases curtas"],     // para o chat; não vão para a ficha nem para o bloco

    "ficha": { }                             // OBRIGATÓRIO: bloco da ficha-cola, abaixo
  }]
}
```

Nomes de ganho/perda reconhecidos: ver `CANON` no motor (dieta, soro, EV, diluição, NPT, CH, ingesta, reposição,
noradrenalina... / diurese, SVD, SNG, resíduo, dreno, evacuação, UF, diálise...). Nome desconhecido não entra na
conta e vira aviso.

## Bloco `ficha` (ficha-cola, modelo aprovado em 12/10/2026)

Um por leito, obrigatório. Sem ele o gerador para com erro (a ficha-cola antiga foi aposentada em 19/10/2026).
Texto curto, sem frase explicativa. `**negrito**` só para alerta (dose divergente, item suspenso, valor crítico).

```jsonc
"ficha": {
  "janela_controles": "11/10  ·  07 - 23 h",      // título da coluna CONTROLES
  "janela_balanco": "07 - 18 h",                  // título do BALANÇO
  "alergia": "nega",                              // != "nega" sai em CAIXA ALTA e negrito
  "dx": "Problema 1  ·  Problema 2  ·  AP",       // linha Dx do cabeçalho (até 2 linhas)
  "disp": "TQT 06/10  ·  PICC MSD 15/09",         // linha Disp. do cabeçalho
  "infusoes": [["DVA", ["Noradrenalina 16 mg/250 ml 2 ml/h"]],   // INFUSÕES E TERAPIAS:
               ["ATB", ["Meronem (meropenem) 1 g EV 8/8 h (D3, I: 09/10) => 14-22-06"]]],  // DVA, SEDAÇÃO, ATB, VM/O2, DIETA/NPT, TRS
  "sistemas": [["NEURO", ["..."]], ["CV", ["..."]], ["RESP", ["..."]], ["TGI", ["..."]],
               ["RENAL", ["..."]], ["ENDÓCRINO", ["..."]], ["ANALGESIA", ["..."]],
               ["PROFILAXIA", ["só TEV/LAMG — nunca analgésico aqui"]], ["SN", ["..."]], ["SUSPENSOS", ["..."]]],
  "vigiar": ["3 a 7 pendências, 1 linha cada, ação concreta"],
  "exames": ["exame relevante em 1 linha"],
  "lab_titulo": "LABORATÓRIO 10/10 -> 11/10",
  "lab": ["Hb 7,3 | Leuco 16.800", "Ur 129 -> 100 | Cr 1,4", "Na 137 | **K 3,3**"]   // 1 grupo por linha
}
```

Itens de prescrição: `Nome (genérico) dose via freq => horários`; vários na mesma linha separados por " · ".
O nome antes do primeiro número/parêntese sai em negrito automaticamente.
