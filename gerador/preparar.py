#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
preparar.py — arruma a pasta de entrada do plantão antes de ler (o passo 1-3 da skill plantao, sem conta manual).

Para cada arquivo de <entrada>:
  - classifica (controles, prescrição, labs, evolução) pelo nome e, no PDF, pelo texto da 1ª página;
  - conta páginas (pdfinfo);
  - controles: PNG de cada página a 150 dpi (visão geral) e as metades de cima e de baixo a 300 dpi (recorte para
    ler o manuscrito); as páginas vão em pares (2 por leito: sinais vitais + balanço). Número ímpar = aviso;
  - prescrição: PNG de cada página a 200 dpi;
  - labs: texto com `pdftotext -layout` (entrada do labs.py) e os leitos citados no laudo;
  - evolução anterior (.docx/.txt): leitos, exame físico, plano e labs (evolucao_anterior.py).
Escreve <saida>/manifest.json com o inventário leito × documentos e os avisos (leito sem lab, sem controles…).

Uso: python3 gerador/preparar.py entrada/ --saida saida/preparo
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evolucao_anterior  # noqa: E402

TIPOS = (("evolucao", r"evolu"), ("controles", r"control|sinais|balan"), ("prescricao", r"prescri"),
         ("labs", r"\blab|exame|laudo"))
PISTAS_TEXTO = (("controles", r"PLANEJAMENTO ASSISTENCIAL|GANHOS|PERDAS"), ("prescricao", r"PRESCRI"),
                ("labs", r"(?i)hemoglobina|creatinina|leuc[oó]citos|pot[aá]ssio"))


def _rodar(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=300).stdout


def paginas(pdf):
    out = _rodar(["pdfinfo", str(pdf)])
    n = int(re.search(r"Pages:\s+(\d+)", out).group(1))
    w, h = (float(x) for x in re.search(r"Page size:\s+([\d.]+) x ([\d.]+)", out).groups())
    return n, w, h


def classificar(arq):
    nome = arq.name.lower()
    for tipo, rx in TIPOS:
        if re.search(rx, nome):
            return tipo
    if arq.suffix.lower() == ".pdf" and shutil.which("pdftotext"):
        texto = _rodar(["pdftotext", "-l", "1", "-layout", str(arq), "-"])
        for tipo, rx in PISTAS_TEXTO:
            if re.search(rx, texto):
                return tipo
    if arq.suffix.lower() in (".docx", ".txt"):
        return "evolucao"
    return "outro"


def rasterizar(pdf, pasta, dpi):
    """Todas as páginas em PNG."""
    pasta.mkdir(parents=True, exist_ok=True)
    _rodar(["pdftoppm", "-r", str(dpi), "-png", str(pdf), str(pasta / "pagina")])
    return sorted(pasta.glob("pagina-*.png"))


def folha_de_controle(pdf, pag, pasta, w, h):
    """Página inteira a 150 dpi e metades de cima/baixo a 300 dpi (com 60 px de sobreposição)."""
    pasta.mkdir(parents=True, exist_ok=True)
    base = ["pdftoppm", "-f", str(pag), "-l", str(pag), "-png", "-singlefile"]
    _rodar(base + ["-r", "150", str(pdf), str(pasta / "150dpi")])
    largura, altura = int(w / 72 * 300), int(h / 72 * 300)
    meio = altura // 2
    for nome, y, alt in (("300dpi-cima", 0, meio + 60), ("300dpi-baixo", meio - 60, altura - meio + 60)):
        _rodar(base + ["-r", "300", "-x", "0", "-y", str(y), "-W", str(largura), "-H", str(alt), str(pdf),
                       str(pasta / nome)])
    return sorted(pasta.glob("*.png"))


def preparar(entrada, saida):
    entrada, saida = Path(entrada), Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    manifest = {"arquivos": [], "leitos": {}, "pares_controles": [], "avisos": []}
    avisos = manifest["avisos"]
    tem_poppler = bool(shutil.which("pdfinfo") and shutil.which("pdftoppm") and shutil.which("pdftotext"))
    if not tem_poppler:
        avisos.append("sem poppler-utils (pdfinfo/pdftoppm/pdftotext): PDFs não foram rasterizados nem lidos")

    def leito(n):
        return manifest["leitos"].setdefault(n, {"evolucao": False, "labs": False})

    for arq in sorted(p for p in entrada.iterdir() if p.is_file() and not p.name.startswith(".")):
        tipo = classificar(arq) if tem_poppler or arq.suffix.lower() != ".pdf" else "outro"
        item = {"arquivo": arq.name, "tipo": tipo, "saidas": []}
        destino = saida / tipo / arq.stem
        if arq.suffix.lower() == ".pdf" and tem_poppler:
            n, w, h = paginas(arq)
            item["paginas"] = n
            if tipo == "controles":
                if n % 2:
                    avisos.append(f"{arq.name}: {n} páginas (ímpar) — o par sinais vitais + balanço de algum leito "
                                  "está incompleto")
                for i in range(0, n, 2):
                    manifest["pares_controles"].append({"arquivo": arq.name, "paginas": [i + 1, i + 2][: n - i],
                                                        "leito": "?"})
                for pag in range(1, n + 1):
                    pngs = folha_de_controle(arq, pag, destino / f"p{pag:02d}", w, h)
                    item["saidas"] += [str(p.relative_to(saida)) for p in pngs]
            elif tipo == "prescricao":
                item["saidas"] = [str(p.relative_to(saida)) for p in rasterizar(arq, destino, 200)]
            elif tipo == "labs":
                destino.parent.mkdir(parents=True, exist_ok=True)
                txt = destino.with_suffix(".txt")
                txt.write_text(_rodar(["pdftotext", "-layout", str(arq), "-"]), encoding="utf-8")
                item["saidas"] = [str(txt.relative_to(saida))]
                leitos_lab = sorted({m.zfill(2) for m in re.findall(r"(?i)leito\s*:?\s*(\d{1,3})",
                                                                    txt.read_text(encoding="utf-8"))})
                item["leitos"] = leitos_lab
                for n_l in leitos_lab:
                    leito(n_l)["labs"] = True
        elif tipo == "evolucao" and arq.suffix.lower() in (".docx", ".txt"):
            lidos, av = evolucao_anterior.ler(evolucao_anterior.linhas_do_arquivo(arq))
            avisos += [f"{arq.name}: {a}" for a in av]
            item["leitos"] = sorted(lidos)
            for n_l in lidos:
                leito(n_l)["evolucao"] = True
            js = (saida / "evolucao_anterior.json")
            js.write_text(json.dumps(lidos, ensure_ascii=False, indent=2), encoding="utf-8")
            item["saidas"] = [js.name]
        manifest["arquivos"].append(item)

    tipos = {a["tipo"] for a in manifest["arquivos"]}
    for falta in ("evolucao", "controles", "prescricao", "labs"):
        if falta not in tipos:
            avisos.append(f"nenhum arquivo de {falta} na entrada")
    leitos_evo = [n for n, d in manifest["leitos"].items() if d["evolucao"]]
    if "labs" in tipos:
        for n in leitos_evo:
            if not manifest["leitos"][n]["labs"]:
                avisos.append(f"L{n}: sem laboratório do dia no laudo")
    if leitos_evo and manifest["pares_controles"] and len(manifest["pares_controles"]) != len(leitos_evo):
        avisos.append(f"{len(manifest['pares_controles'])} par(es) de folhas de controle para {len(leitos_evo)} "
                      "leito(s) nas evoluções")
    (saida / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main():
    ap = argparse.ArgumentParser(description="Arruma a pasta de entrada do plantão.")
    ap.add_argument("entrada")
    ap.add_argument("--saida", default="saida/preparo")
    a = ap.parse_args()
    m = preparar(a.entrada, a.saida)
    for arq in m["arquivos"]:
        print(f"{arq['arquivo']}: {arq['tipo']}" + (f", {arq['paginas']} pág." if "paginas" in arq else "")
              + (f", leitos {', '.join(arq['leitos'])}" if arq.get("leitos") else ""))
    for av in m["avisos"]:
        print("aviso: " + av)
    print(f"manifest: {Path(a.saida) / 'manifest.json'}")


if __name__ == "__main__":
    main()
