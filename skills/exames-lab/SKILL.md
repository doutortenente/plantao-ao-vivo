---
name: exames-lab
description: Labs da internação (Banco de Resultados) via n8n
---

# Exames da internação

O fluxo n8n "Exames - Banco de Resultados" busca o paciente pelo nome no resultados.com.br e devolve todos os exames
desde a admissão, cada valor com a data da coleta.

```bash
curl -s -X POST http://127.0.0.1:5678/webhook/exames-lab -H 'Content-Type: application/json' \
  -d '{"pacientes":[{"leito":"08","nome":"NOME COMPLETO","desde":"2026-10-24"}]}'
```

| Pedido | O que é |
|---|---|
| `nome` | nome completo, como no laudo |
| `desde` | admissão (`admissao_uti` do JSON do plantão) |
| `referencia` | opcional: data e hora de referência (padrão: agora) |
| `forcar` | opcional: `true` relê todos os laudos |

| Resposta, por paciente | O que é |
|---|---|
| `laboratorio` | linhas da seção "Laboratório:" do `docs/BRIEFING.md` |
| `coletas` | data e hora da coleta de cada valor dessas linhas |
| `exames` | série completa de cada exame, com a data da coleta |
| `culturas`, `pendentes`, `avisos` | culturas, exames sem resultado e o que conferir |

Código e detalhes: `n8n/exames/`.
