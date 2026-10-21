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


class RevisaoDe21Out(unittest.TestCase):
    """Achados da revisão adversarial final (21/10/2026)."""

    def test_hora_com_minutos_e_24(self):
        self.assertEqual([m._hora(x) for x in ("7h30", "07:30", "7 h", "24", "25")], ["07", "07", "07", "00", None])

    def test_milhar_em_ml(self):
        self.assertEqual(m._num("1.450", ml=True), (1450.0, None))
        self.assertEqual(m._num("1.450"), (1.45, None))  # vital: ponto é decimal
        self.assertEqual(m._num(True), (None, "?"))
        b = m.calc_balanco([{"nome": "SF", "serie": {"07": "1.450", "09": 50}}, {"nome": "dieta", "ml": "1.000"}], [])
        self.assertEqual(b["ganho_total"], 2500)

    def test_serie_fora_do_formato_avisa(self):
        b = m.calc_balanco([], [{"nome": "diurese", "serie": {"x": 100, "y": 50}}, {"nome": "dreno", "serie": "abc"}])
        self.assertEqual(b["perda_total"], 150)
        self.assertTrue(any("chave que não é hora (x, y)" in a for a in b["avisos"]), b["avisos"])
        self.assertTrue(any("'dreno': série em formato inválido" in a for a in b["avisos"]), b["avisos"])

    def test_agregado_conferido_contra_o_limiar(self):
        self.assertEqual(m.resumo_vital("TAX", {"max": 38.6, "min": 36.2, "flag": 3})[2], ["[3x > 37,8]"])
        self.assertEqual(m.resumo_vital("Dx", {"max": 160, "min": 54, "flag": 2})[2], ["[2x < 70]"])
        _, _, flags, avisos, _ = m.resumo_vital("PAM", {"max": 90, "min": 58})
        self.assertEqual(flags, [])
        self.assertTrue(any("passa do limiar < 65 sem a contagem" in a for a in avisos), avisos)
        _, _, flags, avisos, _ = m.resumo_vital("TAX", {"max": 38.6, "min": 35.0, "flag": 3})
        self.assertEqual(flags, [])
        self.assertTrue(any("sem saber o limiar" in a for a in avisos), avisos)
        self.assertTrue(any("ilegível no agregado" in a for a in m.resumo_vital("PAS", {"max": "?", "min": 88})[3]))

    def test_rodape_em_texto_e_ilegivel(self):
        ex = json.loads((RAIZ / "gerador" / "exemplo" / "plantao-exemplo.json").read_text(encoding="utf-8"))
        ex["leitos"][0]["conferencia_enfermagem"] = {"ganhos": "?", "bh": "1.000"}
        _, avisos = m.build(ex)
        self.assertIn('L99: CONFERÊNCIA — Ganhos: rodapé ilegível ("?"), não conferido', avisos)
        self.assertTrue(any("CONFERÊNCIA — BH: folha diz 1.000," in a for a in avisos), avisos)


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


if __name__ == "__main__":
    unittest.main()
