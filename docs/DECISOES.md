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

## Pendente (não resolvido aqui)

- `labs.py` é beta até ser calibrado com um PDF real de laboratório.
- Esteira: falta criar o segredo, o campo de saída e a automação no Airtable (`esteira/README.md`). Também falta
  conferir no primeiro disparo se o upload do Airtable acrescenta arquivos ou substitui os anteriores.
- O JSON da página `extracao-web` não monta o bloco `ficha`: quem monta é o Claude no chat, a partir de
  `prescricao_lida`.
