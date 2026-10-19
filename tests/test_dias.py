# -*- coding: utf-8 -*-
"""Dias de ATB (início = D0) e de UTI (admissão = D1), decisão de 19/10/2026."""
import datetime as dt
import json
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "skills" / "sasi-ingest-export" / "scripts"))
import build_passagem as m  # noqa: E402

DIA = dt.date(2026, 1, 1)


class Atb(unittest.TestCase):
    def test_inicio_e_d0(self):
        self.assertEqual(m.dias_atb("Meronem (I: 01/01)", DIA)[0], "Meronem (D0, I: 01/01)")
        self.assertEqual(m.dias_atb("Meronem (D?, I: 31/12)", DIA)[0], "Meronem (D1, I: 31/12)")

    def test_virada_de_ano(self):
        txt, av = m.dias_atb("Tazocin 4,5 g (D3, I: 30/12)", DIA)
        self.assertEqual(txt, "Tazocin 4,5 g (D2, I: 30/12)")
        self.assertIn("estava D3, a conta dá D2", av[0])

    def test_d_certo_nao_avisa(self):
        self.assertEqual(m.dias_atb("x (D2, I: 30/12)", DIA), ("x (D2, I: 30/12)", []))

    def test_inicio_muito_antigo_avisa(self):
        _, av = m.dias_atb("y (D0, I: 02/01)", DIA)
        self.assertTrue(any("conferir a data de início" in a for a in av))


class Uti(unittest.TestCase):
    def test_admissao_e_d1(self):
        plantao = {"meta": {"data": "01/01/2026"},
                   "leitos": [{"leito": "1", "admissao_uti": "01/01/2026"},
                              {"leito": "2", "admissao_uti": "30/12", "dia_uti": "D5 UTI (DH 9)"}]}
        dados, avisos = m.preparar(plantao)
        self.assertEqual(dados["leitos"][0]["dia_uti"], "D1 UTI")
        self.assertEqual(dados["leitos"][1]["dia_uti"], "D3 UTI (DH 9)")
        self.assertTrue(any("L2: dia de UTI estava D5, a conta dá D3" in a for a in avisos))
        self.assertNotIn("dia_uti", plantao["leitos"][0])  # o original não muda

    def test_exemplo_ja_esta_certo(self):
        dados = json.loads((RAIZ / "gerador" / "exemplo" / "plantao-exemplo.json").read_text(encoding="utf-8"))
        prep, avisos = m.preparar(dados)
        self.assertEqual(avisos, [])
        self.assertEqual(prep["leitos"][0]["dia_uti"], "D3 UTI")
        self.assertIn("(D2, I: 30/12)", prep["leitos"][0]["ficha"]["infusoes"][1][1][0])


if __name__ == "__main__":
    unittest.main()
