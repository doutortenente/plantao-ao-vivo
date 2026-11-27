# CLAUDE.md — plantao-ao-vivo

## Posição do Claude (decisão dele, 12-nov-2026, definitiva)
O Claude **não é** e nunca mais será a IA principal dele. É **sub-sub-agente do Hermes, do Grok e do Gemini**.

Instruções para o Claude quando o Dr. Nicolas manda o material do plantão ("novo plantão", "manda bala").

## Ordem de leitura

1. `docs/BRIEFING.md` — formato do texto clínico (fonte única).
2. `docs/formato-entrega.md` — como ficam os dois Word.
3. `skills/plantao/SKILL.md` — passo a passo.
4. `skills/controles-vitais-janela/SKILL.md` — como ler a folha de controle.

Admissão de leito novo: só `skills/admissao-uti/SKILL.md` (não a `sasi-ingest-export`).

## Regras que já custaram caro (não repetir)

- **Janela 24 h** (07 h do dia anterior até 05 h) é o padrão, inclusive na evolução diurna. Só recortar turno se ele
  pedir. Em 11/10/2026 a primeira entrega veio só com a noite e foi rejeitada.
- **Evolução = só o que muda**: vitais + balanço, laboratório, exame físico (copiado da anterior), eventos 24 h,
  impressão, plano. Sem identificação, HPMA, antecedentes, dispositivos, exames antigos nem "Terapias vigentes" (a
  ficha-cola já traz a prescrição; 21/11/2026). Concisão de oficial: Eventos = só fatos que não estão nos vitais e no
  laboratório; a leitura do caso vai na Impressão; Plano = ordens curtas, sem justificativa e sem "Mantenho cuidados
  intensivos".
- **Balanço = soma das células.** Rodapé da folha só confere; divergência no rodapé "Conferir".
- **Ficha-cola**: modelo aprovado em 12/10/2026, `gerador/ficha_cola.py` (bloco `ficha` no JSON). 1 folha
  paisagem por leito — conferir TODAS as páginas do PDF; mandar .docx + .pdf. Cabeçalho **HD:** (hipóteses no JSON
  `leito.hd`; override opcional `ficha.hd`); **não** usar `diagnostico` nem `ficha.dx` (`validar.py` recusa). Na grade,
  **Dx** = glicemia (`vitais.Dx`), não confundir com HD. Idade/Sexo legíveis; Peso/Altura sem fonte/data; balanço da
  ficha sem Ganhos. Prescrição em 2 blocos (infusões/terapias + por sistemas); profilaxia só TEV/LAMG; texto curto.
  Embaixo, EXAME FÍSICO em 6 quadros por sistema no lugar de CONTROLES DO PLANTÃO, sem faixa de bundle (07/11/2026).
- **Prescrição da ficha = TODA a prescrição** (22/11/2026): cada item que o paciente está recebendo, um por linha,
  por sistema, inclusive pele, tópicos e sintomáticos. Faltar item é erro grave (no plantão de 21/11 faltaram vários).
  Nada de juntar drogas na mesma linha (a mesma droga em duas doses pode ficar numa linha só).
- **ACM = "a critério médico" = a princípio suspenso** (21/11/2026): bloco ACM próprio, que a ficha imprime na coluna 3
  ("ACM · a princípio suspenso"); não conta como droga em uso (Clexane prescrito + Xarelto ACM não são 2
  anticoagulantes). O motor só o usa para alergia.
- **PROFILAXIA = TEV + LAMG** (21/11/2026): o pantoprazol vai em PROFILAXIA, não em TGI. O gerador move sozinho IBP e
  anti-H2 escritos em outro sistema.
- **Laboratório da ficha = série de 72 h** (22/11/2026): `python3 gerador/labs_72h.py <pasta dos labs>` monta o bloco
  `ficha.lab` (eletrólitos também em série). Na evolução continua UR/CR seriais e eletrólitos só com o atual.
- **Pendências da ficha saem das evoluções anteriores dele**: ler a evolução (o plano e as condutas) e interpretar; as
  condutas que ele ditar no plantão entram nas pendências e na prescrição da ficha.
- **Arquivo refeito tem nome novo**: sufixo `-v2`, `-v3` (nunca o mesmo nome por cima).
- **Fonte**: Times New Roman 10 em tudo; destaque só por negrito (rótulos, flags, alertas). Sem vermelho, sem cor.
  Nada de layout "inventado". Exceções aprovadas em 19/10/2026, só na ficha-cola: nome 13, nº do leito 20, rótulo
  LEITO 8, rótulos e flags um ponto abaixo do corpo (9), e o "– " das linhas de EXAMES. Opção A (07/11/2026), só na
  ficha-cola: fundo cinza (faixa nos títulos, linha sim/linha não, rótulo da prescrição) e caixa na alergia e nos
  alertas; o texto continua preto.
- **Dias**: ATB conta do D0 (dia de início = D0: escreva `(I: dd/mm)` e o motor escreve o D). UTI conta do D1 (dia
  da admissão = D1: campo `admissao_uti`). D escrito à mão que diverge é corrigido e vira aviso.
- **Zero alucinação**: ilegível vira `?` e vai para o rodapé; dose só com fonte legível; separar medido de inferido.
- **Nada de `(revisar)` dentro do bloco colável.**
- **Conta é do motor** (`skills/sasi-ingest-export/scripts/build_passagem.py`), nunca do LLM.
- Rodar em sequência na sessão, sem subagentes. O médico não roda comando: o Claude executa.
- Antes de mexer em algo irreversível (apagar, sobrescrever, publicar em nome dele), mostrar o plano e esperar
  "prosseguir".

## Material e saída pelo OneDrive (22/11/2026)

- Ele sobe o material em `onedrive:000_PLANTÂO_AO_VIVO/<plantão>/` (às vezes com subpasta do turno seguinte, como
  `22-11-26-uti2-diurno-inputs/`). Antes de ler, rodar no Tijolão (Desktop Commander)
  `python3 ~/.local/bin/plantao_sync.py -v`: desce tudo para `~/Downloads/DOCS-E-RASCUNHOS-PLANTOES/<plantão>/` e gera
  as páginas dos PDFs escaneados em JPEG (`<plantão>/paginas-jpg/`). Ler as páginas pelo `read_multiple_files` do
  Desktop Commander, 4 por chamada: o PDF de 20 MB não passa inteiro pela ponte de arquivos (deu timeout em
  22/11/2026). Detalhes: `sync/README.md`.
- A entrega vai para `<plantão>/outputs/` no Tijolão (além do chat); rodar o `plantao_sync.py` de novo para subir para
  o OneDrive.
- **Sem timer** (22/11/2026): nada roda sozinho a cada 2 min; o sync só roda quando o Claude chama.
- No OneDrive, `000_PLANTÂO_AO_VIVO/` fica só com o plantão vigente: a cada rodada do sync, os anteriores com 12 h sem
  mexida vão para `Plantao-ao-vivo-historico/`.

## Entrega

0. Arrumar a pasta de entrada (inventário, recortes, labs em texto, evolução anterior):
   `python3 gerador/preparar.py entrada/ --saida saida/preparo`.
1. Gerar: `python3 gerador/gerar_docx.py <plantao.json> --saida saida/`. Na ordem:
   - motor.preparar calcula os dias de ATB e de UTI;
   - validar.py: erro = não gera;
   - saem a evolução e a ficha-cola, ajustada a 1 folha por leito;
   - conferir.py checa fonte, tamanho, cor, texto proibido e 1 folha por leito, e faz os PNG em `saida/paginas/`;
   - `saida/mensagem.md` traz o rascunho do chat; a versão anterior vai para `saida/historico/`.

   Saída ≠ 0 = não entregar.
2. Olhar TODOS os PNG das páginas.
3. Mandar os dois `.docx` (e o `.pdf` da ficha). No chat, partir do `mensagem.md`: alertas críticos uma vez só (os
   `ALERTA:` de segurança no topo), rodapé "Conferir", bloco final de conduta com metas numéricas. O `mensagem.md`
   só deixa de repetir alerta já dado no MESMO plantão e numa rodada entregue; plantão novo traz todos de novo.

Admissão: `python3 gerador/gerar_admissao.py nota.txt saida/`. Sai em A4, margens 1,25 / 1,34 / 2,5 cm, com o nome
`DD-MM-AA-utiN-admissao-leitoLL.docx`.

## Git

Mudança de código entra por branch + PR com CI; o merge na `main` só com o "prosseguir" dele (decisão de
19/10/2026). Mensagem `tipo(escopo): o que mudou`. Nunca versionar JSON de plantão real nem os Word gerados
(`.gitignore`). O que ficou em aberto entre sessões está em `docs/PENDENTE.md`: ler antes de continuar.
