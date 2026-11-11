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
            "HB: 11,2 => 10,8 g/dl | HT: 33 => 32 % | PLAQ: 210.000 => 180.000 /mm3",
            "LEUCO: 16.200 => 18.400 /mm3 (seg 82 % / bast 6 %)",
            "UR: 58 => 72 mg/dl | CR: 1,3 => 1,7 mg/dl | NA: 138 | K: 4,8 | MG: 1,9 | CAI: 1,12",
            "Gaso: pH 7,31 / pCO2 34 / HCO3 17 / BE -8 / Lactato 3,1",
        ])
        self.assertEqual(avisos, [])

    def test_amostra_maquina_fica_fora(self):
        valores, _ = labs.extrair(LAUDO)
        self.assertEqual(valores["K"], "4,8")
        self.assertEqual(valores["NA"], "138")

    def test_sem_anterior_sem_seta(self):
        linhas, _ = labs.ler_laudo(LAUDO)
        self.assertTrue(any(l.startswith("UR: 72 mg/dl | CR: 1,7 mg/dl | NA: 138") for l in linhas), linhas)

    def test_eletrolito_sem_serie(self):
        linhas, _ = labs.ler_laudo(LAUDO, ANTERIOR + ["NA: 140 | K: 4,1"])
        self.assertIn("UR: 58 => 72 mg/dl | CR: 1,3 => 1,7 mg/dl | NA: 138 | K: 4,8 | MG: 1,9 | CAI: 1,12", linhas)

    def test_layout_desconhecido_avisa(self):
        linhas, avisos = labs.ler_laudo("página em branco")
        self.assertEqual(linhas, [])
        self.assertTrue(any("nenhum analito reconhecido" in a for a in avisos))

    def test_valor_repetido_diferente_avisa(self):
        _, avisos = labs.extrair("Potássio   4,8 mEq/L\nPotássio   5,9 mEq/L\n")
        self.assertTrue(any("K aparece com 4,8 e 5,9" in a for a in avisos))


class RevisaoDe21Out(unittest.TestCase):
    def test_seta_da_evolucao_anterior_nao_vira_maior_que(self):
        self.assertEqual(labs.anteriores(["HB: 11,2 -> 10,8 g/dl | PLAQ: 210.000 -> 180.000 /mm3", "PCR: < 5 mg/l"]),
                         {"HB": "10,8", "PLAQ": "180.000", "PCR": "< 5"})

    # docs/PENDENTE.md §2, conferido em 11/11/2026
    def test_resultado_em_texto_nao_vira_o_numero_da_referencia(self):
        valores, avisos = labs.extrair("Potássio      HEMOLISADO      3,5 a 5,1 mEq/L\n"
                                       "Creatinina:   Pendente   (0,6 a 1,2)\n"
                                       "Sódio   138 mEq/L\n")
        self.assertNotIn("K", valores)
        self.assertNotIn("CR", valores)
        self.assertEqual(valores["NA"], "138")
        self.assertTrue(any(a.startswith("lab: K ") and "HEMOLISADO" in a for a in avisos), avisos)
        self.assertTrue(any(a.startswith("lab: CR ") and "Pendente" in a for a in avisos), avisos)

    def test_decimal_com_ponto_nao_e_truncado(self):
        valores, _ = labs.extrair("Creatinina: 1.7 mg/dl\npH 7.31\nBE -2.5\nPlaquetas: 150.000 /mm3\n")
        self.assertEqual(valores["CR"], "1,7")
        self.assertEqual(valores["pH"], "7,31")
        self.assertEqual(valores["BE"], "-2,5")
        self.assertEqual(valores["PLAQ"], "150.000")  # ponto de milhar continua milhar

    def test_decimal_com_ponto_na_evolucao_anterior(self):
        self.assertEqual(labs.anteriores(["CR: 1.7 mg/dl"]), {"CR": "1,7"})

    def test_unidade_de_outra_escala_nao_sai_com_a_unidade_fixa(self):
        # o bloco escreve g/dl, /mm3 e mg/dl fixos: "16,2 x10³/µL" sairia "LEUCO: 16,2 /mm3" (1000× menor)
        valores, avisos = labs.extrair("Leucócitos: 16,2 x10³/µL\nHemoglobina: 108 g/L\nCreatinina: 150 µmol/L\n"
                                       "Plaquetas: 180 mil/mm3\nHematócrito: 32 %\nUréia: 72 mg/dL\n")
        for sigla in ("LEUCO", "HB", "CR", "PLAQ"):
            self.assertNotIn(sigla, valores)
            self.assertTrue(any(a.startswith(f"lab: {sigla} ") and "unidade" in a for a in avisos), (sigla, avisos))
        self.assertEqual((valores["HT"], valores["UR"]), ("32", "72"))


if __name__ == "__main__":
    unittest.main()
