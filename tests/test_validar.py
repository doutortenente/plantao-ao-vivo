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
        erros, _ = com(lambda l, d: (l["ficha"].pop("lab"), l.pop("diagnostico"), d["meta"].pop("data_prescricao")))
        self.assertIn("L99: falta `ficha.lab`", erros)
        self.assertIn("L99: falta `diagnostico` (ou `ficha.dx`)", erros)
        self.assertIn("meta: falta `data_prescricao`", erros)

    def test_alergia_divergente_e_erro(self):
        # o exemplo antigo: alergia a dipirona no leito, "nega" na ficha e Novalgina prescrita
        erros, _ = com(lambda l, d: l["ficha"].__setitem__("alergia", "nega"))
        self.assertTrue(any("alergia diverge" in e for e in erros))

    def test_copias_divergentes_sao_aviso(self):
        def mudar(l, d):
            l["ficha"]["dx"] = "Outra coisa"
            l["ficha"]["lab"].append("Hb 12,1")
            l["ficha"]["infusoes"][1] = ["ATB", ["Rocefin (ceftriaxona) 2 g EV 1x/dia (D2, I: 31/12)"]]
        _, avisos = com(mudar)
        txt = "\n".join(avisos)
        self.assertIn("diagnostico diverge", txt)
        self.assertIn("12,1", txt)
        self.assertIn("ATB da ficha (ceftriaxona, rocefin) não bate", txt)

    def test_generico_entre_parenteses_conta_como_mesmo_atb(self):
        _, avisos = com(lambda l, d: l["terapias"].__setitem__(0, "ATB: Piperacilina + tazobactam 4,5 g EV 6/6h; Azitromicina 500 mg."))
        self.assertFalse(any("ATB" in a for a in avisos))

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


class RevisaoDe19Out(unittest.TestCase):
    """Achados da revisão adversarial das etapas 1–8 (19/10/2026)."""

    def test_data_sem_ano_e_erro(self):
        erros, _ = com(lambda l, d: d["meta"].__setitem__("data", "01/01"))
        self.assertTrue(any("`data` tem de ser dd/mm/aaaa" in e for e in erros), erros)

    def test_tipos_errados_sao_erro_e_nao_quebram(self):
        for mudar, trecho in ((lambda l, d: l.__setitem__("diagnostico", ["PAC", "Choque"]), "`diagnostico` tem de ser texto"),
                              (lambda l, d: l.__setitem__("alergia", ["Dipirona"]), "`alergia` tem de ser texto"),
                              (lambda l, d: l.__setitem__("leito", 5), "`leito` tem de ser texto"),
                              (lambda l, d: l["ficha"]["sistemas"].append(["SN", "Zofran 8 mg EV"]), "`ficha.sistemas`"),
                              (lambda l, d: l["ficha"].__setitem__("sistemas", {"TGI": ["x"]}), "`ficha.sistemas`")):
            erros, _ = com(mudar)
            self.assertTrue(any(trecho in e for e in erros), (trecho, erros))

    def test_interrogacao_colada_e_no_cabecalho_avisa(self):
        _, avisos = com(lambda l, d: l["terapias"].append("ATB: Vancomicina 1?00 mg EV 12/12h"))
        self.assertTrue(any("1?00" in a for a in avisos), avisos)
        _, avisos = com(lambda l, d: (l.__setitem__("alergia", "?"), l["ficha"].pop("alergia", None)))
        self.assertTrue(any("`alergia`" in a for a in avisos), avisos)

    def test_revisar_no_rodape_e_no_chat_pode(self):
        erros, _ = com(lambda l, d: (l["avisos"].append("PAS 03 h ilegível (revisar)"),
                                     l.setdefault("alertas", []).append("Alergia (revisar)")))
        self.assertEqual([e for e in erros if "(revisar)" in e], [])


if __name__ == "__main__":
    unittest.main()
