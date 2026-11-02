# -*- coding: utf-8 -*-
"""Testes das drogas em BIC (bic.py). Rodar: python3 -m unittest discover -s tests

O gabarito das doses é o autoteste do app calculadoras-uti (docs/index.html, função autoteste), cujos valores foram
conferidos contra a planilha "Calculadoras para UTI". Os casos da Nair (31/10/2026) foram feitos à mão."""
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "skills" / "sasi-ingest-export" / "scripts"))
import bic  # noqa: E402

# (droga, ampolas, volume final em ml (0 = puro), ml/h, peso em kg, dose esperada) — autoteste do app
AUTOTESTE_DO_APP = [
    ("noradrenalina", 8, 250, 5, 69, 0.15458937198067632),
    ("vasopressina", 2, 100, 6, 1, 0.04),
    ("adrenalina", 16, 250, 10, 120, 0.08888888888888888),
    ("dobutamina", 4, 250, 6, 80, 5),
    ("nitroprussiato", 1, 250, 12, 75, 0.5333333333333333),
    ("nitroglicerina", 1, 250, 6, 1, 20),
    ("fentanil", 5, 0, 1, 1, 50),
    ("midazolam", 3, 150, 10, 80, 0.125),
    ("propofol", 5, 0, 13, 40, 54.166666666666664),
    ("cetamina", 1, 100, 5, 25, 0.2),
    ("dexmedetomidina", 2, 100, 20, 54, 1.4814814814814814),
    ("morfina", 5, 100, 1, 1, 0.5),
    ("rocuronio", 5, 250, 70, 130, 8.974358974358974),
    ("milrinone", 1, 100, 15.75, 75, 0.35),  # app: mlhDe(milrinone, 0,35 mcg/kg/min, 75 kg) = 15,75 ml/h
    ("dopamina", 5, 250, 6.75, 75, 1.5),     # app: mlhDe(dopamina, 1,5 mcg/kg/min, 75 kg) = 6,75 ml/h
]


class Tabela(unittest.TestCase):
    def test_autoteste_do_app_confere(self):
        for droga, amp, vol, mlh, kg, esperado in AUTOTESTE_DO_APP:
            with self.subTest(droga=droga):
                d = bic.achar(droga)
                c = bic.concentracao(d, amp, volume_final_ml=vol)
                self.assertAlmostEqual(bic.dose(d, c, mlh, kg), esperado, places=9)

    def test_nome_comercial_e_generico(self):
        self.assertEqual(bic.achar("Hyponor")["id"], "noradrenalina")
        self.assertEqual(bic.achar("NORADRENALINA")["id"], "noradrenalina")
        self.assertEqual(bic.achar("Dormonid")["id"], "midazolam")
        self.assertEqual(bic.achar("precedex")["id"], "dexmedetomidina")
        self.assertEqual(bic.achar("Rocurônio")["id"], "rocuronio")

    def test_toda_marca_e_apelido_da_tabela(self):
        apelidos = {a for d in bic.TABELA.values() for a in d[-1]}
        self.assertEqual(bic.MARCAS - apelidos, set())

    def test_drogas_citadas_num_texto(self):
        self.assertEqual(bic.mencionadas("Hyponor (noradrenalina) 16 mg + SG 5% 234 ml"), ["noradrenalina"])
        self.assertEqual(bic.mencionadas("Fentanil 5 amp puro · Dormonid 150 mg"), ["fentanil", "midazolam"])
        self.assertEqual(bic.mencionadas("Dexametasona 4 mg EV; Isoproterenol 1 mg"), [])

    def test_droga_fora_da_tabela(self):
        self.assertIsNone(bic.achar("amiodarona"))
        self.assertIsNone(bic.achar("dexametasona"))  # não pode cair em dexmedetomidina
        self.assertIsNone(bic.achar(""))


class DiluicaoDaPrescricao(unittest.TestCase):
    """A prescrição traz o diluente; o volume final soma o volume das ampolas (Hyponor 4 amp de 4 ml + SG 5% 234 ml)."""

    def test_noradrenalina_4_amp_em_234_ml(self):
        d = bic.achar("noradrenalina")
        self.assertEqual(bic.volume_final(d, 4, diluente_ml=234), 250)
        self.assertAlmostEqual(bic.concentracao(d, 4, diluente_ml=234), 64)  # 16 mg / 250 ml = 64 mcg/ml

    def test_dobutamina_4_amp_em_170_ml(self):
        self.assertAlmostEqual(bic.concentracao(bic.achar("dobutamina"), 4, diluente_ml=170), 4000)

    def test_midazolam_3_amp_em_120_ml(self):
        self.assertAlmostEqual(bic.concentracao(bic.achar("midazolam"), 3, diluente_ml=120), 1)

    def test_fentanil_puro(self):
        d = bic.achar("fentanil")
        self.assertEqual(bic.volume_final(d, 5, diluente_ml=0), 50)
        self.assertAlmostEqual(bic.concentracao(d, 5, diluente_ml=0), 50)


class Vazao(unittest.TestCase):
    def test_serie_por_hora_vira_sequencia_na_ordem_da_folha(self):
        self.assertEqual(bic.vazoes({"07": 3, "09": 3, "16": 2, "17": 2})[0], [3, 2])
        self.assertEqual(bic.vazoes({"01": 7, "19": 5, "23": 7, "05": 4})[0], [5, 7, 4])  # 19 h vem antes da 01 h

    def test_numero_e_texto(self):
        self.assertEqual(bic.vazoes(5)[0], [5])
        self.assertEqual(bic.vazoes("2,5")[0], [2.5])

    def test_celula_ilegivel_fica_fora_e_avisa(self):
        seq, avisos = bic.vazoes({"07": 3, "09": "?", "11": 2})
        self.assertEqual(seq, [3, 2])
        self.assertTrue(any("ilegível" in a for a in avisos), avisos)


class LinhaDaNair(unittest.TestCase):
    """Leito 11, 31/10/2026: 66 kg (EcoTT 06/12/2025). Doses conferidas à mão."""

    def test_noradrenalina_3_para_2_ml_h(self):
        r = bic.linha({"droga": "noradrenalina", "ampolas": 4, "diluente_ml": 234,
                       "ml_h": {"07": 3, "15": 3, "16": 2, "18": 2}}, 66)
        # 3 x 64 / 66 / 60 = 0,048; 2 x 64 / 66 / 60 = 0,032
        self.assertEqual(r["evolucao"], "Noradrenalina: 16 mg/250 ml (64 mcg/ml), 3 => 2 ml/h (0,05 => 0,03 mcg/kg/min)")
        # na ficha, 1 linha com o que corre agora (a sequência fica na evolução): a folha tem de caber
        self.assertEqual(r["ficha"], "Noradrenalina 16 mg/250 ml · 2 ml/h · 0,03 mcg/kg/min")
        self.assertEqual(r["grupo"], "DVA")

    def test_dobutamina_5_ml_h(self):
        r = bic.linha({"droga": "Dobutrex", "ampolas": 4, "diluente_ml": 170, "ml_h": 5}, 66)
        self.assertEqual(r["evolucao"], "Dobutamina: 1.000 mg/250 ml (4.000 mcg/ml), 5 ml/h (5,05 mcg/kg/min)")
        # na ficha, a marca da prescrição; apelido ("dobuta") sai pelo genérico
        self.assertEqual(r["ficha"], "Dobutrex 1.000 mg/250 ml · 5 ml/h · 5,05 mcg/kg/min")
        apelido = bic.linha({"droga": "dobuta", "ampolas": 4, "diluente_ml": 170, "ml_h": 5}, 66)
        self.assertTrue(apelido["ficha"].startswith("Dobutamina 1.000 mg/250 ml"), apelido["ficha"])

    def test_sedacao(self):
        mida = bic.linha({"droga": "midazolam", "ampolas": 3, "diluente_ml": 120, "ml_h": 4}, 66)
        fenta = bic.linha({"droga": "fentanil", "ampolas": 5, "diluente_ml": 0, "ml_h": 1}, 66)
        self.assertEqual(mida["evolucao"], "Midazolam: 150 mg/150 ml (1 mg/ml), 4 ml/h (0,06 mg/kg/h)")
        self.assertEqual(fenta["evolucao"], "Fentanil: 2,5 mg/50 ml (50 mcg/ml), 1 ml/h (50 mcg/h)")
        self.assertEqual(mida["grupo"], "SEDAÇÃO")


class SemPesoSemVazaoTeto(unittest.TestCase):
    def test_sem_peso_nao_calcula_dose_por_kg(self):
        r = bic.linha({"droga": "noradrenalina", "ampolas": 4, "diluente_ml": 234, "ml_h": 2}, None)
        self.assertEqual(r["evolucao"], "Noradrenalina: 16 mg/250 ml (64 mcg/ml), 2 ml/h")
        self.assertTrue(any("sem peso" in a for a in r["avisos"]), r["avisos"])

    def test_droga_sem_peso_calcula_mesmo_sem_peso(self):
        r = bic.linha({"droga": "vasopressina", "ampolas": 2, "volume_final_ml": 100, "ml_h": 6}, None)
        self.assertEqual(r["evolucao"], "Vasopressina: 40 UI/100 ml (0,4 UI/ml), 6 ml/h (0,04 UI/min)")
        self.assertEqual(r["avisos"], [])

    def test_sem_vazao_na_folha(self):
        r = bic.linha({"droga": "noradrenalina", "ampolas": 4, "diluente_ml": 234}, 66)
        self.assertEqual(r["evolucao"], "Noradrenalina: 16 mg/250 ml (64 mcg/ml), sem vazão na folha")

    def test_vazao_sai_da_serie_do_balanco(self):
        ganhos = [{"nome": "dieta SNE", "serie": {"07": 40}}, {"nome": "Nora", "serie": {"07": 3, "16": 2}}]
        r = bic.linha({"droga": "noradrenalina", "ampolas": 4, "diluente_ml": 234}, 66, ganhos)
        self.assertIn(", 3 => 2 ml/h", r["evolucao"])

    def test_acima_do_teto_e_alerta(self):
        # 70 ml/h x 64 mcg/ml / 66 kg / 60 = 1,13 mcg/kg/min; teto 1 (definido pelo Dr. no app)
        r = bic.linha({"droga": "noradrenalina", "ampolas": 4, "diluente_ml": 234, "ml_h": 70}, 66)
        self.assertIn("(1,13 mcg/kg/min)", r["evolucao"])
        self.assertTrue(any(a.startswith("ALERTA:") and "teto" in a for a in r["avisos"]), r["avisos"])

    def test_no_teto_nao_alerta(self):
        r = bic.linha({"droga": "noradrenalina", "ampolas": 4, "diluente_ml": 234, "ml_h": 61.875}, 66)  # 1,00
        self.assertFalse(any("teto" in a for a in r["avisos"]), r["avisos"])

    def test_nitroprussiato_acima_de_2_e_alerta_antes_do_teto(self):
        # 1 amp em 250 ml = 200 mcg/ml; 60 ml/h, 75 kg: 200 x 60 / 75 / 60 = 2,67 (teto 10)
        r = bic.linha({"droga": "nitroprussiato", "ampolas": 1, "volume_final_ml": 250, "ml_h": 60}, 75)
        self.assertTrue(any(a.startswith("ALERTA:") and "cianeto" in a for a in r["avisos"]), r["avisos"])

    def test_vasopressina_resgate_e_teto(self):
        # 0,4 UI/ml: 7,5 ml/h = 0,05 UI/min (resgate, só aviso); 12 ml/h = 0,08 UI/min (teto 0,07: ALERTA)
        resgate = bic.linha({"droga": "vasopressina", "ampolas": 2, "volume_final_ml": 100, "ml_h": 7.5}, None)
        teto = bic.linha({"droga": "vasopressina", "ampolas": 2, "volume_final_ml": 100, "ml_h": 12}, None)
        self.assertTrue(any("resgate" in a and not a.startswith("ALERTA") for a in resgate["avisos"]), resgate)
        self.assertTrue(any(a.startswith("ALERTA:") and "teto" in a for a in teto["avisos"]), teto)

    def test_diluicao_incompleta_nao_inventa_dose(self):
        r = bic.linha({"droga": "noradrenalina", "ampolas": 4, "ml_h": 3}, 66)
        self.assertIsNone(r["evolucao"])
        self.assertTrue(any("diluição incompleta" in a for a in r["avisos"]), r["avisos"])

    def test_apresentacao_diferente(self):
        # midazolam 15 mg/3 ml: 10 amp + 120 ml = 150 mg / 150 ml = 1 mg/ml
        d = bic.achar("midazolam")
        self.assertAlmostEqual(bic.concentracao(d, 10, diluente_ml=120, mg_por_ampola=15, ml_por_ampola=3), 1)

    def test_ml_h_diferente_da_folha_avisa(self):
        ganhos = [{"nome": "noradrenalina", "serie": {"07": 3, "16": 2}}]
        igual = bic.linha({"droga": "noradrenalina", "ampolas": 4, "diluente_ml": 234, "ml_h": {"07": 3, "16": 2}},
                          66, ganhos)
        difere = bic.linha({"droga": "noradrenalina", "ampolas": 4, "diluente_ml": 234, "ml_h": 5}, 66, ganhos)
        self.assertEqual(igual["avisos"], [])
        self.assertIn(", 5 ml/h", difere["evolucao"])  # vale o `ml_h`, mas o Conferir mostra a folha
        self.assertTrue(any("3 => 2" in a and "balanço" in a for a in difere["avisos"]), difere["avisos"])

    def test_item_estranho_no_balanco_nao_derruba(self):
        r = bic.linha({"droga": "noradrenalina", "ampolas": 4, "diluente_ml": 234}, 66,
                      ["lixo", {"nome": "nora", "serie": {"07": 3}}])
        self.assertIn(", 3 ml/h", r["evolucao"])


class Arredondamento(unittest.TestCase):
    def test_meio_para_cima_como_o_app(self):
        self.assertEqual(bic.fmt(0.125, 2), "0,13")   # Python round() daria 0,12
        self.assertEqual(bic.fmt(4000, 2), "4.000")
        self.assertEqual(bic.fmt(2.5, 1), "2,5")


if __name__ == "__main__":
    unittest.main()
