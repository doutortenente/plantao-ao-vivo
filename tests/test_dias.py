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


def exemplo(mudar=None, data=None):
    dados = json.loads((RAIZ / "gerador" / "exemplo" / "plantao-exemplo.json").read_text(encoding="utf-8"))
    if data:
        dados["meta"]["data"] = data
    if mudar:
        mudar(dados["leitos"][0])
    return dados


class RevisaoDe19Out(unittest.TestCase):
    """Achados da revisão adversarial das etapas 1–8 (19/10/2026)."""

    def test_terapias_em_string_nao_viram_letras(self):
        dados = exemplo(lambda l: l.__setitem__("terapias", "CV: Carvedilol.\nATB: Meronem (D?, I: 30/12)."))
        prep, _ = m.preparar(dados)
        self.assertEqual(prep["leitos"][0]["terapias"], ["CV: Carvedilol.", "ATB: Meronem (D2, I: 30/12)."])
        self.assertIn("Terapias vigentes:\nCV: Carvedilol.\nATB: Meronem (D2, I: 30/12).", m.build(dados)[0])

    def test_atb_suspenso_nao_e_recontado(self):
        def mudar(l):
            l["terapias"] = ["Suspenso: Azitromicina 500 mg EV (D5, I: 12/10) em 17/10."]
            l["ficha"]["sistemas"] = [["SUSPENSOS", ["Azitromicina 500 mg EV (D5, I: 12/10)"]]]
        prep, avisos = m.preparar(exemplo(mudar, "19/10/2026"))
        self.assertIn("(D5, I: 12/10)", prep["leitos"][0]["terapias"][0])
        self.assertIn("(D5, I: 12/10)", prep["leitos"][0]["ficha"]["sistemas"][0][1][0])
        self.assertFalse(any("ATB: estava" in a for a in avisos), avisos)

    def test_d_vale_em_todos_os_textos_e_d_solto_divergente_avisa(self):
        def mudar(l):
            l["conduta"][1] = "- Mantido Tazocin (D3) + Azitromicina (D?, I: 30/12); hemoculturas."
            l["ficha"]["vigiar"][0] = "Tazocin (D3, I: 30/12): completar 7 dias"
        prep, avisos = m.preparar(exemplo(mudar))
        self.assertIn("Azitromicina (D2, I: 30/12)", prep["leitos"][0]["conduta"][1])
        self.assertEqual(prep["leitos"][0]["ficha"]["vigiar"][0], "Tazocin (D2, I: 30/12): completar 7 dias")
        self.assertTrue(any("Tazocin (D3)" in a and "D2" in a for a in avisos), avisos)

    def test_inicio_sem_ano_depois_do_plantao_nao_vira_d364(self):
        txt, av = m.dias_atb("ATB: Meronem (D3, I: 20/10)", dt.date(2026, 10, 19))
        self.assertEqual(txt, "ATB: Meronem (D3, I: 20/10)")
        self.assertTrue(any("conferir a data de início" in a for a in av))

    def test_admissao_implausivel_nao_mexe_no_dia(self):
        for adm, dia in (("20/10/2026", "D1 UTI"), ("25/10/2026", None), ("20/10", None)):
            prep, avisos = m.preparar(exemplo(lambda l, a=adm, d=dia: l.update(admissao_uti=a, dia_uti=d),
                                              "19/10/2026"))
            self.assertEqual(prep["leitos"][0]["dia_uti"], dia, adm)
            self.assertTrue(any("implausível" in a for a in avisos), avisos)

    def test_dia_uti_fora_do_formato_nao_e_reescrito(self):
        prep, avisos = m.preparar(exemplo(lambda l: l.update(admissao_uti="17/10/2026",
                                                             dia_uti="4º dia UTI (DH 10)"), "19/10/2026"))
        self.assertEqual(prep["leitos"][0]["dia_uti"], "4º dia UTI (DH 10)")
        self.assertTrue(any("fora do formato" in a for a in avisos))
        prep, _ = m.preparar(exemplo(lambda l: l.update(admissao_uti="17/10/2026", dia_uti="D10 DH / D4 UTI"),
                                     "19/10/2026"))
        self.assertEqual(prep["leitos"][0]["dia_uti"], "D10 DH / D3 UTI")

    def test_sem_data_do_plantao_o_aviso_diz_isso(self):
        _, avisos = m.preparar(exemplo(lambda l: l.__setitem__("terapias", ["ATB: Tazocin (D?, I: 30/12)"]), "01/01"))
        self.assertTrue(avisos[0].startswith('meta.data "01/01" fora do formato'), avisos)
        self.assertFalse(any("admissao_uti ilegível" in a for a in avisos), avisos)
        self.assertTrue(any('"D?" não calculado' in a for a in avisos), avisos)

    def test_d_interrogacao_sem_inicio_vai_para_o_conferir(self):
        _, avisos = m.preparar(exemplo(lambda l: l.__setitem__("terapias", ["ATB: Meronem 1 g EV 8/8h (D?)"])))
        self.assertTrue(any('"D?" sem data de início' in a for a in avisos), avisos)


class RevisaoDe21Out(unittest.TestCase):
    """Achados da revisão adversarial final (21/10/2026)."""

    def test_forma_farmaceutica_suspensao_tem_o_d_contado(self):
        txt, _ = m.dias_atb("ATB: Bactrim suspensão oral 20 ml (I: 30/12)", DIA)
        self.assertEqual(txt, "ATB: Bactrim suspensão oral 20 ml (D2, I: 30/12)")

    def test_suspensa_so_na_propria_oracao(self):
        txt, _ = m.dias_atb("ATB: Azitromicina (D?, I: 30/12) suspensa; Tazocin (D?, I: 30/12)", DIA)
        self.assertEqual(txt, "ATB: Azitromicina (D?, I: 30/12) suspensa; Tazocin (D2, I: 30/12)")

    def test_suspenso_na_frase_seguinte_nao_trava_o_d(self):
        txt, _ = m.dias_atb("ATB: Meropenem 1 g EV 8/8h (D?, I: 30/12). Azitromicina suspensa ontem.", DIA)
        self.assertIn("Meropenem 1 g EV 8/8h (D2, I: 30/12).", txt)

    def test_d_solto_e_da_droga_da_propria_oracao(self):
        prep, avisos = m.preparar(exemplo(lambda l: l["conduta"].append(
            "- Ceftriaxona (D?, I: 30/12) + Metronidazol (D3)")))
        self.assertIn("Ceftriaxona (D2, I: 30/12) + Metronidazol (D3)", prep["leitos"][0]["conduta"][-1])
        self.assertFalse(any("ceftriaxona" in a.lower() and "D3" in a for a in avisos), avisos)

    def test_item_que_nao_e_texto_passa_para_o_validar(self):
        prep, _ = m.preparar(exemplo(lambda l: l["terapias"].append(123)))
        self.assertEqual(prep["leitos"][0]["terapias"][-1], 123)


if __name__ == "__main__":
    unittest.main()
