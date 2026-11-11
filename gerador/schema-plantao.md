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
    "horas_balanco": 12,         // opcional: horas que o balanço cobre quando a janela não é 24 h (débito em ml/kg/h)
    "data_prescricao": "11/10"
  },
  "leitos": [{
    "leito": "01",
    "nome": "NOME COMPLETO",
    "iniciais": "NC",                       // opcional
    "idade_sexo": "36F",
    "dia_uti": "D4 UTI",                    // calculado se houver admissao_uti (diverge = aviso e vale a conta)
    "admissao_uti": "08/10/2026",           // dia da admissão = D1
    "hd": "Problema 1  ·  Problema 2",            // hipóteses diagnósticas (rótulo HD: na ficha; não é vitais.Dx)
    "alergia": "Nega",                      // fonte única; != "nega" sai em CAIXA ALTA e negrito; sem saber: "?"
    "dieta": "geral VO",                    // vai na linha de balanço
    "peso": {"kg": 66, "altura_cm": 153, "fonte": "EcoTT", "data": "06/12/2025"},  // opcional; ver "Peso" abaixo
    "janela": "desde a admissão (19 h - 05 h)",  // opcional
    "horas_balanco": 10,                    // opcional: sobrescreve o da meta neste leito

    "vitais": {                             // POR HORA (preferido), lista sem hora, ou agregado
      "PAM": {"07": 90, "09": [86, 84], "11": "?", "19": 68},   // hora da folha (07 … 05); 2 leituras = lista
      "PAS": [146, 126, "?", 122],          // aceito, mas sem hora o motor não confere a janela (aviso)
      "PAD": {"max": 94, "min": 71, "flag": 0},          // agregado: flag = nº de vezes no 1º limiar
      "TAX": {"max": 36.8, "min": 35.0, "flag": {"< 35,5": 3}},
      "Dx": [255, 141, "< 20", 176]          // glicemia (rótulo Dx na grade de controles da ficha)
    },
    "sup_o2": "AA" ,                        // AA/cateter → (AA) no SpO2; VM → linha própria
    "ganhos": [{"nome": "dieta SNE", "serie": {"07": 100, "09": 100}}, {"nome": "soro EV", "ml": 500}],
    "perdas": [{"nome": "diurese (SVD)", "serie": [150, 100]}, {"nome": "UF", "serie": [70, 80]},
               {"nome": "resíduo gástrico", "serie": [40, 25]}],
    "conferencia_enfermagem": {"ganhos": 1840, "perdas": 1300, "diurese": 1100, "bh": 540},  // rodapé, só confere
    "evacuacao": "ausente (última 08/10)",
    "infusoes_continuas": [                 // DVA, sedação e BNM em bomba: ver "Bombas" abaixo
      {"droga": "Hyponor", "ampolas": 4, "diluente_ml": 234},             // vazão: série do balanço com o nome
      {"droga": "Dormonid", "ampolas": 3, "diluente_ml": 120, "ml_h": {"07": 4, "19": 6}}],  // ou `ml_h`
    "outros_balanco": ["UF programada: 2.000 ml"],  // linha livre do bloco; droga em bomba NÃO vem aqui
    "avisos": ["vai para o rodapé Conferir, nunca para o bloco"],

    "laboratorio": ["HB: 13,4 => 13,2 g/dl | HT: 39,9 => 40,4 %", "UR: 26,4 => 26,1 mg/dl | CR: 0,8 => 0,9 mg/dl | NA: 138 | K: 4,1"],
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
    "prescricao_lida": {"Infeccioso e Respiratório": ["…"]},  // opcional: o que a página de extração leu da
                                            // prescrição (7 blocos); o Claude monta o bloco `ficha` a partir dela

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

## Peso

`peso` só entra em conta com `kg`, `fonte` (balança, EcoTT, admissão, cama-balança…) e `data` em dd/mm/aaaa; a
altura é opcional. Sem fonte ou sem data é ERRO no validar; peso ilegível: `"kg": "?"` (aviso, nada por kg). Faixas
do app de calculadoras: 30 a 250 kg, 120 a 230 cm. Peso com mais de 30 dias vira aviso. Sem `peso`, nada por kg é
calculado e o bloco sai como antes. O `evolucao_anterior.py` (e a esteira) devolve o peso da linha "Peso:" da véspera,
com a fonte e a data de origem: não redigitar. Com ele, o motor (`peso.py`) escreve:

- `Peso: 66 kg (EcoTT, 06/12/2025) | Altura: 153 cm` e, em VM, `| Peso predito: 46 kg (VC 6 - 8 ml/kg: 276 - 368 ml)`
  (ARDSNet: 50 ou 45,5 + 0,91 x (altura - 152,4)). Em VM sem altura: aviso.
- `Débito urinário: 0,38 ml/kg/h em 12 h [KDIGO 2 pelo débito]`, logo abaixo da Diurese: a média da janela; KDIGO
  pelo débito (< 0,5 em 6 h = 1, em 12 h = 2; < 0,3 em 24 h = 3), nunca pela creatinina. Horas: `horas_balanco` (leito
  ou meta) ou 24 na janela de 24 h; janela recortada sem `horas_balanco`, diurese 0 ou célula de diurese ilegível:
  não calcula e avisa.
- `CLCR (Cockcroft-Gault): 26 ml/min`, última linha do Laboratório, com o peso informado e a linha `CR:` do lab
  (x 0,85 na mulher; idade e sexo de `idade_sexo`). Creatinina subindo ou IMC >= 30: aviso (superestima a função
  renal). CR atual ilegível (`1,4 => ?`): não calcula. Não escreva CLCR à mão: é conta do motor.
- Em TRS (UF, CVVHDF ou diálise no balanço, ou linha TRS na ficha): sem ClCr (dose pela modalidade de TRS) e sem o
  KDIGO pelo débito (TRS já é estágio 3); o débito em ml/kg/h continua.

## Bombas (`infusoes_continuas`)

Uma entrada por droga em BIC da tabela do app calculadoras-uti (`skills/sasi-ingest-export/scripts/bic.py`):
noradrenalina, vasopressina, adrenalina, dobutamina, milrinone, nitroprussiato, nitroglicerina, dopamina, fentanil,
midazolam, propofol, cetamina, dexmedetomidina, morfina, rocurônio (genérico, marca ou apelido: Hyponor, Dormonid,
Precedex…). Droga fora da tabela (amiodarona, insulina…) é ERRO aqui: fica na linha manual da ficha e no texto.

- `droga`, `ampolas` e a diluição DA PRESCRIÇÃO: `diluente_ml` (o volume final soma o das ampolas: 4 amp de 4 ml +
  234 ml = 250 ml) ou `volume_final_ml` (0 = puro), nunca os dois. Apresentação diferente da tabela:
  `mg_por_ampola` / `ml_por_ampola`.
- Vazão: `ml_h` (número ou série por hora da folha) ou, sem ele, a série do balanço cujo nome traz a droga (célula =
  ml/h). `ml_h` que não bate com a série do balanço vira aviso. Sem nenhum dos dois: "sem vazão na folha".
- O motor escreve no bloco, antes do BH: `Noradrenalina: 16 mg/250 ml (64 mcg/ml), 3 => 2 ml/h (0,05 => 0,03
  mcg/kg/min)` (contas e casas decimais do app; sem peso, só a vazão). Acima do teto do app: `ALERTA:` no topo.
- Na ficha, as linhas DVA, SEDAÇÃO e BNM saem do motor, uma linha por bomba com o que corre agora (`Hyponor 16
  mg/250 ml · 2 ml/h · 0,03 mcg/kg/min`; a sequência fica na evolução, e a folha cabe). Linha manual com o mesmo
  rótulo é mesclada (droga fora da tabela fica depois);
  a mesma droga à mão ao lado (na ficha ou em `outros_balanco`) é ERRO, exceto item ACM/SOS/"sem uso". Droga da
  tabela à mão na linha DVA/SEDAÇÃO/BNM sem estar em `infusoes_continuas`: aviso.

Nomes de ganho/perda reconhecidos: ver `CANON` no motor (dieta, soro, EV, diluição, NPT, CH, hemácias, plaquetas,
ingesta, reposição, DVA, sedação, bicarbonato, glicose, ATB... / diurese, débito urinário, SVD, SNG, SOG, resíduo,
dreno, drenagem, hemovac, colostomia, ileostomia, evacuação, UF, CVVHDF, diálise...). Nome desconhecido é ERRO no
validar: ficaria fora da conta e o BH sairia errado.

## Bloco `ficha` (ficha-cola, modelo aprovado em 12/10/2026)

Um por leito, obrigatório. Sem ele o gerador para com erro (a ficha-cola antiga foi aposentada em 19/10/2026).
Cabeçalho impresso (não vem no bloco `ficha`): dia de UTI, Idade/Sexo, Peso e Altura na linha sob o nome
(valores de `idade_sexo` e do bloco `peso`; peso/altura independentes; sem fonte/data no papel), rótulo **HD:**
(a partir de `leito.hd` ou `ficha.hd`) e `Disp.`. Grade de balanço na ficha: sem linha Ganhos (11/11/2026).
Texto curto, sem frase explicativa. `**negrito**` só para alerta (dose divergente, item suspenso, valor crítico).
Todo número de `lab` tem de estar em `laboratorio`, e o ATB da ficha tem de bater com o das terapias
(gerador/validar.py avisa).

```jsonc
"ficha": {
  // opcionais: só quando a ficha precisa de texto diferente do leito. Sem eles, vale o do leito.
  "janela_controles": "11/10  ·  07 - 23 h",      // padrão: "<data>  ·  07 - 05 h" (24 h) ou a janela do leito
  "janela_balanco": "07 - 18 h",                  // padrão: "07 - 05 h" (24 h) ou a janela do leito
  "alergia": "nega",                              // padrão: leito.alergia. Diferente do leito = ERRO na validação
  "hd": "Problema 1  ·  Problema 2  ·  AP",       // opcional; padrão: leito.hd (rótulo HD:)
  "disp": "TQT 06/10  ·  PICC MSD 15/09",         // padrão: leito.dispositivos (aviso se diferente)
  "infusoes": [["ATB", ["Meronem (meropenem) 1 g EV 8/8 h (D3, I: 09/10) => 14-22-06"]],  // INFUSÕES E TERAPIAS:
               ["VM", ["PCV  ·  PEEP 8  ·  FiO2 40%"]],
               ["DIETA", ["Fresubin HP Energy 60 ml/h SNE  ·  Água 200 ml 6/6 h"]]],  // TNE: com a água da sonda, sem horários
                                                          // ATB, VM/O2, DIETA/NPT, TRS; DVA/SEDAÇÃO/BNM saem de
                                                          // `infusoes_continuas`; o VC alvo entra na linha VM
  "sistemas": [["NEURO", ["..."]], ["CV", ["..."]], ["RESP", ["..."]], ["TGI", ["..."]],
               ["RENAL", ["..."]], ["ENDÓCRINO", ["..."]], ["ANALGESIA", ["..."]],
               ["PROFILAXIA", ["só TEV/LAMG — nunca analgésico aqui"]], ["SN", ["..."]], ["SUSPENSOS", ["..."]]],
  "vigiar": ["3 a 7 pendências, 1 linha cada, ação concreta"],
  "exames": ["exame relevante em 1 linha"],
  "lab_titulo": "LABORATÓRIO 10/10 -> 11/10",
  "lab": ["Hb 7,3 | Leuco 16.800", "Ur 129 -> 100 | Cr 1,4", "Na 137 | **K 3,3**"]   // 1 grupo por linha
}
```

Itens de prescrição: `Nome (genérico) dose via freq`; vários na mesma linha separados por " · ". Horários (`=> 14-22-06`)
podem vir no JSON, mas a ficha-cola sai sem eles (02/11/2026: ruído).
O nome antes do primeiro número/parêntese sai em negrito automaticamente.
