#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plantao_sync.py — pasta do plantão sincronizada entre o OneDrive e o Tijolão, pelo rclone (22/11/2026).

Roda quando o Claude chama, no Tijolão: no começo do plantão e depois de pôr a entrega em `outputs/` (sem timer,
22/11/2026). A cada rodada:

1. Arquiva: no OneDrive, `000_PLANTÂO_AO_VIVO/` fica só com o plantão vigente (a pasta com a data mais recente no
   nome, "DD-MM-AA-…"). As mais antigas vão para `Plantao-ao-vivo-historico/` quando ficam 12 h sem mexida (move no
   próprio OneDrive: nada é apagado). Pasta sem data no começo do nome não é tocada.
2. Desce: `000_PLANTÂO_AO_VIVO/<plantão>/` → `~/Downloads/DOCS-E-RASCUNHOS-PLANTOES/<plantão>/`. Cópia, nunca
   espelho (o que sumir da nuvem não some do PC) e `--update` (arquivo mais novo no PC não é sobrescrito).
3. Páginas: PDF escaneado (sem camada de texto) ganha as páginas em JPEG em `<plantão>/paginas-jpg/`, para o Claude
   ler sem subir o PDF inteiro (controles em cor, 200 dpi; o resto em cinza, 180 dpi).
4. Sobe: `<plantão>/outputs/` do PC → a mesma pasta no OneDrive, esteja ela no vigente ou já no histórico (pasta que
   não existe em nenhum dos dois não é criada). `paginas-jpg/` não sobe.

Uso: python3 plantao_sync.py [--dry-run] [-v]
Configuração por ambiente: RCLONE, PLANTAO_REMOTO, PLANTAO_HISTORICO, PLANTAO_LOCAL, PLANTAO_LOG.
"""
import argparse
import fcntl
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

CASA = Path.home()
RCLONE = os.environ.get("RCLONE", str(CASA / ".local" / "bin" / "rclone"))
REMOTO = os.environ.get("PLANTAO_REMOTO", "onedrive:000_PLANTÂO_AO_VIVO")
HISTORICO = os.environ.get("PLANTAO_HISTORICO", "onedrive:Plantao-ao-vivo-historico")
LOCAL = Path(os.environ.get("PLANTAO_LOCAL", str(CASA / "Downloads" / "DOCS-E-RASCUNHOS-PLANTOES")))
LOG = Path(os.environ.get("PLANTAO_LOG", str(CASA / ".local" / "state" / "plantao-sync.log")))
QUIETO_H = 12          # pasta antiga só vai para o histórico depois de 12 h sem mexida
SOBE_DIAS = 3          # só sobem os outputs de pastas locais mexidas nos últimos 3 dias
DATA = re.compile(r"^\s*(\d{2})-(\d{2})-(\d{2})(?!\d)")
SAIDAS, PAGINAS = "outputs", "paginas-jpg"
ERRO = object()        # rclone falhou: na dúvida, a pasta não é arquivada


def data_da_pasta(nome):
    m = DATA.match(nome)
    if not m:
        return None
    try:
        return datetime.strptime("".join(m.groups()), "%d%m%y").date()
    except ValueError:
        return None


def _quando(txt):
    if not txt:
        return None
    try:
        return datetime.fromisoformat(txt.replace("Z", "+00:00"))
    except ValueError:
        return None


def a_arquivar(pastas, mexida, agora, quieto_h=QUIETO_H):
    """Nomes que saem do vigente para o histórico.

    pastas: nomes das pastas em 000_PLANTÂO_AO_VIVO; mexida: {nome: datetime da última mudança dentro dela}.
    Fica a de data mais recente no nome (e as do mesmo dia); as outras, com data e quietas há `quieto_h` h, saem."""
    datadas = [(data_da_pasta(p), p) for p in pastas]
    datadas = [(d, p) for d, p in datadas if d]
    if len(datadas) < 2:
        return []
    mais_nova = max(d for d, _ in datadas)
    sai = []
    for d, p in sorted(datadas):
        if d >= mais_nova:
            continue
        m = mexida.get(p)
        if m is not None and agora - m < timedelta(hours=quieto_h):
            continue
        sai.append(p)
    return sai


def destino_da_saida(nome, vigentes, historico):
    """Onde sobem os outputs da pasta local `nome`: no vigente, no histórico, ou em lugar nenhum (None)."""
    if nome in vigentes:
        return f"{REMOTO}/{nome}/{SAIDAS}"
    if nome in historico:
        return f"{HISTORICO}/{nome}/{SAIDAS}"
    return None


class Sync:
    def __init__(self, seco=False, falante=False):
        self.seco, self.falante = seco, falante

    def log(self, msg):
        linha = f"{datetime.now():%d/%m %H:%M:%S} {'[seco] ' if self.seco else ''}{msg}"
        if self.falante:
            print(linha)
        LOG.parent.mkdir(parents=True, exist_ok=True)
        if LOG.exists() and LOG.stat().st_size > 1_000_000:
            LOG.write_text(LOG.read_text(encoding="utf-8")[-200_000:], encoding="utf-8")
        with LOG.open("a", encoding="utf-8") as f:
            f.write(linha + "\n")

    def rclone(self, *args, ler=False):
        cmd = [RCLONE, *args] + (["--dry-run"] if self.seco and not ler else [])
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            self.log(f"ERRO rclone {' '.join(args[:2])}: {r.stderr.strip()[-300:]}")
        return r

    def pastas(self, remoto):
        r = self.rclone("lsf", "--dirs-only", remoto, ler=True)
        return [x.rstrip("/") for x in r.stdout.splitlines() if x.strip()] if r.returncode == 0 else None

    def ultima_mexida(self, remoto_pasta):
        r = self.rclone("lsjson", "-R", "--files-only", "--no-mimetype", remoto_pasta, ler=True)
        if r.returncode != 0:
            return ERRO
        datas = [_quando(x.get("ModTime")) for x in json.loads(r.stdout or "[]")]
        datas = [d for d in datas if d]
        return max(datas) if datas else None

    def paginas(self, pasta):
        for pdf in sorted(pasta.rglob("*.pdf")):
            if SAIDAS in pdf.parts or PAGINAS in pdf.parts:
                continue
            destino = pasta / PAGINAS
            if any(destino.glob(f"{pdf.stem}-*.jpg")):
                continue
            texto = subprocess.run(["pdftotext", "-l", "1", str(pdf), "-"], capture_output=True, text=True).stdout
            if len(texto.strip()) > 20:  # laudo com texto: o labs.py lê direto
                continue
            if self.seco:
                self.log(f"páginas: {pdf.name}")
                continue
            destino.mkdir(exist_ok=True)
            cor = ["-r", "200"] if "control" in pdf.name.lower() else ["-r", "180", "-gray"]
            r = subprocess.run(["pdftoppm", *cor, "-jpeg", "-jpegopt", "quality=72", str(pdf),
                                str(destino / pdf.stem)], capture_output=True, text=True)
            self.log(f"páginas: {pdf.name} {'ok' if r.returncode == 0 else 'ERRO ' + r.stderr.strip()[-200:]}")

    def rodar(self):
        vigentes = self.pastas(REMOTO)
        if vigentes is None:
            return 1
        historico = self.pastas(HISTORICO) or []
        agora = datetime.now(timezone.utc)

        # 1. arquivar
        candidatas = [p for p in vigentes if data_da_pasta(p)]
        mais_nova = max((data_da_pasta(p) for p in candidatas), default=None)
        mexida, falhou = {}, set()
        for p in candidatas:
            if data_da_pasta(p) != mais_nova:
                m = self.ultima_mexida(f"{REMOTO}/{p}")
                (falhou.add(p) if m is ERRO else mexida.__setitem__(p, m))
        for p in a_arquivar([v for v in vigentes if v not in falhou], mexida, agora):
            if p in historico:
                self.log(f"arquivar: {p} já existe no histórico; fica no vigente")
                continue
            r = self.rclone("moveto", f"{REMOTO}/{p}", f"{HISTORICO}/{p}")
            if r.returncode == 0:
                self.log(f"arquivado: {p} -> {HISTORICO}")
                if not self.seco:
                    vigentes.remove(p); historico.append(p)

        # 2. descer, 3. páginas
        for p in vigentes:
            if not data_da_pasta(p):
                continue
            local = LOCAL / p
            r = self.rclone("copy", f"{REMOTO}/{p}", str(local), "--update", "--exclude", f"{PAGINAS}/**", "-v")
            novos = [l for l in r.stderr.splitlines() if "Copied" in l]
            if novos:
                self.log(f"desceu: {p}: {len(novos)} arquivo(s)")
            if local.exists():
                self.paginas(local)

        # 4. subir os outputs
        limite = datetime.now() - timedelta(days=SOBE_DIAS)
        for saida in sorted(LOCAL.glob(f"*/{SAIDAS}")):
            p = saida.parent.name
            if not saida.is_dir() or datetime.fromtimestamp(saida.stat().st_mtime) < limite and \
                    not any(datetime.fromtimestamp(f.stat().st_mtime) >= limite for f in saida.iterdir()):
                continue
            destino = destino_da_saida(p, vigentes, historico)
            if destino is None:
                continue
            r = self.rclone("copy", str(saida), destino, "--update", "-v")
            subiu = [l for l in r.stderr.splitlines() if "Copied" in l]
            if subiu:
                self.log(f"subiu: {p}/{SAIDAS}: {len(subiu)} arquivo(s)")
        return 0


def main():
    ap = argparse.ArgumentParser(description="Sincroniza a pasta do plantão entre o OneDrive e o Tijolão (rclone)")
    ap.add_argument("--dry-run", action="store_true", help="mostra o que faria, sem mover nem copiar nada")
    ap.add_argument("-v", action="store_true", help="escreve o log também na tela")
    a = ap.parse_args()
    trava = open(Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "plantao-sync.lock", "w")
    try:
        fcntl.flock(trava, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return 0  # a rodada anterior ainda não terminou
    return Sync(seco=a.dry_run, falante=a.v).rodar()


if __name__ == "__main__":
    sys.exit(main())
