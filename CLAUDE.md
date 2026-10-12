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
  Nada de layout "inventado".
- **Zero alucinação**: ilegível vira `?` e vai para o rodapé; dose só com fonte legível; separar medido de inferido.
- **Nada de `(revisar)` dentro do bloco colável.**
- **Conta é do motor** (`skills/sasi-ingest-export/scripts/build_passagem.py`), nunca do LLM.
- Rodar em sequência na sessão, sem subagentes. O médico não roda comando: o Claude executa.
- Antes de mexer em algo irreversível (apagar, sobrescrever, publicar em nome dele), mostrar o plano e esperar
  "prosseguir".

## Entrega

1. Gerar: `python3 gerador/gerar_docx.py <plantao.json> --saida saida/`.
2. Converter para PDF e olhar as páginas (ficha-cola: nº de folhas = nº de leitos).
3. Mandar os dois `.docx`. No chat: alertas críticos uma vez só, rodapé "Conferir", bloco final de conduta com
   metas numéricas.

## Git

Commit direto na `main`. Mensagem `tipo(escopo): o que mudou`. Nunca versionar JSON de plantão real nem os Word
gerados (`.gitignore`).
