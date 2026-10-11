# Decisões e correções

## Decisões do operador (o que vale)

| Data | Decisão |
|---|---|
| 27/09/2026 | Doc do plantão só com sinais vitais, laboratório e prescrição; alertas no chat, uma vez só. |
| 10/10/2026 | Ficha-cola tem de trazer TODOS os sinais vitais e o balanço, não versão resumida. |
| 10/10/2026 | Ficha-cola = 1 folha por leito (paisagem); evolução pode ter mais de uma página. |
| 11/10/2026 | Sinais vitais em 24 h, não só o turno noturno. |
| 11/10/2026 | Evolução só com o que importa (7 blocos); sem repetir identificação, história, dispositivos, exames antigos. |
| 11/10/2026 | Times New Roman 10, negrito mantido, visual limpo. |
| 11/10/2026 | Repositório próprio `plantao-ao-vivo`, independente, sem symlinks. |

## Correções feitas ao montar este repositório (11/10/2026)

Origem: `doutortenente/claude-workspace`. O que estava desatualizado ou errado e como ficou aqui:

1. **Symlinks.** `EXTRACAO-CLINICA-SASI/` era feita de 7 symlinks para `skills-que-prestam/`. Aqui tudo é arquivo real.
2. **Balanço pelo rodapé × pelas células.** A skill `controles-vitais-janela` dizia "rodapés = verdade"; o BRIEFING
   dizia "some as células, nunca o total escrito". Vale o BRIEFING. Corrigidos a skill, o `exemplo-resolvido.md`, a
   skill `plantao` e a página `extracao-web` (diurese). Caso real que mostrou o erro: L10 de 11/10/2026, UF diurno
   920 ml pelas células, 960 ml no rodapé.
3. **Separador do Máx - Mín.** Skill e motor usavam "–"; BRIEFING e exemplo usam " - ". Padronizado " - ".
4. **Sup O2.** Skill: "na linha do SpO2 com ` | `". BRIEFING: AA/cateter entre parênteses; VM em linha própria.
   Vale o BRIEFING (skill, exemplo, motor e página corrigidos).
5. **`(revisar)` dentro do bloco.** Skill e templates mandavam marcar no valor; o BRIEFING proíbe explicação no bloco.
   Agora vai para o rodapé "Conferir".
6. **Janela.** BRIEFING dizia `[12 h / 6 h]`; vale 24 h.
7. **Módulo C da skill de controles** (sequência de 21/06/26) não tinha Laboratório e usava títulos diferentes do
   BRIEFING. Substituído pela sequência do BRIEFING.
8. **Motor `build_passagem.py`:**
   - classificava "evacuação" como GANHO (o radical "ev" casava por substring) — corrigido (radical curto só casa
     palavra inteira; vence o radical mais longo);
   - não conhecia UF/ultrafiltração nem diálise — acrescentado como perda;
   - punha divergência com a enfermagem DENTRO do bloco — agora vai para os avisos;
   - não tinha seção Laboratório e usava títulos fora do BRIEFING — alinhado;
   - Dx agora em ordem decrescente separado por " / ", aceita "< 20".
   - Flags acrescentadas: Dx < 70 e TAX > 37,8 (ver BRIEFING §2).
9. **Workflow `plantao.yml`** passava TODOS os segredos do repositório ao job (`toJSON(secrets)`). Agora passa só
   `AIRTABLE_TOKEN`. Caminhos dos workflows ajustados para este repo.
10. **Skill `plantao`** entregava `.md` no OneDrive via rclone; a entrega hoje é Word. Reescrita.
11. **Skill `admissao-uti`** apontava para caminhos do PC (`~/src/...`) que não existem neste repo — apontada para
    o template daqui.
12. **`doc-plantao-formato.md`** (Google Doc, Arial, caixa cinza) substituído por `docs/formato-entrega.md`.

## Pendente (não resolvido aqui)

- A página `extracao-web` ainda lê ingesta e BH pelos rodapés (o modelo não devolve as células de ganho) e o
  artefato publicado em 02/10/2026 roda a versão antiga até ser republicado.
- A esteira Airtable → Actions está no "teste 2" (só baixa anexos); não lê scan nem monta bloco.
