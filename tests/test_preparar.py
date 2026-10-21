# -*- coding: utf-8 -*-
"""preparar.py com uma entrada fictícia. Rodar: python3 -m unittest discover -s tests"""
import json
import shutil
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
            # stand-ins fictícios: 2 páginas para controles, o laudo fictício para labs
            shutil.move(pdf_de(evo, tmp), ent / "01-01-26-uti2-controles.pdf")
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


if __name__ == "__main__":
    unittest.main()
