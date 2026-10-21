# -*- coding: utf-8 -*-
"""Conversão para PDF com o LibreOffice, num perfil próprio deste processo.

Duas conversões ao mesmo tempo no mesmo perfil (~/.config/libreoffice) falham ao acaso; com um perfil por processo
elas não se cruzam.
"""
import atexit
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

_PERFIL = Path(tempfile.gettempdir()) / f"plantao-libreoffice-{os.getpid()}"
atexit.register(shutil.rmtree, _PERFIL, True)  # apaga o perfil ao sair


def soffice():
    return shutil.which("soffice") or shutil.which("libreoffice")


def para_pdf(arquivo, pasta=None, timeout=300):
    """Converte para PDF em `pasta` (padrão: a do arquivo) e devolve o caminho do PDF."""
    arquivo = Path(arquivo)
    pasta = Path(pasta or arquivo.parent)
    subprocess.run([soffice(), f"-env:UserInstallation={_PERFIL.as_uri()}", "--headless", "--convert-to", "pdf",
                    "--outdir", str(pasta), str(arquivo)], check=True, capture_output=True, timeout=timeout)
    return pasta / (arquivo.stem + ".pdf")
