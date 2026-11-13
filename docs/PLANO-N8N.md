# Plano: n8n como central do plantão

Objetivo: o plantão sai do jeito que está descrito no `CLAUDE.md` (entrada → preparar → gerar → conferir →
mensagem), mas quem dispara e liga as peças é o n8n. O Hermes executa as etapas que precisam do PC. Os arquivos
ficam sincronizados com o OneDrive.

## Onde cada coisa roda (medido em 12/11/2026)

| Peça | Onde | Por quê |
|---|---|---|
| n8n 2.46.6 (`ultron-n8n`) | Container na rede do PC, 127.0.0.1:5678; público pelo Cloudflare | Sem Python e sem poppler (imagem "Hardened Alpine", sem `apk`). Só faz chamadas HTTP, código JS e o banco interno. |
| Hermes (`hermes-agent`) | Container na rede do PC, com `/home/dr/src` montado | Roda os scripts do repositório. Também não tem poppler. |
| Scripts do plantão (`gerador/*.py`) | PC (Python 3.12, poppler, python-docx) | É onde funcionam hoje. |
| rclone 1.75.1 | PC, `~/.local/bin/rclone`, remoto `onedrive:` já configurado | Sincronização com o OneDrive. |

## Etapas

### 1. Exames de laboratório: feito (12/11/2026)

Fluxo "Exames - Banco de Resultados", tabelas `exames_valores` e `exames_laudos`, skill `skills/exames-lab/SKILL.md`.
Pendências na seção 8 do `docs/PENDENTE.md`.

### 2. Sincronizar `entrada/` e `saida/` com o OneDrive (rclone)

- **Peça:** `rclone rcd`, o modo servidor do rclone, que recebe ordens por HTTP.
  - Roda como serviço do systemd do usuário.
  - Escuta só em `127.0.0.1:5572`, com usuário e senha.
  - O n8n chama `sync/copy`. Ele roda na rede do PC, então alcança o 127.0.0.1.
- **Entrada:** `onedrive:<pasta de entrada>` → `~/src/plantao-ao-vivo/entrada/`. Cópia, nunca espelho, para nada sumir do PC se for apagado na nuvem.
- **Saída:** `~/src/plantao-ao-vivo/saida/` (os `.docx`, o `.pdf` da ficha e o `mensagem.md`) → `onedrive:<pasta de saída>`.
- **Reaproveitar** `~/src/scripts/nuvem/` (`arquivar.py`, `onedrive-index`) para nomes e pastas. Não criar outro esquema.
- **Pronto quando:**
  - um PDF posto na pasta do OneDrive aparece em `entrada/`;
  - o Word gerado aparece no OneDrive;
  - os dois com hora conferida.
- **Falta ele decidir:** as duas pastas do OneDrive.

### 3. Plantão disparado pelo n8n

1. **Gatilho:** arquivo novo na entrada (o n8n consulta o rclone a cada X minutos) ou pedido do Hermes ("novo plantão").
2. **Preparar:** o n8n pede ao Hermes, pela ponte ULTRON já existente no `hermes-stack`, para rodar no PC
   `python3 gerador/preparar.py entrada/ --saida saida/preparo`.
3. **Exames:** o n8n chama o fluxo de exames com os leitos e as admissões. As linhas `laboratorio` e `coletas` voltam
   para o JSON do plantão, e os avisos vão para o "Conferir".
4. **Montar o JSON:** é a única etapa que precisa de modelo, e fica com o Hermes ou com o Claude, como hoje. O motor
   (`build_passagem.py`) faz as contas.
5. **Gerar e conferir:** `gerar_docx.py`, depois `conferir.py`. Se a saída não for 0, não entrega.
6. **Sincronizar** a saída para o OneDrive (etapa 2).

**Pronto quando** um plantão de teste, com JSON fictício, sai de ponta a ponta sem comando digitado.

### 4. Entrega da mensagem

O `mensagem.md` e os arquivos chegam a ele pelo canal que ele escolher. Mandar mensagem em nome dele exige o OK dele
e a escolha do canal (pendente).

### 5. Cuidado e manutenção

- Fluxo de erro (Error Trigger) que avisa quando o fluxo de exames falha. Exemplo: o site mudou o layout e aparece
  "bloco sem valor lido".
- Execução de produção não grava os dados (já ligado no fluxo de exames). As execuções de teste são apagadas depois
  de usadas.
- Toda mudança no leitor passa pelos testes (`tests/exames_n8n.test.js`) antes de ir para o n8n.

## Ordem sugerida

Etapa 2, depois a 3 com JSON fictício, depois a 4. A auditoria do Hermes que ficou parada pode correr em paralelo:
- modelo de delegação não definido;
- `swarm.yaml` com 10 workers contra `workers: []` no `AGENTS.md`;
- MCP de arquivos que duplica as ferramentas nativas;
- restos do SASI nas skills;
- token órfão do Supabase em `mcp-tokens`.
