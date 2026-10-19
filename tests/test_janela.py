# -*- coding: utf-8 -*-
"""Janela pela hora: o motor confere a janela de 24 h pelas horas das séries (erro de 11/10/2026)."""
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "skills" / "sasi-ingest-export" / "scripts"))
import build_passagem as m  # noqa: E402

SLOTS = m.SLOTS


def leito(horas, **extra):
    serie = {h: 100 + i for i, h in enumerate(horas)}
    return dict({"leito": "10", "nome": "X", "vitais": {"PAS": serie, "PAM": serie, "FC": serie}}, **extra)


class Janela(unittest.TestCase):
    def test_24h_completa(self):
        r = m.compute_leito(leito(SLOTS), {"janela": "24 h"})
        self.assertEqual(r["janela"], "24 h")
        self.assertEqual(r["secoes"][0][0], "Sinais vitais + balanço 24 h:")
        self.assertFalse(any("janela" in a for a in r["avisos"]))

    def test_so_noite_caso_11_10(self):
        r = m.compute_leito(leito(SLOTS[6:]), {"janela": "24 h"})
        self.assertEqual(r["secoes"][0][0], "Sinais vitais + balanço 19 - 05 h:")
        self.assertTrue(any(a.startswith("ALERTA: janela pedida é 24 h") and "faltou o diurno" in a
                            for a in r["avisos"]))

    def test_buraco_vira_aviso(self):
        r = m.compute_leito(leito([h for h in SLOTS if h not in ("11", "13")]), {})
        self.assertEqual(r["janela"], "24 h")
        self.assertTrue(any("faltando às 11 h, 13 h" in a for a in r["avisos"]))

    def test_recorte_pedido_e_respeitado(self):
        r = m.compute_leito(leito(SLOTS[6:]), {"janela": "12 h noturno (19 - 05 h)", "recorte": "noturno"})
        self.assertEqual(r["janela"], "12 h noturno (19 - 05 h)")
        self.assertFalse(any("ALERTA: janela" in a for a in r["avisos"]))

    def test_lista_sem_hora_avisa(self):
        r = m.compute_leito({"leito": "1", "nome": "X", "vitais": {"PAS": [120, 110]}}, {})
        self.assertTrue(any("séries sem hora" in a for a in r["avisos"]))

    def test_hora_com_duas_leituras_e_ilegivel(self):
        r = m.compute_leito({"leito": "1", "nome": "X", "vitais": {"PAS": {"07": [140, 132], "09": "?", "19": 90}}}, {})
        self.assertIn("PAS: 140 - 90 mmHg", r["secoes"][0][1])
        self.assertTrue(any("(09 h)" in a for a in r["avisos"]))

    def test_balanco_por_hora_soma_igual(self):
        b = m.calc_balanco([{"nome": "dieta", "serie": {"07": 100, "09": 100}}],
                           [{"nome": "UF", "serie": {f"{h:02d}": (70 if h < 11 else 80) for h in range(7, 19)}}])
        self.assertEqual(b["perda_total"], 920)  # caso real de 11/10: 70 × 4 + 80 × 8


if __name__ == "__main__":
    unittest.main()
