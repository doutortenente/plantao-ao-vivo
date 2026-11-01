# -*- coding: utf-8 -*-
"""Testes do peso.py: peso com fonte e data, peso predito, VC, Cockcroft-Gault, débito urinário e KDIGO.
Rodar: python3 -m unittest discover -s tests. Valores esperados feitos à mão (ou do autoteste do app calculadoras-uti)."""
import datetime as dt
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "skills" / "sasi-ingest-export" / "scripts"))
import peso as P  # noqa: E402

NAIR = {"kg": 66, "altura_cm": 153, "fonte": "EcoTT", "data": "06/12/2025"}


class LerPeso(unittest.TestCase):
    def test_peso_com_fonte_e_data(self):
        self.assertEqual(P.ler({"peso": NAIR}),
                         {"kg": 66.0, "altura_cm": 153.0, "fonte": "EcoTT", "data": "06/12/2025"})

    def test_virgula_decimal(self):
        self.assertEqual(P.ler({"peso": {"kg": "66,5", "fonte": "balança", "data": "31/10/2026"}})["kg"], 66.5)

    def test_data_sai_com_dois_digitos(self):
        self.assertEqual(P.ler({"peso": {"kg": 66, "fonte": "EcoTT", "data": "6/12/2025"}})["data"], "06/12/2025")

    def test_sem_fonte_ou_sem_data_nao_vale(self):
        # zero alucinação: peso sem fonte e data não entra em conta nenhuma (o validar dá erro)
        self.assertIsNone(P.ler({"peso": {"kg": 66, "data": "06/12/2025"}}))
        self.assertIsNone(P.ler({"peso": {"kg": 66, "fonte": "EcoTT"}}))
        self.assertIsNone(P.ler({"peso": {"kg": "?", "fonte": "EcoTT", "data": "06/12/2025"}}))
        self.assertIsNone(P.ler({"peso": {"kg": 66, "fonte": "?", "data": "06/12/2025"}}))  # fonte em dúvida
        self.assertIsNone(P.ler({}))

    def test_idade_e_sexo(self):
        self.assertEqual(P.idade_sexo("90F"), (90, "F"))
        self.assertEqual(P.idade_sexo("60 m"), (60, "M"))
        self.assertEqual(P.idade_sexo("?"), (None, None))


class Antropometria(unittest.TestCase):
    def test_peso_predito(self):
        self.assertAlmostEqual(P.peso_predito("M", 180), 75.116, places=6)  # autoteste do app
        self.assertAlmostEqual(P.peso_predito("F", 153), 46.046, places=6)  # 45,5 + 0,91 x 0,6

    def test_vc_6_a_8_ml_kg(self):
        self.assertEqual(P.vc(46.046), (276, 368))  # 276,3 e 368,4

    def test_cockcroft_gault(self):
        # (140 - 90) x 66 / (72 x 1,5) x 0,85 = 25,97
        self.assertAlmostEqual(P.clcr(90, "F", 66, 1.5), 25.972, places=3)
        self.assertAlmostEqual(P.clcr(60, "M", 70, 1.0), 77.778, places=3)  # 80 x 70 / 72

    def test_creatinina_do_laboratorio(self):
        self.assertEqual(P.creatinina(["UR: 75,3 -> 84,4 mg/dl | CR: 1,4 -> 1,5 mg/dl"]), (1.5, 1.4))
        self.assertEqual(P.creatinina(["HB: 9 g/dl", "CR: 1,7 mg/dl"]), (1.7, None))
        self.assertEqual(P.creatinina(["Creatinina 1,2"]), (None, None))  # fora do formato do BRIEFING
        # atual ilegível: não vale pegar a da véspera como atual
        self.assertEqual(P.creatinina(["CR: 1,4 -> ? mg/dl"]), (None, None))
        self.assertEqual(P.creatinina(["CR: ? -> 1,5 mg/dl"]), (1.5, None))


class DebitoUrinario(unittest.TestCase):
    def test_ml_kg_h(self):
        self.assertAlmostEqual(P.debito(300, 12, 66), 0.3788, places=4)

    def test_kdigo_pelo_debito(self):
        self.assertEqual(P.kdigo_debito(0.38, 12), 2)
        self.assertEqual(P.kdigo_debito(0.38, 6), 1)
        self.assertEqual(P.kdigo_debito(0.25, 24), 3)
        self.assertEqual(P.kdigo_debito(0.25, 12), 2)    # < 0,3 só vira 3 com 24 h
        self.assertIsNone(P.kdigo_debito(0.6, 24))
        self.assertIsNone(P.kdigo_debito(0.45, 5))       # menos de 6 h não estadia
        self.assertEqual(P.kdigo_debito(0.5, 12), None)  # desigualdade estrita: < 0,5


class Idade(unittest.TestCase):
    def test_dias_do_peso(self):
        self.assertEqual(P.dias(NAIR, dt.date(2026, 10, 31)), 329)


if __name__ == "__main__":
    unittest.main()
