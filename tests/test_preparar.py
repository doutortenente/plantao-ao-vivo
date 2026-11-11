# -*- coding: utf-8 -*-
"""preparar.py com uma entrada fictícia. Rodar: python3 -m unittest discover -s tests"""
import copy
import json
import shutil
import struct
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "gerador"))
import gerar_docx  # noqa: E402
import office  # noqa: E402
import preparar  # noqa: E402

TEM = all(shutil.which(x) for x in ("soffice", "pdfinfo", "pdftoppm", "pdftotext"))
EXEMPLO = json.loads((RAIZ / "gerador" / "exemplo" / "plantao-exemplo.json").read_text(encoding="utf-8"))


def pdf_de(arquivo, pasta):
    return office.para_pdf(arquivo, pasta)


@unittest.skipUnless(TEM, "sem LibreOffice/poppler")
class Preparar(unittest.TestCase):
    def test_inventario_da_entrada(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp); ent = tmp / "entrada"; ent.mkdir()
            evo = ent / "01-01-26-uti2-evolucoes.docx"
            gerar_docx.gerar_evolucoes(EXEMPLO, evo)
            # stand-ins fictícios: 2 páginas para controles (2 leitos, 1 página cada desde a evolução compacta de
            # 02/11/2026), o laudo fictício para labs
            dois = copy.deepcopy(EXEMPLO); outro = copy.deepcopy(dois["leitos"][0]); outro["leito"] = "98"
            dois["leitos"].append(outro)
            ctl_docx = tmp / "controles-stand-in.docx"
            gerar_docx.gerar_evolucoes(dois, ctl_docx)
            shutil.move(pdf_de(ctl_docx, tmp), ent / "01-01-26-uti2-controles.pdf")
            lab_txt = tmp / "01-01-26-uti2-labs.txt"
            shutil.copy(RAIZ / "tests" / "fixtures" / "laudo-ficticio.txt", lab_txt)
            shutil.move(pdf_de(lab_txt, tmp), ent / "01-01-26-uti2-labs.pdf")
            m = preparar.preparar(ent, tmp / "preparo")
            tipos = {a["arquivo"]: a["tipo"] for a in m["arquivos"]}
            self.assertEqual(tipos["01-01-26-uti2-controles.pdf"], "controles")
            self.assertEqual(tipos["01-01-26-uti2-labs.pdf"], "labs")
            self.assertEqual(tipos["01-01-26-uti2-evolucoes.docx"], "evolucao")
            self.assertEqual(m["leitos"]["99"], {"evolucao": True, "labs": True})
            self.assertEqual(m["pares_controles"], [{"arquivo": "01-01-26-uti2-controles.pdf", "paginas": [1, 2],
                                                     "leito": "?"}])
            self.assertIn("nenhum arquivo de prescricao na entrada", m["avisos"])
            ctl = [a for a in m["arquivos"] if a["tipo"] == "controles"][0]["saidas"]
            self.assertEqual(len(ctl), 6)  # 2 páginas × (150 dpi + metade de cima + metade de baixo)
            self.assertTrue((tmp / "preparo" / "manifest.json").exists())
            self.assertTrue((tmp / "preparo" / "evolucao_anterior.json").exists())


def pdf_paginas(caminho, paginas):
    """PDF mínimo, uma página por (largura, altura, rotação), cada uma com um traço para não sair em branco."""
    objs, kids = ["<< /Type /Catalog /Pages 2 0 R >>", None], []
    for w, h, rot in paginas:
        kids.append(f"{len(objs) + 1} 0 R")
        objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {w} {h}] /Rotate {rot} "
                    f"/Contents {len(objs) + 2} 0 R >>")
        traco = f"10 10 m {w - 10} {h - 10} l S"
        objs.append(f"<< /Length {len(traco)} >>\nstream\n{traco}\nendstream")
    objs[1] = f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(kids)} >>"
    out, offs = bytearray(b"%PDF-1.4\n"), []
    for i, o in enumerate(objs, 1):
        offs.append(len(out)); out += f"{i} 0 obj\n{o}\nendobj\n".encode()
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += "".join(f"{o:010d} 00000 n \n" for o in offs).encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    Path(caminho).write_bytes(bytes(out))


def tamanho_png(caminho):
    """(largura, altura) do PNG, lidos do cabeçalho (sem Pillow, que o CI não instala)."""
    return struct.unpack(">II", Path(caminho).read_bytes()[16:24])


@unittest.skipUnless(TEM, "sem LibreOffice/poppler")
class SuspeitasDoPendente(unittest.TestCase):
    """docs/PENDENTE.md §2: o preparo não pode misturar arquivos de leitos diferentes nem perder pedaço da folha."""

    def test_laudos_com_ponto_no_nome_nao_dividem_o_mesmo_txt(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp); ent = tmp / "entrada"; ent.mkdir()
            for leito, hb in (("05", "10,1"), ("06", "12,2")):
                txt = tmp / f"laudo{leito}.txt"
                txt.write_text(f"Paciente: FICTICIO {leito}   Leito: {leito}\nHemoglobina {hb} g/dl\n", encoding="utf-8")
                shutil.move(pdf_de(txt, tmp), ent / f"labs 11.11.26 leito {leito}.pdf")
            m = preparar.preparar(ent, tmp / "preparo")
            for item in (a for a in m["arquivos"] if a["tipo"] == "labs"):
                leito = item["arquivo"][-6:-4]
                texto = (tmp / "preparo" / item["saidas"][0]).read_text(encoding="utf-8")
                self.assertIn(f"Leito: {leito}", texto, f"{item['arquivo']} aponta para {item['saidas'][0]}")

    def test_varios_arquivos_de_evolucao_ficam_todos_no_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp); ent = tmp / "entrada"; ent.mkdir()
            for leito in ("98", "99"):
                dados = copy.deepcopy(EXEMPLO); dados["leitos"][0]["leito"] = leito
                gerar_docx.gerar_evolucoes(dados, ent / f"evolucao-leito{leito}.docx")
            preparar.preparar(ent, tmp / "preparo")
            lidos = json.loads((tmp / "preparo" / "evolucao_anterior.json").read_text(encoding="utf-8"))
            self.assertEqual(sorted(lidos), ["98", "99"])

    def test_mesmo_leito_em_dois_arquivos_de_evolucao_vira_aviso(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp); ent = tmp / "entrada"; ent.mkdir()
            for nome in ("evolucao-a.docx", "evolucao-b.docx"):
                gerar_docx.gerar_evolucoes(EXEMPLO, ent / nome)
            m = preparar.preparar(ent, tmp / "preparo")
            self.assertTrue(any("L99" in a and "evolucao-a.docx" in a and "evolucao-b.docx" in a for a in m["avisos"]),
                            m["avisos"])

    def test_recorte_da_folha_girada_cobre_a_largura_toda(self):
        # página 1 em retrato; página 2 com /Rotate 90 (scan de folha deitada): desenhada com 842 x 595 pt
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp); ent = tmp / "entrada"; ent.mkdir()
            pdf_paginas(ent / "01-01-26-uti2-controles.pdf", [(595, 842, 0), (595, 842, 90)])
            preparar.preparar(ent, tmp / "preparo")
            pasta = tmp / "preparo" / "controles" / "01-01-26-uti2-controles" / "p02"
            largura, altura = tamanho_png(pasta / "300dpi-cima.png")
            self.assertEqual(largura, int(842 / 72 * 300))
            self.assertEqual(altura, int(595 / 72 * 300) // 2 + 60)


if __name__ == "__main__":
    unittest.main()
