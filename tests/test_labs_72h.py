# -*- coding: utf-8 -*-
"""Laboratório seriado de 72 h da ficha-cola (22/11/2026). Rodar: python3 -m unittest discover -s tests"""
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "gerador"))
import labs_72h as L  # noqa: E402


def laudo(coleta, **valores):
    nomes = {"HB": "HEMOGLOBINA", "PLAQ": "PLAQUETAS", "UR": "UREIA", "CR": "CREATININA", "NA": "SODIO",
             "K": "POTASSIO", "CA": "CALCIO", "CAI": "CALCIO IONICO"}
    linhas = [f"               {nomes[k]}                          {v} mg/dL" for k, v in valores.items()]
    return "\n".join(linhas + [f"               Data da Coleta: {coleta}          Resultado liberado em: {coleta}"])


class Serie72h(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        arquivos = {
            "03-tania-labs-19-11-26.txt": laudo("19/11/2026 00:05:00", HB="10,10", UR="120,0"),
            "03-tania-labs-20-11-26.txt": laudo("20/11/2026 00:05:00", HB="9,60", PLAQ="248.000", UR="135,3",
                                               CR="1,2", NA="163,2"),
            "03-tania-labs-21-11-26.txt": laudo("21/11/2026 00:05:00", HB="7,80", PLAQ="237.000", UR="133,9",
                                               CR="1,4", NA="163,0"),
            "03-tania-labs-22-11-26.txt": laudo("22/11/2026 00:03:00", HB="8,30", PLAQ="247.000", UR="143,1",
                                               CR="1,1"),
            "03-tania-gaso-22-11-26.txt": laudo("22/11/2026 05:00:00", HB="6,1", NA="150"),
            "07-jack-labs-21-11-26.txt": laudo("21/11/2026 10:27:00", CA="8,8", CAI="0,96"),
            "07-jack-labs2-21-11-26.txt": laudo("21/11/2026 18:52:00", CA="8,9", CAI="0,98"),
        }
        for nome, txt in arquivos.items():
            (d / nome).write_text(txt, encoding="utf-8")
        self.por_leito, self.avisos = L.ler(sorted(d.iterdir()))

    def tearDown(self):
        self.tmp.cleanup()

    def test_tres_dias_ate_a_ultima_coleta(self):
        b = L.bloco(self.por_leito["03"], ate=date(2026, 11, 22))
        self.assertEqual(b["lab_titulo"], "LABORATÓRIO 20/11 => 21/11 => 22/11")
        self.assertIn("Hb 9,6 => 7,8 => 8,3 | Plaq 248 => 237 => 247 mil", b["lab"])
        self.assertIn("Ur 135,3 => 133,9 => 143,1 | Cr 1,2 => 1,4 => 1,1", b["lab"])

    def test_laboratorio_central_vence_a_gasometria_no_mesmo_dia(self):
        b = L.bloco(self.por_leito["03"], ate=date(2026, 11, 22))
        self.assertFalse(any("6,1" in l for l in b["lab"]), b["lab"])  # Hb da gaso não substitui a do hemograma
        self.assertTrue(any(l.startswith("Na 163,2 => 163 => 150") for l in b["lab"]), b["lab"])  # Na só na gaso

    def test_dia_sem_coleta_na_janela_aparece_no_titulo(self):
        b = L.bloco(self.por_leito["07"], ate=date(2026, 11, 22))
        self.assertEqual(b["lab_titulo"], "LABORATÓRIO 21/11 (22/11 sem coleta)")
        self.assertIn("Ca 8,9 | CaI 0,98", b["lab"])  # vale a última coleta do dia

    def test_por_coleta_mostra_as_horas(self):
        b = L.bloco(self.por_leito["07"], por_coleta=True, ate=date(2026, 11, 22))
        self.assertEqual(b["lab"][0], "Coletas 21/11 10 h · 21/11 18 h")
        self.assertIn("Ca 8,8 => 8,9 | CaI 0,96 => 0,98", b["lab"])

    def test_buraco_mantem_a_serie_alinhada_com_as_datas(self):
        self.assertEqual(L.serie([(1, {}), (2, {"P": "5,6"}), (3, {"P": "5,2"})], "P"), "— => 5,6 => 5,2")

    def test_numeros(self):
        self.assertEqual(L._valor("HB", "9,00"), "9,0")
        self.assertEqual(L._valor("NA", "138,0"), "138")
        self.assertEqual(L._valor("pH", "7,297"), "7,30")
        self.assertEqual(L._valor("PLAQ", "205.000"), "205")
        self.assertEqual(L._valor("CAI", "1,00"), "1,00")


if __name__ == "__main__":
    unittest.main()
