# -*- coding: utf-8 -*-
"""Ficha-cola: em TNE, a água pela sonda vai na linha DIETA (pedido de 02/11/2026)."""
import copy
import json
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "gerador"))
import validar  # noqa: E402

EXEMPLO = json.loads((RAIZ / "gerador" / "exemplo" / "plantao-exemplo.json").read_text(encoding="utf-8"))


def com_dieta(itens):
    p = copy.deepcopy(EXEMPLO)
    f = p["leitos"][0]["ficha"]
    f["infusoes"] = [x for x in f["infusoes"] if x[0] != "DIETA"] + [["DIETA", itens]]
    return validar.validar(p)


class AguaDaSonda(unittest.TestCase):
    def test_agua_da_sonda_nao_e_mais_tirada_da_ficha(self):
        erros, avisos = com_dieta(["Fresubin HP Energy 60 ml/h SNE · Água 200 ml 6/6 h => 10-16-22-04"])
        self.assertEqual(erros, [])
        self.assertFalse(any("não vai na ficha" in a or "água pela sonda" in a for a in avisos), avisos)

    def test_tne_sem_agua_avisa(self):
        _, avisos = com_dieta(["Fresubin HP Energy 60 ml/h SNE"])
        self.assertTrue(any("sem a água pela sonda" in a for a in avisos), avisos)

    def test_dieta_oral_nao_cobra_agua(self):
        _, avisos = com_dieta(["Geral hipossódica VO"])
        self.assertFalse(any("água pela sonda" in a for a in avisos), avisos)


if __name__ == "__main__":
    unittest.main()
