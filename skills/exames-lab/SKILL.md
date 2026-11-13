---
name: exames-lab
description: Labs da internação (Banco de Resultados) via n8n
---

# Exames de laboratório da internação atual

Fluxo n8n "Exames - Banco de Resultados" (id `KXXBvZ21FYxW72de`). Ele entra no resultados.com.br com a credencial
guardada no n8n, busca cada paciente pelo NOME COMPLETO e lê todos os laudos desde a admissão. Devolve cada valor
preso à DATA DA COLETA, nunca à da liberação.

Os valores ficam guardados nas tabelas do n8n `exames_valores` e `exames_laudos`. No plantão seguinte o fluxo só
baixa laudo novo: na 2ª chamada dos 7 leitos, 19 s e nenhum download (medido em 12/11/2026).

## Chamar (só deste PC; de fora o n8n devolve 403)

```bash
curl -s -X POST http://127.0.0.1:5678/webhook/exames-lab -H 'Content-Type: application/json' \
  -d '{"pacientes":[{"leito":"08","nome":"NOME COMPLETO","desde":"2026-10-24"}]}'
```

- `nome`: o nome completo, igual ao do laudo. O fluxo ignora acento e maiúsculas, mas não aceita nome parcial.
- `desde`: data da admissão (AAAA-MM-DD ou DD/MM/AAAA). No JSON do plantão, é o campo `admissao_uti` de cada leito.
- Opcionais:
  - `referencia` (data e hora ISO): o "atual" é o que foi colhido nas 36 h antes dela. Padrão: agora.
  - `ate` (AAAA-MM-DD).
  - `forcar: true`: relê todos os laudos.
- A primeira leitura de um paciente com internação longa demora de 1 a 2 min. Depois disso, poucos segundos.

## Resposta (por paciente)

- `laboratorio`: linhas prontas da seção "Laboratório:" do `docs/BRIEFING.md` (anterior => atual; eletrólitos só com o atual).
- `coletas`: `{SIGLA: {atual, anterior}}`, a data e hora da coleta de cada valor usado nas linhas. Conferir antes de usar.
- `culturas`, `pendentes` (dos últimos 7 dias) e `avisos`.
- `exames`: a série completa da internação, no formato "valor (dd/mm hh:mm) | ...".

## Regras

- Copiar os valores como vieram, sem arredondar nem completar. Todo aviso da resposta vai para o "Conferir".
- Aviso "antibiograma em colunas: ler S/I/R no PDF": abrir o laudo no site. Nunca deduzir S/I/R.
- Nome com "[máquina]" é amostra do circuito de diálise e não é do paciente.
- Seção vazia com o aviso "nenhuma coleta nas 36 h" quer dizer que não há laboratório novo. Não usar valor velho como atual.
- Código do leitor, README e fluxo exportado: `n8n/exames/`. Testes: `tests/exames_n8n.test.js`.
