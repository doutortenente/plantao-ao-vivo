# Pendente

O que ficou em aberto entre sessões. Quem continuar o trabalho lê isto primeiro e risca o que fechar.

Estado em 11/11/2026: contrato JSON `hd` (fim de `diagnostico` / `ficha.dx`) na `main` — PR [#14](https://github.com/doutortenente/plantao-ao-vivo/pull/14).

Estado em 21/10/2026: o PR [#2](https://github.com/doutortenente/plantao-ao-vivo/pull/2) entrou na `main`
(commit `4db762b`). As etapas 1 a 20 do plano de 19/10 estão feitas, e as lentes de segurança e de esteira da
revisão final estão corrigidas, com teste. O projeto do claude.ai já lê esta versão.

Estado em 11/11/2026: §2 fechada (as 9 suspeitas confirmadas e consertadas, com teste) e o CI vermelho da §6
consertado aqui, à espera da confirmação no GitHub. Suíte: 307 testes (1 pulado sem node/playwright).

## 1. ~~Merge na `main`~~

~~Só com o "prosseguir" do Dr. Nicolas (decisão de 19/10/2026).~~ Feito em 21/10/2026, com o "prosseguir" dele e o
CI verde. Os achados da seção 2 ficam para um PR seguinte.

## 2. ~~Achados da revisão final ainda não conferidos (lente do gerador)~~

A revisão parou por falta de cota antes da etapa de verificação; ficaram 9 suspeitas. Conferidas em 11/11/2026: as 9
se confirmaram. Cada uma ganhou um teste que falhou antes do conserto e passa depois.

- [x] `labs.py`, média: resultado em texto virava o número da referência ("Potássio  HEMOLISADO  3,5 a 5,1" dava
  K 3,5; "Creatinina: Pendente (0,6 a 1,2)" dava CR 0,6). Agora: sem valor e aviso "ler no PDF".
- [x] `labs.py`, média: "1.7" virava 1 (e "7.31" virava 7). Agora decimal com ponto de 1 ou 2 casas vira vírgula;
  milhar ("150.000") continua milhar. Vale também para o laboratório da evolução anterior.
- [x] `labs.py`, baixa: unidade em outra escala saía com a unidade fixa ("16,2 x10³/µL" daria "LEUCO: 16,2 /mm3";
  "108 g/L" daria "HB: 108 g/dl"). Agora: sem valor e aviso com a unidade do laudo.
- [x] `preparar.py`, média: nome com ponto ("labs 11.11.26 leito 05.pdf") era cortado no último ponto; os laudos dos
  leitos 05 e 06 caíam no mesmo `.txt` e o do 05 apontava para o texto do 06. Agora o `.txt` leva o nome inteiro.
- [x] `preparar.py`, média: com um arquivo de evolução por leito, só o último ficava no `evolucao_anterior.json`.
  Agora ficam todos; leito repetido em dois arquivos vira aviso dizendo qual ficou.
- [x] `preparar.py`, média: página girada (/Rotate 90) era recortada com o tamanho da página 1: 2479 px de largura
  numa página de 3508 (perdia 29 %). Agora cada página usa o próprio tamanho, com a rotação.
- [x] `ficha_cola.py`, média: com só a noite nas séries, o motor rebaixava para "19 - 05 h" mas a ficha imprimia o
  "07 - 05 h" do bloco `ficha`. Agora, quando o motor rebaixa, vale a janela dele.
- [x] `evolucao_anterior.py`, baixa: `.txt` salvo no Windows (ANSI) derrubava a leitura; e o BOM do Bloco de Notas
  em UTF-8 escondia o primeiro leito ("﻿LEITO 05"). Agora lê os dois.
- [x] `gerar_admissao.py`, baixa: gerar de novo apagava a admissão anterior. Agora Word e PDF anteriores vão para
  `historico/`.

## 3. Lente da página de extração

Não rodou até o fim. Ainda falta revisar `extracao-web/extracao-controles-labs-prescricao.html` contra o motor:
mesma conta, mesmos limiares, nenhuma marca de dúvida no bloco. O teste `tests/test_pagina.py` cobre o caso do
exemplo e passa.

## 4. Com o Dr. Nicolas (uma vez só)

- Mandar 1 PDF real de laboratório, para calibrar o `labs.py`, que é beta.
- Para ligar a esteira (`esteira/README.md`):
  - o segredo `ANTHROPIC_API_KEY` e a variável `AIRTABLE_CAMPO_SAIDA` no GitHub;
  - o campo de anexo de saída e a opção **enviado** no Status da tabela, que hoje só tem aguardando, lendo, pronto
    e falhou;
  - a automação do Airtable.
  No primeiro disparo, conferir se o upload acrescenta arquivos ou substitui os anteriores.
- Apagar ou atualizar as skills da conta claude.ai com o mesmo nome das do repositório (`sasi-ingest-export`,
  `admissao-uti`), que competem com elas.
- O `api/tokens.md` do design system se regenera ao abrir a página do artefato.

## 5. Peso e bombas (PR `claude/peso-doses-por-kg`, 01/11/2026)

- [x] Merge na `main`: feito em 01/11/2026 (PR [#4](https://github.com/doutortenente/plantao-ao-vivo/pull/4)),
  com o "manda bala" dele e o CI verde.
- [x] Visual da ficha com peso: prévia real (leito 11, 31/10) enviada; ele mandou seguir em 01/11/2026, sem
  ajuste.
- [ ] A esteira (Airtable) leva o peso da evolução anterior, mas não monta `infusoes_continuas` (a prescrição
  lida não separa ampolas e diluente); a página `extracao-web` não lê nenhum dos dois. O Claude completa no chat;
  sem eles, tudo sai como antes (sem nada por kg).
- [ ] A nota de admissão (`gerar_admissao.py`) não escreve a linha "Peso:": o peso do 1º dia entra no JSON à mão.

## 6. Ficha-cola opção A (branch `claude/bold-thompson-sqdlc1`, 07/11/2026)

- [x] Merge na `main` em 08/11/2026, a pedido dele, com o CI vermelho (item seguinte).
- [ ] **CI vermelho: fazer primeiro.** Em 07/11/2026 o `ubuntu-latest` do GitHub virou Ubuntu 26.04 com
  LibreOffice 26.2.6. A `main` de 02/11 e esta sessão usavam o 24.2.7. Lá a ficha do exemplo, sem ajuste e com a
  folga de 1,5 cm, passa de 1 folha, e `tests/test_gerador.py` (`test_sem_ajuste_gera_os_dois`) falha. A `main`
  de antes passa no mesmo runner. Causa provável: o ☐ dos quadros do exame não existe na Times e vem de uma fonte
  de reserva. Simulado aqui com a DejaVu Sans no lugar da FreeSerif (8,1 pt contra 6,8 pt de largura a 9 pt), a
  linha "☐ AA ☐ CN ☐ VNI ☐ CNAF ☐ TOT/TQT" quebra em 2. A fonte de reserva do runner não foi conferida.
  Correção: trocar o ☐ do exame por □ (U+25A1, que a Times e a Liberation Serif têm, com a mesma largura em todo
  computador), deixar folga de largura nas linhas e conferir no CI. A esteira (`plantao.yml`, também em
  `ubuntu-latest`) usa o mesmo LibreOffice 26.2.
  **11/11/2026: consertado aqui, falta o CI confirmar.** Medido: o ☐ não está na Liberation Serif e saía em
  FreeSerif (aqui) ou DejaVu Sans (runner simulado sem a família Free*, onde a linha do RESPIRATÓRIO quebrava). Troca
  feita para □ (5,4 pt, da própria fonte) no exame e nas PENDÊNCIAS; o PDF não usa mais fonte reserva e a linha não
  quebra nas duas máquinas. Teste novo `GlifosDaFonte` (em `test_ficha_exame.py`) reprova qualquer caractere da
  ficha que a fonte do corpo não tenha. A folga extra nas linhas não foi preciso. Se o CI continuar vermelho depois
  de subir, a causa é outra (LibreOffice 26.2 em si) e volta a ser suspeita.
- [ ] Imprimir 1 folha na impressora do plantão e olhar os cinzas (`PAPEL_CINZA_FAIXA` D0D0D0, `_SUB` E0E0E0,
  `_ZEBRA` EFEFEF em `gerador/estilo.py`). Se a zebra sumir no papel, escurecer ali.
- [ ] Conferir num plantão real cheio: com o exame, a faixa de baixo ficou ~1 cm mais alta. No teste com um leito
  fictício pesado, o exame compacto manteve a mesma fonte do modelo antigo (9,5 pt), mas é um caso só.
- [ ] Design system "Plantão ao Vivo" (artefato do claude.ai, fora do repo): acrescentar `papel-cinza-faixa`,
  `papel-cinza-sub`, `papel-cinza-zebra` e `papel-folha` (borda); trocar `GradeControles` por `ExameFisico`; tirar
  `papel-faixa-controles`, `papel-faixa-intercorrencias`, `papel-grade-rotulo` e `papel-grade-celula`, que saíram de
  `gerador/estilo.py`.

## 7. Limites conhecidos (não são erro)

- O JSON da página `extracao-web` não monta o bloco `ficha`: quem monta é o Claude no chat, a partir de
  `prescricao_lida`.
- O teste da página precisa de node e playwright e é pulado no CI.
