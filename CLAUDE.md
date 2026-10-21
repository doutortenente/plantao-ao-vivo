# CLAUDE.md — plantao-ao-vivo

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
- **Evolução = só o que muda**: vitais + balanço, laboratório, terapias, exame físico (copiado da anterior), eventos
  24 h, impressão, plano. Sem identificação, HPMA, antecedentes, dispositivos ou exames antigos.
- **Balanço = soma das células.** Rodapé da folha só confere; divergência no rodapé "Conferir".
- **Ficha-cola**: modelo aprovado em 12/10/2026, `gerador/ficha_cola.py` (bloco `ficha` no JSON). 1 folha
  paisagem por leito — conferir TODAS as páginas do PDF; mandar .docx + .pdf. Dx no cabeçalho; prescrição em 2 blocos
  (infusões/terapias + por sistemas); profilaxia só TEV/LAMG; texto curto, sem encheção.
- **Fonte**: Times New Roman 10 em tudo; destaque só por negrito (rótulos, flags, alertas). Sem vermelho, sem cor.
  Nada de layout "inventado". Exceções aprovadas em 19/10/2026, só na ficha-cola: nome 13, nº do leito 20, rótulo
  LEITO 8, rótulos e flags um ponto abaixo do corpo (9), e o "– " das linhas de EXAMES.
- **Dias**: ATB conta do D0 (dia de início = D0: escreva `(I: dd/mm)` e o motor escreve o D). UTI conta do D1 (dia
  da admissão = D1: campo `admissao_uti`). D escrito à mão que diverge é corrigido e vira aviso.
- **Zero alucinação**: ilegível vira `?` e vai para o rodapé; dose só com fonte legível; separar medido de inferido.
- **Nada de `(revisar)` dentro do bloco colável.**
- **Conta é do motor** (`skills/sasi-ingest-export/scripts/build_passagem.py`), nunca do LLM.
- Rodar em sequência na sessão, sem subagentes. O médico não roda comando: o Claude executa.
- Antes de mexer em algo irreversível (apagar, sobrescrever, publicar em nome dele), mostrar o plano e esperar
  "prosseguir".

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
