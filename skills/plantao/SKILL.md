---
name: plantao
description: >
  ATALHO DE PLANTÃO ("/plantao", "novo plantão", "manda bala" com material do plantão).
  Dr. Nicolas envia evoluções anteriores (docx/txt), folhas de controle (scan PDF),
  prescrições (scan PDF) e laudos de laboratório (PDF). A skill transcreve, passa
  as séries cruas ao motor determinístico, e devolve DOIS Word: a evolução do dia
  (só os blocos que mudam) e a ficha-cola (1 folha paisagem por leito). USE SEMPRE
  que ele mandar esse material no início de um plantão, mesmo sem citar "skill".
  ZERO ALUCINAÇÃO: ilegível = `?` e vai para o rodapé; divergência entre fontes é
  listada, nunca resolvida por palpite.
---

# plantao — evolução + ficha-cola a partir do material do plantão

> Reescrita em 11/10/2026 (repositório `plantao-ao-vivo`). A versão de 18/07/2026 entregava `.md` no OneDrive e
> confiava no rodapé da folha de balanço; as duas coisas mudaram (ver `docs/DECISOES.md`).
> Doutrina de transcrição: `skills/controles-vitais-janela`. Formato do texto: `docs/BRIEFING.md`.
> Formato dos Word: `docs/formato-entrega.md`. Conta: `skills/sasi-ingest-export/scripts/build_passagem.py`.

## Entrada

- Evoluções anteriores (docx ou txt, um leito após o outro).
- Folhas de controle: 2 páginas por leito (sinais vitais + balanço), modelo Beneficência Portuguesa.
- Prescrições do dia (eletrônica impressa + anotação à mão).
- Laudos de laboratório (PDF com texto).

## Passo a passo

1. **Inventário.** Listar leitos pelas evoluções. Conferir que cada leito tem folha de controle, prescrição e lab.
   Leito sem lab do dia → dizer no chat. Número de leito divergente entre folha e prescrição → dizer no chat.
2. **Laboratório.** `pdftotext -layout`; série `anterior -> atual` usando a evolução anterior. Amostra marcada
   "AMOSTRA MAQUINA" é do circuito de diálise, não do paciente.
3. **Folhas de controle.** Rasterizar (`pdftoppm`, 150 dpi visão geral, 250–300 dpi recorte por turno).
   Transcrever as 12 aferições (07 h a 05 h) — **janela 24 h é o padrão**. Balanço: transcrever as CÉLULAS.
4. **Prescrição.** Ler cada página; incorporar o manuscrito (riscado, "suspenso", "modificado"). Doses só como
   escritas. Conferir contra o plano da evolução anterior: o que o plano mandou suspender e continua prescrito vai
   para os alertas.
5. **JSON do plantão.** Montar um arquivo no contrato `gerador/schema-plantao.md`, com:
   vitais (séries), células de balanço, laboratório, terapias, exame físico (copiado da evolução anterior), eventos
   24 h, impressão, plano, até 3 alertas para o chat e o bloco `ficha` de cada leito (obrigatório: Dx, dispositivos,
   alergia, prescrição em infusões/terapias + por sistemas, 3 a 7 pendências tiradas do plano, exames e lab).
6. **Gerar.** `python3 gerador/gerar_docx.py plantao.json --saida saida/` → evolução + ficha-cola (+ PDFs).
   O gerador roda `gerador/conferir.py` no fim: 1 folha por leito, Times New Roman, tamanhos aprovados, sem cor,
   sem `(revisar)`, sem travessão entre números. Saída ≠ 0 = não entregar. Olhar TODOS os PNG de `saida/paginas/`.
7. **Responder no chat.** Os dois arquivos + alertas críticos (uma vez só) + rodapé "Conferir" do motor + bloco
   final de conduta com metas numéricas.

## Regras

- Rodar em sequência na própria sessão; sem subagentes (economia de cota).
- O médico não roda comando: o Claude executa tudo.
- Nada de `(revisar)` dentro do bloco colável. Dúvida → rodapé.
- Exame físico: copiar o da evolução anterior; só tirar o que ficou falso (ex.: droga suspensa).
- Plano: verbo de comando, contingência ("se X → Y"), meta numérica, profilaxias. Raso = refaz.
- Supabase/OneDrive: fora do fluxo padrão. Só se o operador pedir.
