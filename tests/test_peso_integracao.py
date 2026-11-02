# -*- coding: utf-8 -*-
"""Peso no plantão de ponta a ponta: motor (evolução), ficha-cola, validar e checagens.
Rodar: python3 -m unittest discover -s tests

Caso-base: Nair, leito 11, noturno de 31/10/2026 (dados reais do plantão, sem identificação). Valores esperados
feitos à mão: noradrenalina 4 amp + 234 ml = 64 mcg/ml; 3 e 2 ml/h em 66 kg = 0,048 e 0,032 mcg/kg/min;
dobutamina 4 amp + 170 ml = 4.000 mcg/ml, 5 ml/h = 5,05 mcg/kg/min; diurese 300 ml em 12 h = 0,38 ml/kg/h (KDIGO 2);
Cockcroft-Gault (140 - 90) x 66 / (72 x 1,5) x 0,85 = 26 ml/min; peso predito 45,5 + 0,91 x 0,6 = 46 kg,
VC 276 - 368 ml."""
import copy
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "gerador"))
sys.path.insert(0, str(RAIZ / "skills" / "sasi-ingest-export" / "scripts"))
import build_passagem as motor  # noqa: E402
import checagens  # noqa: E402
import validar as V  # noqa: E402

META = {"unidade": "UTI 2", "data": "31/10/2026", "turno": "noturno", "janela": "07 - 19 h",
        "recorte": "07 - 19 h", "horas_balanco": 12, "data_prescricao": "31/10"}
HORAS = ["07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18"]
NAIR = {
    "leito": "11", "nome": "Paciente Teste", "idade_sexo": "90F", "dia_uti": "D4 UTI",
    "diagnostico": "AVCi", "alergia": "nega", "dispositivos": "TOT", "dieta": "SNE 40 ml/h",
    "sup_o2": "VM em PCV, PEEP 6, FiO2 30%",
    "peso": {"kg": 66, "altura_cm": 153, "fonte": "EcoTT", "data": "06/12/2025"},
    "vitais": {"PAM": {"07": 81, "09": 89, "19": 95}},
    "ganhos": [{"nome": "dieta SNE", "serie": {h: 40 for h in HORAS}},
               {"nome": "noradrenalina", "serie": {h: (3 if int(h) < 16 else 2) for h in HORAS}},
               {"nome": "dobutamina", "serie": {h: 5 for h in HORAS}}],
    "perdas": [{"nome": "diurese (SVD)", "serie": {"09": 100, "15": 200}}],
    "infusoes_continuas": [{"droga": "Hyponor", "ampolas": 4, "diluente_ml": 234},
                           {"droga": "Dobutrex", "ampolas": 4, "diluente_ml": 170, "ml_h": 5}],
    "laboratorio": ["UR: 75,3 -> 84,4 mg/dl | CR: 1,4 -> 1,5 mg/dl"],
    "ficha": {"infusoes": [["ATB", ["Rocefin (ceftriaxona) 1 g EV 12/12 h => 10-22"]],
                           ["VM", ["PCV   ·   PEEP 6"]]],
              "sistemas": [["PROFILAXIA", ["TEV: Clexane (enoxaparina) 20 mg SC 1x/dia => 17"]]],
              "vigiar": ["a", "b", "c"], "lab": ["Ur 84,4 | Cr 1,5"]},
}

PESO = "Peso: 66 kg (EcoTT, 06/12/2025) | Altura: 153 cm | Peso predito: 46 kg (VC 6 - 8 ml/kg: 276 - 368 ml)"
DEBITO = "Débito urinário: 0,38 ml/kg/h em 12 h [KDIGO 2 pelo débito]"
NORA = "Noradrenalina: 16 mg/250 ml (64 mcg/ml), 3 => 2 ml/h (0,05 => 0,03 mcg/kg/min)"
DOBUTA = "Dobutamina: 1.000 mg/250 ml (4.000 mcg/ml), 5 ml/h (5,05 mcg/kg/min)"
CLCR = "CLCR (Cockcroft-Gault): 26 ml/min"


def leito(mudar=None, meta=None):
    l = copy.deepcopy(NAIR)
    m = copy.deepcopy(META) if meta is None else meta
    if mudar:
        mudar(l, m)
    return l, m


def bloco(l, m):
    r = motor.compute_leito(l, m)
    return r, r["secoes"][0][1], dict(r["secoes"][1:])


def _celulas(tabelas):
    """Texto de cada célula, entrando nas tabelas dentro de células (as grades da ficha)."""
    for t in tabelas:
        for row in t.rows:
            for c in row.cells:
                yield c.text
                yield from _celulas(c.tables)


class Evolucao(unittest.TestCase):
    def test_linhas_calculadas(self):
        r, linhas, sec = bloco(*leito())
        for esperada in (PESO, DEBITO, NORA, DOBUTA):
            self.assertIn(esperada, linhas)
        self.assertEqual(sec["Laboratório:"][-1], CLCR)

    def test_ordem_no_bloco(self):
        _, linhas, _ = bloco(*leito())
        i = {k: next(n for n, x in enumerate(linhas) if x.startswith(k))
             for k in ("Sup O2", "Peso", "Dieta", "Diurese", "Débito", "Noradrenalina", "BH")}
        self.assertTrue(i["Sup O2"] < i["Peso"] < i["Dieta"] < i["Diurese"] < i["Débito"] < i["Noradrenalina"]
                        < i["BH"], i)

    def test_avisos_de_peso_antigo_e_creatinina_subindo(self):
        r, _, _ = bloco(*leito())
        self.assertTrue(any("peso de 06/12/2025 (há 329 dias)" in a for a in r["avisos"]), r["avisos"])
        self.assertTrue(any("creatinina em ascensão" in a for a in r["avisos"]), r["avisos"])

    def test_janela_de_24_h_usa_24_h(self):
        def mudar(l, m):
            for k in ("janela", "recorte", "horas_balanco"):
                m.pop(k)
            l["vitais"] = {"PAM": {"07": 81, "19": 95}}
        _, linhas, _ = bloco(*leito(mudar))
        # 300 / 24 / 66 = 0,19 ml/kg/h: < 0,3 em 24 h
        self.assertIn("Débito urinário: 0,19 ml/kg/h em 24 h [KDIGO 3 pelo débito]", linhas)

    def test_janela_parcial_sem_horas_nao_calcula(self):
        r, linhas, _ = bloco(*leito(lambda l, m: m.pop("horas_balanco")))
        self.assertFalse(any(x.startswith("Débito") for x in linhas))
        self.assertTrue(any("horas_balanco" in a for a in r["avisos"]), r["avisos"])

    def test_diurese_zero_nao_estadia(self):
        r, linhas, _ = bloco(*leito(lambda l, m: l.__setitem__("perdas", [{"nome": "diurese", "serie": {"09": 0}}])))
        self.assertFalse(any(x.startswith("Débito") for x in linhas))
        self.assertTrue(any("diurese 0" in a for a in r["avisos"]), r["avisos"])

    def test_diurese_com_celula_ilegivel_nao_calcula_debito(self):
        # soma subestimada daria KDIGO falso: sem débito, aviso no Conferir
        r, linhas, _ = bloco(*leito(lambda l, m: l["perdas"][0]["serie"].__setitem__("13", "?")))
        self.assertFalse(any(x.startswith("Débito") for x in linhas))
        self.assertTrue(any("ilegível" in a and "débito" in a.lower() for a in r["avisos"]), r["avisos"])

    def test_kdigo_segue_o_numero_mostrado(self):
        # 395,9 / 12 / 66 = 0,4999: mostra 0,50 e não estadia (não sai "0,50 [KDIGO 2]")
        _, linhas, _ = bloco(*leito(lambda l, m: l.__setitem__("perdas", [{"nome": "diurese", "ml": 395.9}])))
        self.assertIn("Débito urinário: 0,50 ml/kg/h em 12 h", linhas)

    def test_em_trs_sem_clcr_e_sem_kdigo(self):
        # em UF/CVVHDF o Cockcroft-Gault não vale para ajustar dose, e TRS já é KDIGO 3
        r, linhas, sec = bloco(*leito(lambda l, m: l["perdas"].append({"nome": "UF (CVVHDF)", "ml": 800})))
        self.assertNotIn(CLCR, sec["Laboratório:"])
        self.assertIn("Débito urinário: 0,38 ml/kg/h em 12 h", linhas)
        self.assertTrue(any("TRS" in a and "Cockcroft" in a for a in r["avisos"]), r["avisos"])

    def test_obesidade_avisa_que_cockcroft_superestima(self):
        r, _, sec = bloco(*leito(lambda l, m: l["peso"].__setitem__("kg", 90)))  # IMC 38
        self.assertTrue(any("IMC" in a and "superestima" in a for a in r["avisos"]), r["avisos"])

    def test_sem_vm_nao_mostra_vc(self):
        _, linhas, _ = bloco(*leito(lambda l, m: l.__setitem__("sup_o2", "AA")))
        self.assertIn("Peso: 66 kg (EcoTT, 06/12/2025) | Altura: 153 cm", linhas)

    def test_sem_peso_nada_por_kg(self):
        r, linhas, sec = bloco(*leito(lambda l, m: l.pop("peso")))
        self.assertFalse(any(x.startswith(("Peso", "Débito")) for x in linhas))
        self.assertIn("Noradrenalina: 16 mg/250 ml (64 mcg/ml), 3 => 2 ml/h", linhas)
        self.assertNotIn(CLCR, sec["Laboratório:"])
        self.assertTrue(any("sem peso" in a for a in r["avisos"]), r["avisos"])

    def test_droga_fora_da_tabela_vira_aviso(self):
        def mudar(l, m):
            l["infusoes_continuas"].append({"droga": "amiodarona", "ampolas": 6, "diluente_ml": 232, "ml_h": 10})
        r, linhas, _ = bloco(*leito(mudar))
        self.assertFalse(any(x.lower().startswith("amiodarona") for x in linhas))
        self.assertTrue(any("amiodarona" in a and "fora da tabela" in a for a in r["avisos"]), r["avisos"])

    def test_teto_sai_como_alerta_no_topo(self):
        def mudar(l, m):
            l["infusoes_continuas"][0]["ml_h"] = 70  # 1,13 mcg/kg/min
        texto, avisos = motor.build({"meta": META, "leitos": [leito(mudar)[0]]})
        self.assertTrue(avisos[0].startswith("L11: ALERTA: Noradrenalina 1,13"), avisos[:2])


class Ficha(unittest.TestCase):
    def test_ficha_mostra_peso_doses_debito_clcr_e_vc(self):
        import ficha_cola
        from docx import Document
        l, m = leito()
        with tempfile.TemporaryDirectory() as tmp:
            cola = Path(tmp) / "cola.docx"
            ficha_cola.gerar({"meta": m, "leitos": [l]}, cola, {})
            paras = [p.text for p in Document(str(cola)).element.body.iter() if hasattr(p, "text") and p.text]
        texto = "\n".join(paras)
        for esperado in ("90F  ·  D4 UTI  ·  66 kg (EcoTT, 06/12/2025)",  # na linha do nome, sem quebrar o canto
                         "Hyponor 16 mg/250 ml  ·  2 ml/h  ·  0,03 mcg/kg/min",
                         "Dobutrex 1.000 mg/250 ml  ·  5 ml/h  ·  5,05 mcg/kg/min",
                         "Débito", "0,38 ml/kg/h em 12 h", "KDIGO 2", "ClCr 26 ml/min (Cockcroft-Gault)",
                         "VC 6 - 8 ml/kg (PP 46 kg): 276 - 368 ml", "Rocefin"):
            self.assertIn(esperado, texto)
        self.assertNotIn("Altura", texto)  # a linha de peso da evolução não vira célula do balanço
        self.assertNotIn("(64 mcg/ml), 3", texto)  # a linha da evolução não vira célula do balanço

    def test_ordem_dva_sedacao_mesmo_com_dva_manual(self):
        import ficha_cola
        l, m = leito()
        l["infusoes_continuas"] = [{"droga": "fentanil", "ampolas": 5, "diluente_ml": 0, "ml_h": 1}]
        l["ficha"]["infusoes"].insert(1, ["DVA", ["Isoproterenol 1 mg/250 ml 5 ml/h"]])
        r = motor.compute_leito(l, m)
        rotulos = [rot for rot, _ in ficha_cola.infusoes_da_ficha(r, l["ficha"])]
        self.assertEqual(rotulos, ["DVA", "SEDAÇÃO", "ATB", "VM"])

    def test_droga_manual_entra_na_mesma_linha_dva(self):
        import ficha_cola
        from docx import Document
        l, m = leito()
        l["ficha"]["infusoes"].insert(0, ["DVA", ["Isoproterenol 1 mg/250 ml 5 ml/h"]])
        with tempfile.TemporaryDirectory() as tmp:
            cola = Path(tmp) / "cola.docx"
            ficha_cola.gerar({"meta": m, "leitos": [l]}, cola, {})
            celulas = list(_celulas(Document(str(cola)).tables))
        self.assertEqual(sum(1 for c in celulas if c == "DVA"), 1, celulas)  # uma linha DVA só
        dva = next(c for c in celulas if "Isoproterenol" in c)
        self.assertLess(dva.index("Hyponor"), dva.index("Isoproterenol"))  # calculadas primeiro


class Validar(unittest.TestCase):
    def plantao(self, mudar=None):
        l, m = leito(mudar)
        return {"meta": m, "leitos": [l]}

    def erros(self, mudar):
        return V.validar(self.plantao(mudar))[0]

    def test_nair_passa(self):
        self.assertEqual(V.validar(self.plantao())[0], [])

    def test_peso_sem_fonte_ou_fora_de_faixa(self):
        casos = [
            ("fonte", lambda l, m: l["peso"].pop("fonte")),
            ("fonte", lambda l, m: l["peso"].__setitem__("fonte", "?")),  # fonte em dúvida não é fonte
            ("data", lambda l, m: l["peso"].__setitem__("data", "06/12")),
            ("depois do plantão", lambda l, m: l["peso"].__setitem__("data", "01/11/2026")),
            ("kg", lambda l, m: l["peso"].__setitem__("kg", 500)),
            ("altura", lambda l, m: l["peso"].__setitem__("altura_cm", 300)),
        ]
        for n, (trecho, mudar) in enumerate(casos):
            with self.subTest(n=n, trecho=trecho):
                e = self.erros(mudar)
                self.assertTrue(any("`peso`" in x and trecho in x for x in e), e)

    def test_horas_balanco(self):
        e = self.erros(lambda l, m: m.__setitem__("horas_balanco", 30))
        self.assertTrue(any("horas_balanco" in x for x in e), e)

    def test_infusoes_continuas(self):
        casos = {
            "fora da tabela": lambda l, m: l["infusoes_continuas"][0].__setitem__("droga", "amiodarona"),
            "ampolas": lambda l, m: l["infusoes_continuas"][0].__setitem__("ampolas", 0),
            "diluente_ml ou volume_final_ml": lambda l, m: l["infusoes_continuas"][0].pop("diluente_ml"),
            "um dos dois": lambda l, m: l["infusoes_continuas"][0].__setitem__("volume_final_ml", 250),
            "menor que o das ampolas": lambda l, m: (l["infusoes_continuas"][0].pop("diluente_ml"),
                                                     l["infusoes_continuas"][0].__setitem__("volume_final_ml", 10)),
            "ml_h": lambda l, m: l["infusoes_continuas"][1].__setitem__("ml_h", -5),
            "hora": lambda l, m: l["infusoes_continuas"][1].__setitem__("ml_h", {"x": 5}),
        }
        for trecho, mudar in casos.items():
            with self.subTest(trecho):
                e = self.erros(mudar)
                self.assertTrue(any("infusoes_continuas" in x and trecho in x for x in e), e)

    def test_linha_manual_de_dva_com_infusoes_continuas_e_erro(self):
        def mudar(l, m):
            l["ficha"]["infusoes"].insert(0, ["DVA", ["Noradrenalina 16 mg/250 ml 3 ml/h"]])
        e = self.erros(mudar)
        self.assertTrue(any("DVA" in x and "infusoes_continuas" in x for x in e), e)

    def test_droga_fora_da_tabela_na_linha_dva_pode(self):
        # isoproterenol não está nas calculadoras: fica manual na mesma linha DVA, sem erro
        e = self.erros(lambda l, m: l["ficha"]["infusoes"].insert(0, ["DVA", ["Isoproterenol 1 mg/250 ml 5 ml/h"]]))
        self.assertEqual(e, [])

    def test_droga_da_tabela_escrita_a_mao_vira_aviso(self):
        def mudar(l, m):
            l.pop("infusoes_continuas")
            l["ficha"]["infusoes"].insert(0, ["DVA", ["Hyponor 16 mg + SG 5% 234 ml 3 ml/h"]])
        erros, avisos = V.validar(self.plantao(mudar))
        self.assertEqual(erros, [])
        self.assertTrue(any("noradrenalina" in a.lower() and "infusoes_continuas" in a for a in avisos), avisos)

    def test_outros_balanco_repetindo_infusao_e_erro(self):
        e = self.erros(lambda l, m: l.__setitem__("outros_balanco", ["Noradrenalina: 3 -> 2 ml/h"]))
        self.assertTrue(any("outros_balanco" in x and "infusoes_continuas" in x for x in e), e)


class Checagens(unittest.TestCase):
    def test_alergia_a_opioide_e_fentanil_em_bic(self):
        l, _ = leito()
        l["alergia"] = "opioides"
        l["infusoes_continuas"].append({"droga": "fentanil", "ampolas": 5, "diluente_ml": 0, "ml_h": 1})
        self.assertTrue(any("alergia" in a and "fentanil" in a for a in checagens.checar(l)))


class FlagNaEvolucao(unittest.TestCase):
    def test_kdigo_em_negrito(self):
        import gerar_docx
        from docx import Document
        l, m = leito()
        with tempfile.TemporaryDirectory() as tmp:
            evo = Path(tmp) / "evo.docx"
            gerar_docx.gerar_evolucoes({"meta": m, "leitos": [l]}, evo)
            runs = [r for p in Document(str(evo)).paragraphs for r in p.runs]
        kdigo = [r for r in runs if "KDIGO 2 pelo débito" in r.text]
        self.assertTrue(kdigo and all(r.bold for r in kdigo), [(r.text, r.bold) for r in kdigo])


if __name__ == "__main__":
    unittest.main()
