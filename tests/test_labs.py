# -*- coding: utf-8 -*-
"""Parser de laboratório (beta), com laudo fictício. Rodar: python3 -m unittest discover -s tests"""
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "skills" / "sasi-ingest-export" / "scripts"))
import labs  # noqa: E402

LAUDO = (RAIZ / "tests" / "fixtures" / "laudo-ficticio.txt").read_text(encoding="utf-8")
ANTERIOR = ["HB: 11,2 g/dl | HT: 33 % | PLAQ: 210.000 /mm3", "LEUCO: 16.200 /mm3 (seg 80 % / bast 2 %)",
            "UR: 58 mg/dl", "CR: 1,3 mg/dl"]


class Labs(unittest.TestCase):
    def test_monta_secao_do_briefing_com_series(self):
        linhas, avisos = labs.ler_laudo(LAUDO, ANTERIOR)
        self.assertEqual(linhas, [
            "HB: 11,2 -> 10,8 g/dl | HT: 33 -> 32 % | PLAQ: 210.000 -> 180.000 /mm3",
            "LEUCO: 16.200 -> 18.400 /mm3 (seg 82 % / bast 6 %)",
            "UR: 58 -> 72 mg/dl",
            "CR: 1,3 -> 1,7 mg/dl",
            "NA: 138 | K: 4,8 | MG: 1,9 | CAI: 1,12",
            "Gaso: pH 7,31 / pCO2 34 / HCO3 17 / BE -8 / Lactato 3,1",
        ])
        self.assertEqual(avisos, [])

    def test_amostra_maquina_fica_fora(self):
        valores, _ = labs.extrair(LAUDO)
        self.assertEqual(valores["K"], "4,8")
        self.assertEqual(valores["NA"], "138")

    def test_sem_anterior_sem_seta(self):
        linhas, _ = labs.ler_laudo(LAUDO)
        self.assertIn("UR: 72 mg/dl", linhas)

    def test_layout_desconhecido_avisa(self):
        linhas, avisos = labs.ler_laudo("página em branco")
        self.assertEqual(linhas, [])
        self.assertTrue(any("nenhum analito reconhecido" in a for a in avisos))

    def test_valor_repetido_diferente_avisa(self):
        _, avisos = labs.extrair("Potássio   4,8 mEq/L\nPotássio   5,9 mEq/L\n")
        self.assertTrue(any("K aparece com 4,8 e 5,9" in a for a in avisos))


if __name__ == "__main__":
    unittest.main()
