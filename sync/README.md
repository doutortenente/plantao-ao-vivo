# sync — pasta do plantão sincronizada com o OneDrive (rclone, Tijolão)

Pedido de 22/11/2026: o material que o Dr. sobe no OneDrive chega ao Tijolão, e a entrega volta para o OneDrive, sem
ele fazer nada. A pasta do plantão no OneDrive é sempre uma subpasta de `000_PLANTÂO_AO_VIVO/`.

## Quando roda

Só quando o Claude chama, no Tijolão (Desktop Commander):

```bash
python3 ~/.local/bin/plantao_sync.py -v
```

- no começo do plantão, antes de ler o material: desce e gera as páginas;
- depois de pôr a entrega em `<plantão>/outputs/`: sobe.

**Sem timer.** Ele não quer nada rodando a cada 2 minutos: o timer do systemd instalado na manhã de 22/11/2026 saiu
no mesmo dia, a pedido dele.

## O que cada rodada faz

1. **Arquiva**: `000_PLANTÂO_AO_VIVO/` fica só com o plantão vigente (a pasta com a data mais recente no começo do
   nome, `DD-MM-AA-…`). As anteriores vão para `Plantao-ao-vivo-historico/` quando já estão 12 h sem mexida. É um
   move dentro do OneDrive: nada é apagado. Pasta sem data no começo do nome não é tocada.
2. **Desce**: `000_PLANTÂO_AO_VIVO/<plantão>/` → `~/Downloads/DOCS-E-RASCUNHOS-PLANTOES/<plantão>/`. Cópia, nunca
   espelho: o que sumir da nuvem não some do PC. `--update`: arquivo mais novo no PC não é sobrescrito.
3. **Páginas**: PDF escaneado (sem camada de texto) ganha as páginas em JPEG em `<plantão>/paginas-jpg/` (controles
   em cor, 200 dpi; o resto em cinza, 180 dpi). É por elas que o Claude lê o material: o PDF de 20 MB não passa pela
   ponte de arquivos (timeout em 22/11/2026).
4. **Sobe**: `<plantão>/outputs/` do PC → a mesma pasta no OneDrive, esteja ela no vigente ou no histórico. Pasta que
   não existe em nenhum dos dois não é criada. `paginas-jpg/` não sobe.

Log: `~/.local/state/plantao-sync.log`. Duas rodadas nunca se sobrepõem (trava em `$XDG_RUNTIME_DIR`, ou `/tmp`).

## Instalar (no Tijolão)

```bash
install -m 755 sync/plantao_sync.py ~/.local/bin/plantao_sync.py
```

Conferir: `python3 ~/.local/bin/plantao_sync.py --dry-run -v` mostra o que faria; `tail ~/.local/state/plantao-sync.log`
mostra o que fez.

## Configuração

Variáveis de ambiente, com os padrões entre parênteses: `RCLONE` (`~/.local/bin/rclone`), `PLANTAO_REMOTO`
(`onedrive:000_PLANTÂO_AO_VIVO`), `PLANTAO_HISTORICO` (`onedrive:Plantao-ao-vivo-historico`), `PLANTAO_LOCAL`
(`~/Downloads/DOCS-E-RASCUNHOS-PLANTOES`), `PLANTAO_LOG`.

Substitui a etapa 2 do `docs/PLANO-N8N.md` (`rclone rcd` + n8n): o mesmo trabalho, sem servidor e sem timer.
