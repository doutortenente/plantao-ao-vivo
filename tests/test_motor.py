# -*- coding: utf-8 -*-
"""Testes do motor. Rodar: python3 -m unittest discover -s tests"""
import json
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "skills" / "sasi-ingest-export" / "scripts"))
import build_passagem as m  # noqa: E402


class Classificacao(unittest.TestCase):
    def test_evacuacao_nao_cai_em_ev(self):
        self.assertEqual(m.classify("evacuação"), "perda")

    def test_soro_ev_ganho(self):
        self.assertEqual(m.classify("soro EV"), "ganho")

    def test_uf_e_residuo_perda(self):
        self.assertEqual(m.classify("UF"), "perda")
        self.assertEqual(m.classify("resíduo gástrico"), "perda")

    def test_diurese_em_ganho_reclassificada(self):
        b = m.calc_balanco([{"nome": "diurese", "ml": 500}], [])
        self.assertEqual(b["perda_total"], 500)
        self.assertTrue(any("RECLASSIFICADO" in a for a in b["avisos"]))


class Balanco(unittest.TestCase):
    def test_soma_celulas_nao_rodape(self):
        # caso real 11/10/2026: UF 70 ml/h x 4 + 80 ml/h x 8 = 920 (folha dizia 960)
        leito = {"leito": "10", "nome": "X", "ganhos": [{"nome": "dieta", "ml": 702.5}],
                 "perdas": [{"nome": "UF", "serie": [70] * 4 + [80] * 8}],
                 "conferencia_enfermagem": {"perdas": 960}}
        r = m.compute_leito(leito)
        self.assertEqual(r["balanco"]["perda_total"], 920)
        self.assertTrue(any("folha diz 960" in a for a in r["avisos"]))
        txt = "\n".join(r["secoes"][0][1])
        self.assertIn("BH: - 217,5 ml", txt)
        self.assertNotIn("960", txt)  # divergência nunca entra no bloco


class Vitais(unittest.TestCase):
    def test_separador_e_flags(self):
        leito = {"leito": "1", "nome": "X", "sup_o2": "AA",
                 "vitais": {"PAD": [60, 49, 47], "SpO2": [96, 91, "?"], "Dx": [120, "< 20", 250]}}
        linhas = m.compute_leito(leito)["secoes"][0][1]
        self.assertIn("PAD: 60 - 47 mmHg [2x < 50]", linhas)
        self.assertIn("SpO2: 96 - 91 % (AA) [1x < 92]", linhas)
        self.assertIn("Dx: 250 / 120 / < 20 mg/dl [1x > 180] [1x < 70]", linhas)
        self.assertFalse(any("–" in l for l in linhas))

    def test_vm_em_linha_propria(self):
        leito = {"leito": "1", "nome": "X", "sup_o2": "VM por TQT, PCV, PEEP 7, FiO2 40 %",
                 "vitais": {"SpO2": [95, 97], "Dx": [140]}}
        linhas = m.compute_leito(leito)["secoes"][0][1]
        self.assertIn("SpO2: 97 - 95 %", linhas)
        self.assertEqual(linhas[-1], "Sup O2: VM por TQT, PCV, PEEP 7, FiO2 40 %")

    def test_titulos_do_briefing(self):
        r = m.compute_leito({"leito": "1", "nome": "X", "laboratorio": ["HB: 9"], "conduta": ["1. X: y"]})
        titulos = [t for t, _ in r["secoes"]]
        self.assertIn("Laboratório:", titulos)
        self.assertIn("Plano terapêutico e Condutas:", titulos)


class Exemplo(unittest.TestCase):
    def test_exemplo_roda(self):
        dados = json.loads((RAIZ / "gerador" / "exemplo" / "plantao-exemplo.json").read_text(encoding="utf-8"))
        txt, avisos = m.build(dados)
        self.assertIn("LEITO 99", txt)
        self.assertIn("BH: + 400 ml", txt)


class FiltroFicha(unittest.TestCase):
    def test_tira_baixo_valor(self):
        sys.path.insert(0, str(RAIZ / "gerador"))
        import gerar_docx as g
        out = g.filtrar_prescricao([
            {"classe": "SN", "itens": ["Novalgina 1 g"]},
            {"classe": "TGI", "itens": ["Luftal 40 gts", "Tiorfan 100 mg | água 50 ml SNE 8/8h"]},
            {"classe": "ATB", "itens": ["Meronem 1 g EV 8/8h"]}])
        self.assertEqual(out, [{"classe": "TGI", "itens": ["Tiorfan 100 mg"]},
                               {"classe": "ATB", "itens": ["Meronem 1 g EV 8/8h"]}])


if __name__ == "__main__":
    unittest.main()
