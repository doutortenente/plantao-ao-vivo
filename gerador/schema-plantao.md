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
    "turno": "diurno",
    "janela": "24 h",            // padrão; um leito pode sobrescrever
    "data_prescricao": "11/10"
  },
  "leitos": [{
    "leito": "01",
    "nome": "NOME COMPLETO",
    "iniciais": "NC",                       // opcional
    "idade_sexo": "36F",
    "dia_uti": "D4 UTI",
    "diagnostico": "linha curta da ficha-cola",
    "alergia": "Nega",                      // vermelho na ficha se != "Nega..."
    "dieta": "geral VO",                    // vai na linha de balanço
    "dieta_ficha": "Geral VO",              // opcional: texto do topo da ficha
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

    "prescricao": [                          // só para a ficha-cola
      {"classe": "ATB", "itens": ["Rocefin (ceftriaxona) 1 g EV 12/12h — I: 08/10 (D4) => 10-22"]}
    ],
    "alertas": ["até 3 frases curtas"]
  }]
}
```

Nomes de ganho/perda reconhecidos: ver `CANON` no motor (dieta, soro, EV, diluição, NPT, CH, ingesta, reposição,
noradrenalina... / diurese, SVD, SNG, resíduo, dreno, evacuação, UF, diálise...). Nome desconhecido não entra na
conta e vira aviso.
