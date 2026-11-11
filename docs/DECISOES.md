# Decisões e correções

## Decisões do operador (o que vale)

| Data | Decisão |
|---|---|
| 27/09/2026 | Doc do plantão só com sinais vitais, laboratório e prescrição; alertas no chat, uma vez só. |
| 10/10/2026 | Ficha-cola tem de trazer TODOS os sinais vitais e o balanço, não versão resumida. |
| 10/10/2026 | Ficha-cola = 1 folha por leito (paisagem); evolução pode ter mais de uma página. |
| 11/10/2026 | Sinais vitais em 24 h, não só o turno noturno. |
| 11/10/2026 | Evolução só com o que importa (7 blocos); sem repetir identificação, história, dispositivos, exames antigos. |
| 11/10/2026 | Times New Roman 10, negrito mantido, visual limpo. |
| 11/10/2026 | Repositório próprio `plantao-ao-vivo`, independente, sem symlinks. |
| 11/10/2026 | Admissão com skill própria (`admissao-uti`), no padrão das evoluções reais dele: sem escore, sem rodapé, sem "Exame físico por sistemas"; entrega em Word Times New Roman 10. |
| 12/10/2026 | O projeto do claude.ai sincroniza o `plantao-ao-vivo`; as instruções do projeto ficam versionadas em `docs/instrucoes-projeto.md` (v1.0; hoje v1.2, de 13/10/2026). |
| 19/10/2026 | Admissão em A4 (não Carta), margens 1,25 / 1,34 / 2,5 cm. Gerador em `gerador/gerar_admissao.py`. |
| 19/10/2026 | ATB: dia de início = D0 (iniciou ontem: ontem D0, hoje D1). UTI: dia da admissão = D1. O motor calcula os dois (`preparar` em `build_passagem.py`). |
| 19/10/2026 | Plantão roda no projeto do claude.ai (hooks do Claude Code não valem lá): as regras viram script, teste e CI. |
| 19/10/2026 | Exceções aprovadas ao "TNR 10 em tudo", só na ficha-cola: 8 (rótulo LEITO), 9 (rótulos e flags), 13 (nome), 20 (nº do leito) e o "– " de EXAMES. |
| 19/10/2026 | Mudanças entram por branch + PR com CI; o merge na `main` é de uma vez, com o "prosseguir" dele. |
| 11/11/2026 | Ficha-cola, cabeçalho: `HD:` no lugar de Dx para hipóteses (JSON `hd` no leito e opcional `ficha.hd`; `diagnostico` e `ficha.dx` aposentados). Idade/Sexo legíveis; `Peso`/`Altura` no cabeçalho. Balanço da ficha sem Ganhos. `vitais.Dx` = glicemia. |
| 07/11/2026 | Ficha-cola, opção A ("faixas cinza"), escolhida entre 3 no canvas: título em faixa cinza, linha sim/linha não em cinza, alergia e alertas em caixa; o cinza é só de fundo e o texto continua preto. Embaixo, EXAME FÍSICO em 6 quadros por sistema no lugar da grade CONTROLES DO PLANTÃO, sem a faixa de bundle (FAST HUGS BID): ele mandou tirar. Folha cheia: o exame fica compacto antes de a fonte descer. |
| 01/11/2026 | Peso no plantão (item 2 das melhorias): peso só com fonte e data; o motor calcula a dose das bombas pela diluição da prescrição (tabela e contas do app calculadoras-uti), o débito em ml/kg/h com KDIGO pelo débito, o ClCr (Cockcroft-Gault) e, em VM, o peso predito com o VC de 6 a 8 ml/kg. Nada por kg de cabeça. |
| 12/10/2026 | Ficha-cola: modelo novo aprovado (`gerador/ficha_cola.py`) — Dx no cabeçalho, prescrição em 2 blocos (infusões/terapias + por sistemas), controles em grade, PDF junto. Profilaxia só TEV/LAMG. Folha que estoura no Word = erro grave. |

## Correções feitas ao montar este repositório (11/10/2026)

Origem: `doutortenente/claude-workspace`. O que estava desatualizado ou errado e como ficou aqui:

1. **Symlinks.** `EXTRACAO-CLINICA-SASI/` era feita de 7 symlinks para `skills-que-prestam/`. Aqui tudo é arquivo real.
2. **Balanço pelo rodapé × pelas células.** A skill `controles-vitais-janela` dizia "rodapés = verdade"; o BRIEFING
   dizia "some as células, nunca o total escrito". Vale o BRIEFING. Corrigidos a skill, o `exemplo-resolvido.md`, a
   skill `plantao` e a página `extracao-web` (diurese). Caso real que mostrou o erro: L10 de 11/10/2026, UF diurno
   920 ml pelas células, 960 ml no rodapé.
3. **Separador do Máx - Mín.** Skill e motor usavam "–"; BRIEFING e exemplo usam " - ". Padronizado " - ".
4. **Sup O2.** Skill: "na linha do SpO2 com ` | `". BRIEFING: AA/cateter entre parênteses; VM em linha própria.
   Vale o BRIEFING (skill, exemplo, motor e página corrigidos).
5. **`(revisar)` dentro do bloco.** Skill e templates mandavam marcar no valor; o BRIEFING proíbe explicação no bloco.
   Agora vai para o rodapé "Conferir".
6. **Janela.** BRIEFING dizia `[12 h / 6 h]`; vale 24 h.
7. **Módulo C da skill de controles** (sequência de 21/06/26) não tinha Laboratório e usava títulos diferentes do
   BRIEFING. Substituído pela sequência do BRIEFING.
8. **Motor `build_passagem.py`:**
   - classificava "evacuação" como GANHO (o radical "ev" casava por substring) — corrigido (radical curto só casa
     palavra inteira; vence o radical mais longo);
   - não conhecia UF/ultrafiltração nem diálise — acrescentado como perda;
   - punha divergência com a enfermagem DENTRO do bloco — agora vai para os avisos;
   - não tinha seção Laboratório e usava títulos fora do BRIEFING — alinhado;
   - Dx agora em ordem decrescente separado por " / ", aceita "< 20".
   - Flags acrescentadas: Dx < 70 e TAX > 37,8 (ver BRIEFING §2).
9. **Workflow `plantao.yml`** passava TODOS os segredos do repositório ao job (`toJSON(secrets)`). Agora passa só
   `AIRTABLE_TOKEN`. Caminhos dos workflows ajustados para este repo.
10. **Skill `plantao`** entregava `.md` no OneDrive via rclone; a entrega hoje é Word. Reescrita.
11. **Skill `admissao-uti`** apontava para caminhos do PC (`~/src/...`) que não existem neste repo — apontada para
    o template daqui.
12. **`doc-plantao-formato.md`** (Google Doc, Arial, caixa cinza) substituído por `docs/formato-entrega.md`.
13. **Skill `admissao-uti`** trazia o TEMPLATE-BASE v2 do SASI ("Exame físico por sistemas", escores, rodapé),
    espelhado no template de exportação do SASI. Reescrita em 11/10/2026 a partir das evoluções reais do Dr.
    (admissão do leito 02 de 10/10/26) e do rascunho v3 dele; o espelhamento com `04-export-evolucao-template.md` acabou.

## Automações de 19/10/2026 (PR da branch `claude/wonderful-einstein-0bp9p1`)

1. A ficha-cola antiga saiu do código; leito sem bloco `ficha` é erro.
2. `gerador/estilo.py` concentra fonte, tamanhos, cinzas, fios e margens. Os nomes são os do design system.
3. `gerador/validar.py` roda antes de gerar. Erros:
   - campo que falta;
   - tipo errado;
   - `meta.data` sem ano;
   - alergia divergente;
   - item de balanço fora do CANON;
   - "(revisar)" no bloco.

   O resto vira aviso.
4. `gerador/conferir.py` roda depois de gerar: fonte, tamanho, cor, texto proibido, 1 folha por leito (medida com a
   folga de 1,5 cm) e PNG de cada página.
5. `checagens.py` (no motor) cruza a prescrição com a alergia (pela classe), a profilaxia de TEV (o plano só
   dispensa o alerta com justificativa), as duplicidades e o que o plano anterior mandou suspender (lido por oração).
6. Motor:
   - dias de ATB (D0) e de UTI (D1) em todos os textos do leito;
   - janela conferida pelas horas (só noite = ALERTA, como no erro de 11/10);
   - diurese do rodapé também conferida.
7. Leitura de laboratório (`labs.py`, beta), da evolução anterior (`gerador/evolucao_anterior.py`) e da pasta de
   entrada (`gerador/preparar.py`).
8. `gerador/entrega.py`: versão anterior em `historico/`, diff por leito e rascunho do chat em `mensagem.md`.
9. Admissão em arquivo testado (`gerador/gerar_admissao.py`, A4).
10. CI (`.github/workflows/testes.yml`): testes e o exemplo gerado e conferido a cada push e PR.
11. Esteira etapa 3 (`esteira/`): lê os scans com a API do Claude, monta o JSON do leito e devolve no Airtable a
    ficha-cola, o rascunho e o "Conferir". Fica dormente sem o segredo `ANTHROPIC_API_KEY` (passo a passo em
    `esteira/README.md`).
    - As PENDÊNCIAS que a esteira imprime são só as ordens escritas na prescrição: texto que o modelo escrevesse não
      vai para o papel sem revisão.
    - O balanço sai pela coluna impressa da folha.
    - O log do Actions (repositório público) só tem contagens.
12. Página `extracao-web`, republicada no mesmo link:
    - conta pelas células;
    - usa os limiares do motor;
    - tira as marcas de dúvida do bloco;
    - exporta o JSON do plantão;
    - tem teste que compara a página com o motor.
13. `tests/test_doutrina.py`: docs, skills e a página não podem contradizer o BRIEFING nem o motor.

Revisão adversarial das etapas 1 a 8, com cada achado reproduzido antes de corrigir: commit
`fix(motor): corrige os achados da revisão adversarial`.

## Revisão adversarial final (21/10/2026)

Cada achado foi reproduzido antes de corrigir e ganhou teste (commit `fix(revisao): …`). O que muda no uso:

- `mensagem.md`: alerta já dado só deixa de se repetir no mesmo plantão e numa rodada entregue. Antes, o alerta
  de TEV ou de alergia sumia do rascunho do dia seguinte.
- Segurança: "suspensão oral" é forma farmacêutica, não ordem de suspender. "Não tolera X" conta como alergia.
  "Suspendo X e Y" suspende os dois. Heparina de selo de cateter não é profilaxia de TEV. Novas abreviações: PNC,
  AINH, Pip/Tazo, SMX-TMP, Enoxa, HBPM, Flagyl, Dalacin, Fentanest, Ceftriaxone.
- Motor: "1.450" no rodapé = 1450 ml; janela "24h" e "24 horas" é conferida; vital só com máx/mín é conferido
  contra o limiar.
- Esteira: foto no lugar do PDF, página de outro paciente e folha ou prescrição faltando = erro (status
  "falhou"). Ficha reprovada na conferência não volta para o Airtable. O disparo precisa da opção "enviado" no
  Status, que ainda não existe na tabela.

## Formato de entrega da evolução (02/11/2026)

Pedido do Dr. Nicolas no plantão de 01/11:

1. Sinais vitais + balanço numa linha só, itens separados por " | " (`motor.compactar`, usado pelo Word e pelo
   texto). O motor continua guardando as linhas separadas em `secoes`, porque a ficha-cola lê item a item.
2. Sem "Ingesta hídrica" no bloco. Até 10/11/2026 os Ganhos da ficha vinham do motor; desde 11/11/2026 a grade de
   balanço da ficha não traz Ganhos.
3. UR e CR seriais na mesma linha dos eletrólitos; eletrólitos (NA, K, MG, CAI, P) sem série, só o valor atual
   (`labs.py`).
4. Valores seriais com " => " no lugar de " -> " (labs e vazão/dose das bombas). Leitura da CR (`peso.py`) e do
   peso da véspera (`evolucao_anterior.py`) aceitam o formato novo e o antigo.
5. Ficha-cola sem aferição de glicemia e sem escala de correção (`ficha_cola.sem_glicemia`; insulina em horário
   fixo ou em BIC fica).

A página `extracao-web` acompanhou 1 a 4. O modelo próprio da skill `controles-vitais-janela` (pedido
"sinais-labs-prescrição") não mudou.

## Água pela sonda na ficha-cola (02/11/2026)

Em TNE, a linha DIETA da ficha-cola leva a água pela sonda, com volume e frequência. E toda a prescrição da ficha-cola sai sem os horários de
administração ("=> 10-16-22-04"), que são ruído; o JSON pode trazê-los, quem tira é a ficha. O validar deixava a
água fora da ficha ("água NNN ml" estava na lista do que não vai); saiu da lista, e TNE sem água na DIETA agora vira
aviso.

## Pendente (não resolvido aqui)

Lista viva em `docs/PENDENTE.md`.
