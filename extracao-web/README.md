# Extração do plantão: controles, labs e prescrição

## O que é

Uma página web de um arquivo só (`extracao-controles-labs-prescricao.html`). Ela lê os PDFs ou fotos escaneados do plantão e devolve, por leito, o bloco "controles-labs-prescrição" pronto para colar e o JSON do plantão para o motor. Roda dentro do Claude, publicada como artefato. Link (publicado em 02/10/2026, republicado em 19/10/2026): https://claude.ai/artifact/BzQ4t9onXKaWn9EGtGxYCy

## Para que serve

Tirar do chat o trabalho de ler as folhas. Em vez de mandar os PDFs numa conversa e esperar o bloco de volta, você abre a página, escolhe os arquivos e toca em Extrair.

Entra: folha de controles (sinais vitais), balanço hídrico, prescrição e labs anotados à mão, em PDF ou foto (JPG, PNG, WEBP). Pode misturar tudo.

Sai, por leito:

1. Sinais vitais + balanço, no modelo da skill `controles-vitais-janela`.
2. Laboratório, com séries separadas por ` -> `.
3. Prescrição do dia, em 7 blocos (modo D da skill `sasi-ingest-export`).
4. Flags críticos e pendências, fora do bloco.
5. Conduta final isolada, com metas numéricas.
6. O JSON do plantão (botão "Copiar JSON do plantão"), no formato do `gerador/schema-plantao.md`.

## Como usar

1. Abrir o link do artefato dentro do Claude.
2. Escolher os arquivos do plantão.
3. Escolher a janela dos sinais vitais: 24 h, 12 h diurno ou 12 h noturno.
4. Escolher a leitura: Precisão máxima ou Padrão (mais rápida).
5. Tocar em Extrair.
6. Conferir os blocos. Eles são editáveis: corrija qualquer `?` antes de copiar.
7. Copiar o leito ou todos os leitos.
8. Para a evolução e a ficha-cola: copiar o JSON do plantão e colar no chat do projeto.

## Como funciona

1. O PDF.js abre o PDF no navegador e cada página vira imagem.
2. A plataforma reduz cada imagem enviada a cerca de 1,2 megapixel. Para não perder o manuscrito, cada página é cortada em 4 partes com pequena sobreposição. Se o limite da conta permitir 5 imagens, vai também uma visão geral da página.
3. O Claude lê as imagens e devolve os dados transcritos em JSON. Não calcula nada.
4. A página faz as contas: Máx - Mín, contagem dos flags, e ingesta, diurese e BH pela soma das células. O rodapé da folha só confere. A página junta as páginas do mesmo leito e monta o texto.

## Regras que a página segue

- Ilegível vira `?`. Dado ausente é omitido. Nada é estimado.
- Dúvida vai para as pendências, nunca para o bloco. Valor fora do plausível fica como escrito, e a conferência vai
  para as pendências. Leitura incerta da prescrição também.
- Sinal vital sempre em Máx - Mín, inclusive SpO2. O colchete de flag só aparece quando a contagem é maior que 0.
- Limiares dos flags (os mesmos do motor): PAS < 90, PAD < 50, PAM < 65, FC > 100, FR > 20, SpO2 < 92,
  TAX < 35,5 e > 37,8, Dx > 180 e < 70.
- Balanço pela coluna impressa da folha, célula por célula. Ingesta é a soma das células de ganho, diurese a soma da
  coluna Diurese, BH são os ganhos menos as perdas. Os rodapés (Ganhos, Perdas, D:, BH:) só conferem: divergência vai
  para as pendências.
- BIC: o rótulo da coluna Endovenoso sai como escrito ("BIC: NORA"). Se for compatível com vasoativa, a confirmação
  vai para as pendências e para os flags.
- Prescrição: doses só como escritas na folha. Droga suspensa à mão vai para "Suspensos à mão".
- Flags críticos (fora do bloco): PAM < 65 em 3 ou mais aferições, PAM ≤ 55 em qualquer ponto, FC > 100 em 3 ou mais com PAM < 65, SpO2 < 92 em 2 ou mais com O2, Dx > 250 em 2 ou mais, BIC compatível com vasoativa. Esses números são adaptação minha da heurística da skill.

## JSON do plantão

O botão "Copiar JSON do plantão" copia o plantão inteiro no formato do `gerador/schema-plantao.md`:

- `meta`: unidade, data (a da prescrição, ou a da folha + 1 dia com aviso), turno, janela e `recorte` quando a janela é
  de 12 h;
- por leito: cabeçalho, vitais por hora, ganhos e perdas por célula, rodapé em `conferencia_enfermagem`, laboratório
  e as pendências em `avisos`;
- `prescricao_lida`: a prescrição lida, pelos 7 blocos. O Claude monta o bloco `ficha` a partir dela.

No chat, o motor (`build_passagem.py`) refaz as contas e é a conta oficial. O JSON sai da leitura, não das edições
feitas no bloco.

## O que precisa para rodar

- Abrir dentro do Claude, pelo link do artefato. O arquivo HTML sozinho, aberto fora do Claude, mostra o aviso "Abra esta página dentro do Claude" e não lê nada.
- Conta que permita enviar imagens por artefato. Se não permitir, a página avisa.
- Cada página lida gasta o limite de uso do Claude de quem estiver usando.

## O que não faz

- Não grava no Supabase nem no Airtable.
- Não gera JSON de ingest do Supabase nem nota de evolução. A evolução e a ficha-cola saem no chat, a partir do JSON do
  plantão.
- Não calcula oligúria por mL/kg/h, porque a folha não traz peso.
- Não lê ECG nem imagem.

## Estado de teste

Testado em 02/10/2026 só com um PDF de teste e um Claude simulado. Isso validou o fluxo, a montagem dos blocos, os flags e a troca de janela. A leitura de folhas reais manuscritas ainda não foi testada.

Desde 19/10/2026, `tests/test_pagina.py` abre a página num Chromium sem tela e injeta leituras simuladas. O teste
confere que o bloco da página e o motor, rodando sobre o JSON que a página exporta, dão as mesmas linhas, nas janelas
de 24 h e de 12 h noturno. O teste precisa de node e playwright; sem eles, é pulado.

## Correções de 11/10/2026

- Diurese de 24 h agora é a soma das células da coluna Diurese; o `D:` escrito à mão só confere e a divergência vai
  para as pendências (BRIEFING §4).
- Sup O2: ar ambiente/cateter entre parênteses no fim do SpO2; ventilação mecânica em linha própria depois do Dx.
- Título do bloco: "Sinais vitais + balanço <janela>"; Dx separado por " / ".

## Correções de 19/10/2026

- O modelo devolve as células de ganho por coluna, e ingesta e BH saem da soma das células. Os rodapés só conferem.
- Flags novos, iguais aos do motor: Dx < 70 (hipoglicemia) e TAX > 37,8 (febre).
- Nenhuma marca de dúvida dentro do bloco ("revisar", "confirmar", ⚠): tudo vai para as pendências.
- Botão "Copiar JSON do plantão", para o motor ser a conta oficial.
- Números de volume com ponto de milhar, como o motor ("1.736 ml").

## Fontes das regras (neste repositório)

- `docs/BRIEFING.md` (formato — fonte única)
- `skills/controles-vitais-janela/SKILL.md`
- `skills/controles-vitais-janela/references/exemplo-resolvido.md`
- `skills/controles-vitais-janela/references/mapa-folha.md`
- `skills/sasi-ingest-export/references/07-export-prescricao-ordenada.md` (7 blocos da prescrição)
