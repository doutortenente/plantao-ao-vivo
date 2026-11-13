# Pendente

O que ficou em aberto entre sessões. Quem continuar o trabalho lê isto primeiro e risca o que fechar.

Estado em 11/11/2026: contrato JSON `hd` (fim de `diagnostico` / `ficha.dx`) na `main` — PR [#14](https://github.com/doutortenente/plantao-ao-vivo/pull/14).

Estado em 21/10/2026: o PR [#2](https://github.com/doutortenente/plantao-ao-vivo/pull/2) entrou na `main`
(commit `4db762b`). As etapas 1 a 20 do plano de 19/10 estão feitas, e as lentes de segurança e de esteira da
revisão final estão corrigidas, com teste. O projeto do claude.ai já lê esta versão.

## 1. ~~Merge na `main`~~

~~Só com o "prosseguir" do Dr. Nicolas (decisão de 19/10/2026).~~ Feito em 21/10/2026, com o "prosseguir" dele e o
CI verde. Os achados da seção 2 ficam para um PR seguinte.

## 2. Achados da revisão final ainda não conferidos (lente do gerador)

A revisão parou por falta de cota antes da etapa de verificação. Por isso cada item abaixo é uma suspeita: primeiro
reproduzir, depois corrigir e escrever o teste. Os dois de severidade alta já foram corrigidos (alerta de rodada não
entregue, seta "->" lida como ">" no laboratório anterior).

- [ ] `labs.py` ~163, média: quando o resultado é texto ("hemolisado", "pendente", "não reagente"), o primeiro
  número depois do nome pode ser o da faixa de referência, e ele vira o resultado sem aviso.
- [ ] `labs.py` ~131, média: decimal com ponto ("1.7") pode ser truncado em 1, sem aviso.
- [ ] `labs.py` ~200, baixa: `montar()` cola a unidade fixa sem olhar a do laudo, e o fator pode sair errado (10× ou
  1000×).
- [ ] `preparar.py` ~173, média: `with_suffix(".txt")` corta o nome no último ponto. Dois laudos de nome parecido
  podem cair no mesmo `.txt`, e o laudo de um leito acaba apontando para o texto de outro.
- [ ] `preparar.py` ~187, média: cada evolução anterior grava por cima do mesmo `evolucao_anterior.json`, e só
  sobra a última.
- [ ] `preparar.py` ~167, média: a folha de controle é recortada com o tamanho da página 1, sem a rotação. Uma
  página girada ou em paisagem perde parte da largura nos recortes de 300 dpi.
- [ ] `ficha_cola.py` ~198, média: `ficha.janela_controles` e `ficha.janela_balanco` passam por cima da janela que
  o motor conferiu. A ficha pode sair "24 h" quando o motor rebaixou para "19 - 05 h".
- [ ] `evolucao_anterior.py` ~52, baixa: o `.txt` é lido só como UTF-8. Um arquivo salvo em Windows-1252 derruba o
  `preparar.py`.
- [ ] `gerar_admissao.py` ~121, baixa: a admissão grava por cima de um arquivo com o mesmo nome, sem guardar a versão
  anterior em `historico/`.

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

## 8. Exames pelo n8n (12/11/2026, branch `feat/exames-n8n`)

Feito: o fluxo "Exames - Banco de Resultados" (detalhes em `n8n/exames/README.md`).
- Está publicado e só aceita chamada do próprio PC; de fora, devolve 403.
- Guarda tudo nas tabelas do n8n e lê só laudo novo.
- O Hermes chama pela skill `skills/exames-lab/SKILL.md`.
- O leitor foi calibrado em 227 laudos reais. O plano do resto está em `docs/PLANO-N8N.md`.

- [ ] Ligar o fluxo no passo a passo do plantão (`skills/plantao`):
  - o Hermes chama o fluxo com os leitos do JSON e cola as linhas de `laboratorio`;
  - o `labs.py` continua para o PDF que chegar em `entrada/`, e os itens dele na seção 2 continuam valendo.
- [ ] Antibiograma por disco-difusão: a tabela S/I/R vem em colunas, e o texto do PDF perde a coluna. Hoje sai
  "ler no PDF". Para ler sozinho seria preciso usar a posição de cada palavra na página.
- [ ] Há pedidos de semanas atrás ainda marcados como pendentes no site: perguntar a ele se o site marca exame
  cancelado como pendente. Hoje, pendência com mais de 7 dias vira só contagem nos avisos.
- [ ] `desde` = admissão na UTI (`admissao_uti`). Exame do PS de antes da UTI fica de fora, a menos que o pedido mande
  um `desde` mais cedo.
- [ ] Apagar, com o OK dele (são dados de paciente):
  - as execuções de teste do fluxo no n8n (17 a 25);
  - os PDFs e textos de teste na pasta temporária da sessão.
