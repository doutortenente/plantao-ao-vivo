# -*- coding: utf-8 -*-
"""Nota de admissão em A4 (19/10/2026). Rodar: python3 -m unittest discover -s tests"""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "gerador"))
import gerar_admissao as GA  # noqa: E402

from docx import Document  # noqa: E402

NOTA = RAIZ / "tests" / "fixtures" / "admissao-ficticia.txt"


class Admissao(unittest.TestCase):
    def test_a4_margens_e_negrito(self):
        with tempfile.TemporaryDirectory() as tmp:
            saida = Path(tmp) / "a.docx"
            GA.gerar(NOTA, saida)
            doc = Document(str(saida))
        s = doc.sections[0]
        self.assertAlmostEqual(s.page_width.cm, 21.0, places=1)
        self.assertAlmostEqual(s.page_height.cm, 29.7, places=1)
        self.assertAlmostEqual(s.left_margin.cm, 1.25, places=2)
        self.assertAlmostEqual(s.right_margin.cm, 1.34, places=2)
        self.assertAlmostEqual(s.top_margin.cm, 2.5, places=2)
        negritos = [r.text for p in doc.paragraphs for r in p.runs if r.bold]
        for esperado in ("98 - PACIENTE FICTÍCIO DE ADMISSÃO", "ADMISSÃO UTI 2 - 01-01-26", "HPMA:", "ALERGIAS:",
                         "Dispositivos:", "FC:", "- Urina I (01/01):", "1. Infeccioso:", "2. Hemodinâmico:"):
            self.assertIn(esperado, negritos)
        self.assertNotIn("Mantida ceftriaxona; urocultura e hemoculturas colhidas.", negritos)

    def test_nome_do_arquivo_pelo_cabecalho(self):
        self.assertEqual(GA.nome_do_cabecalho(NOTA), "01-01-26-uti2-admissao-leito98.docx")

    def test_conferencia_pega_interrogacao(self):
        with tempfile.TemporaryDirectory() as tmp:
            nota = Path(tmp) / "n.txt"
            nota.write_text(NOTA.read_text(encoding="utf-8").replace("FC: 112 bpm", "FC: ? bpm"), encoding="utf-8")
            GA.gerar(nota, Path(tmp) / "a.docx")
            erros, _ = GA.conferir_admissao(Path(tmp) / "a.docx")
        self.assertTrue(any("campo sem dado" in e for e in erros))

    @unittest.skipUnless(shutil.which("soffice") and shutil.which("pdfinfo"), "sem LibreOffice")
    def test_limpa_cabe_em_uma_folha(self):
        with tempfile.TemporaryDirectory() as tmp:
            GA.gerar(NOTA, Path(tmp) / "a.docx")
            erros, n = GA.conferir_admissao(Path(tmp) / "a.docx")
        self.assertEqual(erros, [])
        self.assertEqual(n, 1)


if __name__ == "__main__":
    unittest.main()
