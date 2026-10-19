# Contrato do JSON do plantão

Um arquivo por plantão. Lido pelo motor (`skills/sasi-ingest-export/scripts/build_passagem.py`) e pelo gerador
(`gerador/gerar_docx.py`). Exemplo completo: `gerador/exemplo/plantao-exemplo.json`.

Regra geral: o JSON leva números CRUS (células, séries). Quem soma, conta flag e formata é o motor.
Séries por hora (`{"07": 146, "09": 126, …}`, horários da folha 07, 09 … 23, 01, 03, 05): com elas o motor confere a
janela. Pedida 24 h e só há 19–05 h → título "19 - 05 h" e ALERTA (erro de 11/10/2026); hora faltando → aviso.
Recorte de turno só com `meta.recorte` (ou `janela` do leito) quando ele pedir.
Campo sem fonte → omitido. Ilegível → `"?"` dentro da série.

```jsonc
{
  "meta": {
    "unidade": "UTI 2",          // nome do arquivo: uti2
    "data": "11/10/2026",        // dd/mm/aaaa (obrigatório: os dias de ATB e de UTI saem dela); arquivo: 11-10-26
    "turno": "diurno",           // nome do arquivo: ...-evolucoes-diurno
    "janela": "24 h",            // padrão; um leito pode sobrescrever
    "data_prescricao": "11/10"
  },
  "leitos": [{
    "leito": "01",
    "nome": "NOME COMPLETO",
    "iniciais": "NC",                       // opcional
    "idade_sexo": "36F",
    "dia_uti": "D4 UTI",                    // calculado se houver admissao_uti (diverge = aviso e vale a conta)
    "admissao_uti": "08/10/2026",           // dia da admissão = D1
    "diagnostico": "Problema 1  ·  Problema 2",   // Dx do cabeçalho da ficha (fonte única)
    "alergia": "Nega",                      // fonte única; != "nega" sai em CAIXA ALTA e negrito; sem saber: "?"
    "dieta": "geral VO",                    // vai na linha de balanço
    "janela": "desde a admissão (19 h - 05 h)",  // opcional

    "vitais": {                             // POR HORA (preferido), lista sem hora, ou agregado
      "PAM": {"07": 90, "09": [86, 84], "11": "?", "19": 68},   // hora da folha (07 … 05); 2 leituras = lista
      "PAS": [146, 126, "?", 122],          // aceito, mas sem hora o motor não confere a janela (aviso)
      "PAD": {"max": 94, "min": 71, "flag": 0},          // agregado: flag = nº de vezes no 1º limiar
      "TAX": {"max": 36.8, "min": 35.0, "flag": {"< 35,5": 3}},
      "Dx": [255, 141, "< 20", 176]
    },
    "sup_o2": "AA" ,                        // AA/cateter → (AA) no SpO2; VM → linha própria
    "ganhos": [{"nome": "dieta SNE", "serie": {"07": 100, "09": 100}}, {"nome": "soro EV", "ml": 500}],
    "perdas": [{"nome": "diurese (SVD)", "serie": [150, 100]}, {"nome": "UF", "serie": [70, 80]},
               {"nome": "resíduo gástrico", "serie": [40, 25]}],
    "conferencia_enfermagem": {"ganhos": 1840, "perdas": 1300, "diurese": 1100, "bh": 540},  // rodapé, só confere
    "evacuacao": "ausente (última 08/10)",
    "outros_balanco": ["Noradrenalina: 7 -> 5 -> 2,5 ml/h"],
    "avisos": ["vai para o rodapé Conferir, nunca para o bloco"],

    "laboratorio": ["HB: 13,4 -> 13,2 g/dl | HT: 39,9 -> 40,4 %", "UR: 26,4 -> 26,1 mg/dl"],
    "terapias": ["RESP: ...", "ATB: Rocefin 1 g EV 12/12h (D?, I: 08/10)."],  // D? ou só (I: dd/mm): o motor
                                            // escreve o D (início = D0); D errado é corrigido e vira aviso
    "exame_fisico": ["- SNC: ...", "- ACV: ..."],
    "evolucao": ["frase com verbo de ação", "..."],
    "impressao": ["Problema, tendência - leitura de 1 linha"],
    "conduta": ["1. Respiratório:", "- ação;", "2. Profilaxias: TEV ...; LAMG ...; cabeceira 30º."],
    "plano_anterior": ["linhas do plano da evolução anterior"],  // opcional: o motor alerta se algo que ele
                                            // mandou suspender continua na prescrição da ficha

    "dispositivos": "TQT 06/10  ·  PICC MSD 15/09  ·  SVD 22/09",  // Disp. do cabeçalho da ficha (fonte única)
    "alertas": ["até 3 frases curtas"],     // para o chat; não vão para a ficha nem para o bloco

    "ficha": { }                             // OBRIGATÓRIO: bloco da ficha-cola, abaixo
  }]
}
```

Cruzamentos de segurança (`skills/sasi-ingest-export/scripts/checagens.py`, rodam no motor): alergia × prescrição
pela classe da droga, falta de profilaxia de TEV (só o plano que diz por quê — contraindicação, plaquetopenia,
sangramento — dispensa o alerta), duplicidade (IBP, anticoagulante, mesma droga em dois itens) e droga suspensa no
`plano_anterior` (lido por oração: "não suspender" e "se sangrar, suspender" não contam). Item suspenso não conta como
prescrito. Saem como `ALERTA:` no topo do "Conferir". Droga fora do dicionário `DROGAS` não é checada: acrescente lá.

O D do ATB é escrito em todos os textos do leito (terapias, plano, evolução, impressão, ficha); "(D3)" sem a data de
início não é recalculado, mas vira aviso se divergir da conta, e "D?" que sobra vai para o "Conferir". Trecho que diz
"suspenso" fica com o D que tinha. Início sem ano que daria mais de 60 dias, e admissão depois do plantão, não são
escritos: ficam como estão e vão para o "Conferir".

Nomes de ganho/perda reconhecidos: ver `CANON` no motor (dieta, soro, EV, diluição, NPT, CH, hemácias, plaquetas,
ingesta, reposição, DVA, sedação, bicarbonato, glicose, ATB... / diurese, débito urinário, SVD, SNG, SOG, resíduo,
dreno, drenagem, hemovac, colostomia, ileostomia, evacuação, UF, CVVHDF, diálise...). Nome desconhecido é ERRO no
validar: ficaria fora da conta e o BH sairia errado.

## Bloco `ficha` (ficha-cola, modelo aprovado em 12/10/2026)

Um por leito, obrigatório. Sem ele o gerador para com erro (a ficha-cola antiga foi aposentada em 19/10/2026).
Texto curto, sem frase explicativa. `**negrito**` só para alerta (dose divergente, item suspenso, valor crítico).
Todo número de `lab` tem de estar em `laboratorio`, e o ATB da ficha tem de bater com o das terapias
(gerador/validar.py avisa).

```jsonc
"ficha": {
  // opcionais: só quando a ficha precisa de texto diferente do leito. Sem eles, vale o do leito.
  "janela_controles": "11/10  ·  07 - 23 h",      // padrão: "<data>  ·  07 - 05 h" (24 h) ou a janela do leito
  "janela_balanco": "07 - 18 h",                  // padrão: "07 - 05 h" (24 h) ou a janela do leito
  "alergia": "nega",                              // padrão: leito.alergia. Diferente do leito = ERRO na validação
  "dx": "Problema 1  ·  Problema 2  ·  AP",       // padrão: leito.diagnostico (aviso se diferente)
  "disp": "TQT 06/10  ·  PICC MSD 15/09",         // padrão: leito.dispositivos (aviso se diferente)
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
