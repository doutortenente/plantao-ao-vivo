# -*- coding: utf-8 -*-
"""Prescrição na ficha-cola (21-22/11/2026): PROFILAXIA = TEV + LAMG; ACM (a princípio suspenso) na coluna 3;
a prescrição inteira, um item por linha. Rodar: python3 -m unittest discover -s tests"""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "gerador"))
import ficha_cola  # noqa: E402
from docx import Document  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402

QN_T = qn("w:t")

EXEMPLO = json.loads((RAIZ / "gerador" / "exemplo" / "plantao-exemplo.json").read_text(encoding="utf-8"))


class LamgEmProfilaxia(unittest.TestCase):
    def test_ibp_sai_do_tgi_e_vai_para_profilaxia(self):
        sis = [["TGI", ["Pantozol (pantoprazol) 40 mg EV 1x/dia", "Bromoprida 10 mg EV 8/8 h"]],
               ["PROFILAXIA", ["Clexane (enoxaparina) 40 mg SC 1x/dia"]], ["SN", ["Zofran 8 mg EV até 8/8 h"]]]
        out = ficha_cola.profilaxia_com_lamg(sis)
        self.assertEqual(out[0], ["TGI", ["Bromoprida 10 mg EV 8/8 h"]])
        self.assertEqual(out[1], ["PROFILAXIA", ["Clexane (enoxaparina) 40 mg SC 1x/dia",
                                                 "Pantozol (pantoprazol) 40 mg EV 1x/dia"]])

    def test_sem_profilaxia_cria_antes_do_sn_e_do_acm(self):
        sis = [["TGI", ["Omeprazol 40 mg EV jejum"]], ["SN", ["Zofran 8 mg EV"]], ["ACM", ["Pantozol 40 mg EV"]]]
        out = ficha_cola.profilaxia_com_lamg(sis)
        self.assertEqual([r for r, _ in out], ["PROFILAXIA", "SN", "ACM"])
        self.assertEqual(out[2], ["ACM", ["Pantozol 40 mg EV"]])  # o ACM fica onde está


class AcmNaColuna3(unittest.TestCase):
    def colunas(self, variante=None):
        p = copy.deepcopy(EXEMPLO)
        f = p["leitos"][0]["ficha"]
        f["sistemas"] = [x for x in f["sistemas"] if x[0].upper() not in ("SN", "ACM")]
        f["sistemas"] += [["SN", ["Zofran (ondansetrona) 8 mg EV até 8/8 h"]],
                          ["ACM", ["Xarelto (rivaroxabana) 20 mg VO", "Comfeel TOP"]]]
        pl, _ = ficha_cola.motor.preparar(p)
        with tempfile.TemporaryDirectory() as tmp:
            cola = Path(tmp) / "cola.docx"
            cfg = {pl["leitos"][0]["leito"]: (6, ficha_cola.N_INTER, 10, False) + ((variante,) if variante else ())}
            ficha_cola.gerar(pl, cola, cfg)
            doc = Document(str(cola))
        corpo = next(t for t in doc.tables
                     if len(t.rows[0].cells) == 3 and "PRESCRIÇÃO" in t.rows[0].cells[1].text)
        # o texto inclui as tabelas aninhadas da célula (o bloco da prescrição é uma grade dentro da coluna)
        return [" ".join(t.text or "" for t in c._tc.iter(QN_T)) for c in corpo.rows[0].cells]

    def test_acm_vai_para_a_coluna_3_e_o_sn_fica(self):
        _, rx, acao = self.colunas()
        self.assertIn("a princípio suspenso", acao)
        self.assertIn("Xarelto", acao)
        self.assertNotIn("Xarelto", rx)
        self.assertIn("Comfeel", acao)  # pele também vai (22/11/2026: a prescrição inteira)
        self.assertIn("Zofran", rx)
        self.assertNotIn("SE NECESSÁRIO", acao)

    def test_variante_sn_lado_leva_o_sn(self):
        _, rx, acao = self.colunas({"sn_lado": True})
        self.assertIn("SE NECESSÁRIO", acao)
        self.assertIn("Zofran", acao)
        self.assertNotIn("Zofran", rx)


if __name__ == "__main__":
    unittest.main()
