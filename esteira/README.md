# Esteira Airtable → GitHub Actions

Uma linha da tabela "Plantão × Leito" (um leito) dispara o workflow `plantao.yml`. O `processar.py`:

1. baixa os anexos;
2. lê os scans com a API do Claude;
3. monta o JSON do leito e gera a ficha-cola (1 folha, conferida);
4. devolve na mesma linha a ficha (.docx + .pdf), o JSON rascunho e o "Conferir".

A evolução (Impressão e Plano) continua no chat do projeto, a partir do JSON rascunho.

Sem a chave da API, a esteira fica como estava: só baixa e confere os anexos, e avisa que a leitura está desligada.

## Arquivos

- `processar.py`: orquestra tudo, conversa com o Airtable e devolve os arquivos. O log do Actions é público: o script
  só imprime contagens e o status.
- `leitura.py`: chama a API (modelo `claude-opus-5-5`, com fallback do servidor) e recebe um JSON preso a um schema.
- `doutrina-leitura.md`: o prompt da leitura (zero alucinação; dúvida vai para as pendências).
- `montar.py`: transforma as leituras no JSON do plantão (`gerador/schema-plantao.md`). Não faz conta nem escreve texto
  novo:
  - o balanço sai pela coluna impressa da folha;
  - as PENDÊNCIAS são só as ordens escritas na prescrição.
- `requirements.txt`: o gerador mais o SDK `anthropic`, com versão fixa.

## Para ligar (uma vez só)

1. **Segredo da API.** No GitHub, abra Settings → Secrets and variables → Actions → New repository secret. Crie
   `ANTHROPIC_API_KEY` com uma chave do console da Anthropic.
2. **Campo de saída no Airtable.** Na tabela "Plantão × Leito", crie um campo do tipo *Attachment* (por exemplo,
   "Ficha gerada") e copie o ID dele (`fld…`). O ID aparece no menu do campo ("Copy field URL") ou na página da API
   da base.
3. **Variável no GitHub.** Ainda em Secrets and variables → Actions, aba *Variables*, crie `AIRTABLE_CAMPO_SAIDA` com
   esse `fld…`.
4. **Automação no Airtable.** Gatilho "quando o Status virar *enviado*". Ação "Run script" com `recordId` como
   variável de entrada:

   ```js
   const { recordId } = input.config();
   const r = await fetch(
     "https://api.github.com/repos/doutortenente/plantao-ao-vivo/actions/workflows/plantao.yml/dispatches",
     { method: "POST",
       headers: { Authorization: "Bearer <TOKEN>", Accept: "application/vnd.github+json" },
       body: JSON.stringify({ ref: "main", inputs: { record_id: recordId } }) });
   if (r.status !== 204) throw new Error("GitHub respondeu " + r.status);
   ```

   `<TOKEN>` é um *fine-grained token* do GitHub. Ele deve valer só para este repositório e ter só a permissão
   *Actions: Read and write*.

5. **Primeiro teste.** Use uma linha com anexos fictícios e confira três coisas:
   - o Status passa por "lendo" e termina em "pronto";
   - o campo de saída recebe três arquivos;
   - o Avisos traz o "Conferir".

   Confira também se um segundo disparo acrescenta arquivos ou substitui os anteriores: a documentação do Airtable não
   diz qual dos dois acontece. Os nomes levam a hora, então a versão mais nova é fácil de achar.

Data e turno: o disparo pode mandar `data` (dd/mm/aaaa) e `turno` (diurno/noturno). Sem eles, a data sai da
prescrição (ou da folha + 1 dia, com aviso) e o turno é diurno.

## O que volta no campo Avisos

- **ERROS:** a ficha não saiu. Os casos são leitura recusada ou cortada, identificação diferente entre os documentos,
  validação e conferência.
- **ALERTAS:** cruzamentos de segurança (alergia × prescrição, TEV, duplicidade, suspenso).
- **CONFERIR:** dúvidas de leitura, células ilegíveis, rodapé que não bate com a soma das células, dias de ATB sem
  início e itens que ficaram fora da ficha.
- **ANEXOS:** o que foi baixado.

Status "pronto" = ficha gerada, conferida e devolvida. "falhou" = olhar ERROS (o JSON rascunho volta mesmo assim,
quando dá para montar).
