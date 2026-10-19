# -*- coding: utf-8 -*-
"""Testes do gerador/validar.py. Rodar: python3 -m unittest discover -s tests"""
import copy
import json
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "gerador"))
import validar as V  # noqa: E402

EXEMPLO = json.loads((RAIZ / "gerador" / "exemplo" / "plantao-exemplo.json").read_text(encoding="utf-8"))


def com(mudar):
    dados = copy.deepcopy(EXEMPLO)
    mudar(dados["leitos"][0], dados)
    return V.validar(dados)


class Validar(unittest.TestCase):
    def test_exemplo_passa_limpo(self):
        self.assertEqual(V.validar(EXEMPLO), ([], []))

    def test_campo_obrigatorio(self):
        erros, _ = com(lambda l, d: (l["ficha"].pop("dx"), d["meta"].pop("data_prescricao")))
        self.assertIn("L99: falta `ficha.dx`", erros)
        self.assertIn("meta: falta `data_prescricao`", erros)

    def test_item_de_balanco_desconhecido_e_erro(self):
        erros, _ = com(lambda l, d: l["ganhos"].append({"nome": "xpto", "ml": 300}))
        self.assertTrue(any("\"xpto\" fora do dicionário" in e for e in erros))

    def test_revisar_e_erro(self):
        erros, _ = com(lambda l, d: l["terapias"].append("CV: nora 5 ml/h (revisar)"))
        self.assertTrue(any("(revisar)" in e for e in erros))

    def test_avisos(self):
        def mudar(l, d):
            l["ficha"]["sistemas"].append(["PROFILAXIA", ["Novalgina (dipirona) 1 g EV"]])
            l["ficha"]["sistemas"].append(["OFTALMO", ["Lacrifilm colírio"]])
            l["impressao"].append("IRA ↑")
            l["terapias"].append("ATB: ? 1 g EV")
            l["ficha"]["vigiar"] = ["só uma"]
        _, avisos = com(mudar)
        txt = "\n".join(avisos)
        for trecho in ("PROFILAXIA só tem TEV e LAMG", "classe OFTALMO", "não vai na ficha-cola", "seta",
                       "\"?\" em `terapias`", "1 pendência(s)"):
            self.assertIn(trecho, txt)

    def test_meta_maior_ou_igual_nao_e_seta(self):
        _, avisos = com(lambda l, d: l["impressao"].append("Choque, meta PAM >= 65 atingida"))
        self.assertFalse(any("seta" in a for a in avisos))

    def test_plano_sem_profilaxia(self):
        _, avisos = com(lambda l, d: l.__setitem__("conduta", [c for c in l["conduta"] if "Profilax" not in c]))
        self.assertTrue(any("Profilaxias" in a for a in avisos))


if __name__ == "__main__":
    unittest.main()
