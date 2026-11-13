# Exames de laboratório pelo n8n

O fluxo do n8n "Exames - Banco de Resultados" faz o seguinte:

1. entra no Banco de Resultados (resultados.com.br, Instituto de Biomedicina do ABC);
2. busca cada paciente pelo nome completo;
3. lê todos os laudos desde a admissão;
4. devolve cada valor preso à **data da coleta**, nunca à data da liberação.

Quem chama é o Hermes, pela skill `exames-lab`.

## Como funciona

| Etapa | Nó do n8n | O que faz |
|---|---|---|
| Pedido | `Pedido` | Endereço (webhook) `POST /webhook/exames-lab`. Só aceita chamada deste PC (127.0.0.1); de fora, 403. |
| Validação | `Pacientes` | Exige nome completo e data de admissão antes de entrar no site. |
| Login | `Entrar no site`, `Sessao` | Usa a credencial "Banco de Resultados" guardada no n8n (a senha não fica no repositório). |
| Busca | `Buscar por nome`, `Documentos` | Percorre todas as páginas. Fica só com laudo de **nome exato** (homônimo fica de fora) e **coleta ≥ admissão**. A janela de datas do site filtra pela inclusão, não pela coleta, por isso a data é conferida depois. |
| Só o novo | `Laudos já lidos`, `A baixar` | Baixa só o laudo que não está no banco, que foi reincluído ou que mudou de pendente. |
| Leitura | `Laudo PDF` … `Ler laudo` | Baixa o PDF, extrai o texto e roda o `ler_laudo.js`. |
| Banco | `Gravar valores`, `Gravar laudos` | Tabelas do n8n `exames_valores` (um valor por linha) e `exames_laudos` (um laudo por linha). |
| Resposta | `Valores da internação`, `Montar resposta` | Monta a resposta com o `montar_resposta.js`. |

**Banco de dados.** São tabelas internas do n8n ("Data table"), gravadas no próprio PC, em
`~/.local/state/n8n/database.sqlite`, sem credencial nova. Supabase (projeto antigo do SASI) e MongoDB (acesso por IA
desligado e sem credencial no n8n) ficaram de fora.

## Leitor (`ler_laudo.js`)

- **Bloco:** as linhas até "Data da Coleta: dd/mm/aaaa hh:mm:ss Resultado liberado em: …". Cada valor herda a coleta do bloco onde está.
- **Formatos aceitos:**
  - valor na linha do nome (bioquímica);
  - "rótulo : valor" em linhas soltas (gasometria, coagulação, painel cardíaco, culturas);
  - hemograma em tabela, com o diferencial em % e em valor absoluto;
  - antibiograma com droga e "CIM S/I/R".
- **Siglas do BRIEFING:**
  - HB, HT, PLAQ, LEUCO, SEG e BAST;
  - UR, CR, NA, K, MG, CAI e P;
  - pH, pCO2, pO2, HCO3, BE (= BE-ecf), SatO2 e Lactato;
  - PCR, Troponina, D-dímero e INR.

  O resto entra com o nome do laudo. A sigla depende do bloco: o "Leucócitos" e o "pH" do exame de urina não viram LEUCO nem pH.
- **Números:** "10.300" vira 10300; "9,30" vira 9,3. "1.03" e "13.7" (INR, TP) ficam como decimal com ponto.
- **Proteções:**
  - nome no cabeçalho do PDF diferente do pedido: o laudo é descartado;
  - amostra marcada "MAQUINA" (circuito de diálise) não vira sigla do paciente;
  - coleta sem hora no laudo: usa a hora do pedido do mesmo dia (`dt_doc_real`) e avisa;
  - antibiograma por disco-difusão (tabela em colunas que o texto do PDF perde) sai como "ler no PDF", sem adivinhar.

## Resposta (`montar_resposta.js`)

Para cada paciente, a resposta traz:

- `laboratorio`: linhas da seção "Laboratório:" do `docs/BRIEFING.md`.
  - A série "anterior => atual" vale para HB, HT, PLAQ, LEUCO, UR e CR; os eletrólitos saem só com o atual.
  - "Atual" é só o que foi colhido nas 36 h antes do pedido. Valor mais velho não entra nas linhas e fica em `exames`.
- `coletas`: a data e hora da coleta de cada valor usado nas linhas.
- `culturas`.
- `pendentes`: pedidos dos últimos 7 dias. Os mais velhos viram só uma contagem em `avisos`.
- `avisos`.
- `exames`: a série completa de cada exame da internação.

## Validação com dado real (12/11/2026)

- 227 laudos dos 7 leitos de um plantão real.
- 1ª leitura: 122 s. 2ª chamada: 19 s, sem nenhum download.
- Com a referência no horário daquele plantão, as linhas batem valor por valor com a seção Laboratório conferida à mão
  em 6 dos 7 leitos. As diferenças têm a fonte identificada: um controle avulso mais novo que a evolução, e um valor
  que a evolução tirou da folha do PS em vez do laudo.
- Nenhum valor real fica no repositório.

## Testes

```bash
node --test tests/exames_n8n.test.js
```

O CI roda esse teste por meio de `tests/test_exames_n8n.py`. O laudo do teste é fictício: `tests/fixtures/laudo-n8n-ficticio.txt`.

## Publicar uma mudança no n8n

O código dos nós `Ler laudo` e `Montar resposta` é o conteúdo destes arquivos, mais umas linhas finais que ligam o
código ao n8n. A única diferença aceita é o intervalo de acentos `̀-ͯ`, que o n8n guarda como caractere. Para
mudar o leitor:

1. editar o arquivo e rodar os testes;
2. atualizar o nó pelo MCP do n8n (`update_workflow`) e publicar;
3. chamar uma vez com `"forcar": true` para reler os laudos;
4. exportar o fluxo para `fluxo-exames-banco-de-resultados.json`. A exportação não leva segredo: credencial só por nome.
